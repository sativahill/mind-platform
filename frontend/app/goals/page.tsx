"use client";

import "./goals.css";

import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import ProtectedLayout from "@/components/ProtectedLayout";
import { apiFetch } from "@/lib/api";

type GoalStatus =
  | "active"
  | "completed"
  | "archived";

type GoalFilter =
  | "active"
  | "completed"
  | "archived";

type TaskStatus =
  | "todo"
  | "in_progress"
  | "done";

type RequestState =
  | "idle"
  | "saving"
  | "deleting"
  | "archiving";

interface Goal {
  id: number;
  title: string;
  description: string;
  why_it_matters: string;
  previous_obstacles: string;
  target_date: string | null;
  status: GoalStatus;
  progress: number;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

interface BoardTask {
  id: number;
  goal: number;
  title: string;
  description: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

interface GoalDraft {
  title: string;
  description: string;
  why_it_matters: string;
  previous_obstacles: string;
  target_date: string;
}

interface TaskDraft {
  title: string;
  description: string;
}

const GOALS_API_URL =
  "/api/goals/";

const BOARD_API_URL =
  "/api/board/";

const EMPTY_GOAL_DRAFT: GoalDraft = {
  title: "",
  description: "",
  why_it_matters: "",
  previous_obstacles: "",
  target_date: "",
};

const EMPTY_TASK_DRAFT: TaskDraft = {
  title: "",
  description: "",
};

function parseApiDate(value: string) {
  const [year, month, day] = value
    .split("-")
    .map(Number);

  return new Date(
    year,
    month - 1,
    day
  );
}

function formatShortDate(value: string) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    }
  ).format(parseApiDate(value));
}

function formatCompletedDate(
  value: string
) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      day: "numeric",
      month: "long",
      year: "numeric",
    }
  ).format(new Date(value));
}

function formatCompletedShortDate(
  value: string
) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    }
  ).format(new Date(value));
}

