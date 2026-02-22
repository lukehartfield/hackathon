import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations, loadRecommendations } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();
const recommendations = loadRecommendations().slice(0, 10);

export const ExpansionNodes: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      <AustinMap delay={0}>
        {stations.map((s) => {
          const { x, y } = projectToScreen(s.lat, s.lng);
          return <StationDot key={s.id} x={x} y={y} status={s.status} radius={2} />;
        })}

        {recommendations.map((r, i) => {
          const rPos = projectToScreen(r.lat, r.lng);
          const nearest = stations
            .map((s) => ({ s, dist: Math.hypot(projectToScreen(s.lat, s.lng).x - rPos.x, projectToScreen(s.lat, s.lng).y - rPos.y) }))
            .sort((a, b) => a.dist - b.dist)
            .slice(0, 3);

          const lineDelay = 40 + i * 25;
          const lineOpacity = interpolate(frame - lineDelay, [0, 30], [0, 0.3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

          return nearest.map((n, j) => {
            const sPos = projectToScreen(n.s.lat, n.s.lng);
            return (
              <line
                key={`conn-${i}-${j}`}
                x1={rPos.x}
                y1={rPos.y}
                x2={sPos.x}
                y2={sPos.y}
                stroke={THEME.suggested}
                strokeWidth={1}
                opacity={lineOpacity}
                strokeDasharray="4 4"
              />
            );
          });
        })}

        {recommendations.map((r, i) => {
          const { x, y } = projectToScreen(r.lat, r.lng);
          return (
            <StationDot
              key={`rec-${r.site_id}`}
              x={x}
              y={y}
              status="balanced"
              colorOverride={THEME.suggested}
              delay={30 + i * 25}
              radius={6}
              pulse
            />
          );
        })}
      </AustinMap>

      <div
        style={{
          position: "absolute", right: 0, top: 0, width: 576, height: 1080,
          display: "flex", flexDirection: "column", padding: "60px 40px",
          backgroundColor: `${THEME.bg}e0`,
        }}
      >
        <TextOverlay text="Expansion Sites" fontSize={40} color={THEME.suggested} delay={10} />
        <TextOverlay text="Top 10 optimal new station locations" fontSize={18} color={THEME.textSecondary} delay={30} subtitle style={{ marginTop: 8 }} />

        <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 8 }}>
          {recommendations.map((r, i) => (
            <NodeRow key={r.site_id} rank={r.rank} siteId={r.site_id} weight={r.node_weight} gain={r.marginal_gain} delay={40 + i * 20} />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const NodeRow: React.FC<{
  rank: number; siteId: string; weight: number; gain: number; delay: number;
}> = ({ rank, siteId, weight, gain, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.4 } });

  return (
    <div
      style={{
        opacity: interpolate(enter, [0, 1], [0, 1]),
        transform: `translateX(${interpolate(enter, [0, 1], [40, 0])}px)`,
        display: "flex", alignItems: "center", gap: 12,
        padding: "8px 12px", backgroundColor: `${THEME.card}80`,
        borderRadius: 8, borderLeft: `3px solid ${THEME.suggested}`,
      }}
    >
      <span style={{ fontFamily: FONTS.mono, fontSize: 14, color: THEME.suggested, width: 24, fontWeight: 700 }}>#{rank}</span>
      <span style={{ fontFamily: FONTS.body, fontSize: 14, color: THEME.textPrimary, flex: 1 }}>{siteId}</span>
      <span style={{ fontFamily: FONTS.mono, fontSize: 12, color: THEME.textSecondary }}>+{gain.toFixed(1)}</span>
      <div style={{ width: 60, height: 6, backgroundColor: THEME.border, borderRadius: 3 }}>
        <div style={{ width: `${weight * 100}%`, height: "100%", backgroundColor: THEME.suggested, borderRadius: 3 }} />
      </div>
    </div>
  );
};
