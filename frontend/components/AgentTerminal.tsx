"use client";

import { ChevronDown, TerminalSquare, Wifi, WifiOff, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { demoLogs } from "@/lib/demo-data";
import type { Language } from "@/lib/types";

export function AgentTerminal({ lang = "hi", embedded = false }: { lang?: Language; embedded?: boolean }) {
  const [open, setOpen] = useState(embedded);
  const [locked, setLocked] = useState(false);
  const logs = useMemo(() => demoLogs, []);
  const terminal = <section className="agent-terminal" aria-label="Agent activity terminal">
    <header className="terminal-header"><div><TerminalSquare aria-hidden="true" /><span>Agent terminal</span></div><span className="connection-chip"><Wifi aria-hidden="true" /> Live</span>{!embedded && <button className="terminal-close" onClick={() => setOpen(false)} aria-label="Close agent terminal"><X aria-hidden="true" /></button>}</header>
    <div className="terminal-log" onScroll={(event) => { const target = event.currentTarget; setLocked(target.scrollHeight - target.scrollTop - target.clientHeight > 24); }}>
      <AnimatePresence initial={false}>{logs.map((log) => <motion.p key={log.id} className={`terminal-line terminal-${log.level.toLowerCase()}`} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}><time>{log.time}</time><strong>[{log.level}]</strong><span>{lang === "hi" ? log.hi : log.en}</span></motion.p>)}</AnimatePresence>
    </div>
    {locked && <button className="new-logs" onClick={() => setLocked(false)}><ChevronDown aria-hidden="true" /> 2 new messages</button>}
    <footer className="terminal-footer"><WifiOff aria-hidden="true" /><span>Logs replay safely in demo mode</span></footer>
  </section>;
  if (embedded) return terminal;
  return <><button className="terminal-launcher" onClick={() => setOpen(true)} aria-label="Open agent terminal"><TerminalSquare aria-hidden="true" /></button><AnimatePresence>{open && <motion.div className="terminal-popover" initial={{ y: "100%", opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: "100%", opacity: 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }}>{terminal}</motion.div>}</AnimatePresence></>;
}
