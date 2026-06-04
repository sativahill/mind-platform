"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import ProtectedLayout from "@/components/ProtectedLayout";

interface Win {
  id: number;
  title: string;
  size: string;
}

export default function WinsPage() {
  const [title, setTitle] = useState("");
  const [size, setSize] = useState("small");
  const [wins, setWins] = useState<Win[]>([]);
  const [error, setError] = useState("");

  async function loadWins() {
    const response = await apiFetch(
      "http://127.0.0.1:8000/api/wins/"
    );

    const data = await response.json();

    if (Array.isArray(data)) {
      setWins(data);
    }
  }

  useEffect(() => {
    loadWins();
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setError("");

    const response = await apiFetch(
      "http://127.0.0.1:8000/api/wins/",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title,
          size,
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

    setTitle("");
    setSize("small");

    await loadWins();
  }

  return (
    <ProtectedLayout>
    <main className="min-h-screen p-8">
      <h1 className="text-4xl font-bold mb-6">
        My Wins
      </h1>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 mb-10"
      >
        <input
          type="text"
          value={title}
          onChange={(e) =>
            setTitle(e.target.value)
          }
          placeholder="Моя победа"
          className="w-full border rounded p-3"
        />

        <select
          value={size}
          onChange={(e) =>
            setSize(e.target.value)
          }
          className="w-full border rounded p-3"
        >
          <option value="small">
            Small
          </option>

          <option value="medium">
            Medium
          </option>

          <option value="large">
            Large
          </option>
        </select>

        <button
          type="submit"
          className="border rounded px-4 py-2"
        >
          Save Win
        </button>

        {error && (
          <p className="text-sm">
            {error}
          </p>
        )}
      </form>

      <div className="space-y-6">
        {wins.map((win) => (
          <div
            key={win.id}
            className="border rounded p-4"
          >
            <h2 className="font-bold">
              {win.title}
            </h2>

            <p className="mt-2">
              {win.size}
            </p>
          </div>
        ))}
      </div>
    </main>
    </ProtectedLayout>
  );
}