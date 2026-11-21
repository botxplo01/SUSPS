/** @author: David Lameck **/

import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

interface RequireAuthProps {
  children: JSX.Element;
}

/**
 * Guard that redirects unauthenticated users to /signin.
 *
 * Preserves the original location in router state so users can be
 * redirected back after signing in.
 */
export function RequireAuth({ children }: RequireAuthProps) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/signin" state={{ from: location }} replace />;
  }

  return children;
}

