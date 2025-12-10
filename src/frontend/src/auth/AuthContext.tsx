/** @author: Lameck David Musumpuka **/

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { AuthUser } from "../types";

interface AuthContextValue {
  user: AuthUser | null;
  signIn: (user: AuthUser) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = "susps_auth_user";

/**
 * Provide authentication state (minimal user object + helpers) to the app.
 *
 * Persists the current user in localStorage so sessions survive page reloads.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as AuthUser;
      if (parsed && typeof parsed.id === "number" && typeof parsed.email === "string") {
        setUser(parsed);
      }
    } catch {
      // Ignore invalid stored state
    }
  }, []);

  useEffect(() => {
    if (!user) {
      window.localStorage.removeItem(STORAGE_KEY);
      return;
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  }, [user]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      signIn: (nextUser: AuthUser) => {
        setUser(nextUser);
      },
      signOut: () => {
        setUser(null);
      },
    }),
    [user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Access the current AuthContext value.
 *
 * Must be called from a descendant of <AuthProvider>.
 */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
