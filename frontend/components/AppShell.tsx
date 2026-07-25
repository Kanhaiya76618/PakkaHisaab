"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BookOpenCheck, ChevronLeft, ChevronRight, ClipboardList, FileUp, ShieldCheck, TerminalSquare } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Suspense, useState } from "react";
import { ThemeLangControls } from "./ThemeLangControls";

const navigation = [
  { href: "/store/demo/digitize", label: "Digitize", icon: FileUp },
  { href: "/store/demo/hisaab", label: "Hisaab", icon: BookOpenCheck },
  { href: "/store/demo/kavach", label: "Kavach", icon: ShieldCheck },
  { href: "/store/demo/evals", label: "Evals", icon: BarChart3 },
  { href: "/codex-log", label: "Codex log", icon: TerminalSquare },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState(false);

  return <div className="app-frame">
    <aside className={`sidebar ${expanded ? "sidebar-expanded" : ""}`} aria-label="Primary navigation">
      <Link className="sidebar-brand" href="/store/demo/hisaab" aria-label="PakkaHisaab home"><ClipboardList aria-hidden="true" /></Link>
      <nav className="sidebar-nav">
        {navigation.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return <Link key={href} href={href} className={`nav-link ${active ? "nav-active" : ""}`} aria-current={active ? "page" : undefined} title={label}>
            {active && <motion.span className="nav-indicator" layoutId="nav-indicator" transition={{ type: "spring", stiffness: 350, damping: 30 }} />}
            <Icon aria-hidden="true" /><span className="nav-label">{label}</span>
          </Link>;
        })}
      </nav>
      <button className="sidebar-toggle" onClick={() => setExpanded((current) => !current)} aria-label={expanded ? "Collapse navigation" : "Expand navigation"}>
        {expanded ? <ChevronLeft aria-hidden="true" /> : <ChevronRight aria-hidden="true" />}
      </button>
    </aside>
    <div className="app-content">
      <header className="topbar">
        <div className="wordmark"><Link href="/store/demo/hisaab">Pakka<span>Hisaab</span></Link><p>Five ways in, one truth out</p></div>
        <div className="topbar-right"><span className="demo-badge">Demo · Sharma Kirana Store</span><Suspense fallback={null}><ThemeLangControls /></Suspense></div>
      </header>
      <main id="main-content" className="main-content" tabIndex={-1}>{children}</main>
    </div>
    <nav className="bottom-nav" aria-label="Mobile navigation">
      {navigation.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return <Link key={href} href={href} className={`bottom-link ${active ? "bottom-active" : ""}`} aria-current={active ? "page" : undefined}><Icon aria-hidden="true" /><span>{label}</span></Link>;
      })}
    </nav>
  </div>;
}
