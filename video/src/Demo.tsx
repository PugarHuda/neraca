import React from "react";
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import manifest from "../public/audio/manifest.json";
import { captions, type Caption } from "./captions";
import { Terminal } from "./Terminal";

export const FPS = 30;
const TITLE_S = 4;
const TERMINAL_S = 222;
const BROWSER_S = 28;
const CLOSE_S = 6;
export const TOTAL_FRAMES = (TITLE_S + TERMINAL_S + BROWSER_S + CLOSE_S) * FPS;

// The ledger world, carried into the video: paper, ink, one status color.
const PAPER = "#e9eedf";
const INK = "#1b1c17";
const INK2 = "#454a3e";
const RULE = "#b3bda6";
const VERMILION = "#b3301c";
const SANS = '"Source Sans 3", "Segoe UI", system-ui, sans-serif';
const MONO = '"Courier Prime", "Courier New", monospace';

const Card: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: PAPER, color: INK, fontFamily: SANS, justifyContent: "center", alignItems: "center" }}>
    {children}
  </AbsoluteFill>
);

const Title: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const rule = Math.min(1, t / 0.8);
  const op = Math.min(1, Math.max(0, (t - 0.5) / 0.8));
  return (
    <Card>
      <div style={{ width: 1100 }}>
        <div style={{ letterSpacing: "0.22em", fontSize: 30, fontWeight: 600, textTransform: "uppercase" }}>NERACA</div>
        <div style={{ height: 1, background: INK, width: `${rule * 100}%`, margin: "18px 0 28px" }} />
        <div style={{ fontSize: 56, lineHeight: 1.15, opacity: op }}>
          Agents hire each other now.<br />Nothing remembers who burned whom.<br /><i>This bureau does.</i>
        </div>
        <div style={{ marginTop: 34, fontFamily: MONO, fontSize: 22, color: INK2, opacity: op }}>
          Sibyl Labs Hackathon · Base · Virtuals ACP · ERC-8004 · github.com/PugarHuda/neraca<br />terminal act rendered from a real run (video/run_log.py); browser act recorded by Playwright
        </div>
      </div>
    </Card>
  );
};

const Close: React.FC = () => (
  <Card>
    <div style={{ width: 1100 }}>
      <div style={{ fontSize: 44, lineHeight: 1.2 }}>Delete the memory and the bureau does not degrade.<br /><i>It exits.</i></div>
      <div style={{ height: 1, background: INK, margin: "28px 0" }} />
      <div style={{ fontFamily: MONO, fontSize: 24, lineHeight: 1.7, color: INK2 }}>
        github.com/PugarHuda/neraca<br />neraca-psi.vercel.app<br />
        <span style={{ color: VERMILION }}>no memory, no bureau</span>
      </div>
    </div>
  </Card>
);

// Subtitles: word-timed captions from edge-tts, grouped into short lines.
const Subtitles: React.FC<{ lines: Caption[] }> = ({ lines }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const line = lines.find((c) => t >= c.start && t < c.end);
  if (!line) return null;
  return (
    <div
      style={{
        position: "absolute", left: 0, right: 0, bottom: 42, display: "flex", justifyContent: "center",
      }}
    >
      <div
        style={{
          background: PAPER, color: INK, fontFamily: SANS, fontSize: 30, lineHeight: 1.3, padding: "10px 22px",
          maxWidth: 1300, borderTop: `2px solid ${INK}`, borderBottom: `1px solid ${RULE}`, textAlign: "center",
        }}
      >
        {line.text}
      </div>
    </div>
  );
};

const Narration: React.FC<{ segments: { id: string; start: number }[] }> = ({ segments }) => (
  <>
    {segments.map((s) => (
      <Sequence key={s.id} from={Math.round(s.start * FPS)} name={`voice ${s.id}`}>
        <Audio src={staticFile(`audio/${s.id}.mp3`)} />
      </Sequence>
    ))}
  </>
);

export const Demo: React.FC = () => {
  const terminalCaptions = captions(manifest.terminal);
  const browserCaptions = captions(manifest.browser);
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Sequence from={0} durationInFrames={TITLE_S * FPS} name="title">
        <Title />
      </Sequence>
      <Sequence from={TITLE_S * FPS} durationInFrames={TERMINAL_S * FPS} name="terminal">
        <Terminal />
        <Narration segments={manifest.terminal} />
        <Subtitles lines={terminalCaptions} />
      </Sequence>
      <Sequence from={(TITLE_S + TERMINAL_S) * FPS} durationInFrames={BROWSER_S * FPS} name="browser">
        <OffthreadVideo src={staticFile("clips/browser.webm")} muted style={{ width: 1600, height: 900 }} />
        <Narration segments={manifest.browser} />
        <Subtitles lines={browserCaptions} />
      </Sequence>
      <Sequence from={(TITLE_S + TERMINAL_S + BROWSER_S) * FPS} durationInFrames={CLOSE_S * FPS} name="close">
        <Close />
      </Sequence>
    </AbsoluteFill>
  );
};
