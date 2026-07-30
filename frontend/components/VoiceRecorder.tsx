"use client";

import { Mic, Square } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { uploadDocument, type UploadResult } from "@/lib/api";

type State = "idle" | "recording" | "processing" | "done" | "error";

export function VoiceRecorder({ storeId }: { storeId: string }) {
  const [state, setState] = useState<State>("idle");
  const [seconds, setSeconds] = useState(0);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (state !== "recording") return;
    const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [state]);

  // Release the microphone if the component unmounts mid-recording.
  useEffect(
    () => () => {
      recorder.current?.stream.getTracks().forEach((track) => track.stop());
    },
    [],
  );

  async function start() {
    setMessage(null);
    setResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
      const media = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      chunks.current = [];
      media.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.current.push(event.data);
      };
      media.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        void send(new Blob(chunks.current, { type: media.mimeType || "audio/webm" }));
      };
      recorder.current = media;
      setSeconds(0);
      setState("recording");
      media.start();
    } catch {
      setState("error");
      setMessage(
        "Microphone access is blocked. Enable it in your browser's site settings, then try again.",
      );
    }
  }

  async function send(blob: Blob) {
    setState("processing");
    try {
      const extension = blob.type.includes("webm") ? "webm" : "wav";
      const file = new File([blob], `voice_note.${extension}`, { type: blob.type || "audio/webm" });
      const uploaded = await uploadDocument(storeId, file, "voice_note");
      setResult(uploaded);
      setState("done");
    } catch (cause) {
      setState("error");
      setMessage(cause instanceof Error ? cause.message : "The voice note could not be processed.");
    }
  }

  function toggle() {
    if (state === "recording") {
      recorder.current?.stop();
      return;
    }
    void start();
  }

  const label =
    state === "recording"
      ? "Stop recording"
      : state === "processing"
        ? "Processing voice note"
        : "Record a Hindi voice note";

  const entry = result?.entries[0];

  return (
    <section className="voice-card">
      <div>
        <span className="eyebrow">Voice note</span>
        <h2>Tell PakkaHisaab what happened</h2>
        <p>
          Say it in Hindi — try &ldquo;Ramesh ko pachchees sau rupaye cash diye&rdquo;. Sarvam Saaras v3
          transcribes it and the amount is parsed by code, never guessed.
        </p>

        {state === "done" && entry && (
          <div className="voice-result">
            <p className="inline-message message-success" lang="hi">
              {entry.description}
            </p>
            <dl className="voice-extract">
              <div>
                <dt>Amount</dt>
                <dd>{entry.amount ?? "not found"}</dd>
              </div>
              <div>
                <dt>Party</dt>
                <dd>{entry.party_name ?? "—"}</dd>
              </div>
              <div>
                <dt>Type</dt>
                <dd>{entry.entry_type}</dd>
              </div>
              <div>
                <dt>Model</dt>
                <dd>
                  <span className="model-badge">{entry.extraction_model}</span>
                </dd>
              </div>
            </dl>
          </div>
        )}

        {state === "done" && !entry && (
          <p className="inline-message message-error" role="status">
            Nothing could be extracted from that recording. Try again, a little slower.
          </p>
        )}

        {message && (
          <p className="inline-message message-error" role="alert">
            {message}
          </p>
        )}
      </div>

      <div className="recorder">
        <motion.span
          className="record-ring"
          animate={state === "recording" && !reduce ? { scale: [1, 1.25, 1], opacity: [0.65, 0, 0.65] } : { scale: 1, opacity: 0 }}
          transition={{ duration: 1.3, repeat: Infinity }}
        />
        <button
          className={`record-button ${state === "recording" ? "is-recording" : ""}`}
          aria-label={label}
          onClick={toggle}
          disabled={state === "processing"}
        >
          {state === "recording" ? <Square aria-hidden="true" /> : <Mic aria-hidden="true" />}
        </button>
        <span aria-live="polite">
          {state === "recording"
            ? `REC · 00:${String(seconds).padStart(2, "0")}`
            : state === "processing"
              ? "Transcribing…"
              : state === "done"
                ? "Transcript ready"
                : "Tap to record"}
        </span>
      </div>
    </section>
  );
}
