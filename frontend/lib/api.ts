const configuredApiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.trim();

if (!configuredApiBaseUrl) {
  throw new Error(
    "NEXT_PUBLIC_API_URL environment variable is required."
  );
}

export const API_BASE_URL =
  configuredApiBaseUrl.replace(/\/+$/, "");

export function apiUrl(path: string) {
  const normalizedPath = path.startsWith("/")
    ? path
    : `/${path}`;

  return `${API_BASE_URL}${normalizedPath}`;
}

export async function apiFetch(
  path: string,
  options: RequestInit = {}
) {
  let accessToken =
    localStorage.getItem("access_token");

  const response = await fetch(apiUrl(path), {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (response.status !== 401) {
    return response;
  }

  const refreshToken =
    localStorage.getItem("refresh_token");

  if (!refreshToken) {
    window.location.href = "/login";
    throw new Error("No refresh token");
  }

  const refreshResponse = await fetch(
    apiUrl("/api/token/refresh/"),
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        refresh: refreshToken,
      }),
    }
  );

  if (!refreshResponse.ok) {
    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "refresh_token"
    );

    window.location.href = "/login";

    throw new Error("Refresh failed");
  }

  const refreshData =
    await refreshResponse.json();

  localStorage.setItem(
    "access_token",
    refreshData.access
  );

  accessToken = refreshData.access;

  return fetch(apiUrl(path), {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${accessToken}`,
    },
  });
}
