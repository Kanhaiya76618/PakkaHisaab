"use client";

import { AgentTerminal } from "@/components/AgentTerminal";
import { useParams } from "next/navigation";
import { AsyncState } from "@/components/AsyncState";
import { UploadZone } from "@/components/UploadZone";
import { VoiceRecorder } from "@/components/VoiceRecorder";
import { useDemoState } from "@/lib/useDemoState";

export default function DigitizePage() {
  const { id: storeId } = useParams<{ id: string }>();
  const { state, setState } = useDemoState();
  return <><section className="page-heading"><div><p className="eyebrow">Digitize · दस्तावेज़</p><h1>Bring scattered records into one place.</h1><p>Each original file stays attached to the entry it creates.</p></div><button className="button button-secondary" onClick={() => setState("empty")}>View empty state</button></section><AsyncState state={state} title="No records to digitize" onRetry={() => setState("success")} emptyAction={() => setState("success")}><div className="digitize-layout"><div className="digitize-content"><UploadZone /><VoiceRecorder /><section className="source-guidance"><h2>Five ways in, one truth out</h2><ol><li>Upload a source document.</li><li>Review the extracted rows and confidence.</li><li>Reconcile with code — never invented math.</li></ol></section></div><AgentTerminal embedded storeId={storeId} /></div></AsyncState><AgentTerminal storeId={storeId} /></>;
}
