"use client";

import { FormEvent, useState } from "react";

import { analyzeWallet, AnalyzeResponse } from "@/lib/api";
import { AnalyzeProgress } from "@/components/AnalyzeProgress";
import { Overview } from "@/components/Overview";
import { TokenBalances } from "@/components/TokenBalances";
import { ActivityMix } from "@/components/ActivityMix";
import { AiInsights } from "@/components/AiInsights";

const EXAMPLE = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK";

export default function HomePage() {
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = address.trim();
    if (!trimmed) {
      setError("Paste a Solana address to analyze.");
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
    <main className="relative mx-auto flex max-w-5xl flex-col gap-10 px-6 py-16 sm:py-24">
      <div
        className="pointer-events-none fixed inset-0 -z-10 opacity-[0.55]"
        style={{
          backgroundImage:
            "radial-gradient(ellipse at 12% 0%, color-mix(in srgb, #0F766E 14%, transparent) 0%, transparent 48%), radial-gradient(ellipse at 88% 8%, color-mix(in srgb, #0B1220 6%, transparent) 0%, transparent 42%)",
        }}
      />

      <header className="reveal max-w-2xl space-y-4">
        <p className="font-display text-2xl font-semibold tracking-[-0.04em] text-ink sm:text-3xl">
          ChainLens
        </p>
        <h1 className="font-display text-3xl font-semibold leading-[1.15] tracking-[-0.03em] text-ink sm:text-4xl">
          Solana address intelligence
        </h1>
        <p className="max-w-xl text-muted">
          Paste any address — wallet, program, token, or vault. ChainLens explains what it is and
          what recent activity looks like.
        </p>
      </header>

      <form
        onSubmit={onSubmit}
        className="reveal flex flex-col gap-3 sm:flex-row"
        style={{ animationDelay: "80ms" }}
      >
        <input
          className="flex-1 rounded-lg border border-line bg-surface px-4 py-3 font-mono text-sm outline-none ring-accent/30 focus:ring-2"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Solana address"
          spellCheck={false}
          aria-label="Solana address"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-ink px-5 py-3 text-sm font-medium text-white transition hover:bg-[#1a2436] active:scale-[0.98] disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      <p className="text-xs text-muted" style={{ animationDelay: "120ms" }}>
        Example address:{" "}
        <button
          type="button"
          className="font-mono text-accent underline decoration-line underline-offset-2 hover:decoration-accent"
          onClick={() => setAddress(EXAMPLE)}
          disabled={loading}
        >
          {EXAMPLE.slice(0, 4)}…{EXAMPLE.slice(-4)}
        </button>
      </p>

      {error && (
        <p
          className="rounded-lg border border-[#E8C4C4] bg-pale-red px-4 py-3 text-sm text-[#9F2F2D]"
          role="alert"
        >
          {error}
        </p>
      )}

      {loading && <AnalyzeProgress address={address.trim()} />}

      {result && !loading && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Overview result={result} />
          <AiInsights result={result} />
          <TokenBalances balances={result.balances} accountKind={result.account_kind} />
          <ActivityMix transactions={result.transactions} />
        </div>
      )}
    </main>
  );
}
