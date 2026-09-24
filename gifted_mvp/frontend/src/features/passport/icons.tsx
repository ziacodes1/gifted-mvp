/** Small stroke icons used across the Passport (kept local; no icon library in the project). */
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

export const LeafIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14Z" />
    <path d="M5 19 13 11" />
  </svg>
);

export const CheckIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} strokeWidth={2.2} className={className}>
    <path d="m5 12.5 4.5 4.5L19 7.5" />
  </svg>
);

export const ChartIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M5 19V13M12 19V8M19 19V5" />
  </svg>
);

export const SparkIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M12 3.5 13.8 10.2 20.5 12l-6.7 1.8L12 20.5l-1.8-6.7L3.5 12l6.7-1.8Z" />
  </svg>
);

export const CompassIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="m15.5 8.5-2 5-5 2 2-5Z" />
  </svg>
);

export const DocIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M7 3.5h7l4 4v13H7Z" />
    <path d="M14 3.5v4h4M10 12h5M10 15.5h5" />
  </svg>
);

export const ArrowIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);

export const ClockIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 7.5V12l3 2" />
  </svg>
);

export const BackIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M19 12H5M11 6l-6 6 6 6" />
  </svg>
);

export const QuoteIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className={className}>
    <path d="M9.5 6C6.5 7 4.5 9.6 4.5 13v5h6v-6h-3c0-2 1-3.6 2.8-4.4L9.5 6Zm10 0c-3 1-5 3.6-5 7v5h6v-6h-3c0-2 1-3.6 2.8-4.4L19.5 6Z" />
  </svg>
);

export const HomeIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M4 11 12 4l8 7v8.5H14.5v-5h-5v5H4Z" />
  </svg>
);

export const UserIcon = ({ className = "h-5 w-5" }: IconProps) => (
  <svg {...base} className={className}>
    <circle cx="12" cy="8.5" r="3.5" />
    <path d="M5 19.5c1.2-3.2 3.8-5 7-5s5.8 1.8 7 5" />
  </svg>
);
