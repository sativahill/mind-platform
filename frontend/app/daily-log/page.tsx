"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import ProtectedLayout from "@/components/ProtectedLayout";

interface DailyLog {
  id: number;
  date: string;
  content: string;
}

export default function DailyLogPage() {
  const [content, setContent] = useState("");
  const [logs, setLogs] = useState<DailyLog[]>([]);
  const [error, setError] = useState("");

  async function loadLogs() {
    const response = await apiFetch(
      "http://127.0.0.1:8000/api/daily-logs/"
    );

    const data = await response.json();

    if (Array.isArray(data)) {
      setLogs(data);
    }
  }

  useEffect(() => {
    loadLogs();
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setError("");

    const response = await apiFetch(
      "http://127.0.0.1:8000/api/daily-logs/",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          date: new Date()
            .toISOString()
            .split("T")[0],
          content,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      setError(
        typeof data === "object"
          ? JSON.stringify(data)
          : "Ошибка сохранения"
      );
      return;
    }

    setContent("");

    await loadLogs();
  }

  return (
    <ProtectedLayout>
    <main className="min-h-screen p-8">
      <h1 className="text-4xl font-bold mb-6">
        Daily Log
      </h1>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 mb-10"
      >
        <textarea
          value={content}
          onChange={(e) =>
            setContent(e.target.value)
          }
          className="w-full h-48 border rounded p-3"
          placeholder="Что произошло сегодня?"
        />

        <button
          type="submit"
          className="border rounded px-4 py-2"
        >
          Save Daily Log
        </button>

        {error && (
          <p className="text-sm">
            {error}
          </p>
        )}
      </form>

      <div className="space-y-6">
        {logs.map((log) => (
          <div
            key={log.id}
            className="border rounded p-4"
          >
            <h2 className="font-bold mb-2">
              {log.date}
            </h2>

            <p>{log.content}</p>
          </div>
        ))}
      </div>
    </main>
    </ProtectedLayout>
  );
}