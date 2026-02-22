import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const CoverageGauge: React.FC<{
  from: number;
  to: number;
  delay?: number;
}> = ({ from, to, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({ frame: frame - delay, fps, config: { damping: 20, mass: 1 } });
  const currentValue = interpolate(progress, [0, 1], [from, to]);
  const angle = interpolate(currentValue, [0, 100], [-180, 0]);

  const r = 120;
  const cx = 150;
  const cy = 150;

  const endAngle = (angle * Math.PI) / 180;
  const startAngle = Math.PI;
  const x1 = cx + r * Math.cos(startAngle);
  const y1 = cy + r * Math.sin(startAngle);
  const x2 = cx + r * Math.cos(Math.PI + endAngle);
  const y2 = cy + r * Math.sin(Math.PI + endAngle);
  const largeArc = currentValue > 50 ? 1 : 0;

  return (
    <div style={{ textAlign: "center" }}>
      <svg width={300} height={180} viewBox="0 0 300 180">
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 1 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={THEME.border}
          strokeWidth={16}
          strokeLinecap="round"
        />
        <path
          d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
          fill="none"
          stroke={currentValue > 80 ? THEME.underutilized : currentValue > 50 ? THEME.balanced : THEME.overloaded}
          strokeWidth={16}
          strokeLinecap="round"
        />
        <text
          x={cx}
          y={cy - 10}
          textAnchor="middle"
          fill={THEME.textPrimary}
          fontSize={48}
          fontFamily={FONTS.display}
          fontWeight={700}
        >
          {Math.round(currentValue)}%
        </text>
        <text
          x={cx}
          y={cy + 20}
          textAnchor="middle"
          fill={THEME.textSecondary}
          fontSize={16}
          fontFamily={FONTS.body}
        >
          Network Coverage
        </text>
      </svg>
    </div>
  );
};
