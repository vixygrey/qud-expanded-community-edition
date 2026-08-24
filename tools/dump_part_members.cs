// Dump every member a <part> attribute can land on, for tools/snapshot_qud_api.py.
//
// Qud applies a <part> attribute by name to a member of the backing class. An attribute naming
// nothing is discarded in silence - the part loads, the object is valid, and the setting does
// nothing. Catching that in CI needs the member list, and the member list only exists inside
// Assembly-CSharp.dll.
//
// Reading it is metadata inspection, not decompilation: System.Reflection.Metadata is in-box in
// the .NET SDK, so there is no package to restore, no network, and no ilspycmd. Nothing is
// executed and no game code is loaded - the assembly is read as a file.
//
// Three things a naive field scan gets wrong, and why each is handled here (see issue #151, whose
// prototype produced 29 false positives on exactly these):
//
//   1. Properties. Armor.AV, Description.Short and TinkerItem.Bits are properties with bodies,
//      not fields. A property counts when it has a public instance setter.
//   2. Inherited members. ChargeUse is on IPoweredPart, not on the five parts that set it, so the
//      base chain is walked and flattened at generation time - the validator stays a lookup.
//   3. Generic bases. ModImprovedConfusion extends a constructed generic, which is a
//      TypeSpecification rather than a plain handle. Its blob is decoded far enough to reach the
//      open generic type, where Tier actually lives.
//
// Fields that cannot be assigned are excluded: static, const (Literal) and readonly (InitOnly).
//
// It also emits the type names in XRL.World.PartBuilders. A <part Builder="X"> names one of
// those rather than setting a member, and an X that does not exist fails the same silent way (#168).
//
// And it emits the mutations that cannot level: classes in XRL.World.Parts.Mutation whose
// CanLevel() returns a constant false. A chip granting one of those is the same item at every
// grade, which is #347 - Kindle and Frost Webs shipped three grades each and all six were one
// item. The catalogue XML carries no attribute for this; only the method body knows.
//
// Reading a method body is still metadata, not decompilation. `return false` compiles to two IL
// bytes - ldc.i4.0 (0x16) then ret (0x2A) - so the test is a two-byte comparison against the body
// the assembly already stores. Anything longer is a real implementation and is left alone, which
// is the safe direction: a missed one costs a check that does not fire, never a false failure.
//
// Usage:  dotnet run -- <path to Assembly-CSharp.dll>
//         -> JSON on stdout: {"members": {"Part": ["Member"]}, "part_builders": ["Name"],
//                             "non_leveling_mutations": ["Class"]}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Text.Json;

internal static class DumpPartMembers
{
    // Parts resolve from this namespace exactly, matching PART_NAMESPACE in snapshot_qud_api.py.
    private const string PartNamespace = "XRL.World.Parts";

    // Where a <part Builder="…"> value resolves. Exactly this namespace, not its children, for
    // the same reason PartNamespace is exact: a wider scope lets a typo land on an unrelated
    // class and pass.
    private const string BuilderNamespace = "XRL.World.PartBuilders";

    // Mutation classes live here. A chip's ModImprovedMutationBase<T> names one of them.
    private const string MutationNamespace = "XRL.World.Parts.Mutation";

    // `return false` as the compiler emits it: ldc.i4.0, ret.
    private static readonly byte[] ReturnsFalse = { 0x16, 0x2A };

    private static MetadataReader md;
    private static PEReader pe;
    private static readonly Dictionary<string, TypeDefinitionHandle> ByFullName = new();

