"use client";

import Link from "next/link";
import { BookOpenCheck, FileUp, ShieldCheck } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { Suspense, useState } from "react";
import { useRouter } from "next/navigation";
import { ThemeLangControls } from "@/components/ThemeLangControls";
import { DEMO_STORE_ID } from "@/lib/constants";
import { loadDemoStore } from "@/lib/api";

const features = [
  { icon: FileUp, title: "Digitize", hi: "कागज़ से साफ़ एंट्री तक", text: "Read khaata photos, invoices, CSVs, and Hindi voice notes." },
  { icon: BookOpenCheck, title: "Reconcile", hi: "हर अंक का सबूत", text: "Match records with deterministic rules and explain every result." },
  { icon: ShieldCheck, title: "Protect", hi: "GST से पहले सतर्क", text: "See risk early and draft replies from verified evidence." },
];

export default function LandingPage() {
  const reduce = useReducedMotion();
  const router = useRouter();
  const [openingDemo, setOpeningDemo] = useState(false);

  async function openDemo() {
    setOpeningDemo(true);
    try {
      const demo = await loadDemoStore();
      router.push(`/store/${demo.store_id}/hisaab?lang=hi`);
    } catch {
      router.push(`/store/${DEMO_STORE_ID}/hisaab?lang=hi`);
    }
  }

  return <main id="main-content" className="landing" tabIndex={-1}>
    <header className="landing-header"><Link className="landing-wordmark" href="/">Pakka<span>Hisaab</span></Link><div><Suspense fallback={null}><ThemeLangControls /></Suspense></div></header>
    <section className="hero"><div className="hero-copy"><p className="eyebrow">For kirana stores and growing MSMEs</p><h1>अपना हिसाब,<br />पक्का करो</h1><motion.span className="hero-underline" initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ duration: reduce ? 0 : 0.6, delay: 0.15 }} /><p className="hero-subtitle">Five ways in, one trusted truth out. PakkaHisaab turns scattered records into an evidence-backed cashbook.</p><div className="hero-actions"><button className="button button-primary button-large" onClick={openDemo} disabled={openingDemo}>{openingDemo ? "Opening demo…" : "Open demo store"}</button><a href="#how-it-works" className="text-link">See how evidence works</a></div></div><KhaataIllustration /></section>
    <section id="how-it-works" className="feature-grid" aria-label="What PakkaHisaab does">{features.map(({ icon: Icon, title, hi, text }) => <motion.article key={title} className="feature-card" whileHover={{ y: -4 }} whileTap={{ scale: 0.99 }} transition={{ duration: 0.2 }}><span className="feature-icon"><Icon aria-hidden="true" /></span><p className="feature-hi">{hi}</p><h2>{title}</h2><p>{text}</p></motion.article>)}</section>
    <footer className="landing-footer">AI reads and reasons. <strong>Only code touches the math.</strong></footer>
  </main>;
}

function KhaataIllustration() {
  const reduce = useReducedMotion();
  return <div className="khaata-art" aria-label="Illustration of a handwritten financial notebook"><div className="notebook-tab">शर्मा किराना</div><div className="notebook-lines">{["रमेश      ₹2,500", "गुप्ता ट्रेडर्स  ₹4,800", "UPI बिक्री   +₹7,250", "कुल        ₹18,730"].map((line, index) => <motion.p key={line} initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }} transition={{ duration: reduce ? 0 : 0.45, delay: index * 0.15 }}>{line}</motion.p>)}</div><span className="notebook-stamp">स्रोत जुड़ा</span></div>;
}
