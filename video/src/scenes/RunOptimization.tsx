import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { TypeWriter } from "../components/TypeWriter";
import { TextOverlay } from "../components/TextOverlay";

const AI_NARRATIVE = `Austin's EV charging network shows significant pressure across downtown and university corridors, with 31% of stations operating above 150% capacity during peak hours.

Our graph-based analysis identifies 10 high-impact expansion sites concentrated in East Riverside, Mueller, and South Congress — areas where demand growth outpaces current infrastructure by 2.4x.

Deploying these recommended stations would lift network coverage from 67% to 89%, reducing average wait times by an estimated 12 minutes during peak demand windows.`;

export const RunOptimization: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const buttonPress = spring({ frame, fps, config: { damping: 10, mass: 0.3 } });
  const spinnerVisible = frame >= 10 && frame < 90;
  const narrativeStart = 100;

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
          width: 800,
          backgroundColor: THEME.card,
          border: `1px solid ${THEME.border}`,
          borderRadius: 16,
          padding: 48,
          boxShadow: `0 0 60px ${THEME.accent}15`,
        }}
      >
        <div
          style={{
            backgroundColor: frame < 10 ? THEME.accent : `${THEME.accent}40`,
            borderRadius: 12,
            padding: "16px 32px",
            textAlign: "center",
            fontFamily: FONTS.display,
            fontSize: 20,
            color: THEME.bg,
            fontWeight: 700,
            transform: `scale(${frame < 10 ? interpolate(buttonPress, [0, 1], [1, 0.95]) : 0.95})`,
            marginBottom: 32,
          }}
        >
          {spinnerVisible ? "Computing..." : frame < 10 ? "Run Optimization Demo" : "Analysis Complete"}
        </div>

        {spinnerVisible && (
          <div style={{ display: "flex", justifyContent: "center", gap: 8, marginBottom: 24 }}>
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  backgroundColor: THEME.accent,
                  opacity: Math.sin((frame - 10) * 0.15 + i * 2) > 0 ? 1 : 0.3,
                }}
              />
            ))}
          </div>
        )}

        {frame >= narrativeStart && (
          <div>
            <TextOverlay text="AI Insights" fontSize={24} color={THEME.accent} delay={narrativeStart} />
            <div style={{ marginTop: 16 }}>
              <TypeWriter text={AI_NARRATIVE} delay={narrativeStart + 15} charsPerFrame={1.2} fontSize={17} />
            </div>
          </div>
        )}
      </div>

      <div
        style={{
          position: "absolute",
          bottom: 40,
          left: "50%",
          transform: "translateX(-50%)",
          opacity: interpolate(frame, [narrativeStart, narrativeStart + 30], [0, 0.6], { extrapolateRight: "clamp" }),
          fontFamily: FONTS.mono,
          fontSize: 14,
          color: THEME.textMuted,
        }}
      >
        Powered by Groq &middot; LLaMA 3.3 70B
      </div>
    </AbsoluteFill>
  );
};
