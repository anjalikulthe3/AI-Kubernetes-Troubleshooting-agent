"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { user, loading, isConfigured, signIn, signUp, verifyOtp } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [mode, setMode] = useState<"signin" | "signup" | "verify">("signin");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [loading, user, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    if (mode === "verify") {
      const err = await verifyOtp(email, otpCode.trim());
      if (err) {
        setError(err);
        setSubmitting(false);
        return;
      }
      router.replace("/dashboard");
      return;
    }

    const err =
      mode === "signin"
        ? await signIn(email, password)
        : await signUp(email, password);

    if (err) {
      setError(err);
      setSubmitting(false);
      return;
    }

    if (mode === "signup") {
      // InsForge sent a verification email — show OTP input
      setMode("verify");
      setSubmitting(false);
      return;
    }

    router.replace("/dashboard");
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
        <p className="text-sm text-slate-400">Loading...</p>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl">
        <h1 className="text-2xl font-semibold text-white">AI Kubernetes Agent</h1>
        <p className="mt-2 text-sm text-slate-400">
          {mode === "verify"
            ? `Enter the verification code sent to ${email}`
            : "Sign in to investigate your cluster and view diagnosis history."}
        </p>

        {!isConfigured && (
          <p className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-300">
            InsForge is not configured. Add `NEXT_PUBLIC_INSFORGE_URL` and
            `NEXT_PUBLIC_INSFORGE_ANON_KEY` to `frontend/.env.local`.
          </p>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {mode !== "verify" && (
            <>
              <div>
                <label htmlFor="email" className="text-sm text-slate-400">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none ring-blue-500 focus:ring-2"
                />
              </div>

              <div>
                <label htmlFor="password" className="text-sm text-slate-400">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none ring-blue-500 focus:ring-2"
                />
              </div>
            </>
          )}

          {mode === "verify" && (
            <div>
              <label htmlFor="otp" className="text-sm text-slate-400">
                Verification Code
              </label>
              <input
                id="otp"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                placeholder="e.g. 123456"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-center text-lg tracking-widest text-white outline-none ring-blue-500 focus:ring-2"
              />
              <p className="mt-2 text-xs text-slate-500">
                Check your email inbox for a 6-digit code from InsForge.
              </p>
            </div>
          )}

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={submitting || !isConfigured}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting
              ? "Please wait..."
              : mode === "signin"
                ? "Sign In"
                : mode === "signup"
                  ? "Create Account"
                  : "Verify Email"}
          </button>
        </form>

        {mode === "verify" ? (
          <button
            type="button"
            onClick={() => { setMode("signup"); setError(null); setOtpCode(""); }}
            className="mt-4 text-sm text-slate-400 transition hover:text-white"
          >
            ← Back to sign up
          </button>
        ) : (
          <button
            type="button"
            onClick={() => { setMode(mode === "signin" ? "signup" : "signin"); setError(null); }}
            className="mt-4 text-sm text-slate-400 transition hover:text-white"
          >
            {mode === "signin"
              ? "Need an account? Create one"
              : "Already have an account? Sign in"}
          </button>
        )}

        <p className="mt-6 text-center text-sm text-slate-500">
          <Link href="/" className="hover:text-slate-300">
            Back to home
          </Link>
        </p>
      </div>
    </main>
  );
}
