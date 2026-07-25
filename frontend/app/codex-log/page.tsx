import { TerminalSquare } from "lucide-react";

const lines = [
  ["2026-07-26", "PLAN", "Frontend milestone scoped: semantic tokens, bilingual type, responsive workspace."],
  ["2026-07-26", "DESIGN", "Dual-theme architecture established; explicit saffron/forest brief takes precedence."],
  ["2026-07-26", "BUILD", "Mocked frontend data created so all interaction states work before API integration."],
  ["NEXT", "CONNECT", "Wire typed FastAPI endpoints, authenticated sessions, and WebSocket agent events."],
] as const;

export default function CodexLogPage() {
  return <main id="main-content" className="codex-log-page" tabIndex={-1}><section className="codex-log"><header><TerminalSquare aria-hidden="true" /><div><p>docs/codex-log.md</p><h1>Codex build log</h1></div></header><p className="codex-lead">A concise, inspectable trail from plan to verification.</p><div className="codex-lines">{lines.map(([date, level, text]) => <p key={`${date}-${level}`}><time>{date}</time><strong>[{level}]</strong><span>{text}</span></p>)}</div><section className="codex-principles"><h2>Working agreement</h2><ul><li>All money is integer paise in the backend engine.</li><li>Models extract and explain; deterministic code does the math.</li><li>Every final number must retain its Evidence Passport.</li></ul></section></section></main>;
}
