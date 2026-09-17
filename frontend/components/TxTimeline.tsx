import { TransactionItem } from "@/lib/api";

const TYPE_STYLE: Record<string, string> = {
  SWAP_HINT: "bg-pale-blue text-[#0369A1]",
  SPL_TRANSFER: "bg-pale-teal text-accent",
  SOL_TRANSFER: "bg-pale-yellow text-amber",
  PROGRAM_INTERACTION: "bg-canvas text-muted",
  UNKNOWN: "bg-canvas text-muted",
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
    <section className="panel reveal" style={{ animationDelay: "220ms" }}>
      <h2 className="mb-4 font-display text-xl font-semibold tracking-[-0.02em]">
        Transaction timeline
      </h2>
      {transactions.length === 0 ? (
        <p className="text-sm text-muted">No recent activity in the fetched window.</p>
      ) : (
        <ol className="space-y-4">
          {transactions.map((tx) => (
            <li key={tx.signature} className="border-b border-line pb-4 last:border-0 last:pb-0">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span
                  className={`rounded px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.06em] ${
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
