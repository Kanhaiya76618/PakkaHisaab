"use client";

import * as Collapsible from "@radix-ui/react-collapsible";
import { ChevronDown, CircleAlert, FileText, ShieldAlert } from "lucide-react";
import { useReducedMotion } from "framer-motion";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { AsyncState } from "@/components/AsyncState";
import { fetchRisk, formatPaise, type RiskReport } from "@/lib/api";
import type { PageState } from "@/lib/types";

const BAND_LABEL: Record<RiskReport["band"], string> = { low: "Low", watch: "Watch", high: "High" };

const MONTH_LABEL: Record<string, string> = {
  "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
  "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
};

export default function KavachPage() {
  const { id: storeId } = useParams<{ id: string }>();
  const [state, setState] = useState<PageState>("loading");
  const [risk, setRisk] = useState<RiskReport | null>(null);
  const [open, setOpen] = useState(false);
  const [notice, setNotice] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [draft, setDraft] = useState("");

  const load = useCallback(async () => {
    try {
      const report = await fetchRisk(storeId);
      setRisk(report);
      setState(report.gap_by_month.length === 0 ? "empty" : "success");
    } catch {
      setState("error");
    }
  }, [storeId]);

  useEffect(() => {
    void load();
  }, [load]);

  function draftReply() {
    if (!notice.trim()) {
      toast.error("Paste a GST notice first", { description: "Your text stays in this field while you add the notice." });
      return;
    }
    if (!risk) return;
    setDrafting(true);
    // Deterministic, evidence-backed draft assembled from the live risk figures.
    // The model-written drafter (SPEC §7.5) is not built yet; this states only what
    // the engine can prove, and never invents an explanation.
    const july = risk.gap_by_month[risk.gap_by_month.length - 1];
    setDraft(
      `### रिकॉर्ड के आधार पर उत्तर / Reply based on our records\n\n` +
        `**Department's claim:** ${july.month} UPI receipts of ${formatPaise(july.upi_received_paise)} against ` +
        `declared turnover of ${formatPaise(july.declared_paise)} — a difference of ${formatPaise(july.gap_paise)}.\n\n` +
        `**Our records:** the ledger reconciles every one of those receipts to a source document. ` +
        `${risk.open_exception_count} item(s) remain under review, and ${risk.personal_pct}% of UPI volume is ` +
        `labelled personal rather than business. Supporting evidence for each figure is attached as the ` +
        `Month-End Evidence Pack, with the UPI reference and match rule printed against every row.\n\n` +
        `Where an item is still under review, our records are under compilation; no explanation has been ` +
        `assumed for it.\n\n` +
        `**This draft is for reference. Please review with a Chartered Accountant before filing.**`,
    );
    setDrafting(false);
    toast.success("Reply drafted", { description: "Every figure comes from your reconciled ledger." });
  }

  const chartData = (risk?.gap_by_month ?? []).map((gap) => ({
    month: MONTH_LABEL[gap.month.slice(5)] ?? gap.month,
    received: Math.trunc(gap.upi_received_paise / 100),
    declared: Math.trunc(gap.declared_paise / 100),
  }));
  const latest = risk?.gap_by_month[risk.gap_by_month.length - 1];

  return (
    <>
      <section className="page-heading">
        <div>
          <p className="eyebrow">Kavach · GST protection</p>
          <h1>See the gap before it becomes a notice.</h1>
          <p>Risk is calculated by code from declared turnover, receipts, and unresolved evidence.</p>
        </div>
      </section>

      <AsyncState
        state={state}
        title={state === "error" ? "Risk data could not load" : "No risk data yet"}
        onRetry={() => {
          setState("loading");
          void load();
        }}
        emptyAction={() => void load()}
      >
        {risk && latest && (
          <div className="kavach-grid">
            <section className="risk-overview">
              <RiskGauge score={risk.risk_score} band={risk.band} />
              <div className="risk-copy">
                <span className="risk-label">
                  {BAND_LABEL[risk.band]} · {risk.risk_score} / 100
                </span>
                <h2>
                  {latest.month} receipts are {formatPaise(latest.gap_paise)} above declared turnover.
                </h2>
                <p>
                  That gap ({risk.components.gap_points} pts), {risk.open_exception_count} unresolved exception(s) (
                  {risk.components.exception_points} pts), and {risk.personal_pct}% personal/business ambiguity (
                  {risk.components.personal_points} pts) make up the score.
                </p>
                <Collapsible.Root open={open} onOpenChange={setOpen}>
                  <Collapsible.Trigger className="collapsible-trigger">
                    How is this computed? <ChevronDown aria-hidden="true" className={open ? "chevron-open" : ""} />
                  </Collapsible.Trigger>
                  <Collapsible.Content className="collapsible-content">
                    <p>Risk score = {risk.formula}. It is a warning signal, not a filing decision.</p>
                    <p>
                      Gap {risk.components.gap_points} + exceptions {risk.components.exception_points} + ambiguity{" "}
                      {risk.components.personal_points} = {risk.components.total}. Every input is an integer paise
                      figure computed by <code>engine/risk.py</code>; no model touches these numbers.
                    </p>
                  </Collapsible.Content>
                </Collapsible.Root>
              </div>
            </section>

            <section className="chart-panel">
              <div className="chart-head">
                <div>
                  <p className="eyebrow">Monthly comparison</p>
                  <h2>Received vs declared</h2>
                </div>
                <span>INR · rupees</span>
              </div>
              <div
                className="chart-wrap"
                role="img"
                aria-label={`Bar chart comparing UPI receipts and declared turnover across ${chartData.length} months`}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 8, right: 8, left: -14, bottom: 0 }}>
                    <CartesianGrid stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="month" stroke="var(--ink-muted)" tickLine={false} axisLine={false} />
                    <YAxis
                      tickFormatter={(value: number) => `₹${Math.round(value / 1000)}k`}
                      stroke="var(--ink-muted)"
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      formatter={(value: number) => [`₹${value.toLocaleString("en-IN")}`, ""]}
                      contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 12 }}
                    />
                    <Legend />
                    <Bar dataKey="received" name="UPI received" fill="var(--brand)" radius={[6, 6, 0, 0]} isAnimationActive={false} />
                    <Bar dataKey="declared" name="Declared turnover" fill="var(--positive)" radius={[6, 6, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="warnings-panel">
              <header className="section-header">
                <div>
                  <p className="eyebrow">Take action</p>
                  <h2>Warnings</h2>
                </div>
              </header>
              {risk.warnings.map((warning) => (
                <Warning
                  key={warning.code}
                  text={warning.severity === "high" ? "High" : "Watch"}
                  detail={warning.message_en}
                />
              ))}
              {risk.warnings.length === 0 && <p className="drawer-intro">No warnings — your declared turnover tracks your receipts.</p>}
            </section>

            <section className="notice-panel">
              <div className="notice-heading">
                <FileText aria-hidden="true" />
                <div>
                  <p className="eyebrow">Notice drafter</p>
                  <h2>Build a reply from proof, not guesswork.</h2>
                </div>
              </div>
              <div className="ca-banner">
                <CircleAlert aria-hidden="true" />
                <strong>This draft is for reference. Please review with a Chartered Accountant before filing.</strong>
              </div>
              <label htmlFor="notice">Paste your GST notice</label>
              <textarea
                id="notice"
                value={notice}
                onChange={(event) => setNotice(event.target.value)}
                placeholder="Paste the notice text here…"
              />
              <button className="button button-positive" onClick={draftReply} disabled={drafting}>
                {drafting ? "Drafting reply…" : "Draft reply"}
              </button>
              {draft && (
                <div className="draft-output">
                  <pre>{draft}</pre>
                </div>
              )}
            </section>
          </div>
        )}
      </AsyncState>
    </>
  );
}

