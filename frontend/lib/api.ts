import { z } from "zod";

const DemoStoreResponse = z.object({
  store_id: z.string().uuid(),
  is_public: z.literal(true),
  is_demo: z.literal(true),
});

export const LedgerEntrySchema = z.object({
  id: z.string(),
  source_id: z.string(),
  entry_type: z.string(),
  party_name: z.string().nullable(),
  amount_paise: z.number().int(),
  entry_date: z.string(),
  upi_ref: z.string().nullable(),
  source_kind: z.string(),
  description: z.string(),
  personal: z.boolean(),
});

const LedgerResponse = z.object({
  entries: z.array(LedgerEntrySchema),
  total_paise: z.number().int(),
});

export const ExceptionSchema = z.object({
  id: z.string(),
  kind: z.enum([
    "unmatched_invoice",
    "possible_duplicate",
    "arithmetic_error",
    "personal_vs_business",
    "amount_mismatch",
  ]),
  related_entry_ids: z.array(z.string()),
  amount_paise: z.number().int(),
  summary_en: z.string(),
  summary_hi: z.string(),
  suggested_action: z.string(),
  party_name: z.string().nullable(),
  status: z.enum(["open", "resolved", "dismissed"]),
  resolution: z.string().optional(),
});

const ExceptionsResponse = z.object({ exceptions: z.array(ExceptionSchema) });

export const EvidenceSchema = z.object({
  ledger_entry_id: z.string(),
  ledger_entry: z.object({
    amount: z.string(),
    amount_paise: z.number().int(),
    party: z.string().nullable(),
    date: z.string(),
    type: z.string(),
    description: z.string(),
  }),
  sources: z.array(
    z.object({
      kind: z.string(),
      filename: z.string(),
      ref: z.string(),
      extracted: z.object({
        amount: z.string(),
        party: z.string().nullable(),
        date: z.string(),
        upi_ref: z.string().nullable(),
      }),
      confidence: z.number(),
      model: z.string(),
      entry_id: z.string(),
      source_id: z.string(),
    }),
  ),
  match_rule: z.string().nullable(),
  match_score: z.number().nullable(),
  match_rule_plain_en: z.string(),
  match_rule_plain_hi: z.string(),
  status: z.string(),
});

export const RiskSchema = z.object({
  risk_score: z.number().int(),
  band: z.enum(["low", "watch", "high"]),
  gap_by_month: z.array(
    z.object({
      month: z.string(),
      upi_received_paise: z.number().int(),
      declared_paise: z.number().int(),
      gap_paise: z.number().int(),
      gap_pct: z.number().int(),
    }),
  ),
  warnings: z.array(
    z.object({
      code: z.string(),
      severity: z.string(),
      message_en: z.string(),
      message_hi: z.string(),
    }),
  ),
  components: z.object({
    gap_points: z.number().int(),
    exception_points: z.number().int(),
    personal_points: z.number().int(),
    total: z.number().int(),
  }),
  personal_pct: z.number().int(),
  open_exception_count: z.number().int(),
  formula: z.string(),
});

export const EvalsSchema = z.object({
  cases: z.array(
    z.object({
      id: z.string(),
      category: z.string(),
      expected: z.record(z.unknown()),
      actual: z.record(z.unknown()),
      passed: z.boolean(),
      cost_usd: z.number(),
      cost_inr: z.number().optional(),
      provider: z.string().optional(),
      note: z.string().optional(),
      measured: z.boolean().optional(),
    }),
  ),
  summary: z.record(z.number()),
  count: z.number().int(),
  measured_count: z.number().int().optional(),
});

export type LedgerEntry = z.infer<typeof LedgerEntrySchema>;
export type ExceptionItem = z.infer<typeof ExceptionSchema>;
export type Evidence = z.infer<typeof EvidenceSchema>;
export type RiskReport = z.infer<typeof RiskSchema>;
export type EvalsReport = z.infer<typeof EvalsSchema>;

export function apiBaseUrl() {
  const configured = process.env.NEXT_PUBLIC_API_URL;
  if (configured) return configured.replace(/\/$/, "");
  if (process.env.NODE_ENV !== "production") return "http://localhost:8000";
  throw new Error("NEXT_PUBLIC_API_URL is required in production.");
}

/** Every amount crossing the wire is integer paise; formatting happens only here. */
export function formatPaise(amountPaise: number): string {
  const negative = amountPaise < 0;
  const absolute = Math.abs(amountPaise);
  const rupees = Math.trunc(absolute / 100);
  const paise = absolute % 100;
  const grouped = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(rupees);
  return `${negative ? "−" : ""}₹${grouped}.${String(paise).padStart(2, "0")}`;
}

const INFLOW_TYPES = new Set(["sale", "payment_in", "credit_received"]);
export function isCredit(entryType: string): boolean {
  return INFLOW_TYPES.has(entryType);
}

async function request<T>(path: string, schema: z.ZodType<T>, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, { cache: "no-store", ...init });
  if (!response.ok) throw new Error(`Request to ${path} failed with ${response.status}.`);
  return schema.parse(await response.json());
}

export async function loadDemoStore() {
  return request("/api/stores/demo", DemoStoreResponse, { method: "POST" });
}

export async function resetDemoStore() {
  return request("/api/demo/reset", z.object({ reset: z.boolean() }), { method: "POST" });
}

export async function runReconciliation(storeId: string) {
  return request(
    `/api/stores/${storeId}/reconcile`,
    z.object({
      ledger_total_paise: z.number().int(),
      exception_count: z.number().int(),
      match_count: z.number().int(),
    }),
    { method: "POST" },
  );
}

export async function fetchLedger(storeId: string) {
  return request(`/api/stores/${storeId}/ledger`, LedgerResponse);
}

export async function fetchExceptions(storeId: string) {
  return request(`/api/stores/${storeId}/exceptions`, ExceptionsResponse);
}

export async function resolveException(exceptionId: string, action: string) {
  return request(`/api/exceptions/${exceptionId}/resolve`, ExceptionSchema, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ action }),
  });
}

export async function fetchEvidence(ledgerEntryId: string) {
  return request(`/api/ledger-entries/${ledgerEntryId}/evidence`, EvidenceSchema);
}

export async function fetchRisk(storeId: string) {
  return request(`/api/stores/${storeId}/risk`, RiskSchema);
}

export async function fetchEvals() {
  return request("/api/evals/run", EvalsSchema);
}

export function exportUrl(storeId: string, fmt: "csv" | "pdf") {
  return `${apiBaseUrl()}/api/stores/${storeId}/export?fmt=${fmt}`;
}
