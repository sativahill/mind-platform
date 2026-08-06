"use client";

import {
  type ChangeEvent,
  type FormEvent,
  type PointerEvent as ReactPointerEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import ProtectedLayout from "@/components/ProtectedLayout";
import { apiFetch } from "@/lib/api";

import "./board.css";

const BOARD_API_URL = "http://127.0.0.1:8000/api/board/";
const BOARD_LAYOUT_API_URL =
  "http://127.0.0.1:8000/api/board/layout/";
const GOALS_API_URL = "http://127.0.0.1:8000/api/goals/";
const BOARD_HINT_STORAGE_KEY =
  "project-board-hint-seen";

type TaskStatus = "todo" | "in_progress" | "done";

type TaskPriority =
  | "low"
  | "medium"
  | "high"
  | "critical";

type TaskImportance =
  | "small"
  | "medium"
  | "large";

type TaskSource =
  | "manual"
  | "goal_ai"
  | "daily_log";

type GoalStatus =
  | "active"
  | "completed"
  | "archived";

type RequestState =
  | "idle"
  | "loading"
  | "saving"
  | "deleting";

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
  importance: TaskImportance;
  source: TaskSource;
  due_date: string | null;
  completed_at: string | null;
  position_x: number;
  position_y: number;
  sort_order: number;
  dependencies: TaskReference[];
  dependent_task_ids: number[];
  is_blocked: boolean;
  blocking_tasks: TaskReference[];
  created_at: string;
  updated_at: string;
}

interface Goal {
  id: number;
  title: string;
  status: GoalStatus;
  progress: number;
  target_date: string | null;
}

interface TaskDraft {
  goal: string;
  title: string;
  description: string;
  priority: TaskPriority;
  importance: TaskImportance;
  due_date: string;
  dependency_ids: number[];
}

interface DragState {
  taskId: number;
  pointerId: number;
  startClientX: number;
  startClientY: number;
  startPositionX: number;
  startPositionY: number;
  hasMoved: boolean;
}

interface LayoutUpdate {
  id: number;
  status?: TaskStatus;
  position_x?: number;
  position_y?: number;
  sort_order?: number;
}

interface UndoState {
  taskId: number;
  previousStatus: TaskStatus;
  previousPositionX: number;
  previousPositionY: number;
  message: string;
}

interface ApiErrorShape {
  detail?: string;
  [key: string]: unknown;
}

const EMPTY_TASK_DRAFT: TaskDraft = {
  goal: "",
  title: "",
  description: "",
  priority: "medium",
  importance: "small",
  due_date: "",
  dependency_ids: [],
};

function clamp(
  value: number,
  minimum: number,
  maximum: number
) {
  return Math.min(
    Math.max(value, minimum),
    maximum
  );
}

function getStatusLabel(
  status: TaskStatus
) {
  if (status === "in_progress") {
    return "In progress";
  }

  if (status === "done") {
    return "Completed";
  }

  return "To do";
}

function getStatusAction(
  status: TaskStatus
) {
  if (status === "todo") {
    return "Start";
  }

  if (status === "in_progress") {
    return "Mark done";
  }

  return "Reopen";
}

function getNextStatus(
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

function getPriorityLabel(
  priority: TaskPriority
) {
  return (
    priority.charAt(0).toUpperCase()
    + priority.slice(1)
  );
}

function getImportanceLabel(
  importance: TaskImportance
) {
  if (importance === "large") {
    return "Major";
  }

  if (importance === "medium") {
    return "Meaningful";
  }

  return "Small";
}

function getSourceLabel(
  source: TaskSource
) {
  if (source === "goal_ai") {
    return "Goal AI";
  }

  if (source === "daily_log") {
    return "Daily Log";
  }

  return "Manual";
}

function getDateLabel(
  value: string | null
) {
  if (!value) {
    return "No deadline";
  }

  const date = new Date(
    `${value}T00:00:00`
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
      year:
        date.getFullYear()
        === new Date().getFullYear()
          ? undefined
          : "numeric",
    }
  ).format(date);
}

function getCompletedDateLabel(
  value: string | null
) {
  if (!value) {
    return null;
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return null;
  }

  return new Intl.DateTimeFormat(
    "en",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
    }
  ).format(date);
}

function isOverdue(
  dueDate: string | null,
  status: TaskStatus
) {
  if (
    !dueDate
    || status === "done"
  ) {
    return false;
  }

  const today = new Date();

  today.setHours(
    0,
    0,
    0,
    0
  );

  const due = new Date(
    `${dueDate}T00:00:00`
  );

  return due < today;
}

