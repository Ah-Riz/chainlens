import { AnalyzeResponse } from "@/lib/api";

export function Overview({ result }: { result: AnalyzeResponse }) {
  return (
    <section className="reveal rounded-lg border border-line bg-surface p-6 transition hover:shadow-lift sm:col-span-2">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h2 className="font-display text-xl tracking-[-0.02em]">Overview</h2>
        {result.mock && (
          <span className="rounded-full bg-pale-yellow px-2 py-0.5 text-[10px] uppercase tracking-[0.08em] text-[#956400]">
            Mock
          </span>
        )}
      </div>
      <p className="mb-4 break-all font-mono text-xs text-muted">{result.address}</p>
      <dl className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <dt className="text-muted">Transactions</dt>
          <dd className="text-2xl font-medium tracking-tight">{result.stats.tx_count}</dd>
        </div>
        <div>
          <dt className="text-muted">Counterparties</dt>
          <dd className="text-2xl font-medium tracking-tight">{result.stats.unique_counterparties}</dd>
        </div>
        <div>
          <dt className="text-muted">Protocols</dt>
          <dd className="text-sm font-medium leading-snug">
            {result.stats.protocols.length ? result.stats.protocols.join(", ") : "—"}
          </dd>
        </div>
      </dl>
    </section>
  );
}
