/** Journal decoration for My Diary: botanicals, washi tape, ribbon, stickers and mood faces.
 * All original inline SVG in the Gifted palette — decorative only, never data. */
import type { CSSProperties, ReactElement } from "react";
import type { Mood, StickerId } from "../../types/diary";

type P = { className?: string; style?: CSSProperties };

/** A daisy sprig (stem, leaves, three flowers) for page margins. */
export function DaisySprig({ className = "h-56 w-20", style }: P) {
  const daisy = (cx: number, cy: number, r: number) => (
    <g transform={`translate(${cx} ${cy})`}>
      {Array.from({ length: 10 }, (_, i) => (
        <ellipse key={i} rx={r * 0.32} ry={r} transform={`rotate(${i * 36}) translate(0 ${-r * 0.95})`} fill="#FFFDF7" stroke="#E6DDC8" strokeWidth="0.6" />
      ))}
      <circle r={r * 0.55} fill="#E3B64B" />
      <circle r={r * 0.3} fill="#D49B2E" opacity="0.6" />
    </g>
  );
  return (
    <svg viewBox="0 0 80 220" className={className} style={style} aria-hidden>
      <path d="M40 218C38 170 44 120 38 70M39 150c-12-6-18-16-20-30M40 118c10-4 18-14 20-26M38 88c-10-6-14-14-16-22" fill="none" stroke="#5E7D52" strokeWidth="2" strokeLinecap="round" />
      {[
        "M39 150c-14 2-24-6-28-18 12-2 24 4 28 18Z",
        "M40 118c12 0 22-8 26-20-14 0-24 8-26 20Z",
        "M40 185c-12-2-20-12-22-24 12 2 20 10 22 24Z",
        "M41 170c10-4 16-14 16-26-10 4-16 14-16 26Z",
      ].map((d) => (
        <path key={d} d={d} fill="#7C9A6B" stroke="#5E7D52" strokeWidth="0.8" />
      ))}
      {daisy(38, 62, 11)}
      {daisy(20, 110, 8)}
      {daisy(60, 88, 7)}
    </svg>
  );
}

/** A small leafy branch. */
export function LeafBranch({ className = "h-24 w-24", style }: P) {
  return (
    <svg viewBox="0 0 100 100" className={className} style={style} aria-hidden>
      <path d="M12 92C34 70 56 44 88 12" fill="none" stroke="#6B5A3E" strokeWidth="2.2" strokeLinecap="round" />
      {[
        [30, 72, -35], [44, 56, -40], [58, 42, -45], [72, 28, -50], [26, 64, 130], [40, 48, 130], [54, 34, 135],
      ].map(([x, y, r]) => (
        <path key={`${x}-${y}`} d="M0 0c6-10 18-12 26-8-6 10-18 14-26 8Z" transform={`translate(${x} ${y}) rotate(${r})`} fill="#6F8F5E" stroke="#4E6B43" strokeWidth="0.8" />
      ))}
    </svg>
  );
}

/** Line-drawn fern for the right page corner. */
export function FernSketch({ className = "h-20 w-16", style }: P) {
  return (
    <svg viewBox="0 0 60 90" className={className} style={style} fill="none" stroke="#2F6B55" strokeWidth="1.4" strokeLinecap="round" aria-hidden>
      <path d="M14 86C24 60 36 34 52 6" />
      {Array.from({ length: 8 }, (_, i) => {
        const t = i / 8;
        const x = 14 + t * 38;
        const y = 86 - t * 80;
        return <path key={i} d={`M${x} ${y}c-8-2-14-8-16-14M${x} ${y}c8 0 14-4 18-10`} />;
      })}
    </svg>
  );
}

export function Tape({ className = "", tone = "cream", style }: P & { tone?: "cream" | "sage" | "rose" }) {
  const fill = { cream: "rgba(233,221,190,0.85)", sage: "rgba(190,210,185,0.85)", rose: "rgba(240,200,190,0.85)" }[tone];
  return (
    <svg viewBox="0 0 90 28" preserveAspectRatio="none" className={`h-6 w-20 ${className}`} style={style} aria-hidden>
      <path d="M2 4 L6 1 L10 4 L14 1 L18 4 L88 3 L86 8 L89 13 L86 18 L89 23 L86 27 L4 26 L1 21 L4 16 L1 11 L4 7Z" fill={fill} />
    </svg>
  );
}

/** Gold bookmark ribbon hanging from the spine. */
export function Ribbon({ className = "h-20 w-7" }: P) {
  return (
    <svg viewBox="0 0 28 80" className={className} aria-hidden>
      <path d="M4 0h20v72l-10-8-10 8Z" fill="#C9A24B" />
      <path d="M4 0h20v72l-10-8-10 8Z" fill="url(#ribbonShade)" />
      <defs>
        <linearGradient id="ribbonShade" x1="0" x2="1">
          <stop offset="0" stopColor="#000" stopOpacity="0.12" />
          <stop offset="0.5" stopColor="#fff" stopOpacity="0.15" />
          <stop offset="1" stopColor="#000" stopOpacity="0.12" />
        </linearGradient>
      </defs>
    </svg>
  );
}

