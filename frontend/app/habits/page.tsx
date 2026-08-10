"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import ProtectedLayout from "@/components/ProtectedLayout";
import { apiFetch } from "@/lib/api";

import "./habits.css";


const HABITS_API_URL =
  "http://127.0.0.1:8000/api/habits/";


type HabitStatus =
  | "active"
  | "archived";

type DayStatus =
  | "completed"
  | "missed"
  | "pending";

type HabitTab =
  | "active"
  | "archived";

type RequestState =
  | "idle"
  | "loading"
  | "saving"
  | "deleting";


interface HabitDay {
  date: string;
  status: DayStatus;
}


interface Habit {
  id: number;

  title: string;
  trigger: string;
  action: string;
  reward: string;

  streak: number;
  status: HabitStatus;

  completed_today: boolean;
  today_status: DayStatus;
  consecutive_misses: number;

  recent_days: HabitDay[];

  created_at: string;
  updated_at: string;
}


interface HabitDraft {
  title: string;
  trigger: string;
  action: string;
  reward: string;
}


interface ApiErrorShape {
  detail?: string;
  [key: string]: unknown;
}


const EMPTY_DRAFT: HabitDraft = {
  title: "",
  trigger: "",
  action: "",
  reward: "",
};


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
    typeof object.detail
    === "string"
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


function getDayName(
  dateValue: string
) {
  const date = new Date(
    `${dateValue}T12:00:00`
  );

  return new Intl.DateTimeFormat(
    "en",
    {
      weekday: "short",
    }
  )
    .format(date)
    .slice(0, 3);
}


function getShortDate(
  dateValue: string
) {
  const date = new Date(
    `${dateValue}T12:00:00`
  );

  return new Intl.DateTimeFormat(
    "en",
    {
      month: "short",
      day: "numeric",
    }
  ).format(date);
}


function getTodayLabel() {
  return new Intl.DateTimeFormat(
    "en",
    {
      month: "long",
      day: "numeric",
    }
  ).format(new Date());
}


function getStreakLabel(
  streak: number
) {
  if (streak <= 0) {
    return "Start your streak today";
  }

  if (streak === 1) {
    return "1 day streak";
  }

  return `${streak} day streak`;
}


function buildHabitDraft(
  habit: Habit
): HabitDraft {
  return {
    title: habit.title,
    trigger: habit.trigger,
    action: habit.action,
    reward: habit.reward,
  };
}


