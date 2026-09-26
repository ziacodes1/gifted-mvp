export { ArrowIcon, ChartIcon, CheckIcon, LeafIcon, UserIcon } from "../passport/icons";

/** Small "i" with a native tooltip (explains what counts as activity). */
export function InfoDot({ title }: { title: string }) {
  return (
    <span
      title={title}
      aria-label={title}
      role="img"
      className="grid h-4 w-4 cursor-help place-items-center rounded-full border border-sage-400 text-[10px] font-semibold text-sage-600"
    >
      i
    </span>
  );
}
