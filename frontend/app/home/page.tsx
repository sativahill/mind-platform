"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import ProtectedLayout from "@/components/ProtectedLayout";

interface HomeData {
  daily_logs_count: number;
  wins_count: number;
}

export default function HomePage() {
  const [data, setData] =
    useState<HomeData | null>(null);

  useEffect(() => {
    async function loadHome() {
      const response = await apiFetch(
        "http://127.0.0.1:8000/api/home/"
      );

      const result =
        await response.json();

      setData(result);
    }

    loadHome();
  }, []);

  return (
    <ProtectedLayout>
      {!data ? (
        <div className="p-8">
          Loading...
        </div>
      ) : (
        <main className="min-h-screen p-8">
          <h1 className="text-4xl font-bold mb-6">
            Home
          </h1>

          <div className="space-y-3">
            <p>
              Daily Logs:{" "}
              {data.daily_logs_count}
            </p>

            <p>
              Wins: {data.wins_count}
            </p>
          </div>
        </main>
      )}
    </ProtectedLayout>
  );
}