import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { BrandMark } from "@/components/BrandMark";
import { InlineError } from "@/components/EmptyState";
import { MachineArt } from "@/components/MachineArt";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { fieldClass } from "@/lib/form";

type CatalogItem = {
  type: string;
  label: string;
  blurb: string;
  autocut: boolean;
};

const CATALOG: CatalogItem[] = [
  {
    type: "compressor",
    label: "Air compressor",
    blurb: "Load / unload waste — AutoCut recommended",
    autocut: true,
  },
  {
    type: "cnc",
    label: "CNC / lathe",
    blurb: "Alert-only while a cycle is running",
    autocut: false,
  },
  {
    type: "press",
    label: "Hydraulic press",
    blurb: "Cycle + idle energy",
    autocut: false,
  },
  {
    type: "conveyor",
    label: "Conveyor",
    blurb: "Utility path — AutoCut recommended",
    autocut: true,
  },
  {
    type: "laptop",
    label: "Laptop / charger",
    blurb: "Desk load or live CT demo",
    autocut: true,
  },
];

type Pick = {
  id: string;
  type: string;
  name: string;
  autocut: boolean;
  deviceId: string;
};

function newPick(item: CatalogItem, index: number): Pick {
  return {
    id: crypto.randomUUID(),
    type: item.type,
    name: index > 1 ? `${item.label} ${index}` : item.label,
    autocut: item.autocut,
    deviceId: "",
  };
}

export function OnboardingPage() {
  const [picks, setPicks] = useState<Pick[]>([]);
  const [error, setError] = useState<string | null>(null);
  const token = useAuth((s) => s.accessToken)!;
  const siteId = useAuth((s) => s.siteId)!;
  const navigate = useNavigate();

  function addFromCatalog(item: CatalogItem) {
    const count = picks.filter((p) => p.type === item.type).length;
    setPicks((prev) => [...prev, newPick(item, count + 1)]);
  }

  function updatePick(id: string, patch: Partial<Pick>) {
    setPicks((prev) => prev.map((p) => (p.id === id ? { ...p, ...patch } : p)));
  }

  const save = useMutation({
    mutationFn: async () => {
      if (!picks.length) throw new Error("Select at least one machine");
      for (const pick of picks) {
        const name = pick.name.trim();
        if (!name) throw new Error("Every machine needs a name");
        await api.createMachine(token, siteId, {
          name,
          machine_type: pick.type,
          eligible_autocut: pick.autocut,
          device_id: pick.deviceId.trim() || null,
        });
      }
    },
    onSuccess: () => navigate({ to: "/dashboard" }),
    onError: (e: Error) => setError(e.message),
  });

  return (
    <div className="ops-shell min-h-screen text-white">
      <div className="ops-shell-bg pointer-events-none fixed inset-0" aria-hidden="true" />
      <div className="relative z-10 mx-auto max-w-6xl px-6 py-10">
        <BrandMark to={null} size="md" />
        <div className="mt-10 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-xs tracking-[0.25em] text-sky-300/80">SETUP</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">
              Which machines are on the floor?
            </h1>
            <p className="mt-2 max-w-xl text-sm text-white/50">
              Tap a type to add it. Name it, choose AutoCut, and optionally paste a CT device id.
            </p>
          </div>
          <p className="font-mono text-sm text-white/40">{picks.length} selected</p>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {CATALOG.map((item) => {
            const count = picks.filter((p) => p.type === item.type).length;
            return (
              <button
                key={item.type}
                type="button"
                onClick={() => addFromCatalog(item)}
                className={`machine-card rounded-2xl p-4 pt-5 text-left transition ${
                  count ? "ring-2 ring-sky-400/70" : "hover:border-white/20"
                }`}
              >
                <div className="machine-well relative flex h-36 items-end justify-center pb-2">
                  <MachineArt
                    machineType={item.type}
                    alt={item.label}
                    className="relative z-[1] h-[96%] w-auto max-w-[94%] object-contain object-bottom"
                  />
                  {count > 0 && (
                    <span className="absolute right-2 top-2 z-10 rounded-full bg-sky-500 px-2 py-0.5 text-xs font-semibold">
                      {count}
                    </span>
                  )}
                </div>
                <p className="mt-2 text-sm font-semibold">{item.label}</p>
                <p className="mt-1 text-xs text-white/45">{item.blurb}</p>
              </button>
            );
          })}
        </div>

        {picks.length > 0 && (
          <div className="mt-10 space-y-3">
            <h2 className="text-lg font-semibold">Floor list</h2>
            {picks.map((pick) => (
              <div key={pick.id} className="glass-card rounded-2xl p-4 md:p-5">
                <div className="flex flex-col gap-4 md:flex-row md:items-end">
                  <label className="block flex-1 text-sm">
                    <span className="text-white/45">Name</span>
                    <input
                      className={fieldClass}
                      value={pick.name}
                      onChange={(e) => updatePick(pick.id, { name: e.target.value })}
                    />
                  </label>
                  <label className="block flex-1 text-sm">
                    <span className="text-white/45">CT / device id (optional)</span>
                    <input
                      className={`${fieldClass} font-mono text-sm`}
                      value={pick.deviceId}
                      placeholder="leave blank to auto-assign"
                      onChange={(e) => updatePick(pick.id, { deviceId: e.target.value })}
                    />
                  </label>
                  <label className="flex items-center gap-2 pb-2 text-sm">
                    <input
                      type="checkbox"
                      className="h-4 w-4 accent-primary"
                      checked={pick.autocut}
                      onChange={(e) => updatePick(pick.id, { autocut: e.target.checked })}
                    />
                    <span>AutoCut</span>
                  </label>
                  <button
                    type="button"
                    className="pb-2 text-sm text-white/40 hover:text-red-300"
                    onClick={() => setPicks((prev) => prev.filter((p) => p.id !== pick.id))}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="mt-4">
            <InlineError>{error}</InlineError>
          </div>
        )}

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <button
            type="button"
            disabled={save.isPending || !picks.length}
            onClick={() => {
              setError(null);
              save.mutate();
            }}
            className="rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-white hover:bg-primary-hover disabled:opacity-40"
          >
            {save.isPending ? "Saving floor…" : "Open ops console"}
          </button>
          <Link
            to="/dashboard"
            className="rounded-full border border-white/15 px-6 py-2.5 text-sm text-white/70 hover:bg-white/5"
          >
            Skip for now
          </Link>
        </div>
      </div>
    </div>
  );
}
