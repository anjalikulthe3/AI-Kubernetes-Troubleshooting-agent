"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { insforge, isInsForgeConfigured } from "@/lib/insforge";
import type { InsForgeUser } from "@/types";

interface AuthContextValue {
  user: InsForgeUser | null;
  loading: boolean;
  isConfigured: boolean;
  signIn: (email: string, password: string) => Promise<string | null>;
  signUp: (email: string, password: string) => Promise<string | null>;
  verifyOtp: (email: string, token: string) => Promise<string | null>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<InsForgeUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (!insforge) {
        setLoading(false);
        return;
      }

      try {
        const { data } = await insforge.auth.getCurrentUser();
        if (data?.user) {
          setUser({
            id: data.user.id,
            email: data.user.email,
          });
        }
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    if (!insforge) {
      return "InsForge is not configured.";
    }

    const { data, error } = await insforge.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      return error.message || "Unable to sign in.";
    }

    if (data?.user) {
      setUser({
        id: data.user.id,
        email: data.user.email,
      });
    }

    return null;
  }, []);

  const signUp = useCallback(async (email: string, password: string) => {
    if (!insforge) {
      return "InsForge is not configured.";
    }

    const { data, error } = await insforge.auth.signUp({
      email,
      password,
    });

    if (error) {
      return error.message || "Unable to create account.";
    }

    if (data?.user) {
      setUser({
        id: data.user.id,
        email: data.user.email,
      });
    }

    return null;
  }, []);

  const verifyOtp = useCallback(async (email: string, token: string) => {
    if (!insforge) {
      return "InsForge is not configured.";
    }

    const { data, error } = await insforge.auth.verifyEmail({
      email,
      otp: token,
    });

    if (error) {
      return error.message || "Invalid verification code.";
    }

    if (data?.user) {
      setUser({
        id: data.user.id,
        email: data.user.email,
      });
    }

    return null;
  }, []);

  const signOut = useCallback(async () => {
    if (insforge) {
      await insforge.auth.signOut();
    }
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isConfigured: isInsForgeConfigured,
      signIn,
      signUp,
      verifyOtp,
      signOut,
    }),
    [user, loading, signIn, signUp, verifyOtp, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
