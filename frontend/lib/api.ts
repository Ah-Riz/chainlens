export type TokenBalance = {
  mint: string;
  symbol: string;
  amount: string;
  decimals: number;
};

export type TransactionItem = {
  signature: string;
  type: string;
  description: string;
  timestamp: number | null;
  programs: string[];
  slot: number | null;
};

export type AnalyzeResponse = {
  address: string;
  summary: string;
  stats: {
    tx_count: number;
    unique_counterparties: number;
    protocols: string[];
  };
  balances: TokenBalance[];
  transactions: TransactionItem[];
  structured: {
    protocol_interactions: { name: string; count: number }[];
    notable_transfers: {
      direction: string;
      asset: string;
      amount: string;
      counterparty_label: string | null;
    }[];
  };
  intelligence: {
    label: string;
    signals: string[];
  };
  account_kind: string;
  owner_program: string | null;
  owner_label: string | null;
  what_is_this: string;
  mock: boolean;
};

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export async function analyzeWallet(address: string): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ address }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return (await res.json()) as AnalyzeResponse;
}
