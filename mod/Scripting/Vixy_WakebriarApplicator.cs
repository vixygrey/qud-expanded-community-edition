using System;
using XRL.World.Effects;

namespace XRL.World.Parts
{
    /// <summary>
    /// The half of the wakebriar injector that applies <see cref="Vixy_Wakebriar"/> when it is used.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Applicator and effect are separate classes because vanilla separates them</b>, and the
    /// blueprint names only this one. Every vanilla tonic has the pair — <c>Salve_Tonic_Applicator</c>
    /// beside <c>Salve_Tonic</c>, <c>Blaze_Tonic_Applicator</c> beside <c>Blaze_Tonic</c> — because
    /// the part lives on the item and the effect lives on whoever drank it.
    /// </para>
    /// <para>
    /// <b><c>ApplyTonic</c> is a legacy string event, not a pooled one</b>, so this registers by name
    /// and answers in <c>FireEvent</c>. <c>Tonic.HandleEvent(InventoryActionEvent)</c> fires it with
    /// <c>Subject</c>, <c>Actor</c> and <c>Dosage</c>, having already run the overdose save.
    /// </para>
    /// <para>
    /// <b>The duration goes through <c>GetTonicDurationEvent</c> rather than straight onto the
    /// effect</b>, which is how every vanilla applicator does it — that is the seam
    /// <c>CyberneticsSocialCoprocessor</c> and the True Kin bonus arrive through, and writing the
    /// constant directly would quietly opt out of both.
    /// </para>
    /// <para>
    /// <b>Dosage multiplies, as it does for vanilla tonics.</b> A double dose is a longer window and
    /// not a stronger one, because there is nothing here to strengthen: the collapse is either
    /// deferred or it is not.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, one string-event handler, no Harmony and no reflection.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_WakebriarApplicator : IPart
    {
        public override bool SameAs(IPart p)
        {
            return true;
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("ApplyTonic");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "ApplyTonic")
            {
                int dosage = E.GetIntParameter("Dosage");
                if (dosage <= 0)
                {
                    return false;
                }

                GameObject actor = E.GetGameObjectParameter("Actor");
                GameObject subject = E.GetGameObjectParameter("Subject");
                if (subject == null)
                {
                    return false;
                }

                int duration = GetTonicDurationEvent.GetFor(
                    ParentObject, actor, subject, "Wakebriar",
                    Vixy_Wakebriar.BaseDuration * dosage, dosage);

                if (!subject.ApplyEffect(new Vixy_Wakebriar(duration)))
                {
                    return false;
                }

                subject.PlayWorldSound("Sounds/StatusEffects/sfx_statusEffect_positiveVitality");
            }
            return base.FireEvent(E);
        }
    }
}
