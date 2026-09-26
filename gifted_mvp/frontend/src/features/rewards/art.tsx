/** Engagement artwork: flame, trophy, gift and the badge medallions — original inline SVG
 * in the Gifted palette, drawn after the supplied badge references. */
import type { ReactElement } from "react";
import type { BadgeIcon, BadgeTone } from "../../types/engagement";

type P = { className?: string };

export function FlameIcon({ className = "h-6 w-6" }: P) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <defs>
        <linearGradient id="flameOuter" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0" stopColor="#D8612A" />
          <stop offset="1" stopColor="#F2A541" />
        </linearGradient>
      </defs>
      <path d="M16 3c1 5 7 8 7 15a7 7 0 0 1-14 0c0-4 2-6 3.5-8 .3 2.3 1.4 3.6 2.8 4C15 11 14 7 16 3Z" fill="url(#flameOuter)" />
      <path d="M16 15c.6 2.4 3.5 3.6 3.5 7a3.5 3.5 0 0 1-7 0c0-2 1-3.2 2-4.2.2 1 .8 1.6 1.4 1.8-.3-1.7-.4-3 .1-4.6Z" fill="#FCE3A6" />
    </svg>
  );
}

export function TrophyIcon({ className = "h-6 w-6" }: P) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M8 4h8v5a4 4 0 0 1-8 0Z" />
      <path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7M10 17h4v3h-4Z" />
    </svg>
  );
}

export function GiftIcon({ className = "h-6 w-6" }: P) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M4 10h16v10H4ZM3 7h18v3H3ZM12 7v13" />
      <path d="M12 7c-2-3-6-3-5 0M12 7c2-3 6-3 5 0" />
    </svg>
  );
}

export function MedalIcon({ className = "h-5 w-5" }: P) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden>
      <path d="M8 2h3l1 5-3 1ZM16 2h-3l-1 5 3 1Z" fill="#C9A24B" />
      <circle cx="12" cy="15" r="6.5" fill="#E0B24F" stroke="#B8872F" strokeWidth="1" />
      <path d="m12 11.6 1 2.1 2.3.3-1.7 1.6.4 2.3-2-1.1-2 1.1.4-2.3-1.7-1.6 2.3-.3Z" fill="#FFF6DD" />
    </svg>
  );
}

const TONES: Record<BadgeTone, { face: string; deep: string; icon: string }> = {
  green: { face: "#1F6B50", deep: "#0F3D2E", icon: "#CFE8C4" },
  gold: { face: "#E3A93C", deep: "#B9781E", icon: "#FFF1C9" },
  purple: { face: "#4F46B8", deep: "#2E2A7A", icon: "#E4E1FF" },
  teal: { face: "#1D6660", deep: "#0E3B38", icon: "#E8D9A8" },
};

