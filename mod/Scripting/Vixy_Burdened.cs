using System;

namespace XRL.World.Effects
{
    /// <summary>
    /// One graded burden band. Vanilla has only a cliff — <c>Overburdened</c> at 100% of carry
    /// capacity, which stops you dead — so between 0 and 100% nothing happens at all and the
    /// optimal play is to sit at 99% forever. This fills that space.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Carries no instance state.</b> The band is derived from the wearer's current load every
    /// time it is asked for, so no field of its own is written into the save and the effect can never
    /// disagree with the weight actually being carried. That also satisfies charter rule 5
    /// without needing an exception: <c>serializable-shape</c> has no allowlist, and here it did
    /// not need one — the first draft stored the band and the penalty, and neither had to exist.
    /// </para>
    /// <para>
    /// Deliberately does <em>not</em> touch the cliff. Moving it would mean intercepting
    /// <c>GetMaxCarriedWeightEvent</c>, and that figure is read by seven UI surfaces and by the
    /// Pack Rat mutation, which forces a character to stay above 90% of whatever capacity reports
    /// — inflating it would pin a Pack Rat permanently in the worst band. So vanilla's
    /// <c>Overburdened</c> stays exactly where it is and these bands sit underneath it.
    /// </para>
    /// <para>
    /// Two effects from the original spec are absent because Qud has nowhere to put them. There
    /// is <b>no stealth system</b> in the game — the word does not appear anywhere in the
    /// assembly — and there is no movement-cost hook, so "movement costs double" would have to be
    /// spent through Quickness, which is the penalty this already applies. Listing both would
    /// double-count one mechanism. A fatigue rider waits on the sleep work in #179.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Burdened : IScribedEffect
    {
        public const int None = 0;
        public const int Light = 1;
        public const int Encumbered = 2;
        public const int Heavy = 3;

        public Vixy_Burdened()
        {
            DisplayName = "burdened";
            // No countdown: Effect does not decrement unless UseStandardDurationCountdown is
            // overridden to true, and Vixy_Burden owns removal.
            Duration = 9999;
        }

        /// <summary>Which band a given load percentage falls in.</summary>
        public static int BandFor(int LoadPercent)
        {
            if (LoadPercent >= 90)
            {
                return Heavy;
            }
            if (LoadPercent >= 75)
            {
                return Encumbered;
            }
            if (LoadPercent >= 50)
            {
                return Light;
            }
            return None;
        }

        /// <summary>Carried weight as a percentage of capacity, or 0 when there is no capacity.</summary>
        public static int LoadPercent(GameObject Who)
        {
            if (Who == null)
            {
                return 0;
            }
            int capacity = Who.GetMaxCarriedWeight();
            if (capacity <= 0)
            {
                return 0;
            }
            // Integer arithmetic so the band edges stay exact at 50, 75 and 90.
            return Who.GetCarriedWeight() * 100 / capacity;
        }

        public static int DVFor(int Band)
        {
            switch (Band)
            {
                case Light:
                    return 1;
                case Encumbered:
                    return 2;
                case Heavy:
                    return 4;
                default:
                    return 0;
            }
        }

        /// <summary>
        /// One Quickness per full 10 points of load above 75, and a flat 10 in the heavy band.
        /// </summary>
        /// <remarks>
        /// Over the encumbered band's 15-point span that first rule yields 0 or 1, which is
        /// nearly nothing. It is carried from the original spec on purpose rather than quietly
        /// improved, and it is the first number to revisit once this has been played.
        /// </remarks>
        public static int SpeedFor(int Band, int LoadPercent)
        {
            if (Band >= Heavy)
            {
                return 10;
            }
            if (Band == Encumbered)
            {
                return (LoadPercent - 75) / 10;
            }
            return 0;
        }

        public static string NameFor(int Band)
        {
            switch (Band)
            {
                case Light:
                    return "lightly burdened";
                case Encumbered:
                    return "encumbered";
                case Heavy:
                    return "heavily burdened";
                default:
                    return "burdened";
            }
        }

        private int Band => BandFor(LoadPercent(Object));

        public override int GetEffectType()
        {
            return 33554432;
        }

        public override string GetDetails()
        {
            int load = LoadPercent(Object);
            int band = BandFor(load);
            int speed = SpeedFor(band, load);

            string details = "-" + DVFor(band) + " DV";
            if (speed > 0)
            {
                details = details + ", -" + speed + " Quickness";
            }
            if (band >= Heavy)
            {
                details += ", cannot run";
            }
            return details;
        }

        public override bool Apply(GameObject Object)
        {
            Refresh();
            return true;
        }

        public override void Remove(GameObject Object)
        {
            StatShifter.RemoveStatShifts(Object);
            base.Remove(Object);
        }

        /// <summary>Bring the display name and the stat shifts in line with the current load.</summary>
        public void Refresh()
        {
            GameObject who = Object;
            if (who == null)
            {
                return;
            }

            int load = LoadPercent(who);
            int band = BandFor(load);

            DisplayName = "{{K|" + NameFor(band) + "}}";
            StatShifter.RemoveStatShifts(who);
            StatShifter.SetStatShift(who, "DV", -DVFor(band));

            int speed = SpeedFor(band, load);
            if (speed > 0)
            {
                StatShifter.SetStatShift(who, "Speed", -speed);
            }
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("ApplyRunning");
            base.Register(Object, Registrar);
        }

        /// <summary>
        /// The heavy band cannot break into a run.
        /// </summary>
        /// <remarks>
        /// Vetoes <c>ApplyRunning</c>, which <c>Running.Apply</c> fires and abandons on a false
        /// return. The obvious alternative — refusing <c>CanChangeMovementModeEvent</c> the way
        /// vanilla's <c>Overburdened</c> refuses flight — does not work here: that event's
        /// <c>To</c> carries the movement <em>message name</em>, which is "sprinting" by default
        /// and configurable per <c>Run</c> part, so matching on "Running" would never fire and the
        /// restriction would ship silently inert.
        /// </remarks>
        public override bool FireEvent(Event E)
        {
            if (E.ID == "ApplyRunning" && Band >= Heavy)
            {
                Object.Fail("You are carrying too much to run.");
                return false;
            }
            return base.FireEvent(E);
        }

        /// <summary>
        /// Reads nothing from a save written before 2.8.0, which wrote no field block at all.
        ///
        /// This class has no serialisable state, so "read nothing" is exactly what the old format
        /// meant. Once every save in circulation postdates the change this override can go, and
        /// removing it is the only maintenance it will ever need. See
        /// <c>QudExpandedCE.Vixy_SaveFormat</c> for why one byte is worth an override (#497).
        /// </summary>
        public override void Read(GameObject Basis, SerializationReader Reader)
        {
            if (QudExpandedCE.Vixy_SaveFormat.PredatesNamedFields(Reader))
            {
                return;
            }

            base.Read(Basis, Reader);
        }
    }
}
