import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { CoverageGauge } from "../components/CoverageGauge";
import { StatCard } from "../components/StatCard";
import { TextOverlay } from "../components/TextOverlay";

export const Results: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const liftSpring = spring({ frame: frame - 120, fps, config: { damping: 12, mass: 0.5 } });
  const liftOpacity = interpolate(liftSpring, [0, 1], [0, 1]);
  const liftScale = interpolate(liftSpring, [0, 1], [0.5, 1]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: THEME.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div style={{ display: "flex", gap: 80, alignItems: "center" }}>
        <div style={{ textAlign: "center" }}>
          <TextOverlay text="Current" fontSize={24} color={THEME.textSecondary} delay={10} />
          <div style={{ marginTop: 16 }}>
            <CoverageGauge from={0} to={67} delay={20} />
          </div>
        </div>

        <div
          style={{
            opacity: liftOpacity,
            transform: `scale(${liftScale})`,
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 72, fontFamily: FONTS.display, fontWeight: 800, color: THEME.underutilized }}>
            +22%
          </div>
          <div style={{ fontSize: 20, fontFamily: FONTS.body, color: THEME.textSecondary, marginTop: 4 }}>
            Coverage Lift
          </div>
        </div>

        <div style={{ textAlign: "center" }}>
          <TextOverlay text="Projected" fontSize={24} color={THEME.accent} delay={60} />
          <div style={{ marginTop: 16 }}>
            <CoverageGauge from={0} to={89} delay={70} />
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 24, marginTop: 80 }}>
        <StatCard label="New Stations" value={10} delay={160} color={THEME.suggested} />
        <StatCard label="Communities Served" value={17} delay={175} color={THEME.cluster} />
        <StatCard label="Avg Wait Reduction" value={12} suffix=" min" delay={190} color={THEME.underutilized} />
      </div>
    </AbsoluteFill>
  );
};
