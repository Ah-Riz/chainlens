"use client";

import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useWallet } from "@solana/wallet-adapter-react";
import { FormEvent, useEffect, useState } from "react";

import { analyzeWallet, AnalyzeResponse } from "@/lib/api";
import { Overview } from "@/components/Overview";
import { TokenBalances } from "@/components/TokenBalances";
import { TxTimeline } from "@/components/TxTimeline";
import { AiInsights } from "@/components/AiInsights";

const EXAMPLE = "11111111111111111111111111111111";

export default function HomePage() {
  const { publicKey } = useWallet();
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  useEffect(() => {
    if (publicKey) {
      setAddress(publicKey.toBase58());
    }
  }, [publicKey]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = address.trim();
    if (!trimmed) {
      setError("Enter a Solana address or connect a wallet.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeWallet(trimmed);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative mx-auto flex max-w-5xl flex-col gap-12 px-6 py-16 sm:py-24">
      <div
        className="pointer-events-none fixed inset-0 -z-10 opacity-[0.04]"
        style={{
          backgroundImage:
            "radial-gradient(ellipse at 20% 10%, #956400 0%, transparent 50%), radial-gradient(ellipse at 80% 0%, #1F6C9F 0%, transparent 40%)",
        }}
      />

      <header className="reveal flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-xl space-y-3">
          <p className="font-mono text-xs uppercase tracking-[0.12em] text-muted">ChainLens</p>
          <h1 className="font-display text-4xl leading-[1.1] tracking-[-0.03em] text-ink sm:text-5xl">
            Solana wallet intelligence
          </h1>
          <p className="text-muted">
            Connect a wallet or paste an address. ChainLens parses on-chain activity and explains it
            in plain language.
          </p>
        </div>
        <WalletMultiButton />
      </header>

      <form onSubmit={onSubmit} className="reveal flex flex-col gap-3 sm:flex-row" style={{ animationDelay: "80ms" }}>
        <input
          className="flex-1 rounded border border-line bg-surface px-4 py-3 font-mono text-sm outline-none ring-ink/20 focus:ring-2"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Solana address"
          spellCheck={false}
          aria-label="Solana wallet address"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-ink px-5 py-3 text-sm text-white transition hover:bg-[#333] active:scale-[0.98] disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      <p className="text-xs text-muted">
        Try mock mode with the System Program address:{" "}
        <button
          type="button"
          className="font-mono underline decoration-line underline-offset-2 hover:text-ink"
          onClick={() => setAddress(EXAMPLE)}
        >
          {EXAMPLE}
        </button>
      </p>

      {error && (
        <p className="rounded border border-[#E8C4C4] bg-pale-red px-4 py-3 text-sm text-[#9F2F2D]" role="alert">
          {error}
        </p>
      )}

      {loading && (
        <div className="grid gap-4 sm:grid-cols-2" aria-busy="true">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-32 animate-pulse rounded-lg border border-line bg-surface" />
          ))}
        </div>
      )}

      {result && !loading && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Overview result={result} />
          <AiInsights result={result} />
          <TokenBalances balances={result.balances} />
          <TxTimeline transactions={result.transactions} />
        </div>
      )}
    </main>
  );
}
