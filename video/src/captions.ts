// Turns edge-tts word boundaries into caption lines of a readable length.
// Each segment's json is bundled at build time; starts come from the manifest.
export type Caption = { start: number; end: number; text: string };

type Word = { t: number; d: number; w: string };
type Segment = { text: string; words: Word[] };

const files: Record<string, Segment> = {
  t01: require("../public/audio/t01.json"),
  t02: require("../public/audio/t02.json"),
  t03: require("../public/audio/t03.json"),
  t04: require("../public/audio/t04.json"),
  t05: require("../public/audio/t05.json"),
  t06: require("../public/audio/t06.json"),
  t07: require("../public/audio/t07.json"),
  t08: require("../public/audio/t08.json"),
  t09: require("../public/audio/t09.json"),
  t10: require("../public/audio/t10.json"),
  b01: require("../public/audio/b01.json"),
  b02: require("../public/audio/b02.json"),
};

const MAX_WORDS = 9;

export function captions(segments: { id: string; start: number }[]): Caption[] {
  const out: Caption[] = [];
  for (const seg of segments) {
    const { words } = files[seg.id];
    let chunk: Word[] = [];
    const flush = () => {
      if (!chunk.length) return;
      const first = chunk[0];
      const last = chunk[chunk.length - 1];
      out.push({
        start: seg.start + first.t,
        end: seg.start + last.t + last.d + 0.25,
        text: chunk.map((w) => w.w).join(" "),
      });
      chunk = [];
    };
    for (const w of words) {
      chunk.push(w);
      const endsSentence = /[.!?:]$/.test(w.w);
      if (chunk.length >= MAX_WORDS || endsSentence) flush();
    }
    flush();
  }
  return out;
}
