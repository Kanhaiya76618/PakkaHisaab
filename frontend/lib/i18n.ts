import type { Language } from "./types";

export const t = {
  openDemo: { en: "Open demo store", hi: "डेमो स्टोर खोलें" },
  login: { en: "Sign in", hi: "साइन इन करें" },
  logout: { en: "Sign out", hi: "साइन आउट करें" },
  digitize: { en: "Digitize", hi: "डिजिटाइज़" },
  hisaab: { en: "Hisaab", hi: "हिसाब" },
  kavach: { en: "Kavach", hi: "कवच" },
  evals: { en: "Evals", hi: "मूल्यांकन" },
  codexLog: { en: "Codex log", hi: "कोडेक्स लॉग" },
  reconcile: { en: "Run reconciliation", hi: "मिलान चलाएं" },
  reconnecting: { en: "Reconnecting…", hi: "फिर से कनेक्ट हो रहा है…" },
  verified: { en: "Verified", hi: "सत्यापित" },
  pending: { en: "Pending", hi: "लंबित" },
  resolve: { en: "Resolve", hi: "सुलझाएं" },
  upload: { en: "Upload documents", hi: "दस्तावेज़ अपलोड करें" },
  retry: { en: "Try again", hi: "फिर कोशिश करें" },
  loading: { en: "Loading your hisaab…", hi: "आपका हिसाब लोड हो रहा है…" },
  empty: { en: "Nothing here yet", hi: "अभी कुछ नहीं है" },
} as const;

export function copy(key: keyof typeof t, lang: Language): string {
  return t[key][lang];
}
