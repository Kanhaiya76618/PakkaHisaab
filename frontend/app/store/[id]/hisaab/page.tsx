"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Download, FileText, RefreshCw, Sparkles } from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { AgentTerminal } from "@/components/AgentTerminal";
import { AsyncState } from "@/components/AsyncState";
import { EvidencePassport } from "@/components/EvidencePassport";
import { ExceptionCard } from "@/components/ExceptionCard";
import {
  exportUrl,
  fetchExceptions,
  fetchLedger,
  formatPaise,
  isCredit,
  resolveException,
  runReconciliation,
  type ExceptionItem,
  type LedgerEntry,
} from "@/lib/api";
import type { PageState } from "@/lib/types";

export default function HisaabPage() {
  const { id: storeId } = useParams<{ id: string }>();
  const [state, setState] = useState<PageState>("loading");
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [totalPaise, setTotalPaise] = useState(0);
  const [exceptions, setExceptions] = useState<ExceptionItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [reconciling, setReconciling] = useState(false);
  const [firstLoad, setFirstLoad] = useState(true);

  const load = useCallback(async () => {
    try {
      const [ledger, exceptionList] = await Promise.all([fetchLedger(storeId), fetchExceptions(storeId)]);
      setEntries(ledger.entries);
      setTotalPaise(ledger.total_paise);
      setExceptions(exceptionList.exceptions);
      setState(ledger.entries.length === 0 ? "empty" : "success");
    } catch {
      setState("error");
    }
  }, [storeId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (state === "success") setFirstLoad(false);
  }, [state]);

  async function reconcile() {
    setReconciling(true);
    try {
      const summary = await runReconciliation(storeId);
      await load();
      toast.success("Reconciliation complete", {
        description: `${summary.match_count} matches, ${summary.exception_count} exceptions to review.`,
      });
    } catch {
      toast.error("Reconciliation failed", { description: "The engine did not respond. Try again." });
    } finally {
      setReconciling(false);
    }
  }

  async function resolve(id: string, action: string) {
    setBusy(id);
    try {
      await resolveException(id, action);
      const refreshed = await fetchExceptions(storeId);
      setExceptions(refreshed.exceptions);
      toast.success("Exception resolved", { description: "Your notice risk has been recalculated." });
    } catch {
      toast.error("Could not resolve that exception", { description: "Nothing was changed. Try again." });
    } finally {
      setBusy(null);
    }
  }

  const open = exceptions.filter((item) => item.status === "open");

  return (
    <>
      <section className="page-heading page-heading-split">
        <div>
          <p className="eyebrow">Hisaab · verified cashbook</p>
          <h1>Every number comes with proof.</h1>
          <p>Deterministic matching turns records into a traceable cashbook.</p>
        </div>
        <div className="export-actions">
          <a className="button button-secondary" href={exportUrl(storeId, "csv")}>
            <Download aria-hidden="true" /> CSV
          </a>
          <a className="button button-secondary" href={exportUrl(storeId, "pdf")}>
            <FileText aria-hidden="true" /> Evidence pack
          </a>
        </div>
      </section>

      <AsyncState
        state={state}
        title={state === "error" ? "Your ledger could not load" : "No entries yet"}
        onRetry={() => {
          setState("loading");
          void load();
        }}
        emptyAction={() => void reconcile()}
      >
        <div className="hisaab-layout">
          <div className="ledger-column">
            <section className="ledger-panel">
              <div className="ledger-toolbar">
                <div>
                  <p className="eyebrow">July 2026 · {entries.length} entries</p>
                  <h2>Verified ledger</h2>
                </div>
                <span className="ledger-total">{formatPaise(totalPaise)} net</span>
              </div>
              <div className="ledger-scroll">
                <table className="ledger-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Party &amp; record</th>
                      <th>Evidence</th>
                      <th>Amount</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((entry, index) => {
                      const credit = isCredit(entry.entry_type);
                      return (
                        <motion.tr
                          key={entry.id}
                          initial={firstLoad ? { opacity: 0, y: 6 } : false}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: firstLoad ? Math.min(index, 12) * 0.03 : 0 }}
                        >
                          <td>{entry.entry_date}</td>
                          <td>
                            <button className="ledger-entry-button" onClick={() => setSelectedId(entry.id)}>
                              <strong>{entry.party_name ?? "—"}</strong>
                              <span>{entry.description || entry.entry_type.replace(/_/g, " ")}</span>
                            </button>
                          </td>
                          <td>
                            <button
                              className="evidence-count"
                              onClick={() => setSelectedId(entry.id)}
                              aria-label={`Open the Evidence Passport for ${entry.party_name ?? entry.id}`}
                            >
                              <Sparkles aria-hidden="true" /> {entry.source_kind.replace(/_/g, " ")}
                            </button>
                          </td>
                          <td className={`amount amount-${credit ? "credit" : "debit"}`}>
                            {credit ? "+" : "−"}
                            {formatPaise(entry.amount_paise)}
                          </td>
                          <td>
                            <span className={`status-badge status-${entry.personal ? "pending" : "verified"}`}>
                              {entry.personal ? "Review" : "Verified"}
                            </span>
                          </td>
                        </motion.tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <button
                className="button button-primary button-full reconcile-button"
                onClick={() => void reconcile()}
                disabled={reconciling}
              >
                {reconciling ? (
                  <>
                    <RefreshCw className="spin" aria-hidden="true" /> Reconciling…
                  </>
                ) : (
                  "Run reconciliation"
                )}
              </button>
            </section>

            <section className="exceptions-section">
              <header className="section-header">
                <div>
                  <p className="eyebrow">Needs your review</p>
                  <h2>Exceptions</h2>
                </div>
                <span className="exception-count">{open.length} open</span>
              </header>
              <AnimatePresence>
                {open.map((item) => (
                  <ExceptionCard key={item.id} item={item} busy={busy === item.id} onResolve={resolve} />
                ))}
              </AnimatePresence>
              {open.length === 0 && (
                <div className="resolved-state">
                  <CheckCircle2 aria-hidden="true" />
                  <div>
                    <h3>All exceptions resolved</h3>
                    <p>Your hisaab is pakka.</p>
                  </div>
                </div>
              )}
            </section>
          </div>
          <aside className="terminal-column">
            <AgentTerminal embedded storeId={storeId} />
          </aside>
        </div>
      </AsyncState>

      <EvidencePassport
        ledgerEntryId={selectedId}
        open={Boolean(selectedId)}
        onOpenChange={(next) => {
          if (!next) setSelectedId(null);
        }}
      />
      <AgentTerminal storeId={storeId} />
    </>
  );
}
