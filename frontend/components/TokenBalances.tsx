import { TokenBalance } from "@/lib/api";

export function TokenBalances({ balances }: { balances: TokenBalance[] }) {
  return (
    <section className="reveal rounded-lg border border-line bg-surface p-6 transition hover:shadow-lift">
      <h2 className="mb-4 font-display text-xl tracking-[-0.02em]">Token balances</h2>
      {balances.length === 0 ? (
        <p className="text-sm text-muted">No token balances found.</p>
      ) : (
        <ul className="divide-y divide-line">
          {balances.map((b) => (
            <li key={b.mint} className="flex items-baseline justify-between gap-4 py-3 text-sm">
              <span className="font-medium">{b.symbol}</span>
              <span className="font-mono text-muted">{b.amount}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
