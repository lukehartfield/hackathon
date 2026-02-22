import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { TextOverlay } from "../components/TextOverlay";

const TECH_STACK = [
  { name: "Next.js 14", color: "#ffffff" },
  { name: "Python", color: "#3776AB" },
  { name: "Groq AI", color: "#f55036" },
  { name: "Leaflet", color: "#199900" },
  { name: "GNN", color: THEME.cluster },
  { name: "Open Charge Map", color: THEME.accent },
];

export const Closing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeOut = interpolate(frame, [240, 300], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: THEME.bg,
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeOut,
      }}
    >
      <div
        style={{
          fontSize: 64,
          fontFamily: FONTS.display,
          fontWeight: 800,
          color: THEME.textPrimary,
          textShadow: `0 0 20px ${THEME.accent}, 0 0 40px ${THEME.accent}40`,
        }}
      >
        ChargePilot
      </div>

      <div style={{ display: "flex", gap: 12, marginTop: 40, flexWrap: "wrap", justifyContent: "center", maxWidth: 600 }}>
        {TECH_STACK.map((tech, i) => {
          const enter = spring({ frame: frame - 30 - i * 8, fps, config: { damping: 12, mass: 0.4 } });
          return (
            <div
              key={tech.name}
              style={{
                opacity: interpolate(enter, [0, 1], [0, 1]),
                transform: `scale(${interpolate(enter, [0, 1], [0.5, 1])})`,
                padding: "8px 20px",
                borderRadius: 20,
                border: `1px solid ${tech.color}60`,
                backgroundColor: `${tech.color}15`,
                fontFamily: FONTS.mono,
                fontSize: 14,
                color: tech.color,
              }}
            >
              {tech.name}
            </div>
          );
        })}
      </div>

      <TextOverlay
        text="Built at Hackathon 2026"
        fontSize={28}
        color={THEME.textSecondary}
        delay={80}
        subtitle
        style={{ marginTop: 48 }}
      />

      <div
        style={{
          width: 300,
          height: 2,
          backgroundColor: THEME.accent,
          marginTop: 32,
          opacity: 0.4,
          boxShadow: `0 0 10px ${THEME.accent}`,
        }}
      />
    </AbsoluteFill>
  );
};
