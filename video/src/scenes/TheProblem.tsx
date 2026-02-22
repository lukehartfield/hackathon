import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();

export const TheProblem: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      <AustinMap delay={15}>
        {stations.map((s, i) => {
          const { x, y } = projectToScreen(s.lat, s.lng);
          const staggerDelay = 20 + Math.floor(i * 0.3);
          return (
            <StationDot
              key={s.id}
              x={x}
              y={y}
              status="balanced"
              delay={staggerDelay}
              colorOverride={THEME.textSecondary}
              radius={2.5}
            />
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
          padding: "0 48px",
          backgroundColor: `${THEME.bg}e0`,
        }}
      >
        <TextOverlay text="684 Stations" fontSize={64} color={THEME.accent} delay={10} />
        <TextOverlay text="Growing Demand" fontSize={48} color={THEME.textPrimary} delay={40} style={{ marginTop: 16 }} />
        <TextOverlay
          text="Where should Austin expand its EV charging network?"
          fontSize={28}
          color={THEME.textSecondary}
          delay={80}
          subtitle
          style={{ marginTop: 32, lineHeight: "1.5" }}
        />
      </div>
    </AbsoluteFill>
  );
};
