"use client";

import { AlertCircle, FilePlus2, RefreshCw } from "lucide-react";
import type { PageState } from "@/lib/types";

type Props = {
  state: PageState;
  title: string;
  onRetry?: () => void;
  emptyAction?: () => void;
  children: React.ReactNode;
};

export function AsyncState({ state, title, onRetry, emptyAction, children }: Props) {
  if (state === "loading") {
    return <div className="skeleton-page" aria-label="Loading content"><div className="skeleton-title" /><div className="skeleton-panel" /><div className="skeleton-panel skeleton-short" /></div>;
  }
  if (state === "empty") {
    return <section className="state-card"><FilePlus2 aria-hidden="true" /><h2>{title}</h2><p>No documents yet — upload a khaata photo to begin.</p><button className="button button-primary" onClick={emptyAction}>Upload a document</button></section>;
  }
  if (state === "error") {
    return <section className="state-card state-error" role="alert"><AlertCircle aria-hidden="true" /><h2>{title}</h2><p>We couldn&apos;t load this view. Check your connection and try again.</p><button className="button button-secondary" onClick={onRetry}><RefreshCw aria-hidden="true" /> Try again</button></section>;
  }
  return <>{children}</>;
}
