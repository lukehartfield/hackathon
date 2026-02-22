import { Series } from "remotion";
import { SCENES } from "./lib/theme";
import { TitleCard } from "./scenes/TitleCard";
import { TheProblem } from "./scenes/TheProblem";
import { Overview } from "./scenes/Overview";
import { Congestion } from "./scenes/Congestion";
import { GraphOptimization } from "./scenes/GraphOptimization";
import { ExpansionNodes } from "./scenes/ExpansionNodes";
import { RunOptimization } from "./scenes/RunOptimization";
import { Results } from "./scenes/Results";
import { Closing } from "./scenes/Closing";

export const DemoVideo: React.FC = () => {
  return (
    <Series>
      <Series.Sequence durationInFrames={SCENES.title.duration}>
        <TitleCard />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.problem.duration}>
        <TheProblem />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.overview.duration}>
        <Overview />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.congestion.duration}>
        <Congestion />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.graphOpt.duration}>
        <GraphOptimization />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.expansion.duration}>
        <ExpansionNodes />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.runOpt.duration}>
        <RunOptimization />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.results.duration}>
        <Results />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.closing.duration}>
        <Closing />
      </Series.Sequence>
    </Series>
  );
};
