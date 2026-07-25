"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Check, FileImage, FileSpreadsheet, X } from "lucide-react";
import { motion } from "framer-motion";
import type { LedgerEntry } from "@/lib/types";

export function EvidencePassport({ entry, open, onOpenChange }: { entry: LedgerEntry | null; open: boolean; onOpenChange: (next: boolean) => void }) {
  if (!entry) return null;
  const money = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(entry.amount);
  return <Dialog.Root open={open} onOpenChange={onOpenChange}>
    <Dialog.Portal>
      <Dialog.Overlay className="drawer-scrim" />
      <Dialog.Content className="evidence-drawer" aria-describedby="evidence-description">
        <motion.div initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }} transition={{ type: "spring", stiffness: 300, damping: 30 }} className="drawer-motion">
          <header className="drawer-header"><div><Dialog.Title>{money}</Dialog.Title><p>{entry.party}</p><small>{entry.date}</small></div><Dialog.Close className="icon-button" aria-label="Close evidence passport"><X aria-hidden="true" /></Dialog.Close></header>
          <p id="evidence-description" className="drawer-intro">Every figure below links this ledger entry to the source that supports it.</p>
          <section className="source-card"><div className="source-card-head"><span className="kind-badge kind-invoice"><FileImage aria-hidden="true" /> Invoice image</span><span className="model-badge">gpt-4o</span></div><h3>gupta_inv_231.jpg</h3><div className="comparison-grid"><span>Extracted amount</span><strong>{money} <Check aria-label="match" /></strong><span>Ledger amount</span><strong>{money} <Check aria-label="match" /></strong><span>Date</span><strong>12 Jul 2026 <Check aria-label="match" /></strong></div><Confidence value={94} /></section>
          <section className="source-card"><div className="source-card-head"><span className="kind-badge kind-csv"><FileSpreadsheet aria-hidden="true" /> UPI CSV row</span><span className="model-badge">deterministic_parser</span></div><h3>july_upi.csv · row 41</h3><div className="comparison-grid"><span>Extracted amount</span><strong>{money} <Check aria-label="match" /></strong><span>UPI reference</span><strong>617234889912</strong></div><Confidence value={100} /></section>
          <aside className="match-explainer"><strong>Why this matches</strong><p>Matched because the amount and date are identical.</p></aside>
          <ol className="action-timeline"><li><time>12 Jul · 10:42</time><span>Auto-matched by reconciler</span></li><li><time>12 Jul · 10:42</time><span>Evidence Passport created</span></li></ol>
        </motion.div>
      </Dialog.Content>
    </Dialog.Portal>
  </Dialog.Root>;
}

function Confidence({ value }: { value: number }) {
  const level = value > 80 ? "confidence-good" : value >= 50 ? "confidence-watch" : "confidence-low";
  return <div className="confidence"><span>Confidence {value}%</span><div className="confidence-track"><motion.i className={level} initial={{ scaleX: 0 }} animate={{ scaleX: value / 100 }} transition={{ duration: 0.35 }} /></div></div>;
}