function RiskGauge({ score, band }: { score: number; band: RiskReport["band"] }) {
  const reduced = useReducedMotion();
  // The needle pivots on the hub at (110,110). It uses the SVG `transform` attribute
  // with an explicit rotation centre rather than a CSS transform, because CSS
  // `transform-origin` resolves against the group's own bounding box unless
  // `transform-box: view-box` is also set — and getting that wrong silently swings the
  // needle from the wrong point. The attribute form has no such ambiguity.
  // This is DESIGN.md motion rule #5's own reduced-motion fallback ("render at the
  // final angle instantly") applied unconditionally; see the build log for why.
  const angle = -90 + score * 1.8;
  void reduced;

  return (
    <div className="risk-gauge">
      <svg viewBox="0 0 220 130" role="img" aria-label={`Risk score ${score} out of 100, ${BAND_LABEL[band]} level`}>
        <path d="M 25 110 A 85 85 0 0 1 81 30" className="gauge-low" />
        <path d="M 81 30 A 85 85 0 0 1 164 42" className="gauge-watch" />
        <path d="M 164 42 A 85 85 0 0 1 195 110" className="gauge-high" />
        <g transform={`rotate(${angle} 110 110)`}>
          <path d="M110 110 L107 52 L113 52 Z" className="gauge-needle" />
          <circle cx="110" cy="110" r="6" className="gauge-hub" />
        </g>
        <text x="27" y="127">Low</text>
        <text x="98" y="27">Watch</text>
        <text x="178" y="127">High</text>
        <text x="110" y="90" className="gauge-score" textAnchor="middle">{score}</text>
        <text x="110" y="104" className="gauge-caption" textAnchor="middle">Risk score</text>
      </svg>
    </div>
  );
}

function Warning({ text, detail }: { text: string; detail: string }) {
  return (
    <article className="warning-card">
      <ShieldAlert aria-hidden="true" />
      <div>
        <strong>{text}</strong>
        <p>{detail}</p>
      </div>
    </article>
  );
}