const ICONS: Record<BadgeIcon, (c: string) => ReactElement> = {
  leaf: (c) => (
    <g>
      <path d="M22 44c0-14 9-22 22-23-1 14-9 22-22 23Z" fill={c} />
      <path d="M23 43 40 26" stroke="rgba(0,0,0,0.18)" strokeWidth="1.6" fill="none" />
    </g>
  ),
  star: (c) => <path d="M32 17l4.4 9.2 10 1.3-7.3 7 1.8 10L32 39.6l-8.9 4.9 1.8-10-7.3-7 10-1.3Z" fill={c} />,
  book: (c) => (
    <g fill={c}>
      <path d="M31 24c-4-3-9-3-13-2v19c4-1 9-1 13 2Z" />
      <path d="M33 24c4-3 9-3 13-2v19c-4-1-9-1-13 2Z" opacity="0.85" />
    </g>
  ),
  compass: (c) => (
    <g>
      <circle cx="32" cy="32" r="12" fill="none" stroke={c} strokeWidth="2.6" />
      <path d="m37 27-3 7-7 3 3-7Z" fill={c} />
    </g>
  ),
  globe: (c) => (
    <g>
      <circle cx="32" cy="32" r="12.5" fill={c} />
      <path d="M24 26c3 1 5 0 7 2s0 5 3 6 1 5 4 5M36 21c-1 3 2 4 4 3" stroke="rgba(0,0,0,0.28)" strokeWidth="2.2" fill="none" strokeLinecap="round" />
    </g>
  ),
  people: (c) => (
    <g fill={c}>
      <circle cx="32" cy="25" r="5" />
      <circle cx="22.5" cy="28" r="3.8" />
      <circle cx="41.5" cy="28" r="3.8" />
      <path d="M23 43c0-6 4-10 9-10s9 4 9 10ZM15 43c0-5 3-8 7-8 1 0 2 .2 3 .6-2 2-3 4.6-3 7.4ZM49 43c0-5-3-8-7-8-1 0-2 .2-3 .6 2 2 3 4.6 3 7.4Z" />
    </g>
  ),
  bulb: (c) => (
    <g fill="none" stroke={c} strokeWidth="2.6" strokeLinecap="round">
      <path d="M26.5 35.5a9 9 0 1 1 11 0c-1.4 1.2-2 2.5-2 4h-7c0-1.5-.6-2.8-2-4Z" />
      <path d="M28.5 43.5h7M29.5 47h5" />
    </g>
  ),
  mountain: (c) => (
    <g fill={c}>
      <path d="M17 44 29 25l6 9 3-4 9 14Z" />
      <path d="M29 25v-8" stroke={c} strokeWidth="1.8" />
      <path d="M29 17h6l-2 2.2 2 2.2h-6Z" />
    </g>
  ),
  passport: (c) => (
    <g>
      <rect x="22" y="18" width="20" height="28" rx="2.5" fill={c} />
      <circle cx="32" cy="30" r="5.5" fill="none" stroke="rgba(0,0,0,0.3)" strokeWidth="1.8" />
      <path d="M26.5 30h11M32 24.5c2.2 3 2.2 8 0 11M32 24.5c-2.2 3-2.2 8 0 11" stroke="rgba(0,0,0,0.3)" strokeWidth="1.4" fill="none" />
    </g>
  ),
};

const HEX = "M32 3 57 17.5v29L32 61 7 46.5v-29Z";
const HEX_INNER = "M32 8.5 52.2 20.2v23.6L32 55.5 11.8 43.8V20.2Z";

/** Hexagon medallion. Locked = warm neutral, never a fake colour state. */
export function BadgeMedallion({ icon, tone, unlocked, className = "h-20 w-20" }: { icon: BadgeIcon; tone: BadgeTone; unlocked: boolean; className?: string }) {
  const t = TONES[tone];
  const id = `${icon}-${tone}-${unlocked ? "on" : "off"}`;
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden>
      <defs>
        <linearGradient id={`rim-${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={unlocked ? "#F4D27A" : "#EFE9E1"} />
          <stop offset="0.5" stopColor={unlocked ? "#C9A24B" : "#DCD3C8"} />
          <stop offset="1" stopColor={unlocked ? "#9E7A2E" : "#CFC5B8"} />
        </linearGradient>
        <linearGradient id={`face-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={unlocked ? t.face : "#ECE6DE"} />
          <stop offset="1" stopColor={unlocked ? t.deep : "#DDD5CA"} />
        </linearGradient>
      </defs>
      <path d={HEX} fill={`url(#rim-${id})`} />
      <path d={HEX_INNER} fill={`url(#face-${id})`} />
      {unlocked && <path d="M32 8.5 52.2 20.2 32 32 11.8 20.2Z" fill="#fff" opacity="0.08" />}
      {ICONS[icon](unlocked ? t.icon : "#B4A898")}
      {unlocked && <path d="M47 38l1 2.6 2.6 1-2.6 1-1 2.6-1-2.6-2.6-1 2.6-1Z" fill="#FBE3A0" />}
    </svg>
  );
}
