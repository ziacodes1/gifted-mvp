export function SignalRing({ score }: { score: number }) {
  const angle = Math.max(0, Math.min(100, score)) * 3.6;
  return (
    <div
      className="grid h-16 w-16 shrink-0 place-items-center rounded-full"
      style={{ background: `conic-gradient(#1E4636 ${angle}deg, #EFE7D6 0deg)` }}
    >
      <div className="grid h-12 w-12 place-items-center rounded-full bg-white text-sm font-semibold text-forest-700">
        {score}%
      </div>
    </div>
  );
}
