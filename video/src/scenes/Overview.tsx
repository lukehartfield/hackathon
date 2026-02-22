import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { StatCard } from "../components/StatCard";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations, computeStats } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();
const stats = computeStats(stations);

export const Overview: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      <AustinMap delay={0}>
        {stations.map((s) => {
          const { x, y } = projectToScreen(s.lat, s.lng);
          return (
            <StationDot key={s.id} x={x} y={y} status={s.status} delay={0} radius={3} />
          );
        })}
      </AustinMap>

      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          width: 576,
          height: 1080,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 40px",
          backgroundColor: `${THEME.bg}e0`,
          gap: 24,
        }}
      >
        <TextOverlay text="Network Overview" fontSize={40} color={THEME.accent} delay={10} />

        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 16 }}>
          <StatCard label="Stations" value={stats.stationCount} delay={30} />
          <StatCard label="Chargers" value={stats.totalChargers} delay={45} />
          <StatCard label="Avg Utilization" value={stats.avgUtilization} suffix="%" delay={60} color={THEME.balanced} />
        </div>

        <div style={{ marginTop: 24 }}>
          <TextOverlay text="Utilization Breakdown" fontSize={20} color={THEME.textSecondary} delay={80} subtitle />
          <div style={{ display: "flex", height: 32, borderRadius: 8, overflow: "hidden", marginTop: 12 }}>
            <BarSegment color={THEME.overloaded} pct={stats.overloadedPct} label={`${stats.overloadedPct}% Overloaded`} delay={90} />
            <BarSegment color={THEME.balanced} pct={stats.balancedPct} label={`${stats.balancedPct}% Balanced`} delay={100} />
            <BarSegment color={THEME.underutilized} pct={stats.underutilizedPct} label={`${stats.underutilizedPct}% Under`} delay={110} />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const BarSegment: React.FC<{
  color: string; pct: number; label: string; delay: number;
}> = ({ color, pct, label, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const grow = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.5 } });

  return (
    <div
      style={{
        width: `${pct * interpolate(grow, [0, 1], [0, 1])}%`,
        backgroundColor: color,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 12,
        fontFamily: "Outfit, sans-serif",
        color: "#fff",
        fontWeight: 600,
        overflow: "hidden",
        whiteSpace: "nowrap",
      }}
    >
      {pct > 15 ? label : ""}
    </div>
  );
};
