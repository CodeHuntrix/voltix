import { Link } from "@tanstack/react-router";
import { MachineArt } from "@/components/MachineArt";
import { stateBadgeClass, stateRailClass, typeLabel } from "@/lib/machineArt";
import { formatInr, liveInrPerHr } from "@/lib/money";

type Props = {
  machineId: string;
  name: string;
  machineType?: string;
  state: string;
  kwEst: number;
  iRmsA: number;
  wasteInrPerHr: number;
  inrPerHr?: number;
  tariffInrPerKwh?: number;
  eligibleAutocut?: boolean;
  modelVersion?: string;
};

export function MachineCard({
  machineId,
  name,
  machineType,
  state,
  kwEst,
  iRmsA,
  wasteInrPerHr,
  inrPerHr,
  tariffInrPerKwh,
  eligibleAutocut,
  modelVersion,
}: Props) {
  const burn = liveInrPerHr({
    inr_per_hr: inrPerHr,
    kw_est: kwEst,
    tariff_inr_per_kwh: tariffInrPerKwh,
  });
  const hero = state === "WASTE" && wasteInrPerHr > 0 ? wasteInrPerHr : burn;
  const heroClass =
    state === "WASTE" ? "text-red-400" : state === "IDLE" ? "text-amber-200" : "text-white";

  return (
    <Link
      to="/machines/$machineId"
      params={{ machineId }}
      className="machine-card group relative flex flex-col overflow-hidden rounded-2xl"
    >
      <span className={`absolute inset-y-0 left-0 w-[3px] ${stateRailClass(state)}`} aria-hidden="true" />

      <div className="flex items-start justify-between gap-2 px-4 pt-4 pl-5">
        <span className="font-mono text-[11px] tracking-[0.18em] text-white/40">{typeLabel(machineType)}</span>
        <span
          className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${stateBadgeClass(state)}`}
        >
          {state}
        </span>
      </div>

      <div className="machine-well relative mx-3 mt-3 flex h-52 items-end justify-center pb-3">
        <MachineArt
          machineType={machineType}
          alt={name}
          className="relative z-[1] h-[96%] w-auto max-w-[94%] object-contain object-bottom transition-transform duration-500 group-hover:scale-[1.03]"
        />
      </div>

      <div className="mt-auto border-t border-white/[0.06] px-4 py-3 pl-5">
        <p className="truncate text-sm font-medium text-white">{name}</p>
        <p className={`mt-1 font-mono text-[1.65rem] font-semibold leading-none tracking-tight ${heroClass}`}>
          {formatInr(hero)}
          <span className="ml-1 text-sm font-medium text-white/35">/hr</span>
        </p>
        <p className="mt-1.5 text-[11px] text-white/40">
          {state === "WASTE" ? "waste · " : ""}
          {kwEst.toFixed(2)} kW · {iRmsA.toFixed(1)} A
          {eligibleAutocut ? " · AutoCut" : ""}
          {modelVersion ? ` · ${modelVersion}` : ""}
        </p>
      </div>
    </Link>
  );
}