    private static int Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.Error.WriteLine("usage: dump_part_members <Assembly-CSharp.dll>");
            return 2;
        }

        using var stream = File.OpenRead(args[0]);
        using var reader = new PEReader(stream);
        pe = reader;
        md = pe.GetMetadataReader();

        foreach (var handle in md.TypeDefinitions)
        {
            var td = md.GetTypeDefinition(handle);
            ByFullName[Qualify(md.GetString(td.Namespace), md.GetString(td.Name))] = handle;
        }

        var members = new SortedDictionary<string, List<string>>(StringComparer.Ordinal);
        var builders = new SortedSet<string>(StringComparer.Ordinal);
        var unlevellable = new SortedSet<string>(StringComparer.Ordinal);
        foreach (var handle in md.TypeDefinitions)
        {
            var td = md.GetTypeDefinition(handle);
            if (td.IsNested) continue;
            var ns = md.GetString(td.Namespace);
            if (ns == PartNamespace) members[md.GetString(td.Name)] = Settable(handle);
            else if (ns == BuilderNamespace) builders.Add(md.GetString(td.Name));
            else if (ns == MutationNamespace && CannotLevel(handle)) unlevellable.Add(md.GetString(td.Name));
        }

        if (members.Count == 0)
        {
            Console.Error.WriteLine($"error: no types found in {PartNamespace}");
            return 1;
        }
        if (builders.Count == 0)
        {
            Console.Error.WriteLine($"error: no types found in {BuilderNamespace}");
            return 1;
        }

        if (unlevellable.Count == 0)
        {
            Console.Error.WriteLine($"error: no CanLevel() overrides found in {MutationNamespace}");
            return 1;
        }

        Console.WriteLine(JsonSerializer.Serialize(new
        {
            members,
            part_builders = builders.ToList(),
            non_leveling_mutations = unlevellable.ToList(),
        }));
        return 0;
    }

    /// True when the nearest CanLevel() in the type's own chain returns a constant false.
    ///
    /// Walks the base chain because a mutation may inherit the override rather than declare it,
    /// and stops at the first declaration - the nearest one is what runs.
    private static bool CannotLevel(TypeDefinitionHandle start)
    {
        var cursor = start;
        var seen = new HashSet<string>(StringComparer.Ordinal);
        while (true)
        {
            var td = md.GetTypeDefinition(cursor);
            foreach (var handle in td.GetMethods())
            {
                var method = md.GetMethodDefinition(handle);
                if (md.GetString(method.Name) != "CanLevel") continue;
                if (method.RelativeVirtualAddress == 0) return false;
                var il = pe.GetMethodBody(method.RelativeVirtualAddress).GetILBytes();
                return il is not null
                    && il.Length == ReturnsFalse.Length
                    && il[0] == ReturnsFalse[0]
                    && il[1] == ReturnsFalse[1];
            }

            var baseName = ResolveBase(td.BaseType);
            if (baseName is null || !ByFullName.TryGetValue(baseName, out cursor) || !seen.Add(baseName))
                return false;
        }
    }

    /// Every settable member of a type and of everything it inherits from, flattened.
    private static List<string> Settable(TypeDefinitionHandle start)
    {
        var members = new SortedSet<string>(StringComparer.Ordinal);
        var seen = new HashSet<string>(StringComparer.Ordinal);
        var cursor = start;
        while (true)
        {
            var td = md.GetTypeDefinition(cursor);
            foreach (var name in Declared(td)) members.Add(name);

            var baseName = ResolveBase(td.BaseType);
            // Stops at System.Object, at any base outside this assembly, and on a cycle.
            if (baseName is null || !ByFullName.TryGetValue(baseName, out cursor) || !seen.Add(baseName))
                break;
        }
        return members.ToList();
    }

    private static IEnumerable<string> Declared(TypeDefinition td)
    {
        foreach (var handle in td.GetFields())
        {
            var field = md.GetFieldDefinition(handle);
            var flags = field.Attributes;
            if ((flags & FieldAttributes.FieldAccessMask) != FieldAttributes.Public) continue;
            if ((flags & (FieldAttributes.Static | FieldAttributes.Literal | FieldAttributes.InitOnly)) != 0) continue;
            yield return md.GetString(field.Name);
        }

        foreach (var handle in td.GetProperties())
        {
            var property = md.GetPropertyDefinition(handle);
            var setter = property.GetAccessors().Setter;
            if (setter.IsNil) continue;
            var flags = md.GetMethodDefinition(setter).Attributes;
            if ((flags & MethodAttributes.MemberAccessMask) != MethodAttributes.Public) continue;
            if ((flags & MethodAttributes.Static) != 0) continue;
            yield return md.GetString(property.Name);
        }
    }

    /// The full name of a base type, or null where the walk should stop.
    private static string ResolveBase(EntityHandle handle)
    {
        if (handle.IsNil) return null;

        switch (handle.Kind)
        {
            case HandleKind.TypeDefinition:
            {
                var td = md.GetTypeDefinition((TypeDefinitionHandle)handle);
                return Qualify(md.GetString(td.Namespace), md.GetString(td.Name));
            }
            case HandleKind.TypeReference:
            {
                var tr = md.GetTypeReference((TypeReferenceHandle)handle);
                return Qualify(md.GetString(tr.Namespace), md.GetString(tr.Name));
            }
            case HandleKind.TypeSpecification:
            {
                // A constructed generic base. The signature is GENERICINST, then CLASS or
                // VALUETYPE, then the coded token of the open type - which is where the
                // inherited members are declared.
                var spec = md.GetTypeSpecification((TypeSpecificationHandle)handle);
                var blob = md.GetBlobReader(spec.Signature);
                if (blob.ReadSignatureTypeCode() != SignatureTypeCode.GenericTypeInstance) return null;
                blob.ReadSignatureTypeCode();
                return ResolveBase(blob.ReadTypeHandle());
            }
            default:
                return null;
        }
    }

    private static string Qualify(string ns, string name) => ns.Length == 0 ? name : ns + "." + name;
}
