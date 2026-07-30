"use client";

import { useParams } from "next/navigation";
import { AgentTerminal } from "@/components/AgentTerminal";
import { UploadZone } from "@/components/UploadZone";
import { VoiceRecorder } from "@/components/VoiceRecorder";

export default function DigitizePage() {
  const { id: storeId } = useParams<{ id: string }>();
  return (
    <>
      <section className="page-heading">
        <div>
          <p className="eyebrow">Digitize · दस्तावेज़</p>
          <h1>Bring scattered records into one place.</h1>
          <p>
            The seeded store is pre-processed so you can look around immediately — but everything
            below is live. Drop in your own invoice, khaata photo, UPI CSV, or Hindi voice note and
            watch it get read.
          </p>
        </div>
      </section>

      {/*
        No AsyncState wrapper here: this page has nothing to load. Its previous four-state
        scaffold was driven by a timer that faked a loading spinner, which was theatre. Real
        progress now belongs to each upload, which reports its own busy / success / error state.
      */}
      <div className="digitize-layout">
        <div className="digitize-content">
          <UploadZone storeId={storeId} />
          <VoiceRecorder storeId={storeId} />
          <section className="source-guidance">
            <h2>Five ways in, one truth out</h2>
            <ol>
              <li>Upload a source document — yours, not ours.</li>
              <li>Review the extracted rows, the confidence, and which model read them.</li>
              <li>Reconcile with code — never invented math.</li>
            </ol>
          </section>
        </div>
        <AgentTerminal embedded storeId={storeId} />
      </div>

      <AgentTerminal storeId={storeId} />
    </>
  );
}
