type EmptyProps = {
  children: React.ReactNode;
  className?: string;
};

export function EmptyState({ children, className = "" }: EmptyProps) {
  return (
    <div className={`rounded-2xl px-1 py-2 text-sm text-white/45 ${className}`}>
      {children}
    </div>
  );
}

export function InlineError({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-sm text-red-400" role="alert">
      {children}
    </p>
  );
}