/* ------------------------------------------------------------------ stickers */

export function Sticker({ id, className = "h-12 w-12", label }: { id: StickerId; className?: string; label?: string }) {
  const outline = { stroke: "#FFFDF7", strokeWidth: 3, strokeLinejoin: "round" as const, paintOrder: "stroke" as const };
  const art: Record<StickerId, ReactElement> = {
    leaf: (
      <g {...outline}>
        <path d="M12 52C12 26 28 12 54 10c0 26-16 42-42 42Z" fill="#5E8C61" />
        <path d="M14 50 44 20" fill="none" stroke="#E9F1E4" strokeWidth="2" />
      </g>
    ),
    flower: (
      <g {...outline}>
        {Array.from({ length: 6 }, (_, i) => (
          <ellipse key={i} cx="32" cy="18" rx="8" ry="12" transform={`rotate(${i * 60} 32 32)`} fill="#F4D7D0" />
        ))}
        <circle cx="32" cy="32" r="8" fill="#E3B64B" />
      </g>
    ),
    star: <path {...outline} d="M32 6l7.6 16.4 17.9 2.1-13.2 12.3 3.5 17.7L32 45.6 16.2 54.5l3.5-17.7L6.5 24.5l17.9-2.1Z" fill="#D9AE4E" />,
    spark: <path {...outline} d="M32 6c2 14 6 18 20 20-14 2-18 6-20 20-2-14-6-18-20-20 14-2 18-6 20-20Z" fill="#1E4636" />,
    heart: <path {...outline} d="M32 54S8 40 8 24c0-8 6-14 13-14 5 0 9 3 11 7 2-4 6-7 11-7 7 0 13 6 13 14 0 16-24 30-24 30Z" fill="#D9776B" />,
    sun: (
      <g {...outline}>
        <circle cx="32" cy="32" r="12" fill="#E8B84F" />
        {Array.from({ length: 8 }, (_, i) => (
          <path key={i} d="M32 8v8" stroke="#E8B84F" strokeWidth="4" strokeLinecap="round" transform={`rotate(${i * 45} 32 32)`} />
        ))}
      </g>
    ),
    sprout: (
      <g {...outline}>
        <path d="M32 56V30" stroke="#5E7D52" strokeWidth="4" strokeLinecap="round" fill="none" />
        <path d="M32 34C32 20 22 14 10 14c0 12 8 20 22 20Z" fill="#7FA36E" />
        <path d="M32 30c0-12 8-18 22-18 0 12-8 18-22 18Z" fill="#5E8C61" />
        <path d="M20 56h24" stroke="#8A6D45" strokeWidth="4" strokeLinecap="round" />
      </g>
    ),
    note_grow: (
      <g>
        <rect x="4" y="12" width="56" height="40" rx="3" fill="#F6E3C8" transform="rotate(-6 32 32)" />
        <path d="M14 30c6-6 10 6 16 0s10 6 16 0" fill="none" stroke="#A9853A" strokeWidth="2" strokeLinecap="round" transform="rotate(-6 32 32)" />
        <path d="M26 44c2-4 6-6 12-6" fill="none" stroke="#1E4636" strokeWidth="2" strokeLinecap="round" transform="rotate(-6 32 32)" />
        <path d="M46 40l2 3 3-1-2 3 2 3-3-1-2 3v-4l-3-1 3-1Z" fill="#C9A24B" />
      </g>
    ),
  };
  return (
    <svg viewBox="0 0 64 64" className={`${className} drop-shadow-[0_2px_2px_rgba(30,70,54,0.18)]`} role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true}>
      {art[id]}
    </svg>
  );
}

/* ------------------------------------------------------------------ moods */

const MOOD_STYLE: Record<Mood, { bg: string; ring: string; face: string }> = {
  very_low: { bg: "#DCE6EE", ring: "#9FB4C6", face: "#5B7489" },
  low: { bg: "#E4EDE6", ring: "#A9BDB0", face: "#5F7A69" },
  neutral: { bg: "#F4EBD6", ring: "#D8C6A0", face: "#8A7447" },
  good: { bg: "#E3EFD9", ring: "#9DC08B", face: "#4E7A45" },
  great: { bg: "#F8E6BF", ring: "#E0B85A", face: "#9A6F17" },
};

export function MoodFace({ mood, className = "h-9 w-9" }: { mood: Mood; className?: string }) {
  const s = MOOD_STYLE[mood];
  const mouth = {
    very_low: "M22 45c4-6 16-6 20 0",
    low: "M23 43c4-3 14-3 18 0",
    neutral: "M23 42h18",
    good: "M22 39c4 6 16 6 20 0",
    great: "M20 37c4 10 20 10 24 0Z",
  }[mood];
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden>
      <circle cx="32" cy="32" r="28" fill={s.bg} stroke={s.ring} strokeWidth="2" />
      <circle cx="24" cy="27" r="3" fill={s.face} />
      <circle cx="40" cy="27" r="3" fill={s.face} />
      <path d={mouth} fill={mood === "great" ? s.face : "none"} stroke={s.face} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
