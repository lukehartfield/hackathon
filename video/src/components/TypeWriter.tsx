import { useCurrentFrame } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const TypeWriter: React.FC<{
  text: string;
  delay?: number;
  charsPerFrame?: number;
  fontSize?: number;
  style?: React.CSSProperties;
}> = ({ text, delay = 0, charsPerFrame = 0.8, fontSize = 20, style }) => {
  const frame = useCurrentFrame();
  const elapsed = Math.max(0, frame - delay);
  const charCount = Math.min(text.length, Math.floor(elapsed * charsPerFrame));

  return (
    <div
      style={{
        fontFamily: FONTS.body,
        fontSize,
        color: THEME.textPrimary,
        lineHeight: 1.6,
        whiteSpace: "pre-wrap",
        ...style,
      }}
    >
      {text.slice(0, charCount)}
      {charCount < text.length && (
        <span style={{ opacity: Math.sin(frame * 0.3) > 0 ? 1 : 0, color: THEME.accent }}>|</span>
      )}
    </div>
  );
};
