import { AnalyzeResponse } from "@/lib/api";

export function Overview({ result }: { result: AnalyzeResponse }) {
  return (
    <section className="panel reveal sm:col-span-2" style={{ animationDelay: "40ms" }}>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h2 className="font-display text-xl font-semibold tracking-[-0.02em]">Overview</h2>
        {result.mock && (
          <span className="rounded border border-line bg-pale-yellow px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.08em] text-amber">
            Rule-based summary
          </span>
        )}
      </div>
      <p className="mb-5 break-all font-mono text-xs text-muted">{result.address}</p>
      <dl className="grid gap-6 sm:grid-cols-3">
        <div>
          <dt className="text-xs uppercase tracking-[0.08em] text-muted">Transactions</dt>
          <dd className="mt-1 font-display text-3xl font-semibold tabular-nums tracking-tight">
            {result.stats.tx_count}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.08em] text-muted">Counterparties</dt>
          <dd className="mt-1 font-display text-3xl font-semibold tabular-nums tracking-tight">
            {result.stats.unique_counterparties}
          </dd>
        </div>
        <div>
          <dt className="mb-2 text-xs uppercase tracking-[0.08em] text-muted">Protocols</dt>
          <dd className="flex flex-wrap gap-1.5">
            {result.stats.protocols.length ? (
              result.stats.protocols.map((p) => (
                <span
                  key={p}
                  className="rounded border border-line bg-canvas px-2 py-0.5 font-mono text-[11px] text-ink"
                >
                  {p}
                </span>
              ))
            ) : (
              <span className="text-sm text-muted">—</span>
            )}
          </dd>
        </div>
      </dl>
    </section>
  );
}
