"use client";

import { Mic, Square } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

export function VoiceRecorder() {
  const [state, setState] = useState<"idle" | "recording" | "processing" | "done">("idle");
  const [seconds, setSeconds] = useState(0);
  const reduce = useReducedMotion();
  useEffect(() => { if (state !== "recording") return; const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000); return () => window.clearInterval(timer); }, [state]);
  function toggle() { if (state === "recording") { setState("processing"); window.setTimeout(() => setState("done"), 800); } else { setSeconds(0); setState("recording"); } }
  const label = state === "recording" ? "Stop recording" : state === "processing" ? "Processing voice note" : state === "done" ? "Record another voice note" : "Record a Hindi voice note";
  return <section className="voice-card"><div><span className="eyebrow">Voice note</span><h2>Tell PakkaHisaab what happened</h2><p>Try: “Ramesh ko ₹2,500 cash diya.” We will show the transcript before it becomes an entry.</p>{state === "done" && <p className="inline-message message-success">Transcript ready: Ramesh को ₹2,500 cash दिया.</p>}</div><div className="recorder"><motion.span className="record-ring" animate={state === "recording" && !reduce ? { scale: [1, 1.25, 1], opacity: [0.65, 0, 0.65] } : { scale: 1, opacity: 0 }} transition={{ duration: 1.3, repeat: Infinity }} /><button className={`record-button ${state === "recording" ? "is-recording" : ""}`} aria-label={label} onClick={toggle} disabled={state === "processing"}>{state === "recording" ? <Square aria-hidden="true" /> : <Mic aria-hidden="true" />}</button><span aria-live="polite">{state === "recording" ? `REC · 00:${String(seconds).padStart(2, "0")}` : state === "processing" ? "Processing…" : state === "done" ? "Transcript ready" : "Tap to record"}</span></div></section>;
}
