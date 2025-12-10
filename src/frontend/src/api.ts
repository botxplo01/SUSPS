/**
 * @author: Lameck David Musumpuka
 * 
 * Base URL for all backend API calls.
 *
 * Defaults to the local FastAPI dev server when VITE_API_BASE_URL is not set.
 */
export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

/**
 * Turn a non-OK fetch response into a user-friendly Error.
 *
 * Uses backend-provided `detail` when present and falls back to a generic
 * status-based message otherwise.
 */
async function buildFriendlyError(res: Response): Promise<never> {
  let message: string;

  // Friendly defaults for common auth/form statuses
  if (res.status === 401) {
    message = "Wrong password or email/username.";
  } else if (res.status === 422) {
    message = "Some of the information you entered is not valid. Please check the fields and try again.";
  } else {
    // Try to use backend-provided detail when available
    try {
      const data = (await res.json().catch(() => null)) as
        | { detail?: unknown }
        | null;
      const detail = data && (data as { detail?: unknown }).detail;
      if (typeof detail === "string" && detail.trim().length > 0) {
        message = detail;
      } else {
        message = `Request failed with status ${res.status}`;
      }
    } catch {
      message = `Request failed with status ${res.status}`;
    }
  }

  throw new Error(message);
}

/**
 * Perform a JSON GET request against the backend with optional query params.
 */
export async function fetchJson<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }

  const res = await fetch(url.toString());
  if (!res.ok) {
    await buildFriendlyError(res);
  }
  return (await res.json()) as T;
}

/**
 * Perform a JSON POST request and parse a JSON response body.
 */
export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    await buildFriendlyError(res);
  }
  return (await res.json()) as T;
}

/**
 * POST JSON and return the raw binary response body (e.g. PDF/ZIP exports).
 */
export async function postBinary(path: string, body: unknown): Promise<Blob> {
  const url = new URL(path, API_BASE_URL);
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    await buildFriendlyError(res);
  }
  return await res.blob();
}

/**
 * Trigger a browser download for an in-memory Blob.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
