import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const TextOverlay: React.FC<{
  text: string;
  delay?: number;
  fontSize?: number;
  color?: string;
  style?: React.CSSProperties;
  subtitle?: boolean;
}> = ({ text, delay = 0, fontSize = 32, color = THEME.textPrimary, style, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.5 } });
  const opacity = interpolate(progress, [0, 1], [0, 1]);
  const translateY = interpolate(progress, [0, 1], [30, 0]);

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${translateY}px)`,
        color,
        fontSize,
        fontFamily: subtitle ? FONTS.body : FONTS.display,
        fontWeight: subtitle ? 400 : 700,
        letterSpacing: subtitle ? 0 : "0.02em",
        ...style,
      }}
    >
      {text}
    </div>
  );
};
