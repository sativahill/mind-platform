"use client";

import {
  type DragEvent,
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import ProtectedLayout from "@/components/ProtectedLayout";
import { apiFetch } from "@/lib/api";

import "./board.css";


const BOARD_API_URL =
  "/api/board/";

const GOALS_API_URL =
  "/api/goals/";


type TaskStatus =
  | "todo"
  | "in_progress"
  | "done";

type TaskPriority =
  | "low"
  | "medium"
  | "high"
  | "critical";

type GoalStatus =
  | "active"
  | "completed"
  | "archived";


interface TaskReference {
  id: number;
  title: string;
  status: TaskStatus;
}


interface BoardTask {
  id: number;

  goal: number;

  title: string;
  description: string;

  status: TaskStatus;
  priority: TaskPriority;

  due_date: string | null;

  is_blocked: boolean;
  blocking_tasks: TaskReference[];

  created_at: string;
  updated_at: string;
}


interface Goal {
  id: number;
  title: string;
  status: GoalStatus;
}


interface ApiErrorShape {
  detail?: string;
  [key: string]: unknown;
}


const COLUMNS: {
  status: TaskStatus;
  title: string;
}[] = [
  {
    status: "todo",
    title: "To Do",
  },
  {
    status: "in_progress",
    title: "In Progress",
  },
  {
    status: "done",
    title: "Done",
  },
];


function getErrorMessage(
  error: unknown
) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong.";
}


function extractApiError(
  data: unknown,
  fallback: string
) {
  if (
    !data
    || typeof data !== "object"
  ) {
    return fallback;
  }

  const object =
    data as ApiErrorShape;

  if (
    typeof object.detail === "string"
  ) {
    return object.detail;
  }

  const messages: string[] = [];

  function collect(
    value: unknown
  ) {
    if (typeof value === "string") {
      messages.push(value);
      return;
    }

    if (Array.isArray(value)) {
      value.forEach(collect);
      return;
    }

    if (
      value
      && typeof value === "object"
    ) {
      Object.values(value)
        .forEach(collect);
    }
  }

  collect(object);

  return messages[0] ?? fallback;
}


async function parseResponse(
  response: Response
) {
  if (response.status === 204) {
    return null;
  }

  const contentType =
    response.headers.get(
      "content-type"
    );

  if (
    contentType?.includes(
      "application/json"
    )
  ) {
    return response.json();
  }

  return null;
}


function getDueDateLabel(
  value: string | null
) {
  if (!value) {
    return null;
  }

  const date = new Date(
    `${value}T12:00:00`
  );

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en",
    {
      month: "short",
      day: "numeric",
    }
  ).format(date);
}


