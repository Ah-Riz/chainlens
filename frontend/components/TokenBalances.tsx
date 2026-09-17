import { TokenBalance } from "@/lib/api";

export function TokenBalances({ balances }: { balances: TokenBalance[] }) {
  return (
    <section className="panel reveal" style={{ animationDelay: "160ms" }}>
      <h2 className="mb-4 font-display text-xl font-semibold tracking-[-0.02em]">Token balances</h2>
      {balances.length === 0 ? (
        <p className="text-sm text-muted">No token balances found.</p>
      ) : (
        <ul className="divide-y divide-line">
          {balances.map((b) => (
            <li key={b.mint} className="flex items-baseline justify-between gap-4 py-3 text-sm">
              <span className="font-medium">{b.symbol}</span>
              <span className="font-mono tabular-nums text-muted">{b.amount}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
