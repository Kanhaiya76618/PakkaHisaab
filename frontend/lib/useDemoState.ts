"use client";

import { useEffect, useState } from "react";
import type { PageState } from "./types";

export function useDemoState(delay = 420) {
  const [state, setState] = useState<PageState>("loading");
  useEffect(() => { const timer = window.setTimeout(() => setState("success"), delay); return () => window.clearTimeout(timer); }, [delay]);
  return { state, setState };
}