export default function BoardPage() {
  const [
    tasks,
    setTasks,
  ] = useState<BoardTask[]>([]);

  const [
    goals,
    setGoals,
  ] = useState<Goal[]>([]);

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    isSaving,
    setIsSaving,
  ] = useState(false);

  const [
    updatingTaskId,
    setUpdatingTaskId,
  ] = useState<number | null>(
    null
  );

  const [
    draggedTaskId,
    setDraggedTaskId,
  ] = useState<number | null>(
    null
  );

  const [
    dragOverStatus,
    setDragOverStatus,
  ] = useState<TaskStatus | null>(
    null
  );

  const [
    selectedTaskId,
    setSelectedTaskId,
  ] = useState<number | null>(
    null
  );

  const [
    isAddOpen,
    setIsAddOpen,
  ] = useState(false);

  const [
    newTaskTitle,
    setNewTaskTitle,
  ] = useState("");

  const [
    newTaskGoal,
    setNewTaskGoal,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState("");

  const [
    formError,
    setFormError,
  ] = useState("");


  const activeGoals =
    useMemo(
      () =>
        goals.filter(
          (goal) =>
            goal.status === "active"
        ),
      [goals]
    );


  const selectedTask =
    useMemo(
      () => {
        if (
          selectedTaskId === null
        ) {
          return null;
        }

        return (
          tasks.find(
            (task) =>
              task.id
              === selectedTaskId
          )
          ?? null
        );
      },
      [
        selectedTaskId,
        tasks,
      ]
    );


  const tasksByStatus =
    useMemo(
      () => {
        return {
          todo:
            tasks.filter(
              (task) =>
                task.status === "todo"
            ),

          in_progress:
            tasks.filter(
              (task) =>
                task.status
                === "in_progress"
            ),

          done:
            tasks.filter(
              (task) =>
                task.status === "done"
            ),
        };
      },
      [tasks]
    );


  const loadBoard =
    useCallback(
      async () => {
        setIsLoading(true);
        setError("");

        try {
          const [
            tasksResponse,
            goalsResponse,
          ] = await Promise.all([
            apiFetch(
              BOARD_API_URL
            ),
            apiFetch(
              GOALS_API_URL
            ),
          ]);

          const tasksData =
            await parseResponse(
              tasksResponse
            );

          const goalsData =
            await parseResponse(
              goalsResponse
            );

          if (!tasksResponse.ok) {
            throw new Error(
              extractApiError(
                tasksData,
                "Could not load tasks."
              )
            );
          }

          if (!goalsResponse.ok) {
            throw new Error(
              extractApiError(
                goalsData,
                "Could not load goals."
              )
            );
          }

          setTasks(
            Array.isArray(tasksData)
              ? tasksData
              : []
          );

          setGoals(
            Array.isArray(goalsData)
              ? goalsData
              : []
          );
        } catch (requestError) {
          setError(
            getErrorMessage(
              requestError
            )
          );
        } finally {
          setIsLoading(false);
        }
      },
      []
    );


  useEffect(() => {
    void loadBoard();
  }, [loadBoard]);


  function openAddTask() {
    setNewTaskTitle("");

    if (
      activeGoals.length === 1
    ) {
      setNewTaskGoal(
        String(
          activeGoals[0].id
        )
      );
    } else {
      setNewTaskGoal("");
    }

    setFormError("");
    setIsAddOpen(true);
  }


  function closeAddTask() {
    if (isSaving) {
      return;
    }

    setIsAddOpen(false);
    setNewTaskTitle("");
    setNewTaskGoal("");
    setFormError("");
  }


  async function createTask(
    event: FormEvent
  ) {
    event.preventDefault();

    const title =
      newTaskTitle.trim();

    if (!title) {
      setFormError(
        "Write a task."
      );
      return;
    }

    if (!newTaskGoal) {
      setFormError(
        "Choose a goal."
      );
      return;
    }

    setIsSaving(true);
    setFormError("");

    try {
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
                Number(
                  newTaskGoal
                ),
              title,
              description: "",
              status: "todo",
              priority: "medium",
              importance: "small",
              due_date: null,
              dependency_ids: [],
            }),
          }
        );

      const data =
        await parseResponse(
          response
        );

      if (!response.ok) {
        throw new Error(
          extractApiError(
            data,
            "Could not create task."
          )
        );
      }

      const createdTask =
        data as BoardTask;

      setTasks(
        (current) => [
          ...current,
          createdTask,
        ]
      );

      setIsAddOpen(false);
      setNewTaskTitle("");
      setNewTaskGoal("");
    } catch (requestError) {
      setFormError(
        getErrorMessage(
          requestError
        )
      );
    } finally {
      setIsSaving(false);
    }
  }


  async function moveTask(
    taskId: number,
    nextStatus: TaskStatus
  ) {
    const task =
      tasks.find(
        (item) =>
          item.id === taskId
      );

    if (
      !task
      || task.status
      === nextStatus
    ) {
      return;
    }

    const previousStatus =
      task.status;

    setUpdatingTaskId(
      taskId
    );

    setError("");

    setTasks(
      (current) =>
        current.map(
          (item) =>
            item.id === taskId
              ? {
                  ...item,
                  status:
                    nextStatus,
                }
              : item
        )
    );

    try {
      const response =
        await apiFetch(
          `${BOARD_API_URL}${taskId}/`,
          {
            method: "PATCH",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              status:
                nextStatus,
            }),
          }
        );

      const data =
        await parseResponse(
          response
        );

      if (!response.ok) {
        throw new Error(
          extractApiError(
            data,
            "Could not move task."
          )
        );
      }

      const updatedTask =
        data as BoardTask;

      setTasks(
        (current) =>
          current.map(
            (item) =>
              item.id
              === updatedTask.id
                ? updatedTask
                : item
          )
      );
    } catch (requestError) {
      setTasks(
        (current) =>
          current.map(
            (item) =>
              item.id === taskId
                ? {
                    ...item,
                    status:
                      previousStatus,
                  }
                : item
          )
      );

      setError(
        getErrorMessage(
          requestError
        )
      );
    } finally {
      setUpdatingTaskId(null);
    }
  }


  async function deleteTask(
    taskId: number
  ) {
    setUpdatingTaskId(
      taskId
    );

    setError("");

    try {
      const response =
        await apiFetch(
          `${BOARD_API_URL}${taskId}/`,
          {
            method: "DELETE",
          }
        );

      const data =
        await parseResponse(
          response
        );

      if (!response.ok) {
        throw new Error(
          extractApiError(
            data,
            "Could not delete task."
          )
        );
      }

      setTasks(
        (current) =>
          current.filter(
            (task) =>
              task.id !== taskId
          )
      );

      setSelectedTaskId(null);
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError
        )
      );
    } finally {
      setUpdatingTaskId(null);
    }
  }


  function handleDragStart(
    event: DragEvent,
    taskId: number
  ) {
    setDraggedTaskId(
      taskId
    );

    event.dataTransfer.effectAllowed =
      "move";

    event.dataTransfer.setData(
      "text/plain",
      String(taskId)
    );
  }


  function handleDragEnd() {
    setDraggedTaskId(null);
    setDragOverStatus(null);
  }


  function handleDragOver(
    event: DragEvent,
    status: TaskStatus
  ) {
    event.preventDefault();

    event.dataTransfer.dropEffect =
      "move";

    setDragOverStatus(
      status
    );
  }


  function handleDrop(
    event: DragEvent,
    status: TaskStatus
  ) {
    event.preventDefault();

    const taskId =
      Number(
        event.dataTransfer.getData(
          "text/plain"
        )
      );

    setDraggedTaskId(null);
    setDragOverStatus(null);

    if (
      !Number.isFinite(
        taskId
      )
    ) {
      return;
    }

    void moveTask(
      taskId,
      status
    );
  }


  return (
    <ProtectedLayout>
      <main className="board-page">
        <section className="board-shell">
          <header className="board-header">
            <div className="board-heading">
              <span className="board-heading-dot" />

              <h1>
                Board
              </h1>
            </div>

            <button
              type="button"
              className="board-add-button"
              onClick={openAddTask}
            >
              <span>+</span>
              Add task
            </button>
          </header>


          {error && (
            <div
              className="board-error"
              role="alert"
            >
              <span>
                {error}
              </span>

              <button
                type="button"
                onClick={() =>
                  setError("")
                }
              >
                ×
              </button>
            </div>
          )}


          {isLoading ? (
            <div className="board-loading">
              <span />
            </div>
          ) : (
            <div className="board-columns">
              {COLUMNS.map(
                (column) => {
                  const columnTasks =
                    tasksByStatus[
                      column.status
                    ];

                  const isDragOver =
                    dragOverStatus
                    === column.status;

                  return (
                    <section
                      key={
                        column.status
                      }
                      className={[
                        "board-column",
                        isDragOver
                          ? "is-drag-over"
                          : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onDragOver={(
                        event
                      ) =>
                        handleDragOver(
                          event,
                          column.status
                        )
                      }
                      onDragLeave={() =>
                        setDragOverStatus(
                          (current) =>
                            current
                            === column.status
                              ? null
                              : current
                        )
                      }
                      onDrop={(
                        event
                      ) =>
                        handleDrop(
                          event,
                          column.status
                        )
                      }
                    >
                      <header className="board-column-header">
                        <h2>
                          {column.title}
                        </h2>

                        <span>
                          {
                            columnTasks.length
                          }
                        </span>
                      </header>


                      <div className="board-task-list">
                        {columnTasks.length
                        === 0 ? (
                          <div className="board-column-empty" />
                        ) : (
                          columnTasks.map(
                            (task) => {
                              const dueLabel =
                                getDueDateLabel(
                                  task.due_date
                                );

                              const isDragging =
                                draggedTaskId
                                === task.id;

                              const isUpdating =
                                updatingTaskId
                                === task.id;

                              return (
                                <article
                                  key={
                                    task.id
                                  }
                                  draggable={
                                    !isUpdating
                                  }
                                  className={[
                                    "board-task",
                                    isDragging
                                      ? "is-dragging"
                                      : "",
                                    task.status
                                    === "done"
                                      ? "is-done"
                                      : "",
                                    task.is_blocked
                                      ? "is-blocked"
                                      : "",
                                  ]
                                    .filter(Boolean)
                                    .join(" ")}
                                  onDragStart={(
                                    event
                                  ) =>
                                    handleDragStart(
                                      event,
                                      task.id
                                    )
                                  }
                                  onDragEnd={
                                    handleDragEnd
                                  }
                                  onClick={() =>
                                    setSelectedTaskId(
                                      task.id
                                    )
                                  }
                                >
                                  <div className="board-task-top">
                                    <h3>
                                      {
                                        task.title
                                      }
                                    </h3>

                                    {isUpdating && (
                                      <span className="board-task-saving" />
                                    )}
                                  </div>


                                  {(dueLabel
                                    || task.is_blocked) && (
                                    <div className="board-task-meta">
                                      {task.is_blocked && (
                                        <span className="is-blocked">
                                          Blocked
                                        </span>
                                      )}

                                      {dueLabel && (
                                        <span>
                                          {dueLabel}
                                        </span>
                                      )}
                                    </div>
                                  )}
                                </article>
                              );
                            }
                          )
                        )}
                      </div>
                    </section>
                  );
                }
              )}
            </div>
          )}
        </section>


        {isAddOpen && (
          <div
            className="board-modal-backdrop"
            onMouseDown={(
              event
            ) => {
              if (
                event.target
                === event.currentTarget
              ) {
                closeAddTask();
              }
            }}
          >
            <section className="board-modal">
              <button
                type="button"
                className="board-modal-close"
                onClick={
                  closeAddTask
                }
              >
                ×
              </button>

              <header className="board-modal-header">
                <span>
                  New task
                </span>

                <h2>
                  What needs to be done?
                </h2>
              </header>


              <form
                className="board-add-form"
                onSubmit={
                  createTask
                }
              >
                <label>
                  <span>
                    Task
                  </span>

                  <input
                    type="text"
                    value={
                      newTaskTitle
                    }
                    onChange={(
                      event
                    ) =>
                      setNewTaskTitle(
                        event.target.value
                      )
                    }
                    placeholder="One concrete action"
                    autoFocus
                    maxLength={255}
                  />
                </label>


                {activeGoals.length
                > 1 && (
                  <label>
                    <span>
                      Goal
                    </span>

                    <select
                      value={
                        newTaskGoal
                      }
                      onChange={(
                        event
                      ) =>
                        setNewTaskGoal(
                          event.target.value
                        )
                      }
                    >
                      <option value="">
                        Choose goal
                      </option>

                      {activeGoals.map(
                        (goal) => (
                          <option
                            key={
                              goal.id
                            }
                            value={
                              goal.id
                            }
                          >
                            {goal.title}
                          </option>
                        )
                      )}
                    </select>
                  </label>
                )}


                {activeGoals.length
                === 0 && (
                  <p className="board-no-goals">
                    Create an active goal first.
                  </p>
                )}


                {formError && (
                  <div className="board-form-error">
                    {formError}
                  </div>
                )}


                <footer className="board-modal-actions">
                  <button
                    type="button"
                    onClick={
                      closeAddTask
                    }
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={
                      isSaving
                      || activeGoals.length
                      === 0
                    }
                  >
                    {isSaving
                      ? "Creating…"
                      : "Create"}
                  </button>
                </footer>
              </form>
            </section>
          </div>
        )}


        {selectedTask && (
          <div
            className="board-modal-backdrop"
            onMouseDown={(
              event
            ) => {
              if (
                event.target
                === event.currentTarget
              ) {
                setSelectedTaskId(null);
              }
            }}
          >
            <section className="board-modal board-task-modal">
              <button
                type="button"
                className="board-modal-close"
                onClick={() =>
                  setSelectedTaskId(null)
                }
              >
                ×
              </button>

              <header className="board-modal-header">
                <span>
                  Task
                </span>

                <h2>
                  {selectedTask.title}
                </h2>
              </header>


              <div className="board-task-detail">
                {selectedTask.description && (
                  <p>
                    {
                      selectedTask.description
                    }
                  </p>
                )}


                {selectedTask.is_blocked && (
                  <div className="board-blocked-note">
                    Blocked by{" "}
                    {selectedTask
                      .blocking_tasks
                      .map(
                        (task) =>
                          task.title
                      )
                      .join(", ")}
                  </div>
                )}


                <div className="board-task-status-actions">
                  {COLUMNS.map(
                    (column) => (
                      <button
                        key={
                          column.status
                        }
                        type="button"
                        className={
                          selectedTask.status
                          === column.status
                            ? "is-active"
                            : ""
                        }
                        disabled={
                          updatingTaskId
                          === selectedTask.id
                        }
                        onClick={() =>
                          void moveTask(
                            selectedTask.id,
                            column.status
                          )
                        }
                      >
                        {column.title}
                      </button>
                    )
                  )}
                </div>
              </div>


              <footer className="board-task-modal-actions">
                <button
                  type="button"
                  className="is-delete"
                  disabled={
                    updatingTaskId
                    === selectedTask.id
                  }
                  onClick={() =>
                    void deleteTask(
                      selectedTask.id
                    )
                  }
                >
                  Delete
                </button>
              </footer>
            </section>
          </div>
        )}
      </main>
    </ProtectedLayout>
  );
}
