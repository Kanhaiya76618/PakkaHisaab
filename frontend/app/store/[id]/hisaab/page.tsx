"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, CircleAlert, RefreshCw, Sparkles } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { AgentTerminal } from "@/components/AgentTerminal";
import { AsyncState } from "@/components/AsyncState";
import { EvidencePassport } from "@/components/EvidencePassport";
import { ExceptionCard } from "@/components/ExceptionCard";
import { demoExceptions, demoLedger } from "@/lib/demo-data";
import type { ExceptionItem, LedgerEntry } from "@/lib/types";
import { useDemoState } from "@/lib/useDemoState";

const money = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });

export default function HisaabPage() {
  const { id: storeId } = useParams<{ id: string }>();
  const { state, setState } = useDemoState();
  const [entries] = useState(demoLedger);
  const [exceptions, setExceptions] = useState<ExceptionItem[]>(demoExceptions);
  const [selected, setSelected] = useState<LedgerEntry | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [reconciling, setReconciling] = useState(false);
  function resolve(id: string) { setBusy(id); window.setTimeout(() => { setExceptions((items) => items.filter((item) => item.id !== id)); setBusy(null); toast.success("Exception resolved", { description: "The reconciliation queue has been updated." }); }, 450); }
  function reconcile() { setReconciling(true); window.setTimeout(() => { setReconciling(false); toast.success("Reconciliation complete", { description: "Four entries have fresh Evidence Passports." }); }, 900); }
  return <><section className="page-heading page-heading-split"><div><p className="eyebrow">Hisaab · verified cashbook</p><h1>Every number comes with proof.</h1><p>Deterministic matching turns records into a traceable cashbook.</p></div><button className="button button-secondary" onClick={() => setState("error")}>Test error state</button></section><AsyncState state={state} title="Your ledger needs attention" onRetry={() => setState("success")} emptyAction={() => setState("success")}><div className="hisaab-layout"><div className="ledger-column"><section className="ledger-panel"><div className="ledger-toolbar"><div><p className="eyebrow">July 2026</p><h2>Verified ledger</h2></div><span className="ledger-total">₹21,050 net</span></div><div className="ledger-scroll"><table className="ledger-table"><thead><tr><th>Date</th><th>Party & record</th><th>Evidence</th><th>Amount</th><th>Status</th></tr></thead><tbody>{entries.map((entry, index) => <motion.tr key={entry.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.03 }}><td>{entry.date}</td><td><button className="ledger-entry-button" onClick={() => setSelected(entry)}><strong>{entry.party}</strong><span>{entry.description}</span></button></td><td><button className="evidence-count" onClick={() => setSelected(entry)} aria-label={`Open ${entry.sourceCount} evidence sources for ${entry.party}`}><Sparkles aria-hidden="true" /> {entry.sourceCount} sources</button></td><td className={`amount amount-${entry.type}`}>{entry.type === "credit" ? "+" : "−"}{money.format(entry.amount)}</td><td><span className={`status-badge status-${entry.status}`}>{entry.status === "verified" ? "Verified" : "Pending"}</span></td></motion.tr>)}</tbody></table></div><button className="button button-primary button-full reconcile-button" onClick={reconcile} disabled={reconciling}>{reconciling ? <><RefreshCw className="spin" aria-hidden="true" /> Reconciling…</> : "Run reconciliation"}</button></section><section className="exceptions-section"><header className="section-header"><div><p className="eyebrow">Needs your review</p><h2>Exceptions</h2></div><span className="exception-count">{exceptions.length} open</span></header><AnimatePresence>{exceptions.map((item) => <ExceptionCard key={item.id} item={item} busy={busy === item.id} onResolve={resolve} />)}</AnimatePresence>{exceptions.length === 0 && <div className="resolved-state"><CheckCircle2 aria-hidden="true" /><div><h3>All exceptions resolved</h3><p>Your hisaab is pakka.</p></div></div>}</section></div><aside className="terminal-column"><AgentTerminal embedded storeId={storeId} /></aside></div></AsyncState><EvidencePassport entry={selected} open={Boolean(selected)} onOpenChange={(open) => { if (!open) setSelected(null); }} /><AgentTerminal storeId={storeId} /></>;
}
