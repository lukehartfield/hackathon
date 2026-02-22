import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const StatCard: React.FC<{
  label: string;
  value: number;
  suffix?: string;
  delay?: number;
  color?: string;
}> = ({ label, value, suffix = "", delay = 0, color = THEME.accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.5 } });
  const opacity = interpolate(enter, [0, 1], [0, 1]);
  const scale = interpolate(enter, [0, 1], [0.8, 1]);
  const countTo = Math.round(interpolate(enter, [0, 1], [0, value]));

  return (
    <div
      style={{
        opacity,
        transform: `scale(${scale})`,
        backgroundColor: THEME.card,
        border: `1px solid ${THEME.border}`,
        borderRadius: 12,
        padding: "20px 28px",
        minWidth: 180,
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: 42, fontFamily: FONTS.display, fontWeight: 700, color }}>
        {countTo.toLocaleString()}{suffix}
      </div>
      <div style={{ fontSize: 16, fontFamily: FONTS.body, color: THEME.textSecondary, marginTop: 6 }}>
        {label}
      </div>
    </div>
  );
};
