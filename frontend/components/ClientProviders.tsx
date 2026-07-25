"use client";

import { MotionConfig } from "framer-motion";
import { Toaster } from "sonner";

export function ClientProviders({ children }: { children: React.ReactNode }) {
  return <MotionConfig reducedMotion="user"><>{children}<Toaster richColors position="bottom-right" /></></MotionConfig>;
}
