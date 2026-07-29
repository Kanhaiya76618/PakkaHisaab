"use client";

import { AlertTriangle, Calculator, Copy, Scale, UserRound } from "lucide-react";
import { motion } from "framer-motion";
import { formatPaise, type ExceptionItem } from "@/lib/api";

const config: Record<ExceptionItem["kind"], { label: string; icon: typeof AlertTriangle; accent: string }> = {
  unmatched_invoice: { label: "Unmatched invoice", icon: AlertTriangle, accent: "unmatched" },
  possible_duplicate: { label: "Possible duplicate", icon: Copy, accent: "duplicate" },
  arithmetic_error: { label: "Arithmetic error", icon: Calculator, accent: "arithmetic" },
  personal_vs_business: { label: "Personal transfer", icon: UserRound, accent: "personal" },
  amount_mismatch: { label: "Amount mismatch", icon: Scale, accent: "arithmetic" },
};

const ACTION_LABEL: Record<string, string> = {
  create_entry: "Create entry",
  merge_duplicates: "Merge duplicates",
  mark_personal: "Mark personal",
  adjust_amount: "Adjust amount",
  ask_user: "Resolve",
};

export function ExceptionCard({
  item,
  onResolve,
  busy,
}: {
  item: ExceptionItem;
  onResolve: (id: string, action: string) => void;
  busy: boolean;
}) {
  const { label, icon: Icon, accent } = config[item.kind];
  const action = ACTION_LABEL[item.suggested_action] ?? "Resolve";
  return (
    <motion.article
      className={`exception-card exception-${accent}`}
      layout="position"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ type: "spring", stiffness: 260, damping: 20 }}
    >
      <div className="exception-icon">
        <Icon aria-hidden="true" />
      </div>
      <div className="exception-copy">
        <span className="exception-kind">
          {label} · {formatPaise(item.amount_paise)}
        </span>
        <h3>{item.summary_hi}</h3>
        <p>{item.summary_en}</p>
      </div>
      <button
        className="button button-primary exception-resolve"
        disabled={busy}
        onClick={() => onResolve(item.id, item.suggested_action)}
      >
        {busy ? "Resolving…" : action}
      </button>
    </motion.article>
  );
}
