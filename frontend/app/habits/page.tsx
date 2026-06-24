"use client";

import { FormEvent, useEffect, useState } from "react";

import ProtectedLayout from "@/components/ProtectedLayout";
import { apiFetch } from "@/lib/api";

interface Habit {
  id: number;
  title: string;
  trigger: string;
  action: string;
  reward: string;
  streak: number;
}

export default function HabitsPage() {
  const [habits, setHabits] = useState<
    Habit[]
  >([]);

  const [title, setTitle] =
    useState("");

  const [trigger, setTrigger] =
    useState("");

  const [action, setAction] =
    useState("");

  const [reward, setReward] =
    useState("");

  async function loadHabits() {
    const response = await apiFetch(
      "http://127.0.0.1:8000/api/habits/"
    );

    const data = await response.json();

    setHabits(data);
  }

  useEffect(() => {
    loadHabits();
  }, []);

  async function createHabit(
    event: FormEvent
  ) {
    event.preventDefault();

    const response = await apiFetch(
      "http://127.0.0.1:8000/api/habits/",
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          title,
          trigger,
          action,
          reward,
        }),
      }
    );

    if (response.ok) {
      setTitle("");
      setTrigger("");
      setAction("");
      setReward("");

      await loadHabits();
    }
  }

  async function completeHabit(
    habitId: number
  ) {
    const response = await apiFetch(
      `http://127.0.0.1:8000/api/habits/${habitId}/complete/`,
      {
        method: "POST",
      }
    );

    if (response.ok) {
      await loadHabits();
    }
  }

  return (
    <ProtectedLayout>
      <main className="min-h-screen p-8">
        <h1 className="text-4xl font-bold mb-6">
          Habits
        </h1>

        <form
          onSubmit={createHabit}
          className="space-y-4 mb-10"
        >
          <input
            type="text"
            placeholder="Habit title"
            value={title}
            onChange={(e) =>
              setTitle(e.target.value)
            }
            className="w-full border rounded p-3"
          />

          <input
            type="text"
            placeholder="Trigger"
            value={trigger}
            onChange={(e) =>
              setTrigger(e.target.value)
            }
            className="w-full border rounded p-3"
          />

          <input
            type="text"
            placeholder="Action"
            value={action}
            onChange={(e) =>
              setAction(e.target.value)
            }
            className="w-full border rounded p-3"
          />

          <input
            type="text"
            placeholder="Reward"
            value={reward}
            onChange={(e) =>
              setReward(e.target.value)
            }
            className="w-full border rounded p-3"
          />

          <button
            type="submit"
            className="border rounded px-4 py-2"
          >
            Create Habit
          </button>
        </form>

        <div className="space-y-4">
          {habits.map((habit) => (
            <div
              key={habit.id}
              className="border rounded p-4"
            >
              <h2 className="font-bold text-lg">
                {habit.title}
              </h2>

              <p className="mt-2">
                Trigger:
                {" "}
                {habit.trigger}
              </p>

              <p>
                Action:
                {" "}
                {habit.action}
              </p>

              <p>
                Reward:
                {" "}
                {habit.reward}
              </p>

              <p className="mt-3">
                Streak:
                {" "}
                {habit.streak}
              </p>

              <button
                onClick={() =>
                  completeHabit(
                    habit.id
                  )
                }
                className="border rounded px-4 py-2 mt-3"
              >
                Done Today
              </button>
            </div>
          ))}
        </div>
      </main>
    </ProtectedLayout>
  );
}