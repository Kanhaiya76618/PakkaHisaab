import { z } from "zod";

const DemoStoreResponse = z.object({
  store_id: z.string().uuid(),
  is_public: z.literal(true),
  is_demo: z.literal(true),
});

function apiBaseUrl() {
  const configured = process.env.NEXT_PUBLIC_API_URL;
  if (configured) return configured.replace(/\/$/, "");
  if (process.env.NODE_ENV !== "production") return "http://localhost:8000";
  throw new Error("NEXT_PUBLIC_API_URL is required in production.");
}

export async function loadDemoStore(): Promise<z.infer<typeof DemoStoreResponse>> {
  const response = await fetch(`${apiBaseUrl()}/api/stores/demo`, { method: "POST" });
  if (!response.ok) throw new Error("Demo store could not be opened. Please retry.");
  return DemoStoreResponse.parse(await response.json());
}
