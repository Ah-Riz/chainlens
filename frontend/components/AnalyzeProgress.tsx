"use client";

import { useEffect, useState } from "react";

const PHASES = [
  { id: "fetch", label: "Fetching signatures", untilMs: 6000 },
  { id: "decode", label: "Decoding instructions", untilMs: 14000 },
  { id: "summary", label: "Writing summary", untilMs: Infinity },
] as const;

function shorten(address: string) {
  if (address.length < 12) return address;
  return `${address.slice(0, 4)}…${address.slice(-4)}`;
}

export function AnalyzeProgress({ address }: { address: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const id = window.setInterval(() => setElapsed(Date.now() - start), 200);
    return () => window.clearInterval(id);
  }, []);

  const activeIndex = PHASES.findIndex((p) => elapsed < p.untilMs);
  const phase = activeIndex === -1 ? PHASES.length - 1 : activeIndex;

  return (
    <section
      className="panel reveal sm:col-span-2"
      aria-busy="true"
      aria-live="polite"
      aria-label="Analysis in progress"
    >
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-xl tracking-[-0.02em] text-ink">Scanning</h2>
        <p className="font-mono text-xs text-muted">{shorten(address)}</p>
      </div>

      <div className="scan-track mb-6" aria-hidden="true" />

      <ol className="space-y-3">
        {PHASES.map((p, i) => {
          const done = i < phase;
          const active = i === phase;
          return (
            <li key={p.id} className="flex items-center gap-3 text-sm">
              <span
                className={`flex h-2.5 w-2.5 shrink-0 rounded-full ${
                  active
                    ? "bg-accent ring-4 ring-accent/25"
                    : done
                      ? "bg-accent"
                      : "border border-line bg-transparent"
                }`}
                aria-hidden="true"
              />
              <span className={active ? "font-medium text-ink" : done ? "text-ink" : "text-muted"}>
                {p.label}
                {active ? "…" : ""}
              </span>
            </li>
          );
        })}
      </ol>

      <p className="mt-5 font-mono text-xs text-muted">
        ~20s typical on free RPC · {Math.floor(elapsed / 1000)}s elapsed
      </p>
    </section>
  );
}
