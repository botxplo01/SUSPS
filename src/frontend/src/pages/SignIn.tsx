// @author: Lameck David Musumpuka

import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AuthLayout } from "../components/AuthLayout";
import { FloatingLabelInput } from "../components/FloatingLabelInput";
import { postJson } from "../api";
import type { AuthUser } from "../types";
import { useAuth } from "../auth/AuthContext";

/**
 * Email/password sign-in page backed by the FastAPI auth endpoints.
 */
export function SignInPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: Location } };
  const { signIn } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await postJson<AuthUser>("/auth/login", { email, password });
      signIn(user);
      const redirectTo = location.state?.from?.pathname || "/dashboard";
      navigate(redirectTo, { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to sign in.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Smart Urban Simulation and Prediction System"
      subtitle="Developed by David Lameck"
      description="Sign in to access the SUSPS dashboard, forecasts, and AI insights."
    >
      <h2 className="text-xl font-semibold text-gray-900">Sign in</h2>
      <p className="mt-2 text-sm text-gray-600">
        Use your email and password to access the Smart Urban Simulation and Prediction System.
      </p>

      <form onSubmit={handleSubmit} className="mt-6">
        <FloatingLabelInput
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <FloatingLabelInput
          id="password"
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error && <p className="mt-4 text-sm text-red-500">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="mt-8 w-full rounded-full bg-black px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-neutral-900 disabled:cursor-not-allowed disabled:bg-neutral-700"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-gray-600">
        Don't have an account?{" "}
        <Link to="/signup" className="font-medium text-emerald-600 hover:text-emerald-500">
          Sign up here
        </Link>
      </p>
    </AuthLayout>
  );
}