export default function HabitsPage() {
  const [
    habits,
    setHabits,
  ] = useState<Habit[]>([]);

  const [
    activeTab,
    setActiveTab,
  ] = useState<HabitTab>(
    "active"
  );

  const [
    requestState,
    setRequestState,
  ] = useState<RequestState>(
    "loading"
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
    selectedHabitId,
    setSelectedHabitId,
  ] = useState<number | null>(
    null
  );

  const [
    changingHabitId,
    setChangingHabitId,
  ] = useState<number | null>(
    null
  );

  const [
    isCreateOpen,
    setIsCreateOpen,
  ] = useState(false);

  const [
    isEditing,
    setIsEditing,
  ] = useState(false);

  const [
    draft,
    setDraft,
  ] = useState<HabitDraft>(
    EMPTY_DRAFT
  );

  const [
    deleteHabitId,
    setDeleteHabitId,
  ] = useState<number | null>(
    null
  );


  const selectedHabit =
    useMemo(
      () => {
        if (
          selectedHabitId === null
        ) {
          return null;
        }

        return (
          habits.find(
            (habit) =>
              habit.id
              === selectedHabitId
          )
          ?? null
        );
      },
      [
        habits,
        selectedHabitId,
      ]
    );


  const visibleHabits =
    useMemo(
      () =>
        habits.filter(
          (habit) =>
            habit.status
            === activeTab
        ),
      [
        activeTab,
        habits,
      ]
    );


  const loadHabits =
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
          const response =
            await apiFetch(
              HABITS_API_URL
            );

          const data =
            await parseResponse(
              response
            );

          if (!response.ok) {
            throw new Error(
              extractApiError(
                data,
                "Could not load habits."
              )
            );
          }

          setHabits(
            Array.isArray(data)
              ? data
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
    void loadHabits();
  }, [loadHabits]);


  useEffect(() => {
    function handleEscape(
      event: KeyboardEvent
    ) {
      if (
        event.key !== "Escape"
      ) {
        return;
      }

      if (
        deleteHabitId !== null
      ) {
        setDeleteHabitId(null);
        return;
      }

      if (isEditing) {
        setIsEditing(false);
        setFormError("");
        return;
      }

      if (
        selectedHabitId !== null
      ) {
        setSelectedHabitId(null);
        return;
      }

      if (isCreateOpen) {
        setIsCreateOpen(false);
        setDraft(EMPTY_DRAFT);
        setFormError("");
      }
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
    deleteHabitId,
    isCreateOpen,
    isEditing,
    selectedHabitId,
  ]);


  function updateDraft<
    Key extends keyof HabitDraft
  >(
    key: Key,
    value: HabitDraft[Key]
  ) {
    setDraft(
      (current) => ({
        ...current,
        [key]: value,
      })
    );
  }


  function openCreate() {
    setDraft(EMPTY_DRAFT);
    setFormError("");
    setIsCreateOpen(true);
    setSelectedHabitId(null);
    setIsEditing(false);
  }


  function closeCreate() {
    if (
      requestState === "saving"
    ) {
      return;
    }

    setIsCreateOpen(false);
    setDraft(EMPTY_DRAFT);
    setFormError("");
  }


  function openHabit(
    habitId: number
  ) {
    setSelectedHabitId(
      habitId
    );

    setIsEditing(false);
    setFormError("");
    setIsCreateOpen(false);
  }


  function closeHabit() {
    setSelectedHabitId(null);
    setIsEditing(false);
    setFormError("");
  }


  function startEditing() {
    if (!selectedHabit) {
      return;
    }

    setDraft(
      buildHabitDraft(
        selectedHabit
      )
    );

    setFormError("");
    setIsEditing(true);
  }


  function cancelEditing() {
    setIsEditing(false);
    setFormError("");
  }


  function validateDraft() {
    if (!draft.title.trim()) {
      return "Write a habit name.";
    }

    if (!draft.trigger.trim()) {
      return "Write when you will do it.";
    }

    if (!draft.action.trim()) {
      return "Write one small action.";
    }

    return "";
  }


  async function createHabit(
    event: FormEvent
  ) {
    event.preventDefault();

    const validationError =
      validateDraft();

    if (validationError) {
      setFormError(
        validationError
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
          HABITS_API_URL,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              title:
                draft.title.trim(),
              trigger:
                draft.trigger.trim(),
              action:
                draft.action.trim(),
              reward:
                draft.reward.trim(),
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
            "Could not create the habit."
          )
        );
      }

      const created =
        data as Habit;

      setHabits(
        (current) => [
          created,
          ...current,
        ]
      );

      setActiveTab("active");

      setDraft(
        EMPTY_DRAFT
      );

      setIsCreateOpen(false);
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


  async function saveHabit(
    event: FormEvent
  ) {
    event.preventDefault();

    if (!selectedHabit) {
      return;
    }

    const validationError =
      validateDraft();

    if (validationError) {
      setFormError(
        validationError
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
          `${HABITS_API_URL}${selectedHabit.id}/`,
          {
            method: "PATCH",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              title:
                draft.title.trim(),
              trigger:
                draft.trigger.trim(),
              action:
                draft.action.trim(),
              reward:
                draft.reward.trim(),
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
            "Could not save the habit."
          )
        );
      }

      const updated =
        data as Habit;

      setHabits(
        (current) =>
          current.map(
            (habit) =>
              habit.id === updated.id
                ? updated
                : habit
          )
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


  async function updateToday(
    habit: Habit,
    nextState:
      | "complete"
      | "miss"
  ) {
    if (
      habit.status
      !== "active"
    ) {
      return;
    }

    setChangingHabitId(
      habit.id
    );

    setPageError("");

    try {
      const response =
        await apiFetch(
          `${HABITS_API_URL}${habit.id}/${nextState}/`,
          {
            method: "POST",
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
            "Could not update today."
          )
        );
      }

      const updated =
        data as Habit;

      setHabits(
        (current) =>
          current.map(
            (item) =>
              item.id === updated.id
                ? updated
                : item
          )
      );
    } catch (error) {
      setPageError(
        getErrorMessage(error)
      );
    } finally {
      setChangingHabitId(null);
    }
  }


  async function archiveHabit(
    habit: Habit
  ) {
    setChangingHabitId(
      habit.id
    );

    setPageError("");

    try {
      const response =
        await apiFetch(
          `${HABITS_API_URL}${habit.id}/archive/`,
          {
            method: "POST",
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
            "Could not archive the habit."
          )
        );
      }

      const updated =
        data as Habit;

      setHabits(
        (current) =>
          current.map(
            (item) =>
              item.id === updated.id
                ? updated
                : item
          )
      );

      closeHabit();
    } catch (error) {
      setPageError(
        getErrorMessage(error)
      );
    } finally {
      setChangingHabitId(null);
    }
  }


  async function restoreHabit(
    habit: Habit
  ) {
    setChangingHabitId(
      habit.id
    );

    setPageError("");

    try {
      const response =
        await apiFetch(
          `${HABITS_API_URL}${habit.id}/restore/`,
          {
            method: "POST",
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
            "Could not restore the habit."
          )
        );
      }

      const updated =
        data as Habit;

      setHabits(
        (current) =>
          current.map(
            (item) =>
              item.id === updated.id
                ? updated
                : item
          )
      );

      closeHabit();
      setActiveTab("active");
    } catch (error) {
      setPageError(
        getErrorMessage(error)
      );
    } finally {
      setChangingHabitId(null);
    }
  }


  async function deleteHabit(
    habit: Habit
  ) {
    setRequestState(
      "deleting"
    );

    setPageError("");

    try {
      const response =
        await apiFetch(
          `${HABITS_API_URL}${habit.id}/`,
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
            "Could not delete the habit."
          )
        );
      }

      setHabits(
        (current) =>
          current.filter(
            (item) =>
              item.id !== habit.id
          )
      );

      setDeleteHabitId(null);
      closeHabit();
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
      <main className="habits-page">
        <section className="habits-shell">
          <header className="habits-header">
            <div className="habits-heading">
              <span
                className="habits-heading-dot"
              />

              <h1>
                Habits
              </h1>
            </div>

            <button
              type="button"
              className="habits-add-button"
              onClick={openCreate}
            >
              <span>+</span>
              Add habit
            </button>
          </header>


          <nav
            className="habits-tabs"
            aria-label="Habit status"
          >
            <button
              type="button"
              className={
                activeTab === "active"
                  ? "is-active"
                  : ""
              }
              onClick={() =>
                setActiveTab("active")
              }
            >
              Active
            </button>

            <button
              type="button"
              className={
                activeTab === "archived"
                  ? "is-active"
                  : ""
              }
              onClick={() =>
                setActiveTab(
                  "archived"
                )
              }
            >
              Archived
            </button>
          </nav>


          {pageError && (
            <div
              className="habits-error"
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
            <div className="habits-loading">
              <span />

              <p>
                Loading habits
              </p>
            </div>
          ) : (
            <>
              {activeTab
              === "active" && (
                <div className="habits-today">
                  <span>
                    Today
                  </span>

                  <strong>
                    {getTodayLabel()}
                  </strong>
                </div>
              )}


              {visibleHabits.length
              === 0 ? (
                <section className="habits-empty">
                  <span
                    className="habits-empty-mark"
                  />

                  <h2>
                    {activeTab
                    === "active"
                      ? "No habits yet."
                      : "No archived habits."}
                  </h2>

                  <p>
                    {activeTab
                    === "active"
                      ? "Build one small action you can repeat every day."
                      : "Habits you archive will stay here."}
                  </p>

                  {activeTab
                  === "active" && (
                    <button
                      type="button"
                      onClick={openCreate}
                    >
                      + Add habit
                    </button>
                  )}
                </section>
              ) : (
                <div className="habits-list">
                  {visibleHabits.map(
                    (habit) => {
                      const isChanging =
                        changingHabitId
                        === habit.id;

                      return (
                        <article
                          key={habit.id}
                          className={[
                            "habit-row",
                            habit.today_status
                            === "completed"
                              ? "is-completed"
                              : "",
                            habit.today_status
                            === "missed"
                              ? "is-missed"
                              : "",
                            habit.status
                            === "archived"
                              ? "is-archived"
                              : "",
                          ]
                            .filter(Boolean)
                            .join(" ")}
                        >
                          <button
                            type="button"
                            className="habit-main"
                            onClick={() =>
                              openHabit(
                                habit.id
                              )
                            }
                          >
                            <div className="habit-copy">
                              <h2>
                                {
                                  habit.title
                                }
                              </h2>

                              <p>
                                <span>
                                  {
                                    habit.trigger
                                  }
                                </span>

                                <i />

                                <strong>
                                  {
                                    habit.action
                                  }
                                </strong>
                              </p>
                            </div>
                          </button>


                          <div className="habit-week">
                            {habit.recent_days.map(
                              (
                                day,
                                index
                              ) => {
                                const isToday =
                                  index
                                  === habit
                                    .recent_days
                                    .length
                                    - 1;

                                return (
                                  <div
                                    key={
                                      day.date
                                    }
                                    className={[
                                      "habit-day",
                                      `status-${day.status}`,
                                      isToday
                                        ? "is-today"
                                        : "",
                                    ]
                                      .filter(Boolean)
                                      .join(" ")}
                                    title={
                                      `${getShortDate(
                                        day.date
                                      )} · ${day.status}`
                                    }
                                  >
                                    <span>
                                      {getDayName(
                                        day.date
                                      )}
                                    </span>

                                    <i>
                                      {day.status
                                      === "completed"
                                        ? "✓"
                                        : day.status
                                          === "missed"
                                          ? "×"
                                          : ""}
                                    </i>
                                  </div>
                                );
                              }
                            )}
                          </div>


                          <div className="habit-row-footer">
                            <div className="habit-streak">
                              <span />

                              <strong>
                                {getStreakLabel(
                                  habit.streak
                                )}
                              </strong>

                              {habit.consecutive_misses
                              >= 2 && (
                                <small>
                                  {
                                    habit.consecutive_misses
                                  }{" "}
                                  missed days
                                </small>
                              )}
                            </div>


                            {habit.status
                            === "archived" ? (
                              <button
                                type="button"
                                className="habit-restore-button"
                                disabled={
                                  isChanging
                                }
                                onClick={() =>
                                  void restoreHabit(
                                    habit
                                  )
                                }
                              >
                                {isChanging
                                  ? "Restoring…"
                                  : "Restore"}
                              </button>
                            ) : (
                              <div className="habit-today-actions">
                                {habit.today_status
                                === "pending" && (
                                  <>
                                    <button
                                      type="button"
                                      className="habit-missed-button"
                                      disabled={
                                        isChanging
                                      }
                                      onClick={() =>
                                        void updateToday(
                                          habit,
                                          "miss"
                                        )
                                      }
                                    >
                                      Missed
                                    </button>

                                    <button
                                      type="button"
                                      className="habit-done-button"
                                      disabled={
                                        isChanging
                                      }
                                      onClick={() =>
                                        void updateToday(
                                          habit,
                                          "complete"
                                        )
                                      }
                                    >
                                      {isChanging
                                        ? "Saving…"
                                        : "Done today"}
                                    </button>
                                  </>
                                )}


                                {habit.today_status
                                === "completed" && (
                                  <>
                                    <span className="habit-today-state is-done">
                                      Completed today
                                    </span>

                                    <button
                                      type="button"
                                      className="habit-change-state"
                                      disabled={
                                        isChanging
                                      }
                                      onClick={() =>
                                        void updateToday(
                                          habit,
                                          "miss"
                                        )
                                      }
                                    >
                                      Mark missed
                                    </button>
                                  </>
                                )}


                                {habit.today_status
                                === "missed" && (
                                  <>
                                    <span className="habit-today-state is-missed">
                                      Missed today
                                    </span>

                                    <button
                                      type="button"
                                      className="habit-done-button"
                                      disabled={
                                        isChanging
                                      }
                                      onClick={() =>
                                        void updateToday(
                                          habit,
                                          "complete"
                                        )
                                      }
                                    >
                                      {isChanging
                                        ? "Saving…"
                                        : "Mark done"}
                                    </button>
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        </article>
                      );
                    }
                  )}
                </div>
              )}
            </>
          )}
        </section>


        {isCreateOpen && (
          <div
            className="habit-modal-backdrop"
            role="presentation"
            onMouseDown={(
              event
            ) => {
              if (
                event.target
                === event.currentTarget
              ) {
                closeCreate();
              }
            }}
          >
            <section
              className="habit-modal habit-create-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="habit-create-title"
            >
              <button
                type="button"
                className="habit-modal-close"
                onClick={
                  closeCreate
                }
                aria-label="Close"
              >
                ×
              </button>

              <header className="habit-modal-header">
                <span>
                  New habit
                </span>

                <h2 id="habit-create-title">
                  Build something small.
                </h2>

                <p>
                  Make it easy enough to
                  repeat every day.
                </p>
              </header>


              <form
                className="habit-form"
                onSubmit={
                  createHabit
                }
              >
                <label>
                  <span>
                    Habit
                  </span>

                  <input
                    type="text"
                    value={
                      draft.title
                    }
                    onChange={(
                      event
                    ) =>
                      updateDraft(
                        "title",
                        event.target.value
                      )
                    }
                    placeholder="For example: Read every day"
                    autoFocus
                    maxLength={255}
                  />
                </label>


                <label>
                  <span>
                    When will you do it?
                  </span>

                  <input
                    type="text"
                    value={
                      draft.trigger
                    }
                    onChange={(
                      event
                    ) =>
                      updateDraft(
                        "trigger",
                        event.target.value
                      )
                    }
                    placeholder="After breakfast"
                    maxLength={255}
                  />

                  <small>
                    Choose a moment that
                    already happens every
                    day.
                  </small>
                </label>


                <label>
                  <span>
                    What will you do?
                  </span>

                  <input
                    type="text"
                    value={
                      draft.action
                    }
                    onChange={(
                      event
                    ) =>
                      updateDraft(
                        "action",
                        event.target.value
                      )
                    }
                    placeholder="Read one page"
                    maxLength={255}
                  />

                  <small>
                    Make the first version
                    take about 2 minutes.
                  </small>
                </label>


                <label>
                  <span>
                    Small reward
                    <i>
                      optional
                    </i>
                  </span>

                  <input
                    type="text"
                    value={
                      draft.reward
                    }
                    onChange={(
                      event
                    ) =>
                      updateDraft(
                        "reward",
                        event.target.value
                      )
                    }
                    placeholder="Make coffee"
                    maxLength={255}
                  />
                </label>


                {formError && (
                  <div
                    className="habit-form-error"
                    role="alert"
                  >
                    {formError}
                  </div>
                )}


                <footer className="habit-form-actions">
                  <button
                    type="button"
                    onClick={
                      closeCreate
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
                      ? "Creating…"
                      : "Create habit"}
                  </button>
                </footer>
              </form>
            </section>
          </div>
        )}


        {selectedHabit && (
          <div
            className="habit-modal-backdrop"
            role="presentation"
            onMouseDown={(
              event
            ) => {
              if (
                event.target
                === event.currentTarget
              ) {
                closeHabit();
              }
            }}
          >
            <section
              className="habit-modal habit-detail-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="habit-detail-title"
            >
              <button
                type="button"
                className="habit-modal-close"
                onClick={
                  closeHabit
                }
                aria-label="Close"
              >
                ×
              </button>


              <header className="habit-modal-header">
                <span>
                  {selectedHabit.status
                  === "archived"
                    ? "Archived habit"
                    : selectedHabit.today_status
                    === "completed"
                      ? "Completed today"
                      : "Active habit"}
                </span>

                <h2 id="habit-detail-title">
                  {selectedHabit.title}
                </h2>
              </header>


              {isEditing ? (
                <form
                  className="habit-form"
                  onSubmit={
                    saveHabit
                  }
                >
                  <label>
                    <span>
                      Habit
                    </span>

                    <input
                      type="text"
                      value={
                        draft.title
                      }
                      onChange={(
                        event
                      ) =>
                        updateDraft(
                          "title",
                          event.target.value
                        )
                      }
                      maxLength={255}
                      autoFocus
                    />
                  </label>


                  <label>
                    <span>
                      When will you do it?
                    </span>

                    <input
                      type="text"
                      value={
                        draft.trigger
                      }
                      onChange={(
                        event
                      ) =>
                        updateDraft(
                          "trigger",
                          event.target.value
                        )
                      }
                      maxLength={255}
                    />
                  </label>


                  <label>
                    <span>
                      What will you do?
                    </span>

                    <input
                      type="text"
                      value={
                        draft.action
                      }
                      onChange={(
                        event
                      ) =>
                        updateDraft(
                          "action",
                          event.target.value
                        )
                      }
                      maxLength={255}
                    />
                  </label>


                  <label>
                    <span>
                      Small reward
                      <i>
                        optional
                      </i>
                    </span>

                    <input
                      type="text"
                      value={
                        draft.reward
                      }
                      onChange={(
                        event
                      ) =>
                        updateDraft(
                          "reward",
                          event.target.value
                        )
                      }
                      maxLength={255}
                    />
                  </label>


                  {formError && (
                    <div
                      className="habit-form-error"
                      role="alert"
                    >
                      {formError}
                    </div>
                  )}


                  <footer className="habit-form-actions">
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
                  <div className="habit-detail-body">
                    <section className="habit-detail-plan">
                      <div>
                        <span>
                          When
                        </span>

                        <strong>
                          {
                            selectedHabit.trigger
                          }
                        </strong>
                      </div>

                      <i />

                      <div>
                        <span>
                          Action
                        </span>

                        <strong>
                          {
                            selectedHabit.action
                          }
                        </strong>
                      </div>
                    </section>


                    <section className="habit-detail-streak">
                      <div>
                        <span>
                          Current streak
                        </span>

                        <strong>
                          {
                            selectedHabit.streak
                          }
                        </strong>

                        <small>
                          {selectedHabit.streak
                          === 1
                            ? "day"
                            : "days"}
                        </small>
                      </div>

                      {selectedHabit
                        .consecutive_misses
                      > 0 && (
                        <div className="habit-detail-misses">
                          <span>
                            Recent misses
                          </span>

                          <strong>
                            {
                              selectedHabit
                                .consecutive_misses
                            }
                          </strong>
                        </div>
                      )}
                    </section>


                    <section className="habit-detail-week">
                      <span>
                        This week
                      </span>

                      <div>
                        {selectedHabit
                          .recent_days
                          .map(
                            (
                              day,
                              index
                            ) => {
                              const isToday =
                                index
                                === selectedHabit
                                  .recent_days
                                  .length
                                  - 1;

                              return (
                                <div
                                  key={
                                    day.date
                                  }
                                  className={[
                                    "habit-day",
                                    `status-${day.status}`,
                                    isToday
                                      ? "is-today"
                                      : "",
                                  ]
                                    .filter(Boolean)
                                    .join(" ")}
                                >
                                  <span>
                                    {
                                      getDayName(
                                        day.date
                                      )
                                    }
                                  </span>

                                  <i>
                                    {day.status
                                    === "completed"
                                      ? "✓"
                                      : day.status
                                        === "missed"
                                        ? "×"
                                        : ""}
                                  </i>
                                </div>
                              );
                            }
                          )}
                      </div>
                    </section>


                    <section className="habit-detail-reward">
                      <span>
                        Small reward
                      </span>

                      <p>
                        {selectedHabit.reward
                        || "Not added."}
                      </p>
                    </section>
                  </div>


                  <footer className="habit-detail-actions">
                    <div>
                      <button
                        type="button"
                        onClick={
                          startEditing
                        }
                      >
                        Edit
                      </button>

                      {selectedHabit.status
                      === "active" ? (
                        <button
                          type="button"
                          onClick={() =>
                            void archiveHabit(
                              selectedHabit
                            )
                          }
                          disabled={
                            changingHabitId
                            === selectedHabit.id
                          }
                        >
                          Archive
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() =>
                            void restoreHabit(
                              selectedHabit
                            )
                          }
                          disabled={
                            changingHabitId
                            === selectedHabit.id
                          }
                        >
                          Restore
                        </button>
                      )}

                      <button
                        type="button"
                        className="is-delete"
                        onClick={() =>
                          setDeleteHabitId(
                            selectedHabit.id
                          )
                        }
                      >
                        Delete
                      </button>
                    </div>


                    {selectedHabit.status
                    === "active" && (
                      <>
                        {selectedHabit
                          .today_status
                        === "pending" && (
                          <button
                            type="button"
                            className="habit-detail-primary"
                            disabled={
                              changingHabitId
                              === selectedHabit.id
                            }
                            onClick={() =>
                              void updateToday(
                                selectedHabit,
                                "complete"
                              )
                            }
                          >
                            Done today
                          </button>
                        )}

                        {selectedHabit
                          .today_status
                        === "missed" && (
                          <button
                            type="button"
                            className="habit-detail-primary"
                            disabled={
                              changingHabitId
                              === selectedHabit.id
                            }
                            onClick={() =>
                              void updateToday(
                                selectedHabit,
                                "complete"
                              )
                            }
                          >
                            Mark done
                          </button>
                        )}

                        {selectedHabit
                          .today_status
                        === "completed" && (
                          <span className="habit-detail-complete">
                            ✓ Done today
                          </span>
                        )}
                      </>
                    )}
                  </footer>
                </>
              )}
            </section>
          </div>
        )}


        {deleteHabitId !== null && (
          <div
            className="habit-delete-backdrop"
            role="presentation"
            onMouseDown={(
              event
            ) => {
              if (
                event.target
                === event.currentTarget
              ) {
                setDeleteHabitId(null);
              }
            }}
          >
            <section
              className="habit-delete-dialog"
              role="dialog"
              aria-modal="true"
              aria-labelledby="habit-delete-title"
            >
              <span>
                Delete habit
              </span>

              <h2 id="habit-delete-title">
                Delete this habit?
              </h2>

              <p>
                Its completion history
                will also be removed.
              </p>

              <div>
                <button
                  type="button"
                  onClick={() =>
                    setDeleteHabitId(
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
                    const habit =
                      habits.find(
                        (item) =>
                          item.id
                          === deleteHabitId
                      );

                    if (habit) {
                      void deleteHabit(
                        habit
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