import { TokenBalance } from "@/lib/api";

function emptyHint(kind: string | undefined): string {
  if (kind === "program") {
    return "Programs usually don’t hold user tokens.";
  }
  if (kind === "token_mint") {
    return "A mint defines a token; it isn’t a balance list for a wallet.";
  }
  if (kind === "protocol_account") {
    return "Protocol accounts may hold SOL for rent; they aren’t personal wallets.";
  }
  if (kind === "token_account") {
    return "This is a single-token account — check the amount below if present.";
  }
  return "No token balances found.";
}

export function TokenBalances({
  balances,
  accountKind,
}: {
  balances: TokenBalance[];
  accountKind?: string;
}) {
  const showList =
    balances.length > 0 && accountKind !== "program" && accountKind !== "token_mint";

  return (
    <section className="panel reveal" style={{ animationDelay: "160ms" }}>
      <h2 className="mb-4 font-display text-xl font-semibold tracking-[-0.02em]">Token balances</h2>
      {!showList ? (
        <p className="text-sm text-muted">{emptyHint(accountKind)}</p>
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
