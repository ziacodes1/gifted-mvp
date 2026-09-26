import type { ReactNode } from "react";
import { usePhotoUrl } from "./queries";
import { Ribbon, Tape } from "./decor";

/** An open leather journal: dark-green cover, two cream pages with a spine shadow and page
 * edges, and a gold ribbon. Stacks to one page column on small screens. Pure layout. */
export function DiaryBook({
  left,
  right,
  header,
  className = "",
  overlay,
}: {
  left: ReactNode;
  right: ReactNode;
  /** Optional full-width strip across the top of both pages (e.g. progress). */
  header?: ReactNode;
  className?: string;
  overlay?: ReactNode;
}) {
  return (
    <div className={`relative pb-10 ${className}`}>
      <div className="relative rounded-[26px] bg-gradient-to-br from-forest-700 via-forest-800 to-forest-900 p-2.5 shadow-[0_18px_40px_-12px_rgba(15,36,25,0.45)] ring-1 ring-gold-500/30 md:p-3.5">
        {/* stitched edge */}
        <div className="pointer-events-none absolute inset-1.5 rounded-[22px] border border-dashed border-gold-400/25" />
        {header && <div className="diary-page relative rounded-t-[18px] border-b border-dashed border-[#e2d5b8] px-5 py-4 md:px-8">{header}</div>}
        <div className="relative grid md:grid-cols-2">
          <div className={`diary-page relative min-h-[18rem] ${header ? "" : "rounded-t-[18px]"} px-5 pb-8 pt-7 shadow-[-3px_3px_0_#EFE4CC,-6px_6px_0_#E4D6B8] md:rounded-bl-[18px] ${header ? "" : "md:rounded-tl-[18px]"} md:rounded-tr-none md:px-8 md:pb-10 md:pt-9`}>
            <div className="pointer-events-none absolute inset-y-0 right-0 hidden w-10 bg-gradient-to-l from-[#d9c9a6]/60 to-transparent md:block" />
            {left}
          </div>
          <div className={`diary-page relative min-h-[18rem] rounded-b-[18px] px-5 pb-8 pt-7 shadow-[3px_3px_0_#EFE4CC,6px_6px_0_#E4D6B8] md:rounded-bl-none md:rounded-br-[18px] ${header ? "" : "md:rounded-tr-[18px]"} md:px-8 md:pb-10 md:pt-9`}>
            <div className="pointer-events-none absolute inset-y-0 left-0 hidden w-10 bg-gradient-to-r from-[#d9c9a6]/60 to-transparent md:block" />
            <div className="pointer-events-none absolute inset-x-0 top-0 h-6 bg-gradient-to-b from-[#d9c9a6]/50 to-transparent md:hidden" />
            {right}
          </div>
        </div>
        {overlay}
      </div>
      <Ribbon className="absolute bottom-0 left-1/2 h-16 w-6 -translate-x-1/2 md:h-20 md:w-7" />
    </div>
  );
}

/** Taped polaroid. `src` wins over `photoId` (local previews before upload). */
export function Polaroid({
  photoId,
  src,
  caption,
  tilt = -2,
  tape = "cream",
  className = "",
  children,
}: {
  photoId?: number;
  src?: string;
  caption?: ReactNode;
  tilt?: number;
  tape?: "cream" | "sage" | "rose";
  className?: string;
  children?: ReactNode;
}) {
  const remote = usePhotoUrl(src ? undefined : photoId);
  const url = src ?? remote;
  return (
    <figure className={`relative bg-white p-2 pb-3 shadow-[0_6px_14px_-4px_rgba(60,45,20,0.35)] ${className}`} style={{ transform: `rotate(${tilt}deg)` }}>
      <Tape tone={tape} className="absolute -top-3 left-1/2 -translate-x-1/2" />
      <div className="aspect-[4/3] w-full overflow-hidden bg-cream-100">
        {url ? <img src={url} alt="" className="h-full w-full object-cover" /> : <div className="h-full w-full animate-pulse bg-cream-200" />}
      </div>
      {caption && <figcaption className="mt-1.5 px-1 text-center font-hand text-lg leading-tight text-forest-800">{caption}</figcaption>}
      {children}
    </figure>
  );
}
