"use client";

import { Moon, Sun } from "lucide-react";
import { motion } from "framer-motion";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useId, useState } from "react";
import type { Language, Theme } from "@/lib/types";

export function ThemeLangControls() {
  const pathname = usePathname();
  const router = useRouter();
  const params = useSearchParams();
  const groupId = useId();
  const [theme, setTheme] = useState<Theme>("light");
  const lang = (params.get("lang") === "en" ? "en" : "hi") as Language;

  useEffect(() => {
    const saved = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    setTheme(saved);
    document.documentElement.dataset.theme = saved;
    document.documentElement.lang = lang;
  }, []);

  useEffect(() => { document.documentElement.lang = lang; }, [lang]);

  function setLanguage(next: Language) {
    const nextParams = new URLSearchParams(params.toString());
    nextParams.set("lang", next);
    router.replace(`${pathname}?${nextParams.toString()}`);
  }

  function toggleTheme() {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.dataset.theme = next;
  }

  return <div className="top-controls">
    <button className="icon-button" onClick={toggleTheme} aria-label={theme === "light" ? "Use dark theme" : "Use light theme"} title={theme === "light" ? "Use dark theme" : "Use light theme"}>
      {theme === "light" ? <Moon aria-hidden="true" /> : <Sun aria-hidden="true" />}
    </button>
    <div className="language-toggle" role="radiogroup" aria-label="Language">
      {(["hi", "en"] as const).map((option) => <button key={option} type="button" role="radio" aria-checked={lang === option} className="language-option" onClick={() => setLanguage(option)}>
        {lang === option && <motion.span layoutId={`lang-pill-${groupId}`} className="language-pill" transition={{ type: "spring", stiffness: 360, damping: 28 }} />}
        <span>{option === "hi" ? "हिं" : "EN"}</span>
      </button>)}
    </div>
  </div>;
}
