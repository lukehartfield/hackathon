import { interpolate, useCurrentFrame, spring, useVideoConfig, staticFile, Img } from "remotion";
import { THEME } from "../lib/theme";
import { MAP_BOUNDS } from "../lib/projections";

export const AustinMap: React.FC<{
  children: React.ReactNode;
  delay?: number;
  showGrid?: boolean;
}> = ({ children, delay = 0, showGrid = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { MAP_X, MAP_Y, MAP_W, MAP_H } = MAP_BOUNDS;

  const enter = spring({ frame: frame - delay, fps, config: { damping: 20, mass: 0.8 } });
  const opacity = interpolate(enter, [0, 1], [0, 1]);

  return (
    <div style={{ opacity, position: "absolute", left: 0, top: 0, width: MAP_W, height: MAP_H }}>
      {/* Real dark map background */}
      <Img
        src={staticFile("austin-map.png")}
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: MAP_W,
          height: MAP_H,
        }}
      />
      {/* SVG overlay for dots and shapes */}
      <svg
        width={MAP_W}
        height={MAP_H}
        viewBox={`${MAP_X} ${MAP_Y} ${MAP_W} ${MAP_H}`}
        style={{ position: "absolute", left: 0, top: 0 }}
      >
        {children}
      </svg>
    </div>
  );
};
