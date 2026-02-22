// Austin bounding box with padding
const LAT_MIN = 30.10;
const LAT_MAX = 30.55;
const LNG_MIN = -97.97;
const LNG_MAX = -97.53;

// Map area within the 1920x1080 frame (left 70% like the web app)
const MAP_X = 0;
const MAP_Y = 0;
const MAP_W = 1344; // 70% of 1920
const MAP_H = 1080;

export function projectToScreen(lat: number, lng: number): { x: number; y: number } {
  const xNorm = (lng - LNG_MIN) / (LNG_MAX - LNG_MIN);
  const yNorm = 1 - (lat - LAT_MIN) / (LAT_MAX - LAT_MIN); // flip Y
  return {
    x: MAP_X + xNorm * MAP_W,
    y: MAP_Y + yNorm * MAP_H,
  };
}

export const MAP_BOUNDS = { MAP_X, MAP_Y, MAP_W, MAP_H };
