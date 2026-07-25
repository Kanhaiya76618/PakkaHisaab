"use client";

import { AlertTriangle, Calculator, Copy, UserRound } from "lucide-react";
import { motion } from "framer-motion";
import type { ExceptionItem } from "@/lib/types";

const config = {
  unmatched: { label: "Unmatched invoice", icon: AlertTriangle },
  duplicate: { label: "Possible duplicate", icon: Copy },
  arithmetic: { label: "Arithmetic error", icon: Calculator },
  personal: { label: "Personal transfer", icon: UserRound },
};

export function ExceptionCard({ item, onResolve, busy }: { item: ExceptionItem; onResolve: (id: string) => void; busy: boolean }) {
  const { label, icon: Icon } = config[item.kind];
  return <motion.article className={`exception-card exception-${item.kind}`} layout="position" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.96 }} transition={{ type: "spring", stiffness: 260, damping: 20 }}>
    <div className="exception-icon"><Icon aria-hidden="true" /></div><div className="exception-copy"><span className="exception-kind">{label}</span><h3>{item.titleHi}</h3><p>{item.detail}</p></div>
    <button className="button button-primary exception-resolve" disabled={busy} onClick={() => onResolve(item.id)}>{busy ? "Resolving…" : "Resolve"}</button>
  </motion.article>;
}
