/** Stroke icons for Resources / Opportunities / Community (same style as passport/icons). */
type IconProps = { className?: string };

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  viewBox: "0 0 24 24",
  "aria-hidden": true,
};

export const BookmarkIcon = ({ className = "h-5 w-5", filled = false }: IconProps & { filled?: boolean }) => (
  <svg {...base} className={className} fill={filled ? "currentColor" : "none"}>
    <path d="M7 4h10v16l-5-3.5L7 20Z" />
  </svg>
);

export const OpenBookIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M3.5 5.5c3-1 6-.8 8.5 1 2.5-1.8 5.5-2 8.5-1v13c-3-1-6-.8-8.5 1-2.5-1.8-5.5-2-8.5-1Z" />
    <path d="M12 6.5v13" />
  </svg>
);

export const BriefcaseIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className}>
    <rect x="3.5" y="7" width="17" height="12.5" rx="2" />
    <path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3.5 12.5h17" />
  </svg>
);

export const PeopleIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className}>
    <circle cx="9" cy="8.5" r="3" />
    <path d="M3.5 19c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5" />
    <circle cx="16.5" cy="9.5" r="2.4" />
    <path d="M16 14.2c2.4 0 4 1.5 4.5 4.3" />
  </svg>
);

export const ArticleIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M7 3.5h7l4 4v13H7Z" />
    <path d="M10 11h5M10 14.5h5M10 18h3" />
  </svg>
);

export const PlayIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <rect x="3.5" y="5" width="17" height="14" rx="3" />
    <path d="m10 9 5 3-5 3Z" />
  </svg>
);

export const WrenchIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M14.5 5.5a4 4 0 0 0 4.8 4.8l-9 9a2 2 0 0 1-2.8-2.8l9-9a4 4 0 0 1-2-2Z" />
  </svg>
);

export const CapIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="m2.5 9.5 9.5-4.5 9.5 4.5-9.5 4.5Z" />
    <path d="M6.5 11.5v4c1.5 1.3 3.3 2 5.5 2s4-.7 5.5-2v-4" />
  </svg>
);

export const GridIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <rect x="4" y="4" width="6.5" height="6.5" rx="1.5" />
    <rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5" />
    <rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5" />
    <rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5" />
  </svg>
);

export const PinIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M12 20.5s6-5.4 6-10.5a6 6 0 1 0-12 0c0 5.1 6 10.5 6 10.5Z" />
    <circle cx="12" cy="10" r="2.2" />
  </svg>
);

export const CalendarIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <rect x="4" y="5.5" width="16" height="14.5" rx="2" />
    <path d="M4 10h16M8.5 3.5v4M15.5 3.5v4" />
  </svg>
);

export const MonitorIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <rect x="3.5" y="4.5" width="17" height="11.5" rx="2" />
    <path d="M9 20h6M12 16v4" />
  </svg>
);

export const SearchIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="m16 16 4 4" />
  </svg>
);

export const FlagIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M5.5 20.5v-16M5.5 4.5h11l-2 4 2 4h-11" />
  </svg>
);

export const ExternalIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M13.5 4.5h6v6M19.5 4.5l-8 8M17 13.5v5a1.5 1.5 0 0 1-1.5 1.5h-10A1.5 1.5 0 0 1 4 18.5v-10A1.5 1.5 0 0 1 5.5 7h5" />
  </svg>
);

export const StarIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className} fill="currentColor" stroke="none">
    <path d="m12 3.5 2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8-4.3-4.1 5.9-.8Z" />
  </svg>
);

export const LayersIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="m12 4 8.5 4.5L12 13 3.5 8.5Z" />
    <path d="m3.5 12.5 8.5 4.5 8.5-4.5M3.5 16.5 12 21l8.5-4.5" />
  </svg>
);

const circleIcons: Record<string, (p: IconProps) => React.JSX.Element> = {
  flask: ({ className }) => (
    <svg {...base} className={className}>
      <path d="M9.5 3.5h5M10.5 3.5v5.5L5 18.5a1.5 1.5 0 0 0 1.3 2h11.4a1.5 1.5 0 0 0 1.3-2L13.5 9V3.5M7.5 14.5h9" />
    </svg>
  ),
  palette: ({ className }) => (
    <svg {...base} className={className}>
      <path d="M12 3.5a8.5 8.5 0 1 0 0 17c1.3 0 1.8-1 1.3-2-.6-1.2.2-2.5 1.5-2.5h2.2c2 0 3.5-1.5 3.5-3.5 0-5-3.8-9-8.5-9Z" />
      <circle cx="7.5" cy="11" r="1" />
      <circle cx="10.5" cy="7.5" r="1" />
      <circle cx="15" cy="8" r="1" />
    </svg>
  ),
  rocket: ({ className }) => (
    <svg {...base} className={className}>
      <path d="M12.5 15.5 8.5 11.5c1.5-4.5 5-7.5 11-8-.5 6-3.5 9.5-8 11Z" />
      <path d="M8.5 11.5 5 11l2.5-3.5h4M12.5 15.5l.5 3.5 3.5-2.5v-4M6 18c-1 .5-1.5 1.5-1.5 1.5S5.5 19 6 18Z" />
    </svg>
  ),
  people: PeopleIcon,
  cpu: ({ className }) => (
    <svg {...base} className={className}>
      <rect x="6.5" y="6.5" width="11" height="11" rx="2" />
      <path d="M9.5 3.5v3M14.5 3.5v3M9.5 17.5v3M14.5 17.5v3M3.5 9.5h3M3.5 14.5h3M17.5 9.5h3M17.5 14.5h3" />
    </svg>
  ),
  leaf: ({ className }) => (
    <svg {...base} className={className}>
      <path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14Z" />
      <path d="M5 19 13 11" />
    </svg>
  ),
  globe: ({ className }) => (
    <svg {...base} className={className}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M3.5 12h17M12 3.5c2.5 2.5 3.5 5.3 3.5 8.5s-1 6-3.5 8.5c-2.5-2.5-3.5-5.3-3.5-8.5s1-6 3.5-8.5Z" />
    </svg>
  ),
};

export function CircleIcon({ name, className = "h-6 w-6" }: { name: string; className?: string }) {
  const Icon = circleIcons[name] ?? PeopleIcon;
  return <Icon className={className} />;
}
