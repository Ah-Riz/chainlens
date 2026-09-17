/**
 * Temporary edge mock of ChainLens API so Pages can demo without AWS.
 * Replace NEXT_PUBLIC_API_URL with App Runner once scripts/deploy-api.sh succeeds.
 */
const MOCK = {
  address: "11111111111111111111111111111111",
  summary:
    "This wallet swapped SOL for USDC via Jupiter, received SPL tokens, and interacted with the System Program. (Edge mock — deploy FastAPI to App Runner for live Solana + TiDB.)",
  stats: { tx_count: 12, unique_counterparties: 5, protocols: ["Jupiter", "SPL Token"] },
  balances: [
    {
      mint: "So11111111111111111111111111111111111111112",
      symbol: "SOL",
      amount: "2.5",
      decimals: 9,
    },
    {
      mint: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      symbol: "USDC",
      amount: "150.00",
      decimals: 6,
    },
  ],
  transactions: [
    {
      signature: "MockSig111111111111111111111111111111111111111111111111111111111",
      type: "SWAP_HINT",
      description: "Likely swap via Jupiter",
      timestamp: 1700000000,
      programs: ["Jupiter", "SPL Token"],
      slot: 1,
    },
  ],
  structured: {
    protocol_interactions: [
      { name: "Jupiter", count: 3 },
      { name: "SPL Token", count: 5 },
    ],
    notable_transfers: [
      { direction: "in", asset: "SOL", amount: "1.0", counterparty_label: "external wallet" },
    ],
  },
  mock: true,
};

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin || "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function json(data, origin, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
  });
}

export default {
  async fetch(request) {
    const origin = request.headers.get("Origin") || "*";
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/health") {
      return json({ status: "ok", service: "chainlens", chain: "solana", edge: true }, origin);
    }

    if (path === "/analyze" && request.method === "POST") {
      const body = await request.json().catch(() => ({}));
      const address = body.address || MOCK.address;
      if (!address || address.length < 32) {
        return json({ detail: "Invalid Solana address" }, origin, 400);
      }
      return json({ ...MOCK, address }, origin);
    }

    const txMatch = path.match(/^\/wallets\/([^/]+)\/transactions$/);
    if (txMatch && request.method === "GET") {
      return json({ address: decodeURIComponent(txMatch[1]), transactions: MOCK.transactions }, origin);
    }

    const balMatch = path.match(/^\/wallets\/([^/]+)\/balances$/);
    if (balMatch && request.method === "GET") {
      return json({ address: decodeURIComponent(balMatch[1]), balances: MOCK.balances }, origin);
    }

    const sumMatch = path.match(/^\/wallets\/([^/]+)\/summary$/);
    if (sumMatch && request.method === "POST") {
      return json(
        {
          address: decodeURIComponent(sumMatch[1]),
          summary: MOCK.summary,
          structured: MOCK.structured,
          mock: true,
        },
        origin,
      );
    }

    if (path === "/analyses/similar") {
      return json({ items: [] }, origin);
    }

    return json({ detail: "Not found" }, origin, 404);
  },
};
