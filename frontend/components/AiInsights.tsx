import { AnalyzeResponse } from "@/lib/api";

export function AiInsights({ result }: { result: AnalyzeResponse }) {
  return (
    <section className="reveal rounded-lg border border-line bg-surface p-6 transition hover:shadow-lift sm:col-span-2">
      <h2 className="mb-3 font-display text-xl tracking-[-0.02em]">AI insights</h2>
      <p className="text-base leading-relaxed text-ink">{result.summary}</p>
      {result.structured.protocol_interactions.length > 0 && (
        <ul className="mt-4 flex flex-wrap gap-2">
          {result.structured.protocol_interactions.map((p) => (
            <li
              key={p.name}
              className="rounded-full bg-pale-green px-3 py-1 text-xs uppercase tracking-[0.06em] text-[#346538]"
            >
              {p.name} · {p.count}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
