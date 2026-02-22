import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations, loadClusters } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();
const clusters = loadClusters();

const communityGroups = new Map<number, { x: number; y: number }[]>();
clusters.forEach((c) => {
  const { x, y } = projectToScreen(c.lat, c.lng);
  if (!communityGroups.has(c.community_id)) communityGroups.set(c.community_id, []);
  communityGroups.get(c.community_id)!.push({ x, y });
});

const communityCentroids = Array.from(communityGroups.entries()).map(([id, points]) => ({
  id,
  cx: points.reduce((s, p) => s + p.x, 0) / points.length,
  cy: points.reduce((s, p) => s + p.y, 0) / points.length,
  count: points.length,
}));

export const GraphOptimization: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const clusterOpacity = interpolate(frame, [30, 120], [0, 0.25], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      <AustinMap delay={0}>
        {communityCentroids.map((c) => (
          <circle
            key={`cluster-${c.id}`}
            cx={c.cx}
            cy={c.cy}
            r={Math.max(40, c.count * 4)}
            fill={THEME.cluster}
            opacity={clusterOpacity}
          />
        ))}

        {stations.slice(0, 100).map((s, i) => {
          if (i === 0) return null;
          const prev = stations[i - 1];
          const p1 = projectToScreen(s.lat, s.lng);
          const p2 = projectToScreen(prev.lat, prev.lng);
          const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
          if (dist > 80) return null;
          const lineDelay = 60 + i * 0.5;
          const lineOpacity = interpolate(frame - lineDelay, [0, 30], [0, 0.15], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <line
              key={`line-${i}`}
              x1={p1.x}
              y1={p1.y}
              x2={p2.x}
              y2={p2.y}
              stroke={THEME.accent}
              strokeWidth={0.8}
              opacity={lineOpacity}
            />
          );
        })}

        {stations.map((s) => {
          const { x, y } = projectToScreen(s.lat, s.lng);
          return <StationDot key={s.id} x={x} y={y} status={s.status} radius={2.5} />;
        })}
      </AustinMap>

      <div
        style={{
          position: "absolute", right: 0, top: 0, width: 576, height: 1080,
          display: "flex", flexDirection: "column", justifyContent: "center",
          padding: "0 48px", backgroundColor: `${THEME.bg}e0`,
        }}
      >
        <TextOverlay text="Graph Optimization" fontSize={40} color={THEME.cluster} delay={10} />
        <TextOverlay text="Community Detection + GNN" fontSize={24} color={THEME.textSecondary} delay={40} subtitle style={{ marginTop: 8 }} />

        <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 20 }}>
          <MethodCard icon="G" title="Graph Neural Network" desc="Models station connectivity and demand propagation across the network" delay={70} />
          <MethodCard icon="C" title="Community Detection" desc="Identifies 17 distinct service communities in Austin's charging network" delay={100} />
          <MethodCard icon="O" title="Coverage Optimization" desc="Maximizes marginal coverage gain per new station placement" delay={130} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

const MethodCard: React.FC<{
  icon: string; title: string; desc: string; delay: number;
}> = ({ icon, title, desc, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.5 } });

  return (
    <div
      style={{
        opacity: interpolate(enter, [0, 1], [0, 1]),
        transform: `translateY(${interpolate(enter, [0, 1], [20, 0])}px)`,
        backgroundColor: THEME.card,
        border: `1px solid ${THEME.border}`,
        borderRadius: 12,
        padding: "20px 24px",
        display: "flex",
        gap: 16,
        alignItems: "flex-start",
      }}
    >
      <span style={{ fontSize: 28, fontFamily: FONTS.display, color: THEME.accent, fontWeight: 800, width: 36, textAlign: "center" }}>{icon}</span>
      <div>
        <div style={{ fontSize: 18, fontFamily: FONTS.display, color: THEME.textPrimary, fontWeight: 600 }}>{title}</div>
        <div style={{ fontSize: 14, fontFamily: FONTS.body, color: THEME.textSecondary, marginTop: 4, lineHeight: 1.4 }}>{desc}</div>
      </div>
    </div>
  );
};
