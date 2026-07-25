"use client";

import * as Collapsible from "@radix-ui/react-collapsible";
import { ChevronDown, CircleCheck, CircleDashed, CircleX } from "lucide-react";
import { Scatter, ScatterChart, Tooltip, XAxis, YAxis, ResponsiveContainer, Legend } from "recharts";
import { AsyncState } from "@/components/AsyncState";
import { evalCases } from "@/lib/demo-data";
import { useDemoState } from "@/lib/useDemoState";

const cards = [{ label: "Extraction", score: "94%", note: "5 cases" }, { label: "Matching", score: "100%", note: "5 cases" }, { label: "Classification", score: "87%", note: "3 cases" }, { label: "End-to-end", score: "90%", note: "2 cases" }];

export default function EvalsPage() {
  const { state, setState } = useDemoState();
  return <><section className="page-heading"><div><p className="eyebrow">Evals · quality and cost</p><h1>Model decisions stay measurable.</h1><p>We track extraction quality, deterministic matching, and the cost of every model call.</p></div><button className="button button-secondary" onClick={() => setState("error")}>Test error state</button></section><AsyncState state={state} title="No evaluation results yet" onRetry={() => setState("success")} emptyAction={() => setState("success")}><section className="stats-grid">{cards.map((card) => <article className="stat-card" key={card.label}><span>{card.label}</span><strong>{card.score}</strong><p>{card.note} · accuracy</p></article>)}</section><section className="eval-highlight"><strong>−42% cost vs all-GPT-4o</strong><p>The router uses the small model where structured tasks do not need full vision reasoning.</p></section><section className="scatter-panel"><div className="chart-head"><div><p className="eyebrow">Router trade-off</p><h2>Cost vs accuracy</h2></div><span>Each dot is an eval case</span></div><div className="scatter-wrap"><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{ top: 12, right: 12, bottom: 12, left: 0 }}><XAxis type="number" dataKey="cost" name="Cost" unit="$" tickLine={false} axisLine={false} /><YAxis type="number" dataKey="accuracy" name="Accuracy" domain={[0.6, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} tickLine={false} axisLine={false} /><Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 12 }} /><Legend /><Scatter name="Evaluation cases" data={evalCases} fill="var(--brand)" /></ScatterChart></ResponsiveContainer></div></section><section className="case-list"><header className="section-header"><div><p className="eyebrow">Inspectable results</p><h2>Per-case evidence</h2></div></header>{evalCases.map((item) => <CaseRow key={item.id} {...item} />)}</section></AsyncState></>;
}

function CaseRow({ id, category, result, accuracy, cost }: (typeof evalCases)[number]) {
  const icon = result === "Pass" ? <CircleCheck aria-hidden="true" /> : result === "Fail" ? <CircleX aria-hidden="true" /> : <CircleDashed aria-hidden="true" />;
  return <Collapsible.Root className="case-row"><Collapsible.Trigger className="case-trigger"><span className={`case-result result-${result.toLowerCase()}`}>{icon} {result}</span><strong>{id}</strong><span>{category}</span><span>{Math.round(accuracy * 100)}% accuracy</span><ChevronDown aria-hidden="true" /></Collapsible.Trigger><Collapsible.Content className="case-detail"><p>This test records the expected outcome, the verified output, and its evidence trace.</p><span>Model cost: ${cost.toFixed(3)}</span></Collapsible.Content></Collapsible.Root>;
}
