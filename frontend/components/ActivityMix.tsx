import { TransactionItem } from "@/lib/api";

const TYPE_LABEL: Record<string, string> = {
  SWAP_HINT: "DEX swaps",
  SPL_TRANSFER: "SPL transfers",
  SOL_TRANSFER: "SOL transfers",
  PROGRAM_INTERACTION: "Program calls",
  UNKNOWN: "Other",
};

const TYPE_ORDER = [
  "SWAP_HINT",
  "SPL_TRANSFER",
  "SOL_TRANSFER",
  "PROGRAM_INTERACTION",
  "UNKNOWN",
] as const;

export function ActivityMix({ transactions }: { transactions: TransactionItem[] }) {
  const total = transactions.length;
  const counts = new Map<string, number>();
  for (const tx of transactions) {
    counts.set(tx.type, (counts.get(tx.type) ?? 0) + 1);
  }
  const rows = TYPE_ORDER.filter((t) => (counts.get(t) ?? 0) > 0).map((t) => {
    const n = counts.get(t) ?? 0;
    return { type: t, count: n, share: total ? Math.round((n / total) * 100) : 0 };
  });

  return (
    <section className="panel reveal" style={{ animationDelay: "220ms" }}>
      <h2 className="mb-4 font-display text-xl font-semibold tracking-[-0.02em]">Activity mix</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-muted">No recent activity in the fetched window.</p>
      ) : (
        <ul className="space-y-3">
          {rows.map((r) => (
            <li key={r.type}>
              <div className="mb-1 flex items-baseline justify-between gap-3 text-sm">
                <span className="font-medium text-ink">{TYPE_LABEL[r.type] ?? r.type}</span>
                <span className="font-mono text-xs tabular-nums text-muted">
                  {r.count} · {r.share}%
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-canvas">
                <div
                  className="h-full rounded-full bg-accent/70"
                  style={{ width: `${r.share}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
