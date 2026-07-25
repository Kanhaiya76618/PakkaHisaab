"use client";

import { ChevronDown, TerminalSquare, Wifi, WifiOff, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import type { Language } from "@/lib/types";
import { DEMO_STORE_ID } from "@/lib/constants";

type LogLevel = "info" | "success" | "warning" | "error";
type ConnectionState = "connecting" | "live" | "reconnecting" | "offline";
type AgentLog = { id: string; time: string; agent: string; level: LogLevel; message_en: string; message_hi: string; detail: string | null };

function websocketUrl(storeId: string) {
  const configured = process.env.NEXT_PUBLIC_WS_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const base = configured.replace(/^http/, "ws").replace(/\/$/, "");
  return `${base}/ws/stores/${storeId}/agent-log`;
}

function connectionCopy(state: ConnectionState) {
  if (state === "live") return "Live";
  if (state === "connecting") return "Connecting";
  if (state === "reconnecting") return "Reconnecting";
  return "Offline";
}

export function AgentTerminal({ lang = "hi", embedded = false, storeId = DEMO_STORE_ID }: { lang?: Language; embedded?: boolean; storeId?: string }) {
  const [open, setOpen] = useState(embedded);
  const [locked, setLocked] = useState(false);
  const [newLogs, setNewLogs] = useState(0);
  const [connection, setConnection] = useState<ConnectionState>("connecting");
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const logRef = useRef<HTMLDivElement>(null);
  const lockedRef = useRef(false);

  useEffect(() => {
    if (!embedded && !open) {
      setConnection("offline");
      return;
    }
    let disposed = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: number | undefined;
    let attempts = 0;
    const connect = () => {
      setConnection(attempts ? "reconnecting" : "connecting");
      socket = new WebSocket(websocketUrl(storeId));
      socket.onopen = () => { attempts = 0; setConnection("live"); };
      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data) as Omit<AgentLog, "id" | "time">;
          if (!event.agent || !event.level || !event.message_en || !event.message_hi) return;
          const log = { ...event, id: `${Date.now()}-${Math.random()}`, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) } as AgentLog;
          setLogs((current) => [...current.slice(-79), log]);
          if (lockedRef.current) setNewLogs((current) => current + 1);
        } catch { /* Ignore malformed frames; stream remains available. */ }
      };
      socket.onerror = () => socket?.close();
      socket.onclose = () => {
        if (disposed) return;
        attempts += 1;
        setConnection("reconnecting");
        const delay = Math.min(1000 * 2 ** (attempts - 1), 15000);
        reconnectTimer = window.setTimeout(connect, delay);
      };
    };
    connect();
    return () => { disposed = true; if (reconnectTimer) window.clearTimeout(reconnectTimer); socket?.close(); };
  }, [storeId, embedded, open]);

  useEffect(() => {
    if (!locked && logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs, locked]);

  function handleScroll() {
    const target = logRef.current;
    if (!target) return;
    const isLocked = target.scrollHeight - target.scrollTop - target.clientHeight > 24;
    lockedRef.current = isLocked;
    setLocked(isLocked);
    if (!isLocked) setNewLogs(0);
  }

  const terminal = <section className="agent-terminal" aria-label="Agent activity terminal">
    <header className="terminal-header"><div><TerminalSquare aria-hidden="true" /><span>Agent terminal</span></div><span className={`connection-chip connection-${connection}`}><Wifi aria-hidden="true" /> {connectionCopy(connection)}</span>{!embedded && <button className="terminal-close" onClick={() => setOpen(false)} aria-label="Close agent terminal"><X aria-hidden="true" /></button>}</header>
    <div ref={logRef} className="terminal-log" onScroll={handleScroll} aria-live="polite">
      <AnimatePresence initial={false}>{logs.map((log) => <motion.p key={log.id} className={`terminal-line terminal-${log.level}`} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}><time>{log.time}</time><strong>[{log.level.toUpperCase()}]</strong><span>{lang === "hi" ? log.message_hi : log.message_en}</span></motion.p>)}</AnimatePresence>
      {logs.length === 0 && <p className="terminal-line terminal-info"><time>—</time><strong>[WAIT]</strong><span>Connecting to the agent log…</span></p>}
    </div>
    {locked && newLogs > 0 && <button className="new-logs" onClick={() => { setLocked(false); lockedRef.current = false; setNewLogs(0); }}><ChevronDown aria-hidden="true" /> {newLogs} new {newLogs === 1 ? "message" : "messages"}</button>}
    <footer className="terminal-footer"><WifiOff aria-hidden="true" /><span>{connection === "live" ? "Structured logs stream from the backend" : "Reconnect backoff is active"}</span></footer>
  </section>;
  if (embedded) return terminal;
  return <><button className="terminal-launcher" onClick={() => setOpen(true)} aria-label="Open agent terminal"><TerminalSquare aria-hidden="true" /></button><AnimatePresence>{open && <motion.div className="terminal-popover" initial={{ y: "100%", opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: "100%", opacity: 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }}>{terminal}</motion.div>}</AnimatePresence></>;
}