function getTodayForApi() {
  const today = new Date();

  const year = today.getFullYear();

  const month = String(
    today.getMonth() + 1
  ).padStart(2, "0");

  const day = String(
    today.getDate()
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function getDaysUntil(
  targetDate: string | null
) {
  if (!targetDate) {
    return null;
  }

  const today = new Date();
  const target = parseApiDate(
    targetDate
  );

  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);

  return Math.ceil(
    (
      target.getTime() -
      today.getTime()
    ) /
      86_400_000
  );
}

function getDeadlineLabel(
  goal: Goal
) {
  if (goal.status === "completed") {
    return goal.completed_at
      ? `Completed ${formatCompletedDate(
          goal.completed_at
        )}`
      : "Completed";
  }

  if (!goal.target_date) {
    return "No deadline";
  }

  const daysUntil = getDaysUntil(
    goal.target_date
  );

  if (daysUntil === null) {
    return formatShortDate(
      goal.target_date
    );
  }

  if (daysUntil < 0) {
    const overdueDays = Math.abs(
      daysUntil
    );

    return `${overdueDays} ${
      overdueDays === 1
        ? "day"
        : "days"
    } overdue`;
  }

  if (daysUntil === 0) {
    return "Due today";
  }

  if (daysUntil === 1) {
    return "Due tomorrow";
  }

  return `${daysUntil} days left`;
}

function getTaskStatusLabel(
  status: TaskStatus
) {
  const labels: Record<
    TaskStatus,
    string
  > = {
    todo: "To do",
    in_progress: "In progress",
    done: "Done",
  };

  return labels[status];
}

function pluralize(
  count: number,
  singular: string,
  plural = `${singular}s`
) {
  return count === 1
    ? singular
    : plural;
}

function getNextTaskStatus(
  status: TaskStatus
): TaskStatus {
  if (status === "todo") {
    return "in_progress";
  }

  if (status === "in_progress") {
    return "done";
  }

  return "todo";
}

function getErrorMessage(
  data: unknown
) {
  if (
    typeof data === "object" &&
    data !== null
  ) {
    const response = data as Record<
      string,
      unknown
    >;

    if (
      typeof response.detail ===
      "string"
    ) {
      return response.detail;
    }

    for (
      const value of Object.values(
        response
      )
    ) {
      if (
        Array.isArray(value) &&
        typeof value[0] === "string"
      ) {
        return value[0];
      }

      if (
        typeof value === "string"
      ) {
        return value;
      }

      if (
        typeof value === "object" &&
        value !== null
      ) {
        const nested =
          value as Record<
            string,
            unknown
          >;

        for (
          const nestedValue of Object.values(
            nested
          )
        ) {
          if (
            Array.isArray(
              nestedValue
            ) &&
            typeof nestedValue[0] ===
              "string"
          ) {
            return nestedValue[0];
          }
        }
      }
    }
  }

  return "Something went wrong. Please try again.";
}

function normalizeDraft(
  goal: Goal
): GoalDraft {
  return {
    title: goal.title,
    description:
      goal.description ?? "",
    why_it_matters:
      goal.why_it_matters ?? "",
    previous_obstacles:
      goal.previous_obstacles ?? "",
    target_date:
      goal.target_date ?? "",
  };
}

function isSameDraft(
  draft: GoalDraft,
  goal: Goal | null
) {
  if (!goal) {
    return false;
  }

  const original =
    normalizeDraft(goal);

  return (
    draft.title ===
      original.title &&
    draft.description ===
      original.description &&
    draft.why_it_matters ===
      original.why_it_matters &&
    draft.previous_obstacles ===
      original.previous_obstacles &&
    draft.target_date ===
      original.target_date
  );
}

export default function GoalsPage() {
  const today = useMemo(
    () => getTodayForApi(),
    []
  );

  const [goals, setGoals] =
    useState<Goal[]>([]);

  const [tasks, setTasks] =
    useState<BoardTask[]>([]);

  const [filter, setFilter] =
    useState<GoalFilter>("active");

  const [
    selectedGoalId,
    setSelectedGoalId,
  ] = useState<number | null>(
    null
  );

  const [
    editingGoal,
    setEditingGoal,
  ] = useState<Goal | null>(
    null
  );

  const [goalDraft, setGoalDraft] =
    useState<GoalDraft>(
      EMPTY_GOAL_DRAFT
    );

  const [taskDraft, setTaskDraft] =
    useState<TaskDraft>(
      EMPTY_TASK_DRAFT
    );

  const [
    isComposerOpen,
    setIsComposerOpen,
  ] = useState(false);

  const [
    isTaskComposerOpen,
    setIsTaskComposerOpen,
  ] = useState(false);

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    isTasksLoading,
    setIsTasksLoading,
  ] = useState(true);

  const [
    requestState,
    setRequestState,
  ] = useState<RequestState>(
    "idle"
  );

  const [
    taskRequestId,
    setTaskRequestId,
  ] = useState<number | null>(
    null
  );

  const [
    isCreatingTask,
    setIsCreatingTask,
  ] = useState(false);

  const [
    deleteTarget,
    setDeleteTarget,
  ] = useState<Goal | null>(
    null
  );

  const [error, setError] =
    useState("");

  const [taskError, setTaskError] =
    useState("");

  const visibleGoals =
    useMemo(
      () =>
        goals.filter(
          (goal) =>
            goal.status === filter
        ),
      [goals, filter]
    );

  const selectedGoal =
    useMemo(() => {
      return (
        visibleGoals.find(
          (goal) =>
            goal.id ===
            selectedGoalId
        ) ?? null
      );
    }, [
      visibleGoals,
      selectedGoalId,
    ]);

  const selectedGoalTasks =
    useMemo(() => {
      if (!selectedGoal) {
        return [];
      }

      return tasks
        .filter(
          (task) =>
            task.goal ===
            selectedGoal.id
        )
        .sort((first, second) => {
          const order: Record<
            TaskStatus,
            number
          > = {
            in_progress: 0,
            todo: 1,
            done: 2,
          };

          if (
            order[first.status] !==
            order[second.status]
          ) {
            return (
              order[first.status] -
              order[second.status]
            );
          }

          return (
            new Date(
              first.created_at
            ).getTime() -
            new Date(
              second.created_at
            ).getTime()
          );
        });
    }, [
      selectedGoal,
      tasks,
    ]);

  const goalCounts = useMemo(
    () => ({
      active: goals.filter(
        (goal) =>
          goal.status === "active"
      ).length,
      completed: goals.filter(
        (goal) =>
          goal.status ===
          "completed"
      ).length,
      archived: goals.filter(
        (goal) =>
          goal.status ===
          "archived"
      ).length,
    }),
    [goals]
  );

  const completedTaskCount =
    selectedGoalTasks.filter(
      (task) =>
        task.status === "done"
    ).length;

  const nextTask = useMemo(() => {
    const inProgress =
      selectedGoalTasks.find(
        (task) =>
          task.status ===
          "in_progress"
      );

    if (inProgress) {
      return inProgress;
    }

    return (
      selectedGoalTasks.find(
        (task) =>
          task.status === "todo"
      ) ?? null
    );
  }, [selectedGoalTasks]);

  const goalDetailItems =
    useMemo(() => {
      if (!selectedGoal) {
        return [];
      }

      return [
        {
          label: "Outcome",
          value:
            selectedGoal.description,
        },
        {
          label: "Why it matters",
          value:
            selectedGoal.why_it_matters,
        },
        {
          label: "Main obstacle",
          value:
            selectedGoal.previous_obstacles,
        },
      ].filter(
        (item) => item.value.trim()
      );
    }, [selectedGoal]);

  const isEditing =
    editingGoal !== null;

  const hasGoalChanges =
    isEditing
      ? !isSameDraft(
          goalDraft,
          editingGoal
        )
      : Boolean(
          goalDraft.title.trim() ||
            goalDraft.description.trim() ||
            goalDraft.why_it_matters.trim() ||
            goalDraft.previous_obstacles.trim() ||
            goalDraft.target_date
        );

  const canSaveGoal =
    goalDraft.title.trim()
      .length > 0 &&
    requestState === "idle" &&
    (
      !isEditing ||
      hasGoalChanges
    );

  const canCreateTask =
    taskDraft.title.trim()
      .length > 0 &&
    !isCreatingTask;

  const loadGoals =
    useCallback(async () => {
      try {
        setIsLoading(true);
        setError("");

        const response =
          await apiFetch(
            GOALS_API_URL
          );

        const data: unknown =
          await response.json();

        if (!response.ok) {
          throw new Error(
            getErrorMessage(data)
          );
        }

        if (!Array.isArray(data)) {
          throw new Error(
            "Unexpected Goals response."
          );
        }

        const loadedGoals =
          data as Goal[];

        setGoals(loadedGoals);

        setSelectedGoalId(
          (currentId) => {
            if (
              currentId !== null &&
              loadedGoals.some(
                (goal) =>
                  goal.id ===
                  currentId
              )
            ) {
              return currentId;
            }

            const firstActive =
              loadedGoals.find(
                (goal) =>
                  goal.status ===
                  "active"
              );

            return (
              firstActive?.id ??
              loadedGoals[0]?.id ??
              null
            );
          }
        );

        return loadedGoals;
      } catch (loadError) {
        console.error(
          "Goals load error:",
          loadError
        );

        setError(
          loadError instanceof Error
            ? loadError.message
            : "Unable to load goals."
        );
      } finally {
        setIsLoading(false);
      }
    }, []);

  const loadTasks =
    useCallback(async () => {
      try {
        setIsTasksLoading(true);
        setTaskError("");

        const response =
          await apiFetch(
            BOARD_API_URL
          );

        const data: unknown =
          await response.json();

        if (!response.ok) {
          throw new Error(
            getErrorMessage(data)
          );
        }

        if (!Array.isArray(data)) {
          throw new Error(
            "Unexpected Board response."
          );
        }

        setTasks(
          data as BoardTask[]
        );
      } catch (loadError) {
        console.error(
          "Board load error:",
          loadError
        );

        setTaskError(
          loadError instanceof Error
            ? loadError.message
            : "Unable to load tasks."
        );
      } finally {
        setIsTasksLoading(false);
      }
    }, []);

  useEffect(() => {
    void Promise.all([
      // Initial API synchronization for this client page.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadGoals(),
      loadTasks(),
    ]);
  }, [
    loadGoals,
    loadTasks,
  ]);

  useEffect(() => {
    if (visibleGoals.length === 0) {
      if (selectedGoalId !== null) {
        // Keep the detail panel in sync with the active filter.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setSelectedGoalId(null);
      }

      return;
    }

    const selectedIsVisible =
      selectedGoalId !== null &&
      visibleGoals.some(
        (goal) =>
          goal.id === selectedGoalId
      );

    if (!selectedIsVisible) {
      // Select only when the current goal is unavailable in this filter.
      setSelectedGoalId(
        visibleGoals[0].id
      );
    }
  }, [
    visibleGoals,
    selectedGoalId,
  ]);

  useEffect(() => {
    if (
      !isComposerOpen &&
      !deleteTarget
    ) {
      return;
    }

    function handleEscape(
      event: KeyboardEvent
    ) {
      if (event.key !== "Escape") {
        return;
      }

      if (
        requestState !== "idle"
      ) {
        return;
      }

      setIsComposerOpen(false);
      setDeleteTarget(null);
    }

    window.addEventListener(
      "keydown",
      handleEscape
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleEscape
      );
    };
  }, [
    isComposerOpen,
    deleteTarget,
    requestState,
  ]);

  function updateGoalDraft<
    Key extends keyof GoalDraft
  >(
    key: Key,
    value: GoalDraft[Key]
  ) {
    setGoalDraft(
      (current) => ({
        ...current,
        [key]: value,
      })
    );
  }

  function updateTaskDraft<
    Key extends keyof TaskDraft
  >(
    key: Key,
    value: TaskDraft[Key]
  ) {
    setTaskDraft(
      (current) => ({
        ...current,
        [key]: value,
      })
    );
  }

  function openNewGoal() {
    setEditingGoal(null);
    setGoalDraft(
      EMPTY_GOAL_DRAFT
    );
    setError("");
    setIsComposerOpen(true);
  }

  function openEditGoal(
    goal: Goal
  ) {
    if (
      goal.status !== "active"
    ) {
      return;
    }

    setEditingGoal(goal);
    setGoalDraft(
      normalizeDraft(goal)
    );
    setError("");
    setIsComposerOpen(true);
  }

  function closeComposer() {
    if (
      requestState !== "idle"
    ) {
      return;
    }

    setIsComposerOpen(false);
    setEditingGoal(null);
    setGoalDraft(
      EMPTY_GOAL_DRAFT
    );
    setError("");
  }

  function openGoal(
    goal: Goal
  ) {
    setSelectedGoalId(
      goal.id
    );
    setTaskError("");
    setIsTaskComposerOpen(
      false
    );
    setTaskDraft(
      EMPTY_TASK_DRAFT
    );
  }

  function changeFilter(
    nextFilter: GoalFilter
  ) {
    setFilter(nextFilter);
    setTaskError("");
    setIsTaskComposerOpen(false);
    setTaskDraft(
      EMPTY_TASK_DRAFT
    );
  }

  async function handleGoalSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!canSaveGoal) {
      return;
    }

    try {
      setRequestState("saving");
      setError("");

      const response =
        await apiFetch(
          isEditing
            ? `${GOALS_API_URL}?id=${editingGoal.id}`
            : GOALS_API_URL,
          {
            method: isEditing
              ? "PATCH"
              : "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              title:
                goalDraft.title.trim(),
              description:
                goalDraft.description.trim(),
              why_it_matters:
                goalDraft.why_it_matters.trim(),
              previous_obstacles:
                goalDraft.previous_obstacles.trim(),
              target_date:
                goalDraft.target_date ||
                null,
            }),
          }
        );

      const data: unknown =
        await response.json();

      if (!response.ok) {
        setError(
          getErrorMessage(data)
        );
        return;
      }

      const savedGoal =
        data as Goal;

      await loadGoals();

      setFilter(
        savedGoal.status
      );
      setSelectedGoalId(
        savedGoal.id
      );

      closeComposer();
    } catch (saveError) {
      console.error(
        "Goal save error:",
        saveError
      );

      setError(
        "Unable to save this goal."
      );
    } finally {
      setRequestState("idle");
    }
  }

  async function updateGoalStatus(
    goal: Goal,
    goalStatus: GoalStatus
  ) {
    try {
      setRequestState(
        "archiving"
      );
      setError("");

      const response =
        await apiFetch(
          `${GOALS_API_URL}?id=${goal.id}`,
          {
            method: "PATCH",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              status: goalStatus,
            }),
          }
        );

      const data: unknown =
        await response.json();

      if (!response.ok) {
        setError(
          getErrorMessage(data)
        );
        return;
      }

      const loadedGoals =
        await loadGoals();

      setFilter("active");

      if (loadedGoals) {
        const nextSelectedGoal =
          goalStatus === "active"
            ? loadedGoals.find(
                (loadedGoal) =>
                  loadedGoal.id ===
                  goal.id
              )
            : loadedGoals.find(
                (loadedGoal) =>
                  loadedGoal.status ===
                  "active"
              );

        setSelectedGoalId(
          nextSelectedGoal?.id ??
            null
        );
      }
    } catch (statusError) {
      console.error(
        "Goal status error:",
        statusError
      );

      setError(
        "Unable to update this goal."
      );
    } finally {
      setRequestState("idle");
    }
  }

  async function handleDeleteGoal() {
    if (!deleteTarget) {
      return;
    }

    try {
      setRequestState("deleting");
      setError("");

      const response =
        await apiFetch(
          `${GOALS_API_URL}?id=${deleteTarget.id}`,
          {
            method: "DELETE",
          }
        );

      if (!response.ok) {
        let data: unknown = null;

        try {
          data =
            await response.json();
        } catch {
          data = null;
        }

        setError(
          getErrorMessage(data)
        );
        return;
      }

      setTasks(
        (current) =>
          current.filter(
            (task) =>
              task.goal !==
              deleteTarget.id
          )
      );

      setDeleteTarget(null);

      const loadedGoals =
        await loadGoals();

      if (loadedGoals) {
        const nextSelectedGoal =
          loadedGoals.find(
            (goal) =>
              goal.status === filter
          ) ?? null;

        setSelectedGoalId(
          nextSelectedGoal?.id ??
            null
        );
      }
    } catch (deleteError) {
      console.error(
        "Goal delete error:",
        deleteError
      );

      setError(
        "Unable to delete this goal."
      );
    } finally {
      setRequestState("idle");
    }
  }

  async function handleTaskSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (
      !selectedGoal ||
      !canCreateTask
    ) {
      return;
    }

    try {
      setIsCreatingTask(true);
      setTaskError("");

      const response =
        await apiFetch(
          BOARD_API_URL,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              goal:
                selectedGoal.id,
              title:
                taskDraft.title.trim(),
              description:
                taskDraft.description.trim(),
              status: "todo",
            }),
          }
        );

      const data: unknown =
        await response.json();

      if (!response.ok) {
        setTaskError(
          getErrorMessage(data)
        );
        return;
      }

      setTaskDraft(
        EMPTY_TASK_DRAFT
      );
      setIsTaskComposerOpen(
        false
      );

      await Promise.all([
        loadTasks(),
        loadGoals(),
      ]);
    } catch (saveError) {
      console.error(
        "Task save error:",
        saveError
      );

      setTaskError(
        "Unable to add this task."
      );
    } finally {
      setIsCreatingTask(false);
    }
  }

  async function advanceTask(
    task: BoardTask
  ) {
    try {
      setTaskRequestId(
        task.id
      );
      setTaskError("");

      const response =
        await apiFetch(
          `${BOARD_API_URL}${task.id}/`,
          {
            method: "PATCH",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              status:
                getNextTaskStatus(
                  task.status
                ),
            }),
          }
        );

      const data: unknown =
        await response.json();

      if (!response.ok) {
        setTaskError(
          getErrorMessage(data)
        );
        return;
      }

      await Promise.all([
        loadTasks(),
        loadGoals(),
      ]);
    } catch (taskUpdateError) {
      console.error(
        "Task update error:",
        taskUpdateError
      );

      setTaskError(
        "Unable to update this task."
      );
    } finally {
      setTaskRequestId(null);
    }
  }

  return (
    <ProtectedLayout>
      <main className="goals-page">
        <div
          className="goals-background"
          aria-hidden="true"
        />

        <div className="goals-shell">
          <header className="goals-header">
            <div className="goals-title-group">
              <div className="goals-title-row">
                <span className="goals-heading-mark" />

                <h1>Goals</h1>
              </div>

              <p>
                {goalCounts.active}{" "}
                {pluralize(
                  goalCounts.active,
                  "active goal"
                )}
              </p>
            </div>

          </header>

          <section className="goals-toolbar">
            <div
              className="goals-filters"
              aria-label="Filter goals"
            >
              {(
                [
                  "active",
                  "completed",
                  "archived",
                ] as GoalFilter[]
              ).map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`goals-filter ${
                    filter === item
                      ? "goals-filter-active"
                      : ""
                  }`}
                  onClick={() =>
                    changeFilter(item)
                  }
                >
                  <span>{item}</span>

                  <strong>
                    {goalCounts[item]}
                  </strong>
                </button>
              ))}
            </div>
          </section>

          {error &&
            !isComposerOpen &&
            !deleteTarget && (
              <div
                className="goals-page-error"
                role="alert"
              >
                <span>{error}</span>

                <button
                  type="button"
                  onClick={() =>
                    setError("")
                  }
                  aria-label="Dismiss error"
                >
                  ×
                </button>
              </div>
            )}

          <div className="goals-workspace">
            <section className="goals-list-panel">
              {isLoading ? (
                <div className="goals-loading">
                  <span />
                  <span />
                  <span />
                </div>
              ) : error &&
                goals.length === 0 ? (
                <div className="goals-load-error">
                  <span className="goals-empty-mark" />

                  <p>{error}</p>

                  <button
                    type="button"
                    onClick={loadGoals}
                  >
                    Try again
                  </button>
                </div>
              ) : visibleGoals.length ===
                0 ? (
                <div className="goals-empty">
                  <h2>
                    {filter === "active"
                        ? "No active goals"
                      : filter ===
                          "completed"
                        ? "No completed goals yet"
                        : "Archive is empty"}
                  </h2>

                  <p>
                    {filter === "active"
                      ? "Create one clear goal and decide what to do next."
                      : filter ===
                          "completed"
                        ? "Completed goals will appear here."
                        : "Archived goals will appear here."}
                  </p>

                  {filter ===
                    "active" && (
                    <button
                      type="button"
                      onClick={openNewGoal}
                    >
                      <span aria-hidden="true">
                        +
                      </span>
                      Add goal
                    </button>
                  )}
                </div>
              ) : (
                <div className="goals-list">
                  {visibleGoals.map(
                    (goal, index) => {
                      const daysUntil =
                        getDaysUntil(
                          goal.target_date
                        );

                      const isOverdue =
                        goal.status ===
                          "active" &&
                        daysUntil !== null &&
                        daysUntil < 0;

                      const taskCount =
                        tasks.filter(
                          (task) =>
                            task.goal ===
                            goal.id
                        ).length;

                      return (
                        <article
                          key={goal.id}
                          className={`goal-card goal-card-${goal.status} ${
                            selectedGoalId ===
                            goal.id
                              ? "goal-card-selected"
                              : ""
                          }`}
                          style={{
                            "--goal-index":
                              index,
                          } as React.CSSProperties}
                        >
                          <button
                            type="button"
                            className="goal-card-main"
                            onClick={() =>
                              openGoal(goal)
                            }
                          >
                            <span className="goal-card-copy">
                              <span className="goal-card-header">
                                <strong className="goal-card-title">
                                  {goal.title}
                                </strong>

                                <span className="goal-progress-value">
                                  {goal.progress}%
                                </span>
                              </span>

                              <span className="goal-card-meta">
                                <span
                                  className={`goal-deadline ${
                                    isOverdue
                                      ? "goal-deadline-overdue"
                                      : ""
                                  }`}
                                >
                                  {goal.status ===
                                    "completed" &&
                                  goal.completed_at
                                    ? `Completed ${formatCompletedShortDate(
                                        goal.completed_at
                                      )}`
                                    : getDeadlineLabel(
                                        goal
                                      )}
                                </span>

                                <span>
                                  {taskCount}{" "}
                                  {pluralize(
                                    taskCount,
                                    "task"
                                  )}
                                </span>
                              </span>

                              <span className="goal-progress-track">
                                <span
                                  className="goal-progress-fill"
                                  style={{
                                    width: `${goal.progress}%`,
                                  }}
                                />
                              </span>
                            </span>
                          </button>
                        </article>
                      );
                    }
                  )}
                </div>
              )}
            </section>

            <aside className="goal-detail-panel">
              {!selectedGoal ? (
                <div className="goal-detail-placeholder">
                  <span className="goal-detail-orbit">
                    <span />
                  </span>

                  <p>
                    {filter === "active"
                      ? "Create a goal to start."
                      : filter ===
                          "completed"
                        ? "Completed goals will appear here."
                        : "Archived goals will appear here."}
                  </p>
                </div>
              ) : (
                <div
                  className={`goal-detail goal-detail-${selectedGoal.status}`}
                >
                  <header className="goal-detail-header">
                    <div className="goal-detail-heading">
                      <h2>
                        {selectedGoal.title}
                      </h2>
                    </div>

                    {selectedGoal.status ===
                      "active" && (
                      <button
                        type="button"
                        className="goal-detail-edit"
                        onClick={() =>
                          openEditGoal(
                            selectedGoal
                          )
                        }
                      >
                        Edit
                      </button>
                    )}
                  </header>

                  <section className="goal-detail-progress">
                    <div className="goal-detail-progress-copy">
                      <span>
                        Progress
                      </span>

                      <strong>
                        {selectedGoal.progress}
                        <small>%</small>
                      </strong>
                    </div>

                    <div className="goal-detail-progress-track">
                      <span
                        style={{
                          width: `${selectedGoal.progress}%`,
                        }}
                      />
                    </div>

                    <div className="goal-detail-progress-meta">
                      <span>
                        {isTasksLoading
                          ? "Loading tasks…"
                          : selectedGoal.status ===
                                "active" &&
                              selectedGoalTasks.length ===
                              0
                            ? "Add tasks to calculate progress"
                            : `${completedTaskCount} of ${selectedGoalTasks.length} ${pluralize(
                                selectedGoalTasks.length,
                                "task"
                              )} completed`}
                      </span>

                      <span>
                        {getDeadlineLabel(
                          selectedGoal
                        )}
                      </span>
                    </div>
                  </section>

                  {selectedGoal.status ===
                    "active" &&
                    nextTask && (
                      <section className="goal-next-task">
                        <div className="goal-next-task-copy">
                          <span>
                            Next task
                          </span>

                          <strong>
                            {nextTask.title}
                          </strong>

                          {nextTask.description && (
                            <p>
                              {
                                nextTask.description
                              }
                            </p>
                          )}
                        </div>

                        <button
                          type="button"
                          onClick={() =>
                            advanceTask(
                              nextTask
                            )
                          }
                          disabled={
                            taskRequestId ===
                            nextTask.id
                          }
                        >
                          {taskRequestId ===
                          nextTask.id
                            ? "Updating…"
                            : nextTask.status ===
                                "in_progress"
                              ? "Mark done"
                              : "Start"}
                        </button>
                      </section>
                    )}

                  <section className="goal-plan">
                    <header className="goal-plan-header">
                      <div>
                        <span className="goal-detail-label">
                          {selectedGoal.status ===
                          "completed"
                            ? "Completed tasks"
                            : "Tasks"}
                        </span>

                        <p>
                          {isTasksLoading
                            ? "Loading tasks…"
                            : selectedGoal.status ===
                          "completed"
                            ? `${completedTaskCount} of ${selectedGoalTasks.length} ${pluralize(
                                selectedGoalTasks.length,
                                "task"
                              )} completed`
                            : selectedGoalTasks.length ===
                                0
                              ? "Add tasks to start tracking progress."
                              : "Complete tasks to move this goal forward."}
                        </p>
                      </div>

                      {selectedGoal.status ===
                        "active" &&
                        !isTaskComposerOpen &&
                        selectedGoalTasks.length >
                          0 && (
                        <button
                          type="button"
                          className="goal-plan-add"
                          onClick={() => {
                            setTaskError(
                              ""
                            );
                            setIsTaskComposerOpen(
                              (current) =>
                                !current
                            );
                          }}
                        >
                          <span aria-hidden="true">
                            +
                          </span>

                          Add task
                        </button>
                      )}
                    </header>

                    {isTaskComposerOpen &&
                      selectedGoal.status ===
                        "active" && (
                        <form
                          className="goal-task-form"
                          onSubmit={
                            handleTaskSubmit
                          }
                        >
                          <input
                            type="text"
                            value={
                              taskDraft.title
                            }
                            maxLength={255}
                            onChange={(
                              event
                            ) =>
                              updateTaskDraft(
                                "title",
                                event
                                  .target
                                  .value
                              )
                            }
                            placeholder="A small, concrete action"
                            autoFocus
                          />

                          <textarea
                            value={
                              taskDraft.description
                            }
                            onChange={(
                              event
                            ) =>
                              updateTaskDraft(
                                "description",
                                event
                                  .target
                                  .value
                              )
                            }
                            placeholder="Optional detail"
                          />

                          <div className="goal-task-form-actions">
                            <button
                              type="button"
                              onClick={() => {
                                setIsTaskComposerOpen(
                                  false
                                );
                                setTaskDraft(
                                  EMPTY_TASK_DRAFT
                                );
                              }}
                            >
                              Cancel
                            </button>

                            <button
                              type="submit"
                              disabled={
                                !canCreateTask
                              }
                            >
                              {isCreatingTask
                                ? "Adding…"
                                : "Add task"}
                            </button>
                          </div>
                        </form>
                      )}

                    {taskError && (
                      <p
                        className="goal-task-error"
                        role="alert"
                      >
                        {taskError}
                      </p>
                    )}

                    {isTasksLoading ? (
                      <div className="goal-plan-loading">
                        <span />
                        <span />
                        <span />
                      </div>
                    ) : selectedGoalTasks.length ===
                      0 ? (
                      <div className="goal-plan-empty">
                        <strong>
                          No tasks yet
                        </strong>

                        <p>
                          Add one concrete action
                          to begin.
                        </p>

                        {selectedGoal.status ===
                          "active" &&
                          !isTaskComposerOpen && (
                          <button
                            type="button"
                            onClick={() =>
                              setIsTaskComposerOpen(
                                true
                              )
                            }
                          >
                            <span aria-hidden="true">
                              +
                            </span>
                            Add task
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="goal-task-list">
                        {selectedGoalTasks.map(
                          (
                            task,
                            index
                          ) => (
                            <article
                              key={task.id}
                              className={`goal-task goal-task-${task.status} ${
                                selectedGoal.status !==
                                "active"
                                  ? "goal-task-readonly"
                                  : ""
                              }`}
                            >
                              <button
                                type="button"
                                className="goal-task-state"
                                onClick={() =>
                                  advanceTask(
                                    task
                                  )
                                }
                                disabled={
                                  selectedGoal.status !==
                                    "active" ||
                                  task.status ===
                                    "done" ||
                                  taskRequestId ===
                                    task.id
                                }
                                aria-label={`Move ${task.title} to ${getTaskStatusLabel(
                                  getNextTaskStatus(
                                    task.status
                                  )
                                )}`}
                              >
                                <span>
                                  {task.status ===
                                  "done"
                                    ? "✓"
                                    : String(
                                        index +
                                          1
                                      ).padStart(
                                        2,
                                        "0"
                                      )}
                                </span>
                              </button>

                              <div className="goal-task-copy">
                                <strong>
                                  {task.title}
                                </strong>

                                {task.description && (
                                  <p>
                                    {
                                      task.description
                                    }
                                  </p>
                                )}

                                {(taskRequestId ===
                                  task.id ||
                                  task.status !==
                                    "done") && (
                                  <span>
                                    {taskRequestId ===
                                    task.id
                                      ? "Updating…"
                                      : getTaskStatusLabel(
                                          task.status
                                        )}
                                  </span>
                                )}
                              </div>
                            </article>
                          )
                        )}
                      </div>
                    )}
                  </section>

                  <section className="goal-info">
                    <header className="goal-info-header">
                      <span>
                        Goal details
                      </span>
                    </header>

                    {goalDetailItems.length >
                    0 ? (
                      <div className="goal-info-grid">
                        {goalDetailItems.map(
                          (item) => (
                            <div
                              key={item.label}
                              className={
                                item.label ===
                                "Outcome"
                                  ? "goal-info-item goal-info-item-wide"
                                  : "goal-info-item"
                              }
                            >
                              <span>
                                {item.label}
                              </span>

                              <p>
                                {item.value}
                              </p>
                            </div>
                          )
                        )}
                      </div>
                    ) : (
                      <div className="goal-info-empty">
                        <div>
                          <strong>
                            {selectedGoal.status ===
                            "completed"
                              ? "No additional details."
                              : "No details added."}
                          </strong>

                          {selectedGoal.status ===
                            "active" && (
                            <p>
                              Add a reason or
                              outcome to make this
                              goal clearer.
                            </p>
                          )}
                        </div>

                      </div>
                    )}
                  </section>

                  <footer className="goal-detail-footer">
                    {selectedGoal.status ===
                      "active" && (
                      <button
                        type="button"
                        onClick={() =>
                          updateGoalStatus(
                            selectedGoal,
                            "archived"
                          )
                        }
                        disabled={
                          requestState !==
                          "idle"
                        }
                      >
                        Archive
                      </button>
                    )}

                    {selectedGoal.status ===
                      "archived" && (
                      <button
                        type="button"
                        onClick={() =>
                          updateGoalStatus(
                            selectedGoal,
                            "active"
                          )
                        }
                        disabled={
                          requestState !==
                          "idle"
                        }
                      >
                        Restore
                      </button>
                    )}

                    <button
                      type="button"
                      className="goal-delete-button"
                      onClick={() =>
                        setDeleteTarget(
                          selectedGoal
                        )
                      }
                      disabled={
                        requestState !==
                        "idle"
                      }
                    >
                      Delete
                    </button>
                  </footer>
                </div>
              )}
            </aside>
          </div>
        </div>

        <div
          className={`goals-composer-backdrop ${
            isComposerOpen
              ? "goals-composer-backdrop-open"
              : ""
          }`}
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeComposer();
            }
          }}
          aria-hidden={
            !isComposerOpen
          }
        >
          <aside
            className={`goals-composer ${
              isComposerOpen
                ? "goals-composer-open"
                : ""
            }`}
            aria-label={
              isEditing
                ? "Edit goal"
                : "Create goal"
            }
          >
            <header className="goals-composer-header">
              <div>
                <span>
                  {isEditing
                    ? "Goal"
                    : "New goal"}
                </span>

                <h2>
                  {isEditing
                    ? "Edit goal"
                    : "What do you want to achieve?"}
                </h2>
              </div>

              <button
                type="button"
                className="goals-composer-close"
                onClick={
                  closeComposer
                }
                aria-label="Close"
              >
                ×
              </button>
            </header>

            <form
              className="goals-form"
              onSubmit={
                handleGoalSubmit
              }
            >
              <label className="goals-field goals-field-primary">
                <span>
                  Goal
                </span>

                <input
                  type="text"
                  value={
                    goalDraft.title
                  }
                  maxLength={255}
                  onChange={(event) =>
                    updateGoalDraft(
                      "title",
                      event.target.value
                    )
                  }
                  placeholder="For example: Pass IELTS with 6.5"
                  autoFocus
                />
              </label>

              <label className="goals-field">
                <span>
                  Success looks like
                  <small>
                    optional
                  </small>
                </span>

                <textarea
                  value={
                    goalDraft.description
                  }
                  onChange={(event) =>
                    updateGoalDraft(
                      "description",
                      event.target.value
                    )
                  }
                  placeholder="Describe the concrete result."
                />
              </label>

              <label className="goals-field">
                <span>
                  Why it matters
                  <small>
                    optional
                  </small>
                </span>

                <textarea
                  value={
                    goalDraft.why_it_matters
                  }
                  onChange={(event) =>
                    updateGoalDraft(
                      "why_it_matters",
                      event.target.value
                    )
                  }
                  placeholder="What makes this worth doing?"
                />
              </label>

              <label className="goals-field">
                <span>
                  Previous obstacle
                  <small>
                    optional
                  </small>
                </span>

                <textarea
                  value={
                    goalDraft.previous_obstacles
                  }
                  onChange={(event) =>
                    updateGoalDraft(
                      "previous_obstacles",
                      event.target.value
                    )
                  }
                  placeholder="What usually gets in the way?"
                />
              </label>

              <label className="goals-field goals-field-date">
                <span>
                  Deadline
                  <small>
                    optional
                  </small>
                </span>

                <input
                  type="date"
                  value={
                    goalDraft.target_date
                  }
                  min={today}
                  onChange={(event) =>
                    updateGoalDraft(
                      "target_date",
                      event.target.value
                    )
                  }
                />
              </label>

              {error && (
                <p
                  className="goals-form-error"
                  role="alert"
                >
                  {error}
                </p>
              )}

              <footer className="goals-form-footer">
                <button
                  type="button"
                  className="goals-form-cancel"
                  onClick={
                    closeComposer
                  }
                  disabled={
                    requestState !==
                    "idle"
                  }
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="goals-form-submit"
                  disabled={
                    !canSaveGoal
                  }
                >
                  {requestState ===
                  "saving"
                    ? "Saving…"
                    : isEditing
                      ? "Save changes"
                      : "Create goal"}
                </button>
              </footer>
            </form>
          </aside>
        </div>

        {deleteTarget && (
          <div
            className="goals-dialog-backdrop"
            onMouseDown={(event) => {
              if (
                event.target ===
                event.currentTarget &&
                requestState ===
                  "idle"
              ) {
                setDeleteTarget(
                  null
                );
              }
            }}
          >
            <section
              className="goals-delete-dialog"
              role="dialog"
              aria-modal="true"
              aria-labelledby="delete-goal-title"
            >
              <span className="goals-delete-mark">
                ×
              </span>

              <span className="goals-delete-eyebrow">
                Permanent action
              </span>

              <h2 id="delete-goal-title">
                Delete this goal?
              </h2>

              <p>
                “{deleteTarget.title}”
                and all of its connected
                Board tasks will be
                removed permanently.
              </p>

              {error && (
                <p className="goals-delete-error">
                  {error}
                </p>
              )}

              <div className="goals-delete-actions">
                <button
                  type="button"
                  onClick={() =>
                    setDeleteTarget(
                      null
                    )
                  }
                  disabled={
                    requestState !==
                    "idle"
                  }
                >
                  Keep goal
                </button>

                <button
                  type="button"
                  className="goals-delete-confirm"
                  onClick={
                    handleDeleteGoal
                  }
                  disabled={
                    requestState !==
                    "idle"
                  }
                >
                  {requestState ===
                  "deleting"
                    ? "Deleting…"
                    : "Delete permanently"}
                </button>
              </div>
            </section>
          </div>
        )}
      </main>
    </ProtectedLayout>
  );
}
