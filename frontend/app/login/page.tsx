"use client";

import { ArrowRight, LockKeyhole } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { DEMO_STORE_ID } from "@/lib/constants";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState<"google" | "email" | null>(null);
  async function signInWithGoogle() {
    const supabase = createClient();
    if (!supabase) return setMessage("Add Supabase browser variables to enable sign-in.");
    setLoading("google");
    const { error } = await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: `${window.location.origin}/auth/callback` } });
    if (error) { setMessage(error.message); setLoading(null); }
  }
  async function sendMagicLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const supabase = createClient();
    if (!supabase) return setMessage("Add Supabase browser variables to enable sign-in.");
    setLoading("email");
    const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: `${window.location.origin}/auth/callback` } });
    setLoading(null);
    setMessage(error ? error.message : "Magic link sent — check your email.");
  }
  return <main id="main-content" className="auth-page"><section className="auth-panel"><div className="auth-brand">Pakka<span>Hisaab</span></div><p className="eyebrow">Secure workspace</p><h1>अपने स्टोर में वापस आएं</h1><p className="auth-copy">Google sign-in is fastest on mobile. Magic link email is the secure fallback.</p><button className="button button-primary button-full" onClick={signInWithGoogle} disabled={loading !== null}>{loading === "google" ? "Opening Google…" : <>Continue with Google <ArrowRight aria-hidden="true" /></>}</button><div className="auth-divider">or</div><form onSubmit={sendMagicLink}><label htmlFor="email">Email address</label><input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /><button className="button button-secondary button-full" disabled={loading !== null}>{loading === "email" ? "Sending link…" : "Email me a magic link"}</button></form>{message && <p className="inline-message" role="status">{message}</p>}<p className="auth-note"><LockKeyhole aria-hidden="true" /> No password is stored here. <Link href={`/store/${DEMO_STORE_ID}/hisaab?lang=hi`}>Open the public demo</Link> anytime.</p></section></main>;
}
