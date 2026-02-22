import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const TitleCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoSpring = spring({ frame, fps, config: { damping: 12, mass: 0.5 } });
  const taglineSpring = spring({ frame: frame - 30, fps, config: { damping: 15, mass: 0.5 } });
  const subtitleSpring = spring({ frame: frame - 60, fps, config: { damping: 15, mass: 0.5 } });

  const glowIntensity = 20 + 10 * Math.sin(frame * 0.08);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: THEME.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          opacity: interpolate(logoSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(logoSpring, [0, 1], [0.5, 1])})`,
          fontSize: 96,
          fontFamily: FONTS.display,
          fontWeight: 800,
          color: THEME.textPrimary,
          textShadow: `0 0 ${glowIntensity}px ${THEME.accent}, 0 0 ${glowIntensity * 2}px ${THEME.accent}40`,
          letterSpacing: "0.04em",
        }}
      >
        ChargePilot
      </div>

      <div
        style={{
          opacity: interpolate(taglineSpring, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(taglineSpring, [0, 1], [20, 0])}px)`,
          fontSize: 32,
          fontFamily: FONTS.body,
          color: THEME.textSecondary,
          marginTop: 24,
          letterSpacing: "0.08em",
        }}
      >
        AI-Powered EV Charging Network Optimizer
      </div>

      <div
        style={{
          opacity: interpolate(subtitleSpring, [0, 1], [0, 1]),
          fontSize: 24,
          fontFamily: FONTS.body,
          color: THEME.accent,
          marginTop: 16,
          letterSpacing: "0.12em",
          textTransform: "uppercase",
        }}
      >
        Austin, TX
      </div>

      <div
        style={{
          width: interpolate(logoSpring, [0, 1], [0, 400]),
          height: 2,
          backgroundColor: THEME.accent,
          marginTop: 40,
          opacity: 0.5,
          boxShadow: `0 0 10px ${THEME.accent}`,
        }}
      />
    </AbsoluteFill>
  );
};
