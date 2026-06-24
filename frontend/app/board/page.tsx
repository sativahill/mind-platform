"use client";

import { FormEvent, useEffect, useState } from "react";

import ProtectedLayout from "@/components/ProtectedLayout";
import { apiFetch } from "@/lib/api";

interface Task {
  id: number;
  goal: number;
  title: string;
  description: string;
  status: string;
}

interface Goal {
  id: number;
  title: string;
}

export default function BoardPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);

  const [goalId, setGoalId] =
    useState("");

  const [title, setTitle] =
    useState("");

  const [description, setDescription] =
    useState("");

  async function loadTasks() {
    const response = await apiFetch(
      "http://127.0.0.1:8000/api/board/"
    );

    const data = await response.json();

    setTasks(data);
  }

  async function loadGoals() {
    const response = await apiFetch(
      "http://127.0.0.1:8000/api/goals/"
    );

    const data = await response.json();

    setGoals(data);
  }

  useEffect(() => {
    loadTasks();
    loadGoals();
  }, []);

  async function createTask(
    event: FormEvent
  ) {
    event.preventDefault();

    const response = await apiFetch(
      "http://127.0.0.1:8000/api/board/",
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          goal: Number(goalId),
          title,
          description,
        }),
      }
    );

    if (response.ok) {
      setGoalId("");
      setTitle("");
      setDescription("");

      await loadTasks();
    }
  }

  async function updateStatus(
    taskId: number,
    status: string
  ) {
    const response = await apiFetch(
      `http://127.0.0.1:8000/api/board/${taskId}/`,
      {
        method: "PATCH",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          status,
        }),
      }
    );

    if (response.ok) {
      await loadTasks();
    }
  }

  return (
    <ProtectedLayout>
      <main className="min-h-screen p-8">
        <h1 className="text-4xl font-bold mb-6">
          Board
        </h1>

        <form
          onSubmit={createTask}
          className="space-y-4 mb-10"
        >
          <select
            value={goalId}
            onChange={(e) =>
              setGoalId(e.target.value)
            }
            className="w-full border rounded p-3"
          >
            <option value="">
              Select Goal
            </option>

            {goals.map((goal) => (
              <option
                key={goal.id}
                value={goal.id}
              >
                {goal.title}
              </option>
            ))}
          </select>

          <input
            type="text"
            placeholder="Task title"
            value={title}
            onChange={(e) =>
              setTitle(e.target.value)
            }
            className="w-full border rounded p-3"
          />

          <textarea
            placeholder="Task description"
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
            Create Task
          </button>
        </form>

        <div className="space-y-4">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="border rounded p-4"
            >
              <h2 className="font-bold">
                {task.title}
              </h2>

              <p className="mt-2">
                {task.description}
              </p>

              <p className="mt-2">
                Status: {task.status}
              </p>

              <div className="flex gap-2 mt-3">
                <button
                  onClick={() =>
                    updateStatus(
                      task.id,
                      "todo"
                    )
                  }
                  className="border rounded px-3 py-1"
                >
                  Todo
                </button>

                <button
                  onClick={() =>
                    updateStatus(
                      task.id,
                      "in_progress"
                    )
                  }
                  className="border rounded px-3 py-1"
                >
                  In Progress
                </button>

                <button
                  onClick={() =>
                    updateStatus(
                      task.id,
                      "done"
                    )
                  }
                  className="border rounded px-3 py-1"
                >
                  Done
                </button>
              </div>

              <p className="mt-3">
                Goal ID: {task.goal}
              </p>
            </div>
          ))}
        </div>
      </main>
    </ProtectedLayout>
  );
}