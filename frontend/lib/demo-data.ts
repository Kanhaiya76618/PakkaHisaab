import type { ExceptionItem, LedgerEntry, LogItem } from "./types";

export const demoLedger: LedgerEntry[] = [
  { id: "led-001", date: "12 Jul 2026", party: "Gupta Traders", description: "Stock purchase · invoice 231", type: "debit", amount: 4800, status: "pending", sourceCount: 1 },
  { id: "led-002", date: "11 Jul 2026", party: "Ramesh General", description: "UPI sale · 617234889912", type: "credit", amount: 7250, status: "verified", sourceCount: 2 },
  { id: "led-003", date: "10 Jul 2026", party: "Sharma wholesale", description: "Khaata credit settled", type: "credit", amount: 12500, status: "verified", sourceCount: 2 },
  { id: "led-004", date: "09 Jul 2026", party: "Airtel Payments", description: "UPI collection", type: "credit", amount: 3400, status: "verified", sourceCount: 1 },
  { id: "led-005", date: "08 Jul 2026", party: "Ramesh", description: "Cash payment from voice note", type: "debit", amount: 2500, status: "verified", sourceCount: 2 },
  { id: "led-006", date: "07 Jul 2026", party: "Gupta Traders", description: "Packaging supplies", type: "debit", amount: 4800, status: "pending", sourceCount: 1 },
];

export const demoExceptions: ExceptionItem[] = [
  { id: "ex-1", kind: "unmatched", title: "Unmatched invoice", titleHi: "बिना मिलान वाला इनवॉइस", detail: "Gupta Traders invoice has no payment within the 3-day window.", amount: 4800 },
  { id: "ex-2", kind: "duplicate", title: "Possible duplicate", titleHi: "संभावित डुप्लिकेट", detail: "Two Gupta Traders invoices share the same amount one day apart.", amount: 4800 },
  { id: "ex-3", kind: "arithmetic", title: "Arithmetic error", titleHi: "गणितीय त्रुटि", detail: "Khaata page total is ₹200 higher than its extracted rows.", amount: 200 },
  { id: "ex-4", kind: "personal", title: "Personal transfer", titleHi: "निजी ट्रांसफर", detail: "₹15,000 brother transfer appears in the business UPI account.", amount: 15000 },
];

export const demoLogs: LogItem[] = [
  { id: "log-1", time: "10:42:08", level: "INFO", hi: "जुलाई UPI फ़ाइल पढ़ रहा है", en: "Reading July UPI file" },
  { id: "log-2", time: "10:42:09", level: "OK", hi: "60 लेनदेन सामान्यीकृत हुए", en: "Normalized 60 transactions" },
  { id: "log-3", time: "10:42:10", level: "INFO", hi: "इनवॉइस और भुगतान का मिलान कर रहा है", en: "Matching invoices and payments" },
  { id: "log-4", time: "10:42:11", level: "WARN", hi: "₹4,800 का कोई मिलान नहीं मिला", en: "No match found for ₹4,800" },
  { id: "log-5", time: "10:42:12", level: "OK", hi: "Evidence Passport पूरा: 4/4 एंट्री स्रोत से जुड़ी हैं", en: "Evidence Passport complete: 4/4 entries sourced" },
];

export const riskMonths = [
  { month: "Apr", received: 176000, declared: 169000 },
  { month: "May", received: 188000, declared: 181000 },
  { month: "Jun", received: 210000, declared: 191000 },
  { month: "Jul", received: 241000, declared: 198000 },
];

export const evalCases = [
  { id: "KH-01", category: "Extraction", result: "Pass", accuracy: 0.96, cost: 0.008 },
  { id: "KH-02", category: "Extraction", result: "Pass", accuracy: 0.91, cost: 0.006 },
  { id: "MT-03", category: "Matching", result: "Pass", accuracy: 1, cost: 0 },
  { id: "CL-04", category: "Classification", result: "Partial", accuracy: 0.75, cost: 0.001 },
  { id: "E2E-01", category: "End-to-end", result: "Pass", accuracy: 0.9, cost: 0.014 },
];
