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
// Usage:  dotnet run -- <path to Assembly-CSharp.dll>   ->   JSON on stdout, {"Part": ["Member"]}

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

    private static MetadataReader md;
    private static readonly Dictionary<string, TypeDefinitionHandle> ByFullName = new();

    private static int Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.Error.WriteLine("usage: dump_part_members <Assembly-CSharp.dll>");
            return 2;
        }

        using var stream = File.OpenRead(args[0]);
        using var pe = new PEReader(stream);
        md = pe.GetMetadataReader();

        foreach (var handle in md.TypeDefinitions)
        {
            var td = md.GetTypeDefinition(handle);
            ByFullName[Qualify(md.GetString(td.Namespace), md.GetString(td.Name))] = handle;
        }

        var result = new SortedDictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var handle in md.TypeDefinitions)
        {
            var td = md.GetTypeDefinition(handle);
            if (md.GetString(td.Namespace) != PartNamespace || td.IsNested) continue;
            result[md.GetString(td.Name)] = Settable(handle);
        }

        if (result.Count == 0)
        {
            Console.Error.WriteLine($"error: no types found in {PartNamespace}");
            return 1;
        }

        Console.WriteLine(JsonSerializer.Serialize(result));
        return 0;
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
