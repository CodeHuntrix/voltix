import { Link } from "@tanstack/react-router";

type Props = {
  to?: string | null;
  size?: "sm" | "md" | "lg";
};

const sizes = {
  sm: {
    mark: "h-11 w-11",
    title: "text-[1.75rem] leading-none",
    tag: "text-sm",
    gap: "gap-3",
  },
  md: {
    mark: "h-14 w-14",
    title: "text-[2.15rem] leading-none",
    tag: "text-[15px]",
    gap: "gap-3.5",
  },
  lg: {
    mark: "h-[4.25rem] w-[4.25rem]",
    title: "text-5xl leading-none",
    tag: "text-base",
    gap: "gap-4",
  },
} as const;

export function BrandMark({ to = "/dashboard", size = "lg" }: Props) {
  const s = sizes[size];

  const inner = (
    <span className={`flex items-center ${s.gap}`}>
      <span
        className={`${s.mark} flex shrink-0 items-center justify-center rounded-xl bg-[#e6a17c]`}
        aria-hidden="true"
      >
        <svg className="h-[58%] w-[58%]" viewBox="0 0 24 24" fill="none">
          <path d="M4 3h4.8L12 14.2 16.5 3H21l-8.1 18h-3L4 3Z" fill="#171b1d" />
        </svg>
      </span>
      <span className="min-w-0 whitespace-nowrap">
        <span className={`block font-semibold tracking-tight text-white ${s.title}`}>
          Voltix
        </span>
        <span className={`mt-1.5 block font-medium text-white/70 ${s.tag}`}>
          Machine energy intelligence
        </span>
      </span>
    </span>
  );

  if (!to) return inner;
  return (
    <Link to={to} className="inline-flex hover:opacity-90">
      {inner}
    </Link>
  );
}
