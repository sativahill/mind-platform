export async function apiFetch(
  url: string,
  options: RequestInit = {}
) {
  let accessToken =
    localStorage.getItem("access_token");

  const response = await fetch(url, {
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
    "http://127.0.0.1:8000/api/token/refresh/",
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

  return fetch(url, {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${accessToken}`,
    },
  });
}