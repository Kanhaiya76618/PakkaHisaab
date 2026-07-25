import type { Metadata } from "next";
import "./globals.css";
import { ClientProviders } from "@/components/ClientProviders";

export const metadata: Metadata = {
  title: "PakkaHisaab · Five ways in, one truth out",
  description: "Evidence-backed financial digitization for Indian microbusinesses.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="hi" suppressHydrationWarning><body><a className="skip-link" href="#main-content">Skip to main content</a><ClientProviders>{children}</ClientProviders></body></html>;
}
