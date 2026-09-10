export function CardSkeleton() {
  return (
    <div
      className="machine-card relative overflow-hidden rounded-2xl"
      aria-hidden="true"
    >
      <span className="absolute inset-y-0 left-0 w-[3px] bg-white/10" />
      <div className="flex items-start justify-between gap-2 px-4 pt-4 pl-5">
        <span className="h-3 w-12 animate-pulse rounded bg-white/10" />
        <span className="h-4 w-14 animate-pulse rounded-md bg-white/10" />
      </div>
      <div className="machine-well relative mx-3 mt-3 h-52 animate-pulse" />
      <div className="mt-auto border-t border-white/[0.06] px-4 py-3 pl-5">
        <span className="block h-4 w-2/3 animate-pulse rounded bg-white/10" />
        <span className="mt-2 block h-7 w-1/2 animate-pulse rounded bg-white/10" />
        <span className="mt-2 block h-3 w-3/4 animate-pulse rounded bg-white/10" />
      </div>
    </div>
  );
}

export function ListSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-hidden="true">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="glass-card h-16 animate-pulse rounded-2xl" />
      ))}
    </div>
  );
}
