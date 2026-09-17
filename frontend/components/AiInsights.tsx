import { AnalyzeResponse } from "@/lib/api";

export function AiInsights({ result }: { result: AnalyzeResponse }) {
  return (
    <section className="panel reveal sm:col-span-2" style={{ animationDelay: "100ms" }}>
      <h2 className="mb-3 font-display text-xl font-semibold tracking-[-0.02em]">AI insights</h2>
      <p className="text-base leading-relaxed text-ink">{result.summary}</p>
      {result.intelligence.signals.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-2">
          {result.intelligence.signals.map((s) => (
            <li
              key={s}
              className="rounded border border-line bg-canvas px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.04em] text-muted"
            >
              {s.replaceAll("_", " ")}
            </li>
          ))}
        </ul>
      )}
      {result.structured.protocol_interactions.length > 0 && (
        <ul className="mt-4 flex flex-wrap gap-2">
          {result.structured.protocol_interactions.map((p) => (
            <li
              key={p.name}
              className="rounded border border-line bg-pale-teal px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.04em] text-accent"
            >
              {p.name} · {p.count}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
