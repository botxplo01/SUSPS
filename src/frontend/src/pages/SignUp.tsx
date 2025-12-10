// @author: Lameck David Musumpuka

import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthLayout } from "../components/AuthLayout";
import { FloatingLabelInput } from "../components/FloatingLabelInput";
import { postJson } from "../api";
import type { AuthUser } from "../types";
import { useAuth } from "../auth/AuthContext";

/**
 * Account creation page wired to the /auth/signup endpoint.
 */
export function SignUpPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { signIn } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const user = await postJson<AuthUser>("/auth/signup", {
        email,
        full_name: fullName || undefined,
        password,
      });
      signIn(user);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to sign up.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Smart Urban Simulation and Prediction System"
      subtitle="Developed by David Lameck"
      description="Create an account to explore SUSPS forecasts, simulations, and AI-driven insights."
    >
      <h2 className="text-xl font-semibold text-gray-900">Sign up</h2>
      <p className="mt-2 text-sm text-gray-600">
        Create your account to start exploring urban growth, energy, and mobility scenarios.
      </p>

      <form onSubmit={handleSubmit} className="mt-6">
        <FloatingLabelInput
          id="full-name"
          label="Full name"
          type="text"
          autoComplete="name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
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
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <FloatingLabelInput
          id="confirm-password"
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />

        {error && <p className="mt-4 text-sm text-red-500">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="mt-8 w-full rounded-full bg-black px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-neutral-900 disabled:cursor-not-allowed disabled:bg-neutral-700"
        >
          {loading ? "Creating account..." : "Sign up"}
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-gray-600">
        Already have an account?{" "}
        <Link to="/signin" className="font-medium text-emerald-600 hover:text-emerald-500">
          Sign in here
        </Link>
      </p>
    </AuthLayout>
  );
}
