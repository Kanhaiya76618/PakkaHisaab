"use client";

import * as Collapsible from "@radix-ui/react-collapsible";
import { ChevronDown, CircleCheck, CircleX } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { AsyncState } from "@/components/AsyncState";
import { fetchEvals, type EvalsReport } from "@/lib/api";
import type { PageState } from "@/lib/types";

const CATEGORY_LABEL: Record<string, string> = {
  extraction: "Extraction",
  matching: "Matching",
  classification: "Classification",
  end_to_end: "End-to-end",
  indic_asr: "Indic ASR",
};

export default function EvalsPage() {
  const [state, setState] = useState<PageState>("loading");
  const [report, setReport] = useState<EvalsReport | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchEvals();
      setReport(data);
      setState(data.count === 0 ? "empty" : "success");
    } catch {
      setState("error");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const categories = Object.entries(report?.summary ?? {});
  const asrCases = (report?.cases ?? []).filter((item) => item.category === "indic_asr");
  const totalInr = (report?.cases ?? []).reduce((sum, item) => sum + (item.cost_inr ?? 0), 0);
  const totalUsd = (report?.cases ?? []).reduce((sum, item) => sum + item.cost_usd, 0);

  return (
    <>
      <section className="page-heading">
        <div>
          <p className="eyebrow">Evals · quality and cost</p>
          <h1>Model decisions stay measurable.</h1>
          <p>We track extraction quality, deterministic matching, and the cost of every model call.</p>
        </div>
      </section>

      <AsyncState
        state={state}
        title={state === "error" ? "Evaluation results could not load" : "No evaluation results yet"}
        onRetry={() => {
          setState("loading");
          void load();
        }}
        emptyAction={() => void load()}
      >
        {report && (
          <>
            <section className="stats-grid">
              {categories.map(([name, score]) => {
                const count = report.cases.filter((item) => item.category === name).length;
                return (
                  <article className="stat-card" key={name}>
                    <span>{CATEGORY_LABEL[name] ?? name}</span>
                    <strong>{Math.round(score * 100)}%</strong>
                    <p>
                      {count} case{count === 1 ? "" : "s"} · accuracy
                    </p>
                  </article>
                );
              })}
            </section>

            {asrCases.length > 0 && (
              <section className="scatter-panel">
                <div className="chart-head">
                  <div>
                    <p className="eyebrow">Provider comparison</p>
                    <h2>Indic ASR: Sarvam vs Whisper</h2>
                  </div>
                  <span>Same Hindi voice note, both providers</span>
                </div>
                <table className="ledger-table">
                  <thead>
                    <tr>
                      <th>Provider</th>
                      <th>Transcript</th>
                      <th>Amount extracted</th>
                      <th>Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {asrCases.map((item) => (
                      <tr key={item.id}>
                        <td>
                          <strong>{item.provider ?? "—"}</strong>
                        </td>
                        <td lang="hi">{String(item.actual.transcript ?? "—")}</td>
                        <td>{String(item.actual.amount_paise ?? "not extracted")}</td>
                        <td>
                          <span className={`case-result result-${item.passed ? "pass" : "fail"}`}>
                            {item.passed ? <CircleCheck aria-hidden="true" /> : <CircleX aria-hidden="true" />}{" "}
                            {item.passed ? "Pass" : "Fail"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {asrCases[0]?.note && <p className="drawer-intro">{asrCases[0].note}</p>}
              </section>
            )}

            <section className="eval-highlight">
              <strong>
                ₹{totalInr.toFixed(2)} + ${totalUsd.toFixed(3)}
              </strong>
              <p>
                Total measured cost across all {report.count} cases, shown in each provider&apos;s own currency —
                Sarvam bills in INR, OpenAI in USD, and mixing them into one number would be a fiction. Every figure
                comes from the <code>model_calls</code> table.
              </p>
            </section>

            <section className="case-list">
              <header className="section-header">
                <div>
                  <p className="eyebrow">Inspectable results</p>
                  <h2>Per-case evidence</h2>
                </div>
              </header>
              {report.cases.map((item) => (
                <Collapsible.Root className="case-row" key={item.id}>
                  <Collapsible.Trigger className="case-trigger">
                    <span className={`case-result result-${item.passed ? "pass" : "fail"}`}>
                      {item.passed ? <CircleCheck aria-hidden="true" /> : <CircleX aria-hidden="true" />}{" "}
                      {item.passed ? "Pass" : "Fail"}
                    </span>
                    <strong>{item.id}</strong>
                    <span>{CATEGORY_LABEL[item.category] ?? item.category}</span>
                    <span>{item.provider ?? "deterministic"}</span>
                    <ChevronDown aria-hidden="true" />
                  </Collapsible.Trigger>
                  <Collapsible.Content className="case-detail">
                    <p>Expected: {JSON.stringify(item.expected)}</p>
                    <p>Actual: {JSON.stringify(item.actual)}</p>
                    <span>
                      Cost:{" "}
                      {item.cost_inr !== undefined && item.cost_inr > 0
                        ? `₹${item.cost_inr.toFixed(4)} (INR)`
                        : `$${item.cost_usd.toFixed(4)} (USD)`}
                    </span>
                  </Collapsible.Content>
                </Collapsible.Root>
              ))}
            </section>
          </>
        )}
      </AsyncState>
    </>
  );
}
