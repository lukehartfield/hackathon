import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME } from "../lib/theme";

const STATUS_COLORS = {
  overloaded: THEME.overloaded,
  balanced: THEME.balanced,
  underutilized: THEME.underutilized,
};

export const StationDot: React.FC<{
  x: number;
  y: number;
  status: "overloaded" | "balanced" | "underutilized";
  delay?: number;
  radius?: number;
  colorOverride?: string;
  pulse?: boolean;
}> = ({ x, y, status, delay = 0, radius = 3.5, colorOverride, pulse }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({ frame: frame - delay, fps, config: { damping: 12, mass: 0.3 } });
  const scale = interpolate(enter, [0, 1], [0, 1]);
  const color = colorOverride ?? STATUS_COLORS[status];
  const pulseScale = pulse ? 1 + 0.3 * Math.sin(frame * 0.15) : 1;

  return (
    <circle
      cx={x}
      cy={y}
      r={radius * scale * pulseScale}
      fill={color}
      opacity={interpolate(enter, [0, 1], [0, 0.85])}
    />
  );
};
