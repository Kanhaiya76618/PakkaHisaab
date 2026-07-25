import { readFile } from "node:fs/promises";
import path from "node:path";
import { TerminalSquare } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function CodexLogPage() {
  const logPath = path.join(process.cwd(), "..", "docs", "codex-log.md");
  const buildLog = await readFile(logPath, "utf8");

  return <main id="main-content" className="codex-log-page" tabIndex={-1}><section className="codex-log"><header><TerminalSquare aria-hidden="true" /><div><p>docs/codex-log.md</p><h1>Codex build log</h1></div></header><p className="codex-lead">A concise, inspectable trail from plan to verification.</p><pre className="codex-markdown">{buildLog}</pre></section></main>;
}
