import { TransactionItem } from "@/lib/api";

const TYPE_STYLE: Record<string, string> = {
  SWAP_HINT: "bg-pale-blue text-[#1F6C9F]",
  SPL_TRANSFER: "bg-pale-green text-[#346538]",
  SOL_TRANSFER: "bg-pale-yellow text-[#956400]",
  PROGRAM_INTERACTION: "bg-[#F3F3F2] text-muted",
  UNKNOWN: "bg-[#F3F3F2] text-muted",
};

function formatTime(ts: number | null) {
  if (!ts) return "—";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(ts * 1000));
}

export function TxTimeline({ transactions }: { transactions: TransactionItem[] }) {
  return (
    <section className="reveal rounded-lg border border-line bg-surface p-6 transition hover:shadow-lift">
      <h2 className="mb-4 font-display text-xl tracking-[-0.02em]">Transaction timeline</h2>
      {transactions.length === 0 ? (
        <p className="text-sm text-muted">No recent activity in the fetched window.</p>
      ) : (
        <ol className="space-y-4">
          {transactions.map((tx, index) => (
            <li
              key={tx.signature}
              className="border-b border-line pb-4 last:border-0 last:pb-0"
              style={{ animationDelay: `${index * 80}ms` }}
            >
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-[0.06em] ${
                    TYPE_STYLE[tx.type] ?? TYPE_STYLE.UNKNOWN
                  }`}
                >
                  {tx.type.replace("_", " ")}
                </span>
                <span className="text-xs text-muted">{formatTime(tx.timestamp)}</span>
              </div>
              <p className="text-sm text-ink">{tx.description}</p>
              <p className="mt-1 truncate font-mono text-[11px] text-muted">{tx.signature}</p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
