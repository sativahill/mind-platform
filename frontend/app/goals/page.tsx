"use client";

import { FormEvent, useEffect, useState } from "react";

import ProtectedLayout from "@/components/ProtectedLayout";
import { apiFetch } from "@/lib/api";

interface Goal {
  id: number;
  title: string;
  description: string;
  status: string;
  progress: number;
}

export default function GoalsPage() {
  const [goals, setGoals] = useState<
    Goal[]
  >([]);

  const [title, setTitle] =
    useState("");

  const [description, setDescription] =
    useState("");

  async function loadGoals() {
    const response = await apiFetch(
      "http://127.0.0.1:8000/api/goals/"
    );

    const data = await response.json();

    setGoals(data);
  }

  useEffect(() => {
    loadGoals();
  }, []);

  async function createGoal(
    event: FormEvent
  ) {
    event.preventDefault();

    const response = await apiFetch(
      "http://127.0.0.1:8000/api/goals/",
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          title,
          description,
        }),
      }
    );

    if (response.ok) {
      setTitle("");
      setDescription("");

      await loadGoals();
    }
  }

  return (
    <ProtectedLayout>
      <main className="min-h-screen p-8">
        <h1 className="text-4xl font-bold mb-6">
          Goals
        </h1>

        <form
          onSubmit={createGoal}
          className="space-y-4 mb-10"
        >
          <input
            type="text"
            placeholder="Goal title"
            value={title}
            onChange={(e) =>
              setTitle(e.target.value)
            }
            className="w-full border rounded p-3"
          />

          <textarea
            placeholder="Goal description"
            value={description}
            onChange={(e) =>
              setDescription(
                e.target.value
              )
            }
            className="w-full h-32 border rounded p-3"
          />

          <button
            type="submit"
            className="border rounded px-4 py-2"
          >
            Create Goal
          </button>
        </form>

        <div className="space-y-4">
          {goals.map((goal) => (
            <div
              key={goal.id}
              className="border rounded p-4"
            >
              <h2 className="font-bold text-lg">
                {goal.title}
              </h2>

              <p className="mt-2">
                {goal.description}
              </p>

              <p className="mt-3">
                Status: {goal.status}
              </p>

              <p>
                Progress: {goal.progress}%
              </p>
            </div>
          ))}
        </div>
      </main>
    </ProtectedLayout>
  );
}