function getErrorMessage(
  error: unknown
) {
  if (
    error instanceof Error
  ) {
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

  const object = data as ApiErrorShape;

  if (
    typeof object.detail === "string"
  ) {
    return object.detail;
  }

  const messages: string[] = [];

  function collect(
    value: unknown
  ) {
    if (
      typeof value === "string"
    ) {
      messages.push(value);
      return;
    }

    if (
      Array.isArray(value)
    ) {
      value.forEach(collect);
      return;
    }

    if (
      value
      && typeof value === "object"
    ) {
      Object.values(value).forEach(
        collect
      );
    }
  }

  collect(object);

  return messages[0] ?? fallback;
}

async function parseResponse(
  response: Response
) {
  if (
    response.status === 204
  ) {
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

function getNodeSize(
  task: BoardTask
) {
  let size = 18;

  if (
    task.importance === "medium"
  ) {
    size += 5;
  }

  if (
    task.importance === "large"
  ) {
    size += 10;
  }

  if (
    task.priority === "high"
  ) {
    size += 3;
  }

  if (
    task.priority === "critical"
  ) {
    size += 6;
  }

  if (
    task.status === "in_progress"
  ) {
    size += 8;
  }

  if (
    task.status === "done"
  ) {
    size -= 5;
  }

  return clamp(
    size,
    13,
    42
  );
}

function getCompletedPosition(
  taskId: number
) {
  const side = taskId % 4;
  const offset =
    (taskId * 733) % 1800;

  if (side === 0) {
    return {
      x: 900 + offset,
      y: 8100 + (
        (taskId * 281) % 900
      ),
    };
  }

  if (side === 1) {
    return {
      x: 8100 + offset,
      y: 6900 + (
        (taskId * 317) % 1500
      ),
    };
  }

  if (side === 2) {
    return {
      x: 700 + offset,
      y: 1000 + (
        (taskId * 239) % 1500
      ),
    };
  }

  return {
    x: 8100 + offset,
    y: 900 + (
      (taskId * 353) % 1500
    ),
  };
}

function getNewTaskPosition(
  tasks: BoardTask[]
) {
  const activeTasks =
    tasks.filter(
      (task) =>
        task.status !== "done"
    );

  const index =
    activeTasks.length;

  const angle =
    index * 2.399963229728653;

  const radius =
    Math.min(
      2800,
      650
      + Math.sqrt(index + 1)
      * 590
    );

  return {
    x: Math.round(
      clamp(
        5000
        + Math.cos(angle)
        * radius,
        950,
        9050
      )
    ),
    y: Math.round(
      clamp(
        4700
        + Math.sin(angle)
        * radius,
        1150,
        8500
      )
    ),
  };
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
    requestState,
    setRequestState,
  ] = useState<RequestState>(
    "loading"
  );

  const [
    selectedTaskId,
    setSelectedTaskId,
  ] = useState<number | null>(
    null
  );

  const [
    hoveredTaskId,
    setHoveredTaskId,
  ] = useState<number | null>(
    null
  );

  const [
    dragState,
    setDragState,
  ] = useState<DragState | null>(
    null
  );

  const [
    updatingTaskId,
    setUpdatingTaskId,
  ] = useState<number | null>(
    null
  );

  const [
    isQuickAddOpen,
    setIsQuickAddOpen,
  ] = useState(false);

  const [
    showBoardHint,
    setShowBoardHint,
  ] = useState(false);

  const [
    quickTitle,
    setQuickTitle,
  ] = useState("");

  const [
    quickGoalId,
    setQuickGoalId,
  ] = useState("");

  const [
    isEditing,
    setIsEditing,
  ] = useState(false);

  const [
    taskDraft,
    setTaskDraft,
  ] = useState<TaskDraft>(
    EMPTY_TASK_DRAFT
  );

  const [
    pageError,
    setPageError,
  ] = useState("");

  const [
    formError,
    setFormError,
  ] = useState("");

  const [
    undoState,
    setUndoState,
  ] = useState<UndoState | null>(
    null
  );

  const [
    deleteConfirmTaskId,
    setDeleteConfirmTaskId,
  ] = useState<number | null>(
    null
  );

  const canvasRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const undoTimerRef =
    useRef<
      ReturnType<typeof setTimeout>
      | null
    >(null);

  const activeGoals = useMemo(
    () =>
      goals.filter(
        (goal) =>
          goal.status === "active"
      ),
    [goals]
  );

  const selectedTask = useMemo(
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
        ) ?? null
      );
    },
    [
      selectedTaskId,
      tasks,
    ]
  );

  const selectedGoal = useMemo(
    () => {
      if (!selectedTask) {
        return null;
      }

      return (
        goals.find(
          (goal) =>
            goal.id
            === selectedTask.goal
        ) ?? null
      );
    },
    [
      goals,
      selectedTask,
    ]
  );

  const availableDependencies =
    useMemo(
      () => {
        if (!selectedTask) {
          return [];
        }

        const selectedGoalId =
          Number(taskDraft.goal);

        return tasks.filter(
          (task) =>
            task.id
            !== selectedTask.id
            && (
              !selectedGoalId
              || task.goal
                === selectedGoalId
            )
        );
      },
      [
        selectedTask,
        taskDraft.goal,
        tasks,
      ]
    );

  const selectedDependents =
    useMemo(
      () => {
        if (!selectedTask) {
          return [];
        }

        return tasks.filter(
          (task) =>
            selectedTask
              .dependent_task_ids
              .includes(task.id)
        );
      },
      [
        selectedTask,
        tasks,
      ]
    );

  const relatedTaskIds =
    useMemo(
      () => {
        const focusTaskId =
          hoveredTaskId
          ?? selectedTaskId;

        if (
          focusTaskId === null
        ) {
          return new Set<number>();
        }

        const focusTask =
          tasks.find(
            (task) =>
              task.id
              === focusTaskId
          );

        if (!focusTask) {
          return new Set<number>();
        }

        return new Set([
          focusTask.id,
          ...focusTask
            .dependencies
            .map(
              (dependency) =>
                dependency.id
            ),
          ...focusTask
            .dependent_task_ids,
        ]);
      },
      [
        hoveredTaskId,
        selectedTaskId,
        tasks,
      ]
    );

  const selectedGoalTaskCount =
    selectedGoal
      ? tasks.filter(
          (task) =>
            task.goal
            === selectedGoal.id
        ).length
      : 0;

  const selectedGoalDoneCount =
    selectedGoal
      ? tasks.filter(
          (task) =>
            task.goal
            === selectedGoal.id
            && task.status
            === "done"
        ).length
      : 0;

  const loadBoard =
    useCallback(
      async (
        showLoading = true
      ) => {
        if (showLoading) {
          setRequestState(
            "loading"
          );
        }

        setPageError("");

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

          if (
            !tasksResponse.ok
          ) {
            throw new Error(
              extractApiError(
                tasksData,
                "Could not load tasks."
              )
            );
          }

          if (
            !goalsResponse.ok
          ) {
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
        } catch (error) {
          setPageError(
            getErrorMessage(error)
          );
        } finally {
          setRequestState(
            "idle"
          );
        }
      },
      []
    );

  useEffect(() => {
    // Initial API synchronization for this client page.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadBoard();

    return () => {
      if (
        undoTimerRef.current
      ) {
        clearTimeout(
          undoTimerRef.current
        );
      }
    };
  }, [loadBoard]);

  useEffect(() => {
    try {
      if (
        window.localStorage.getItem(
          BOARD_HINT_STORAGE_KEY
        ) !== "true"
      ) {
        // This client-only preference is available after hydration.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setShowBoardHint(true);
      }
    } catch {
      // The hint remains optional when storage is unavailable.
    }
  }, []);

  useEffect(() => {
    if (!isQuickAddOpen) {
      return;
    }

    function handleQuickAddEscape(
      event: KeyboardEvent
    ) {
      if (
        event.key !== "Escape"
        || requestState === "saving"
      ) {
        return;
      }

      setQuickTitle("");
      setQuickGoalId("");
      setFormError("");
      setIsQuickAddOpen(false);
    }

    window.addEventListener(
      "keydown",
      handleQuickAddEscape
    );

    return () =>
      window.removeEventListener(
        "keydown",
        handleQuickAddEscape
      );
  }, [
    isQuickAddOpen,
    requestState,
  ]);

  useEffect(() => {
    if (
      selectedTaskId === null
    ) {
      return;
    }

    const stillExists =
      tasks.some(
        (task) =>
          task.id
          === selectedTaskId
      );

    if (!stillExists) {
      // Clear modal state when its task disappears after synchronization.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedTaskId(
        null
      );
      setIsEditing(false);
    }
  }, [
    selectedTaskId,
    tasks,
  ]);

  function chooseDefaultGoal() {
    if (
      activeGoals.length === 1
    ) {
      return String(
        activeGoals[0].id
      );
    }

    return "";
  }

  function openQuickAdd() {
    setQuickTitle("");
    setQuickGoalId(
      chooseDefaultGoal()
    );
    setFormError("");
    setIsQuickAddOpen(true);
  }

  function closeQuickAdd() {
    if (
      requestState === "saving"
    ) {
      return;
    }

    setQuickTitle("");
    setQuickGoalId("");
    setFormError("");
    setIsQuickAddOpen(false);
  }

  function dismissBoardHint() {
    setShowBoardHint(false);

    try {
      window.localStorage.setItem(
        BOARD_HINT_STORAGE_KEY,
        "true"
      );
    } catch {
      // Dragging and opening tasks must still work without storage.
    }
  }

  async function saveLayout(
    updates: LayoutUpdate[]
  ) {
    const response =
      await apiFetch(
        BOARD_LAYOUT_API_URL,
        {
          method: "PATCH",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            tasks: updates,
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
          "Could not save the layout."
        )
      );
    }

    return data;
  }

  async function createQuickTask(
    event: FormEvent
  ) {
    event.preventDefault();

    const title =
      quickTitle.trim();

    if (!title) {
      setFormError(
        "Write one concrete action."
      );
      return;
    }

    if (!quickGoalId) {
      setFormError(
        "Choose a goal."
      );
      return;
    }

    const position =
      getNewTaskPosition(
        tasks
      );

    setRequestState(
      "saving"
    );

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
              goal: Number(
                quickGoalId
              ),
              title,
              description: "",
              status: "todo",
              priority: "medium",
              importance: "small",
              due_date: null,
              dependency_ids: [],
              position_x:
                position.x,
              position_y:
                position.y,
              sort_order:
                tasks.length,
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
            "Could not create the task."
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

      setQuickTitle("");
      setQuickGoalId("");
      setIsQuickAddOpen(false);
    } catch (error) {
      setFormError(
        getErrorMessage(error)
      );
    } finally {
      setRequestState(
        "idle"
      );
    }
  }

  function openTask(
    taskId: number
  ) {
    dismissBoardHint();
    setSelectedTaskId(
      taskId
    );
    setIsEditing(false);
    setFormError("");
  }

  function closeTask() {
    setSelectedTaskId(
      null
    );
    setIsEditing(false);
    setFormError("");
  }

  function startEditing() {
    if (!selectedTask) {
      return;
    }

    setTaskDraft({
      goal: String(
        selectedTask.goal
      ),
      title:
        selectedTask.title,
      description:
        selectedTask.description,
      priority:
        selectedTask.priority,
      importance:
        selectedTask.importance,
      due_date:
        selectedTask.due_date
        ?? "",
      dependency_ids:
        selectedTask
          .dependencies
          .map(
            (dependency) =>
              dependency.id
          ),
    });

    setFormError("");
    setIsEditing(true);
  }

  function cancelEditing() {
    setIsEditing(false);
    setFormError("");
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

  async function saveTaskDetails(
    event: FormEvent
  ) {
    event.preventDefault();

    if (!selectedTask) {
      return;
    }

    const title =
      taskDraft.title.trim();

    if (!title) {
      setFormError(
        "Task title cannot be empty."
      );
      return;
    }

    if (!taskDraft.goal) {
      setFormError(
        "Choose a goal."
      );
      return;
    }

    setRequestState(
      "saving"
    );

    setFormError("");

    try {
      const response =
        await apiFetch(
          `${BOARD_API_URL}${selectedTask.id}/`,
          {
            method: "PATCH",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              goal: Number(
                taskDraft.goal
              ),
              title,
              description:
                taskDraft
                  .description
                  .trim(),
              priority:
                taskDraft.priority,
              importance:
                taskDraft.importance,
              due_date:
                taskDraft.due_date
                || null,
              dependency_ids:
                taskDraft
                  .dependency_ids,
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
            "Could not save the task."
          )
        );
      }

      const updatedTask =
        data as BoardTask;

      setTasks(
        (current) =>
          current.map(
            (task) =>
              task.id
              === updatedTask.id
                ? updatedTask
                : task
          )
      );

      setSelectedTaskId(
        updatedTask.id
      );
      setIsEditing(false);
    } catch (error) {
      setFormError(
        getErrorMessage(error)
      );
    } finally {
      setRequestState(
        "idle"
      );
    }
  }

  function showUndo(
    updatedTask: BoardTask,
    previousStatus: TaskStatus,
    previousPositionX: number,
    previousPositionY: number
  ) {
    if (
      undoTimerRef.current
    ) {
      clearTimeout(
        undoTimerRef.current
      );
    }

    let message =
      "Task reopened.";

    if (
      updatedTask.status
      === "in_progress"
    ) {
      message =
        "Task started.";
    }

    if (
      updatedTask.status
      === "done"
    ) {
      message =
        "Task completed.";
    }

    setUndoState({
      taskId:
        updatedTask.id,
      previousStatus,
      previousPositionX,
      previousPositionY,
      message,
    });

    undoTimerRef.current =
      setTimeout(() => {
        setUndoState(null);
      }, 5000);
  }

  async function changeTaskStatus(
    task: BoardTask,
    nextStatus: TaskStatus
  ) {
    if (
      task.is_blocked
      && nextStatus !== "todo"
    ) {
      setPageError(
        "Complete the blocking tasks first."
      );
      return;
    }

    const previousStatus =
      task.status;

    const previousPositionX =
      task.position_x;

    const previousPositionY =
      task.position_y;

    const nextPosition =
      nextStatus === "done"
        ? getCompletedPosition(
            task.id
          )
        : {
            x: task.position_x,
            y: task.position_y,
          };

    setUpdatingTaskId(
      task.id
    );

    setPageError("");

    setTasks(
      (current) =>
        current.map(
          (item) =>
            item.id === task.id
              ? {
                  ...item,
                  status:
                    nextStatus,
                  position_x:
                    nextPosition.x,
                  position_y:
                    nextPosition.y,
                  completed_at:
                    nextStatus === "done"
                      ? new Date()
                          .toISOString()
                      : null,
                }
              : item
        )
    );

    try {
      await saveLayout([
        {
          id: task.id,
          status: nextStatus,
          position_x:
            nextPosition.x,
          position_y:
            nextPosition.y,
          sort_order:
            task.sort_order,
        },
      ]);

      const response =
        await apiFetch(
          `${BOARD_API_URL}${task.id}/`
        );

      const data =
        await parseResponse(
          response
        );

      if (!response.ok) {
        throw new Error(
          extractApiError(
            data,
            "Could not refresh the task."
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

      showUndo(
        updatedTask,
        previousStatus,
        previousPositionX,
        previousPositionY
      );
    } catch (error) {
      await loadBoard(false);

      setPageError(
        getErrorMessage(error)
      );
    } finally {
      setUpdatingTaskId(
        null
      );
    }
  }

  async function undoStatusChange() {
    if (!undoState) {
      return;
    }

    const task =
      tasks.find(
        (item) =>
          item.id
          === undoState.taskId
      );

    if (!task) {
      setUndoState(null);
      return;
    }

    setUpdatingTaskId(
      task.id
    );

    try {
      await saveLayout([
        {
          id: task.id,
          status:
            undoState.previousStatus,
          position_x:
            undoState
              .previousPositionX,
          position_y:
            undoState
              .previousPositionY,
          sort_order:
            task.sort_order,
        },
      ]);

      await loadBoard(false);

      setUndoState(null);
    } catch (error) {
      setPageError(
        getErrorMessage(error)
      );
    } finally {
      setUpdatingTaskId(
        null
      );
    }
  }

  function handlePointerDown(
    event:
      ReactPointerEvent<HTMLButtonElement>,
    task: BoardTask
  ) {
    if (
      event.button !== 0
    ) {
      return;
    }

    event.currentTarget
      .setPointerCapture(
        event.pointerId
      );

    setDragState({
      taskId:
        task.id,
      pointerId:
        event.pointerId,
      startClientX:
        event.clientX,
      startClientY:
        event.clientY,
      startPositionX:
        task.position_x,
      startPositionY:
        task.position_y,
      hasMoved: false,
    });
  }

  function handlePointerMove(
    event:
      ReactPointerEvent<HTMLButtonElement>
  ) {
    if (
      !dragState
      || dragState.pointerId
      !== event.pointerId
    ) {
      return;
    }

    const canvas =
      canvasRef.current;

    if (!canvas) {
      return;
    }

    const deltaX =
      event.clientX
      - dragState.startClientX;

    const deltaY =
      event.clientY
      - dragState.startClientY;

    const distance =
      Math.hypot(
        deltaX,
        deltaY
      );

    if (
      distance < 4
      && !dragState.hasMoved
    ) {
      return;
    }

    const rect =
      canvas.getBoundingClientRect();

    const positionX =
      Math.round(
        clamp(
          dragState.startPositionX
          + (
            deltaX
            / Math.max(
                rect.width,
                1
              )
            * 10000
          ),
          300,
          9700
        )
      );

    const positionY =
      Math.round(
        clamp(
          dragState.startPositionY
          + (
            deltaY
            / Math.max(
                rect.height,
                1
              )
            * 10000
          ),
          450,
          9550
        )
      );

    setDragState(
      (current) =>
        current
          ? {
              ...current,
              hasMoved: true,
            }
          : null
    );

    setTasks(
      (current) =>
        current.map(
          (task) =>
            task.id
            === dragState.taskId
              ? {
                  ...task,
                  position_x:
                    positionX,
                  position_y:
                    positionY,
                }
              : task
        )
    );
  }

  async function handlePointerUp(
    event:
      ReactPointerEvent<HTMLButtonElement>
  ) {
    if (
      !dragState
      || dragState.pointerId
      !== event.pointerId
    ) {
      return;
    }

    const currentDrag =
      dragState;

    const task =
      tasks.find(
        (item) =>
          item.id
          === currentDrag.taskId
      );

    setDragState(null);

    if (!task) {
      return;
    }

    if (
      !currentDrag.hasMoved
    ) {
      openTask(
        task.id
      );
      return;
    }

    dismissBoardHint();

    try {
      await saveLayout([
        {
          id: task.id,
          position_x:
            task.position_x,
          position_y:
            task.position_y,
          sort_order:
            task.sort_order,
        },
      ]);
    } catch (error) {
      setPageError(
        getErrorMessage(error)
      );

      await loadBoard(false);
    }
  }

  function handlePointerCancel() {
    setDragState(null);
  }

  async function deleteTask(
    task: BoardTask
  ) {
    setRequestState(
      "deleting"
    );

    setPageError("");

    try {
      const response =
        await apiFetch(
          `${BOARD_API_URL}${task.id}/`,
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
            "Could not delete the task."
          )
        );
      }

      setTasks(
        (current) =>
          current.filter(
            (item) =>
              item.id !== task.id
          )
      );

      setSelectedTaskId(null);
      setDeleteConfirmTaskId(null);
      setIsEditing(false);
    } catch (error) {
      setPageError(
        getErrorMessage(error)
      );
    } finally {
      setRequestState(
        "idle"
      );
    }
  }

  return (
    <ProtectedLayout>
      <main className="board-page">
        <header className="board-header">
          <div className="board-title">
            <span />

            <h1>Board</h1>
          </div>

          <button
            type="button"
            className="board-add-task"
            onClick={
              isQuickAddOpen
                ? closeQuickAdd
                : openQuickAdd
            }
            disabled={
              activeGoals.length === 0
            }
          >
            <span>
              {isQuickAddOpen
                ? "×"
                : "+"}
            </span>

            {isQuickAddOpen
              ? "Close"
              : "Add task"}
          </button>
        </header>

        {isQuickAddOpen && (
          <form
            className="board-quick-add"
            onSubmit={
              createQuickTask
            }
          >
            <div>
              <span>
                New task
              </span>
            </div>

            <input
              type="text"
              value={quickTitle}
              onChange={(
                event:
                  ChangeEvent<HTMLInputElement>
              ) =>
                setQuickTitle(
                  event.target.value
                )
              }
              placeholder="Write one concrete action…"
              autoFocus
              maxLength={255}
            />

            <select
              value={
                quickGoalId
              }
              onChange={(
                event
              ) =>
                setQuickGoalId(
                  event.target.value
                )
              }
              aria-label="Choose goal"
            >
              <option value="">
                Goal
              </option>

              {activeGoals.map(
                (goal) => (
                  <option
                    key={goal.id}
                    value={goal.id}
                  >
                    {goal.title}
                  </option>
                )
              )}
            </select>

            <button
              type="submit"
              disabled={
                requestState
                === "saving"
              }
            >
              {requestState
              === "saving"
                ? "Adding…"
                : "Add"}
            </button>

            {formError && (
              <p role="alert">
                {formError}
              </p>
            )}
          </form>
        )}

        {pageError && (
          <div
            className="board-error"
            role="alert"
          >
            <span>
              {pageError}
            </span>

            <button
              type="button"
              onClick={() =>
                setPageError("")
              }
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        {requestState
        === "loading" ? (
          <section className="board-loading">
            <span />

            <strong>
              Opening Board
            </strong>
          </section>
        ) : (
          <section className="board-canvas-shell">
            <div
              ref={canvasRef}
              className={[
                "board-canvas",
                selectedTask
                  ? "has-open-task"
                  : "",
                dragState
                  ? "is-dragging"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <div className="board-space board-space-one" />
              <div className="board-space board-space-two" />
              <div className="board-space board-space-three" />

              <svg
                className="board-connections"
                viewBox="0 0 10000 10000"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                {tasks.flatMap(
                  (task) =>
                    task.dependencies.map(
                      (dependency) => {
                        const source =
                          tasks.find(
                            (item) =>
                              item.id
                              === dependency.id
                          );

                        if (!source) {
                          return null;
                        }

                        const isActive =
                          relatedTaskIds.has(
                            source.id
                          )
                          && relatedTaskIds.has(
                            task.id
                          );

                        const curve =
                          Math.max(
                            220,
                            Math.abs(
                              task.position_x
                              - source.position_x
                            ) * 0.18
                          );

                        const path = [
                          `M ${source.position_x} ${source.position_y}`,
                          `C ${source.position_x + curve} ${source.position_y},`,
                          `${task.position_x - curve} ${task.position_y},`,
                          `${task.position_x} ${task.position_y}`,
                        ].join(" ");

                        return (
                          <path
                            key={
                              `${source.id}-${task.id}`
                            }
                            d={path}
                            className={[
                              "board-connection",
                              isActive
                                ? "is-active"
                                : "",
                              source.status
                              === "done"
                              || task.status
                              === "done"
                                ? "is-completed"
                                : "",
                            ]
                              .filter(Boolean)
                              .join(" ")}
                          />
                        );
                      }
                    )
                )}
              </svg>

              {tasks.length === 0 ? (
                <div className="board-empty">
                  <span />

                  <h2>
                    No tasks yet.
                  </h2>

                  <p>
                    Add one concrete action
                    to begin.
                  </p>

                  <button
                    type="button"
                    onClick={
                      openQuickAdd
                    }
                    disabled={
                      activeGoals.length
                      === 0
                    }
                  >
                    + Add task
                  </button>
                </div>
              ) : (
                tasks.map(
                  (task) => {
                    const nodeSize =
                      getNodeSize(
                        task
                      );

                    const isRelated =
                      relatedTaskIds.has(
                        task.id
                      );

                    const hasFocus =
                      hoveredTaskId
                      !== null
                      || selectedTaskId
                      !== null;

                    const isDimmed =
                      hasFocus
                      && !isRelated;

                    const overdue =
                      isOverdue(
                        task.due_date,
                        task.status
                      );

                    return (
                      <button
                        key={task.id}
                        type="button"
                        className={[
                          "board-node",
                          `status-${task.status}`,
                          `priority-${task.priority}`,
                          `importance-${task.importance}`,
                          hoveredTaskId
                          === task.id
                            ? "is-hovered"
                            : "",
                          isRelated
                            ? "is-related"
                            : "",
                          isDimmed
                            ? "is-dimmed"
                            : "",
                          dragState?.taskId
                          === task.id
                            ? "is-dragged"
                            : "",
                          task.is_blocked
                            ? "is-blocked"
                            : "",
                          overdue
                            ? "is-overdue"
                            : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        style={{
                          left:
                            `${task.position_x / 100}%`,
                          top:
                            `${task.position_y / 100}%`,
                          zIndex:
                            dragState?.taskId
                            === task.id
                              ? 80
                              : hoveredTaskId
                                === task.id
                                ? 40
                                : task.status
                                  === "in_progress"
                                  ? 20
                                  : 10,
                        }}
                        onPointerDown={(
                          event
                        ) =>
                          handlePointerDown(
                            event,
                            task
                          )
                        }
                        onPointerMove={
                          handlePointerMove
                        }
                        onPointerUp={
                          handlePointerUp
                        }
                        onPointerCancel={
                          handlePointerCancel
                        }
                        onMouseEnter={() =>
                          setHoveredTaskId(
                            task.id
                          )
                        }
                        onMouseLeave={() =>
                          setHoveredTaskId(
                            null
                          )
                        }
                        aria-label={
                          `Open task: ${task.title}`
                        }
                      >
                        <span
                          className="board-node-dot"
                          style={{
                            width:
                              `${nodeSize}px`,
                            height:
                              `${nodeSize}px`,
                          }}
                        >
                          {task.status
                          === "done" && (
                            <b>✓</b>
                          )}
                        </span>

                        <span className="board-node-copy">
                          <strong>
                            {task.title}
                          </strong>

                          <i>
                            {task.is_blocked
                              ? "Blocked"
                              : overdue
                                ? "Overdue"
                                : getStatusLabel(
                                  task.status
                                )}

                            {!task.is_blocked
                              && !overdue
                              && task.due_date
                              ? ` · ${getDateLabel(
                                  task.due_date
                                )}`
                              : ""}
                          </i>
                        </span>
                      </button>
                    );
                  }
                )
              )}

              {showBoardHint
                && tasks.length > 0 && (
                <p className="board-canvas-hint">
                  Drag tasks to arrange them. Click to open.
                </p>
              )}
            </div>

            {selectedTask && (
              <div
                className="board-task-overlay"
                role="presentation"
                onMouseDown={(
                  event
                ) => {
                  if (
                    event.target
                    === event.currentTarget
                  ) {
                    closeTask();
                  }
                }}
              >
                <article
                  className="board-task-modal"
                  role="dialog"
                  aria-modal="true"
                  aria-labelledby="board-task-title"
                >
                  <button
                    type="button"
                    className="board-task-close"
                    onClick={
                      closeTask
                    }
                    aria-label="Close task"
                  >
                    ×
                  </button>

                  <header className="board-task-modal-header">
                    <span
                      className={
                        `board-modal-status status-${selectedTask.status}`
                      }
                    />

                    <div>
                      <span>
                        {getStatusLabel(
                          selectedTask.status
                        )}
                      </span>

                      <h2 id="board-task-title">
                        {selectedTask.title}
                      </h2>

                      <p>
                        {selectedGoal?.title
                        ?? "Unknown goal"}
                      </p>
                    </div>
                  </header>

                  {isEditing ? (
                    <form
                      className="board-task-form"
                      onSubmit={
                        saveTaskDetails
                      }
                    >
                      <label className="board-form-primary">
                        <span>
                          Task
                        </span>

                        <input
                          type="text"
                          value={
                            taskDraft.title
                          }
                          onChange={(
                            event
                          ) =>
                            updateTaskDraft(
                              "title",
                              event.target.value
                            )
                          }
                          maxLength={255}
                        />
                      </label>

                      <label>
                        <span>
                          Goal
                        </span>

                        <select
                          value={
                            taskDraft.goal
                          }
                          onChange={(
                            event
                          ) =>
                            updateTaskDraft(
                              "goal",
                              event.target.value
                            )
                          }
                        >
                          {activeGoals.map(
                            (goal) => (
                              <option
                                key={goal.id}
                                value={goal.id}
                              >
                                {goal.title}
                              </option>
                            )
                          )}
                        </select>
                      </label>

                      <label>
                        <span>
                          Description
                          <small>
                            optional
                          </small>
                        </span>

                        <textarea
                          value={
                            taskDraft.description
                          }
                          onChange={(
                            event
                          ) =>
                            updateTaskDraft(
                              "description",
                              event.target.value
                            )
                          }
                          rows={4}
                        />
                      </label>

                      <div className="board-task-form-grid">
                        <label>
                          <span>
                            Priority
                          </span>

                          <select
                            value={
                              taskDraft.priority
                            }
                            onChange={(
                              event
                            ) =>
                              updateTaskDraft(
                                "priority",
                                event.target.value as TaskPriority
                              )
                            }
                          >
                            <option value="low">
                              Low
                            </option>

                            <option value="medium">
                              Medium
                            </option>

                            <option value="high">
                              High
                            </option>

                            <option value="critical">
                              Critical
                            </option>
                          </select>
                        </label>

                        <label>
                          <span>
                            Importance
                          </span>

                          <select
                            value={
                              taskDraft.importance
                            }
                            onChange={(
                              event
                            ) =>
                              updateTaskDraft(
                                "importance",
                                event.target.value as TaskImportance
                              )
                            }
                          >
                            <option value="small">
                              Small
                            </option>

                            <option value="medium">
                              Meaningful
                            </option>

                            <option value="large">
                              Major
                            </option>
                          </select>
                        </label>

                        <label>
                          <span>
                            Deadline
                            <small>
                              optional
                            </small>
                          </span>

                          <input
                            type="date"
                            value={
                              taskDraft.due_date
                            }
                            onChange={(
                              event
                            ) =>
                              updateTaskDraft(
                                "due_date",
                                event.target.value
                              )
                            }
                          />
                        </label>
                      </div>

                      <fieldset className="board-task-dependencies">
                        <legend>
                          Dependencies
                          <small>
                            optional
                          </small>
                        </legend>

                        {availableDependencies
                          .length > 0 ? (
                          <div>
                            {availableDependencies.map(
                              (
                                dependency
                              ) => {
                                const checked =
                                  taskDraft
                                    .dependency_ids
                                    .includes(
                                      dependency.id
                                    );

                                return (
                                  <label
                                    key={
                                      dependency.id
                                    }
                                  >
                                    <input
                                      type="checkbox"
                                      checked={
                                        checked
                                      }
                                      onChange={() =>
                                        updateTaskDraft(
                                          "dependency_ids",
                                          checked
                                            ? taskDraft
                                                .dependency_ids
                                                .filter(
                                                  (
                                                    id
                                                  ) =>
                                                    id
                                                    !== dependency.id
                                                )
                                            : [
                                                ...taskDraft
                                                  .dependency_ids,
                                                dependency.id,
                                              ]
                                        )
                                      }
                                    />

                                    <span>
                                      {
                                        dependency.title
                                      }
                                    </span>

                                    <small>
                                      {
                                        getStatusLabel(
                                          dependency.status
                                        )
                                      }
                                    </small>
                                  </label>
                                );
                              }
                            )}
                          </div>
                        ) : (
                          <p>
                            No other tasks
                            are available.
                          </p>
                        )}
                      </fieldset>

                      {formError && (
                        <div
                          className="board-form-error"
                          role="alert"
                        >
                          {formError}
                        </div>
                      )}

                      <footer className="board-task-form-actions">
                        <button
                          type="button"
                          onClick={
                            cancelEditing
                          }
                        >
                          Cancel
                        </button>

                        <button
                          type="submit"
                          disabled={
                            requestState
                            === "saving"
                          }
                        >
                          {requestState
                          === "saving"
                            ? "Saving…"
                            : "Save changes"}
                        </button>
                      </footer>
                    </form>
                  ) : (
                    <>
                      <div className="board-task-modal-body">
                        {selectedTask.is_blocked && (
                          <section className="board-task-blocked">
                            <span>
                              Blocked
                            </span>

                            <strong>
                              Complete these tasks first
                            </strong>

                            <ul>
                              {selectedTask
                                .blocking_tasks
                                .map(
                                  (
                                    task
                                  ) => (
                                    <li
                                      key={
                                        task.id
                                      }
                                    >
                                      {task.title}
                                    </li>
                                  )
                                )}
                            </ul>
                          </section>
                        )}

                        {selectedTask.description && (
                          <section className="board-task-section">
                            <span>
                              Description
                            </span>

                            <p>
                              {
                                selectedTask.description
                              }
                            </p>
                          </section>
                        )}

                        <section className="board-task-facts">
                          <div>
                            <span>
                              Deadline
                            </span>

                            <strong
                              className={
                                isOverdue(
                                  selectedTask.due_date,
                                  selectedTask.status
                                )
                                  ? "is-overdue"
                                  : ""
                              }
                            >
                              {getDateLabel(
                                selectedTask.due_date
                              )}
                            </strong>
                          </div>

                          <div>
                            <span>
                              Priority
                            </span>

                            <strong>
                              {getPriorityLabel(
                                selectedTask.priority
                              )}
                            </strong>
                          </div>

                          <div>
                            <span>
                              Importance
                            </span>

                            <strong>
                              {getImportanceLabel(
                                selectedTask.importance
                              )}
                            </strong>
                          </div>

                          <div>
                            <span>
                              Source
                            </span>

                            <strong>
                              {getSourceLabel(
                                selectedTask.source
                              )}
                            </strong>
                          </div>
                        </section>

                        {selectedGoal && (
                          <section className="board-goal-progress">
                            <div>
                              <span>
                                Goal progress
                              </span>

                              <strong>
                                {selectedGoal.title}
                              </strong>
                            </div>

                            <b>
                              {selectedGoal.progress}%
                            </b>

                            <i>
                              <span
                                style={{
                                  width:
                                    `${selectedGoal.progress}%`,
                                }}
                              />
                            </i>

                            <small>
                              {
                                selectedGoalDoneCount
                              }{" "}
                              of{" "}
                              {
                                selectedGoalTaskCount
                              }{" "}
                              tasks completed
                            </small>
                          </section>
                        )}

                        <section className="board-task-section">
                          <span>
                            Dependencies
                          </span>

                          {selectedTask
                            .dependencies
                            .length > 0 ? (
                            <div className="board-task-links">
                              {selectedTask
                                .dependencies
                                .map(
                                  (
                                    dependency
                                  ) => (
                                    <button
                                      key={
                                        dependency.id
                                      }
                                      type="button"
                                      onClick={() => {
                                        setSelectedTaskId(
                                          dependency.id
                                        );
                                        setIsEditing(
                                          false
                                        );
                                      }}
                                    >
                                      <i
                                        className={
                                          `status-${dependency.status}`
                                        }
                                      />

                                      <span>
                                        {
                                          dependency.title
                                        }
                                      </span>

                                      <small>
                                        {
                                          getStatusLabel(
                                            dependency.status
                                          )
                                        }
                                      </small>
                                    </button>
                                  )
                                )}
                            </div>
                          ) : (
                            <p className="board-task-empty-copy">
                              No dependencies.
                            </p>
                          )}
                        </section>

                        {selectedDependents.length > 0 && (
                          <section className="board-task-section">
                            <span>
                              Unlocks
                            </span>

                            <div className="board-task-links">
                              {selectedDependents.map(
                                (
                                  dependent
                                ) => (
                                  <button
                                    key={
                                      dependent.id
                                    }
                                    type="button"
                                    onClick={() => {
                                      setSelectedTaskId(
                                        dependent.id
                                      );
                                      setIsEditing(
                                        false
                                      );
                                    }}
                                  >
                                    <i
                                      className={
                                        `status-${dependent.status}`
                                      }
                                    />

                                    <span>
                                      {
                                        dependent.title
                                      }
                                    </span>

                                    <small>
                                      {
                                        getStatusLabel(
                                          dependent.status
                                        )
                                      }
                                    </small>
                                  </button>
                                )
                              )}
                            </div>
                          </section>
                        )}

                        {selectedTask.completed_at && (
                          <section className="board-task-completed">
                            <span>
                              Completed
                            </span>

                            <strong>
                              {getCompletedDateLabel(
                                selectedTask.completed_at
                              )}
                            </strong>
                          </section>
                        )}
                      </div>

                      <footer className="board-task-actions">
                        <div>
                          <button
                            type="button"
                            onClick={
                              startEditing
                            }
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            className="is-delete"
                            onClick={() =>
                              setDeleteConfirmTaskId(
                                selectedTask.id
                              )
                            }
                          >
                            Delete
                          </button>
                        </div>

                        <button
                          type="button"
                          className="board-task-primary"
                          disabled={
                            updatingTaskId
                            === selectedTask.id
                            || (
                              selectedTask.is_blocked
                              && selectedTask.status
                              !== "done"
                            )
                          }
                          onClick={() =>
                            void changeTaskStatus(
                              selectedTask,
                              getNextStatus(
                                selectedTask.status
                              )
                            )
                          }
                        >
                          {updatingTaskId
                          === selectedTask.id
                            ? "Updating…"
                            : getStatusAction(
                                selectedTask.status
                              )}
                        </button>
                      </footer>
                    </>
                  )}
                </article>
              </div>
            )}
          </section>
        )}

        {undoState && (
          <div
            className="board-undo-toast"
            role="status"
          >
            <span>
              {undoState.message}
            </span>

            <button
              type="button"
              onClick={() =>
                void undoStatusChange()
              }
              disabled={
                updatingTaskId
                === undoState.taskId
              }
            >
              Undo
            </button>
          </div>
        )}

        {deleteConfirmTaskId
          !== null && (
          <div
            className="board-dialog-backdrop"
            role="presentation"
            onMouseDown={(
              event
            ) => {
              if (
                event.target
                === event.currentTarget
              ) {
                setDeleteConfirmTaskId(
                  null
                );
              }
            }}
          >
            <section
              className="board-delete-dialog"
              role="dialog"
              aria-modal="true"
              aria-labelledby="board-delete-title"
            >
              <span>
                Delete task
              </span>

              <h2 id="board-delete-title">
                Remove this task?
              </h2>

              <p>
                Its dependency links will
                be removed and Goal
                progress will be
                recalculated.
              </p>

              <div>
                <button
                  type="button"
                  onClick={() =>
                    setDeleteConfirmTaskId(
                      null
                    )
                  }
                >
                  Cancel
                </button>

                <button
                  type="button"
                  className="is-destructive"
                  disabled={
                    requestState
                    === "deleting"
                  }
                  onClick={() => {
                    const task =
                      tasks.find(
                        (item) =>
                          item.id
                          === deleteConfirmTaskId
                      );

                    if (task) {
                      void deleteTask(
                        task
                      );
                    }
                  }}
                >
                  {requestState
                  === "deleting"
                    ? "Deleting…"
                    : "Delete"}
                </button>
              </div>
            </section>
          </div>
        )}
      </main>
    </ProtectedLayout>
  );
}
