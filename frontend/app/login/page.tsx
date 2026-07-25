"use client";

import { ArrowRight, LockKeyhole } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("owner@sharmakirana.in");
  const [loading, setLoading] = useState(false);
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setLoading(true); window.setTimeout(() => router.push("/store/demo/hisaab?lang=hi"), 500); }
  return <main id="main-content" className="auth-page"><section className="auth-panel"><div className="auth-brand">Pakka<span>Hisaab</span></div><p className="eyebrow">Secure workspace</p><h1>अपने स्टोर में वापस आएं</h1><p className="auth-copy">Sign in to keep your documents, evidence, and GST notices private to your store.</p><form onSubmit={submit}><label htmlFor="email">Email address</label><input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /><label htmlFor="password">Password</label><input id="password" type="password" defaultValue="pakkahisaab" autoComplete="current-password" required /><button className="button button-primary button-full" disabled={loading}>{loading ? "Signing in…" : <>Sign in <ArrowRight aria-hidden="true" /></>}</button></form><p className="auth-note"><LockKeyhole aria-hidden="true" /> Demo credentials are prefilled. Production authentication will connect to the protected API.</p></section></main>;
}
