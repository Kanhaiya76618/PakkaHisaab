export type Language = "hi" | "en";
export type Theme = "light" | "dark";
export type PageState = "loading" | "empty" | "error" | "success";

export type LedgerEntry = {
  id: string;
  date: string;
  party: string;
  description: string;
  type: "credit" | "debit";
  amount: number;
  status: "verified" | "pending";
  sourceCount: number;
};

export type ExceptionItem = {
  id: string;
  kind: "unmatched" | "duplicate" | "arithmetic" | "personal";
  title: string;
  titleHi: string;
  detail: string;
  amount?: number;
};

export type LogItem = {
  id: string;
  time: string;
  level: "INFO" | "OK" | "WARN" | "ERR";
  hi: string;
  en: string;
};
