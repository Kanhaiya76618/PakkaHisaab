"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Check, FileImage, FileSpreadsheet, Mic, NotebookPen, X } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { fetchEvidence, type Evidence } from "@/lib/api";

const KIND_ICON: Record<string, typeof FileImage> = {
  khaata_photo: NotebookPen,
  invoice_image: FileImage,
  upi_csv: FileSpreadsheet,
  bank_csv: FileSpreadsheet,
  voice_note: Mic,
};

const KIND_LABEL: Record<string, string> = {
  khaata_photo: "Khaata photo",
  invoice_image: "Invoice image",
  upi_csv: "UPI CSV row",
  bank_csv: "Bank CSV row",
  voice_note: "Voice note",
  manual: "Manual entry",
};

export function EvidencePassport({
  ledgerEntryId,
  open,
  onOpenChange,
}: {
  ledgerEntryId: string | null;
  open: boolean;
  onOpenChange: (next: boolean) => void;
}) {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!ledgerEntryId) return;
    let active = true;
    setEvidence(null);
    setFailed(false);
    fetchEvidence(ledgerEntryId)
      .then((data) => {
        if (active) setEvidence(data);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
    };
  }, [ledgerEntryId]);

  if (!ledgerEntryId) return null;

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="drawer-scrim" />
        <Dialog.Content className="evidence-drawer" aria-describedby="evidence-description">
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="drawer-motion"
          >
            <header className="drawer-header">
              <div>
                <Dialog.Title>{evidence ? evidence.ledger_entry.amount : "Loading evidence…"}</Dialog.Title>
                <p>{evidence?.ledger_entry.party ?? " "}</p>
                <small>{evidence?.ledger_entry.date ?? " "}</small>
              </div>
              <Dialog.Close className="icon-button" aria-label="Close evidence passport">
                <X aria-hidden="true" />
              </Dialog.Close>
            </header>

            <p id="evidence-description" className="drawer-intro">
              Every figure below links this ledger entry to the source that supports it.
            </p>

            {failed && (
              <section className="state-card state-error" role="alert">
                <h3>Evidence could not load</h3>
                <p>The entry is still in your ledger. Close this drawer and try again.</p>
              </section>
            )}

            {!evidence && !failed && (
              <div className="skeleton-page" aria-label="Loading evidence">
                <div className="skeleton-panel" />
                <div className="skeleton-panel skeleton-short" />
              </div>
            )}

            {evidence?.sources.map((source) => {
              const Icon = KIND_ICON[source.kind] ?? FileImage;
              const matches = source.extracted.amount === evidence.ledger_entry.amount;
              return (
                <section className="source-card" key={source.entry_id}>
                  <div className="source-card-head">
                    <span className={`kind-badge kind-${source.kind}`}>
                      <Icon aria-hidden="true" /> {KIND_LABEL[source.kind] ?? source.kind}
                    </span>
                    <span className="model-badge">{source.model}</span>
                  </div>
                  <h3>
                    {source.filename} · {source.ref}
                  </h3>
                  <div className="comparison-grid">
                    <span>Extracted amount</span>
                    <strong>
                      {source.extracted.amount} {matches ? <Check aria-hidden="true" /> : <X aria-hidden="true" />}
                      <em className="comparison-word">{matches ? "match" : "differs"}</em>
                    </strong>
                    <span>Ledger amount</span>
                    <strong>{evidence.ledger_entry.amount}</strong>
                    <span>Party</span>
                    <strong>{source.extracted.party ?? "—"}</strong>
                    <span>Date</span>
                    <strong>{source.extracted.date}</strong>
                    {source.extracted.upi_ref && (
                      <>
                        <span>UPI reference</span>
                        <strong>{source.extracted.upi_ref}</strong>
                      </>
                    )}
                  </div>
                  <Confidence value={Math.round(source.confidence * 100)} />
                </section>
              );
            })}

            {evidence && (
              <>
                <aside className="match-explainer">
                  <strong>Why this matches</strong>
                  <p>{evidence.match_rule_plain_en}</p>
                  <p lang="hi">{evidence.match_rule_plain_hi}</p>
                  {evidence.match_rule && (
                    <p className="match-rule-code">
                      Rule: {evidence.match_rule} · score {evidence.match_score}
                    </p>
                  )}
                </aside>
                <ol className="action-timeline">
                  <li>
                    <time>{evidence.ledger_entry.date}</time>
                    <span>
                      {evidence.match_rule ? "Auto-matched by the reconciler" : "Recorded, awaiting a matching source"}
                    </span>
                  </li>
                  <li>
                    <time>{evidence.ledger_entry.date}</time>
                    <span>Evidence Passport assembled from {evidence.sources.length} source(s)</span>
                  </li>
                </ol>
              </>
            )}
          </motion.div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function Confidence({ value }: { value: number }) {
  const level = value > 80 ? "confidence-good" : value >= 50 ? "confidence-watch" : "confidence-low";
  return (
    <div className="confidence">
      <span>Confidence {value}%</span>
      <div className="confidence-track">
        <motion.i
          className={level}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: value / 100 }}
          transition={{ duration: 0.35 }}
        />
      </div>
    </div>
  );
}
