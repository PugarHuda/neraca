import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import log from "../public/terminal.json";

// A terminal rendered from a real run (video/run_log.py): commands type out at
// their scheduled second, then their real output prints line by line.
type Ev =
  | { t: number; kind: "say" | "stamp"; text: string }
  | { t: number; kind: "cmd"; text: string; session?: string | null }
  | { t: number; kind: "out"; lines: string[]; exit: number; session?: string | null };

const EVENTS = log as Ev[];
const TYPE_S = 0.8;      // seconds to type a command
const LINE_S = 0.045;    // seconds per output line
const ROWS = 30;
const MONO = '"Cascadia Mono", "Consolas", "Courier New", monospace';

type Row = { text: string; color: string; bold?: boolean };

function rowsAt(t: number): { rows: Row[]; fresh: boolean } {
  const rows: Row[] = [];
  let fresh = false;
  for (const ev of EVENTS) {
    if (ev.t > t) break;
    if ("session" in ev && ev.session === "fresh") fresh = true;
    if (ev.kind === "say") {
      rows.push({ text: "", color: "#9aa48c" });
      rows.push({ text: `# ${ev.text}`, color: "#e6c85a" });
    } else if (ev.kind === "stamp") {
      rows.push({ text: ev.text, color: "#7fcf8a", bold: true });
    } else if (ev.kind === "cmd") {
      const done = Math.min(1, (t - ev.t) / TYPE_S);
      const shown = ev.text.slice(0, Math.ceil(ev.text.length * done));
      rows.push({ text: "", color: "#9aa48c" });
      rows.push({ text: `> ${shown}${done < 1 ? "▌" : ""}`, color: "#8fd3e8" });
    } else if (ev.kind === "out") {
      const n = Math.min(ev.lines.length, Math.floor((t - ev.t) / LINE_S) + 1);
      for (const line of ev.lines.slice(0, n)) {
        const bad = /DECLINE|refus|exit=1|no memory|did not broadcast|REJECTED|memory moved/i.test(line);
        const good = /APPROVE|SUCCESS|passed|journaled|explorer|tx"/i.test(line);
        rows.push({ text: line, color: bad ? "#ef8a7a" : good ? "#bfe3a6" : "#d8dccf" });
      }
    }
  }
  return { rows, fresh };
}

export const Terminal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const { rows, fresh } = rowsAt(t);
  const visible = rows.slice(-ROWS);
  return (
    <AbsoluteFill style={{ background: fresh ? "#0f1a2e" : "#141511", color: "#d8dccf", fontFamily: MONO }}>
      <div
        style={{
          position: "absolute", top: 0, left: 0, right: 0, height: 40, background: "#1f221c",
          borderBottom: "1px solid #3a3d34", display: "flex", alignItems: "center", padding: "0 18px",
          fontSize: 18, letterSpacing: "0.06em", color: "#9aa48c",
        }}
      >
        {fresh ? "NERACA · fresh session (new process)" : "NERACA · demo"}
        <span style={{ marginLeft: "auto", fontSize: 15 }}>rendered from a real run · log in video/public/terminal.json</span>
      </div>
      <div style={{ position: "absolute", top: 52, left: 22, right: 22, bottom: 110, fontSize: 21, lineHeight: "26px", whiteSpace: "pre", overflow: "hidden" }}>
        {visible.map((r, i) => (
          <div key={i} style={{ color: r.color, fontWeight: r.bold ? 700 : 400 }}>{r.text}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
