import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();
const congested = [...stations]
  .sort((a, b) => b.utilization - a.utilization)
  .slice(0, 15);

export const Congestion: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const zoomProgress = spring({ frame, fps, config: { damping: 25, mass: 1.5 } });
  const scale = interpolate(zoomProgress, [0, 1], [1, 1.3]);
  const translateX = interpolate(zoomProgress, [0, 1], [0, -100]);
  const translateY = interpolate(zoomProgress, [0, 1], [0, -50]);

  const heatOpacity = interpolate(frame, [30, 120], [0, 0.4], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      <div style={{ transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`, transformOrigin: "center center" }}>
        <AustinMap delay={0}>
          {stations
            .filter((s) => s.status === "overloaded")
            .map((s) => {
              const { x, y } = projectToScreen(s.lat, s.lng);
              return (
                <circle
                  key={`heat-${s.id}`}
                  cx={x}
                  cy={y}
                  r={30}
                  fill={THEME.overloaded}
                  opacity={heatOpacity * 0.5}
                  filter="url(#blur)"
                />
              );
            })}
          <defs>
            <filter id="blur">
              <feGaussianBlur stdDeviation="15" />
            </filter>
          </defs>
          {stations.map((s) => {
            const { x, y } = projectToScreen(s.lat, s.lng);
            return (
              <StationDot
                key={s.id}
                x={x}
                y={y}
                status={s.status}
                radius={3}
                pulse={s.status === "overloaded"}
              />
            );
          })}
        </AustinMap>
      </div>

      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          width: 576,
          height: 1080,
          display: "flex",
          flexDirection: "column",
          padding: "60px 40px",
          backgroundColor: `${THEME.bg}e0`,
        }}
      >
        <TextOverlay text="Congestion Hotspots" fontSize={36} color={THEME.overloaded} delay={10} />
        <TextOverlay text="Critical areas where demand exceeds supply" fontSize={18} color={THEME.textSecondary} delay={30} subtitle style={{ marginTop: 8 }} />

        <div style={{ marginTop: 28, display: "flex", flexDirection: "column", gap: 8 }}>
          {congested.slice(0, 10).map((s, i) => (
            <CongestionRow key={s.id} rank={i + 1} name={s.title || s.town} utilization={Math.round(s.utilization)} delay={50 + i * 10} />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const CongestionRow: React.FC<{
  rank: number; name: string; utilization: number; delay: number;
}> = ({ rank, name, utilization, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.4 } });

  return (
    <div
      style={{
        opacity: interpolate(enter, [0, 1], [0, 1]),
        transform: `translateX(${interpolate(enter, [0, 1], [40, 0])}px)`,
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "8px 12px",
        backgroundColor: `${THEME.card}80`,
        borderRadius: 8,
        borderLeft: `3px solid ${THEME.overloaded}`,
      }}
    >
      <span style={{ fontFamily: FONTS.mono, fontSize: 14, color: THEME.textMuted, width: 24 }}>#{rank}</span>
      <span style={{ fontFamily: FONTS.body, fontSize: 14, color: THEME.textPrimary, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {name}
      </span>
      <span style={{ fontFamily: FONTS.mono, fontSize: 14, color: THEME.overloaded, fontWeight: 700 }}>
        {utilization}%
      </span>
    </div>
  );
};
