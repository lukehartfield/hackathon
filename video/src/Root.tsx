import { Composition } from "remotion";
import { loadFont as loadSyne } from "@remotion/google-fonts/Syne";
import { loadFont as loadOutfit } from "@remotion/google-fonts/Outfit";
import { loadFont as loadAzeretMono } from "@remotion/google-fonts/AzeretMono";
import { DemoVideo } from "./Video";

// Load fonts globally
loadSyne();
loadOutfit();
loadAzeretMono();

export const Root: React.FC = () => {
  return (
    <Composition
      id="DemoVideo"
      component={DemoVideo}
      durationInFrames={3600}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
