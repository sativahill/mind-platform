"use client";

import "./wins.css";

import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { apiFetch } from "@/lib/api";
import ProtectedLayout from "@/components/ProtectedLayout";

type WinSize =
  | "small"
  | "medium"
  | "large";

type WinSource =
  | "manual"
  | "daily_log"
  | "goal"
  | "board"
  | "habit"
  | "library"
  | "finance"
  | "progress_photo";

type WinFilter =
  | "all"
  | WinSize;

interface Win {
  id: number;
  title: string;
  description: string;
  date: string;
  size: WinSize;
  size_label: string;
  source: WinSource;
  source_label: string;
  source_id: string;
  event_key: string | null;
  created_at: string;
  updated_at: string;
}

interface WinDraft {
  title: string;
  description: string;
  date: string;
  size: WinSize;
}

type RequestState =
  | "idle"
  | "saving"
  | "deleting";

const API_URL =
  "/api/wins/";

const EMPTY_DRAFT: WinDraft = {
  title: "",
  description: "",
  date: "",
  size: "small",
};

function formatDateForApi(date: Date) {
  const year = date.getFullYear();

  const month = String(
    date.getMonth() + 1
  ).padStart(2, "0");

  const day = String(
    date.getDate()
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

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

function formatWinDate(value: string) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      day: "numeric",
      month: "long",
      year: "numeric",
    }
  ).format(parseApiDate(value));
}

function formatWinDay(value: string) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      day: "2-digit",
    }
  ).format(parseApiDate(value));
}

function formatWinMonth(value: string) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "long",
    }
  ).format(parseApiDate(value));
}

function formatWinYear(value: string) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      year: "numeric",
    }
  ).format(parseApiDate(value));
}

function getToday() {
  return formatDateForApi(
    new Date()
  );
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

      if (typeof value === "string") {
        return value;
      }
    }
  }

  return "Something went wrong.";
}

function getSourceLabel(
  source: WinSource
) {
  const labels: Record<
    WinSource,
    string
  > = {
    manual: "Added manually",
    daily_log: "From Daily Log",
    goal: "Goal completed",
    board: "From Board",
    habit: "Habit milestone",
    library: "Book completed",
    finance: "Finance goal",
    progress_photo: "Progress photo",
  };

  return labels[source];
}

function isSameDraft(
  draft: WinDraft,
  win: Win | null
) {
  if (!win) {
    return false;
  }

  return (
    draft.title === win.title &&
    draft.description ===
      win.description &&
    draft.date === win.date &&
    draft.size === win.size
  );
}

export default function WinsPage() {
  const today = useMemo(
    () => getToday(),
    []
  );

  const [wins, setWins] = useState<
    Win[]
  >([]);

  const [filter, setFilter] =
    useState<WinFilter>("all");

  const [draft, setDraft] =
    useState<WinDraft>({
      ...EMPTY_DRAFT,
      date: today,
    });

  const [editingWin, setEditingWin] =
    useState<Win | null>(null);

  const [isComposerOpen, setIsComposerOpen] =
    useState(false);

  const [isLoading, setIsLoading] =
    useState(true);

  const [requestState, setRequestState] =
    useState<RequestState>("idle");

  const [deleteTarget, setDeleteTarget] =
    useState<number | null>(null);

  const [error, setError] =
    useState("");

  const filteredWins = useMemo(() => {
    if (filter === "all") {
      return wins;
    }

    return wins.filter(
      (win) => win.size === filter
    );
  }, [wins, filter]);

  const winCounts = useMemo(() => {
    return {
      all: wins.length,
      small: wins.filter(
        (win) =>
          win.size === "small"
      ).length,
      medium: wins.filter(
        (win) =>
          win.size === "medium"
      ).length,
      large: wins.filter(
        (win) =>
          win.size === "large"
      ).length,
    };
  }, [wins]);

  const groupedWins = useMemo(() => {
    const groups = new Map<
      string,
      Win[]
    >();

    filteredWins.forEach((win) => {
      const year =
        formatWinYear(win.date);

      const current =
        groups.get(year) ?? [];

      current.push(win);

      groups.set(year, current);
    });

    return Array.from(
      groups.entries()
    );
  }, [filteredWins]);

  const isEditing =
    editingWin !== null;

  const hasChanges = isEditing
    ? !isSameDraft(
        draft,
        editingWin
      )
    : Boolean(
        draft.title.trim() ||
        draft.description.trim()
      );

  const canSubmit =
    Boolean(draft.title.trim()) &&
    Boolean(draft.date) &&
    requestState === "idle" &&
    (
      !isEditing ||
      hasChanges
    );

  const loadWins = useCallback(
    async () => {
      try {
        setIsLoading(true);
        setError("");

        const response =
          await apiFetch(API_URL);

        const data: unknown =
          await response.json();

        if (!response.ok) {
          throw new Error(
            getErrorMessage(data)
          );
        }

        if (Array.isArray(data)) {
          setWins(data as Win[]);
        }
      } catch (loadError) {
        console.error(
          "Wins loading error:",
          loadError
        );

        setError(
          loadError instanceof Error
            ? loadError.message
            : "Unable to load wins."
        );
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    loadWins();
  }, [loadWins]);

  function resetComposer() {
    setDraft({
      ...EMPTY_DRAFT,
      date: today,
    });

    setEditingWin(null);
    setDeleteTarget(null);
    setError("");
  }

  function closeComposer() {
    if (
      hasChanges &&
      !window.confirm(
        "Discard unsaved changes?"
      )
    ) {
      return;
    }

    resetComposer();
    setIsComposerOpen(false);
  }

  function openNewWin() {
    resetComposer();
    setIsComposerOpen(true);
  }

  function openEditWin(win: Win) {
    setEditingWin(win);

    setDraft({
      title: win.title,
      description:
        win.description,
      date: win.date,
      size: win.size,
    });

    setDeleteTarget(null);
    setError("");
    setIsComposerOpen(true);
  }

  function updateDraft<
    Key extends keyof WinDraft
  >(
    key: Key,
    value: WinDraft[Key]
  ) {
    setDraft((current) => ({
      ...current,
      [key]: value,
    }));

    setError("");
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    try {
      setRequestState("saving");
      setError("");

      const response = await apiFetch(
        isEditing
          ? `${API_URL}?id=${editingWin.id}`
          : API_URL,
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
              draft.title.trim(),
            description:
              draft.description.trim(),
            date: draft.date,
            size: draft.size,
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

      await loadWins();

      resetComposer();
      setIsComposerOpen(false);
    } catch (saveError) {
      console.error(
        "Win save error:",
        saveError
      );

      setError(
        "Unable to save this win."
      );
    } finally {
      setRequestState("idle");
    }
  }

  async function handleDelete(
    winId: number
  ) {
    try {
      setRequestState("deleting");
      setError("");

      const response = await apiFetch(
        `${API_URL}?id=${winId}`,
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

      await loadWins();

      resetComposer();
      setIsComposerOpen(false);
    } catch (deleteError) {
      console.error(
        "Win delete error:",
        deleteError
      );

      setError(
        "Unable to delete this win."
      );
    } finally {
      setRequestState("idle");
    }
  }

  return (
    <ProtectedLayout>
      <main className="wins-page">
        <div
          className="wins-background"
          aria-hidden="true"
        />

        <div className="wins-shell">
          <header className="wins-header">
            <div className="wins-heading">
              <span className="wins-heading-mark" />

              <h1>My Wins</h1>
            </div>

            <button
              type="button"
              className="wins-add-button"
              onClick={openNewWin}
            >
              <span aria-hidden="true">
                +
              </span>

              Add win
            </button>
          </header>

          <section className="wins-toolbar">
            <div className="wins-total">
              <strong>
                {wins.length}
              </strong>

              <span>
                {wins.length === 1
                  ? "win"
                  : "wins"}
              </span>
            </div>

            <div
              className="wins-filters"
              aria-label="Filter wins"
            >
              {(
                [
                  "all",
                  "small",
                  "medium",
                  "large",
                ] as WinFilter[]
              ).map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`wins-filter ${
                    filter === item
                      ? "wins-filter-active"
                      : ""
                  }`}
                  onClick={() =>
                    setFilter(item)
                  }
                >
                  <span>
                    {item}
                  </span>

                  <strong>
                    {winCounts[item]}
                  </strong>
                </button>
              ))}
            </div>
          </section>

          <section className="wins-content">
            {isLoading ? (
              <div className="wins-loading">
                <span />
                <span />
                <span />
              </div>
            ) : error &&
              wins.length === 0 ? (
              <div className="wins-load-error">
                <p>{error}</p>

                <button
                  type="button"
                  onClick={loadWins}
                >
                  Try again
                </button>
              </div>
            ) : filteredWins.length ===
              0 ? (
              <div className="wins-empty">
                <span className="wins-empty-mark" />

                <p>
                  {filter === "all"
                    ? "No wins recorded yet."
                    : `No ${filter} wins yet.`}
                </p>

                {filter === "all" && (
                  <button
                    type="button"
                    onClick={openNewWin}
                  >
                    Add the first one
                  </button>
                )}
              </div>
            ) : (
              <div className="wins-years">
                {groupedWins.map(
                  ([year, yearWins]) => (
                    <section
                      key={year}
                      className="wins-year"
                    >
                      <div className="wins-year-label">
                        <span>
                          {year}
                        </span>
                      </div>

                      <div className="wins-list">
                        {yearWins.map(
                          (win) => (
                            <article
                              key={win.id}
                              className={`win-item win-item-${win.size}`}
                            >
                              <button
                                type="button"
                                className="win-item-main"
                                onClick={() =>
                                  openEditWin(
                                    win
                                  )
                                }
                              >
                                <span className="win-date">
                                  <strong>
                                    {formatWinDay(
                                      win.date
                                    )}
                                  </strong>

                                  <span>
                                    {formatWinMonth(
                                      win.date
                                    )}
                                  </span>
                                </span>

                                <span className="win-rail">
                                  <span className="win-dot" />
                                  <span className="win-line" />
                                </span>

                                <span className="win-copy">
                                  <strong className="win-title">
                                    {win.title}
                                  </strong>

                                  {win.description && (
                                    <span className="win-description">
                                      {
                                        win.description
                                      }
                                    </span>
                                  )}

                                  <span className="win-meta">
                                    <span>
                                      {win.size}
                                    </span>

                                    {win.source !==
                                      "manual" && (
                                      <span>
                                        {getSourceLabel(
                                          win.source
                                        )}
                                      </span>
                                    )}
                                  </span>
                                </span>

                                <span
                                  className="win-edit-mark"
                                  aria-hidden="true"
                                >
                                  ↗
                                </span>
                              </button>
                            </article>
                          )
                        )}
                      </div>
                    </section>
                  )
                )}
              </div>
            )}
          </section>
        </div>

        <div
          className={`wins-composer-backdrop ${
            isComposerOpen
              ? "wins-composer-backdrop-open"
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
            className={`wins-composer ${
              isComposerOpen
                ? "wins-composer-open"
                : ""
            }`}
            aria-label={
              isEditing
                ? "Edit win"
                : "Add win"
            }
          >
            <header className="wins-composer-header">
              <div>
                <span>
                  {isEditing
                    ? formatWinDate(
                        editingWin.date
                      )
                    : "New win"}
                </span>

                <h2>
                  {isEditing
                    ? "Edit the memory."
                    : "What happened?"}
                </h2>
              </div>

              <button
                type="button"
                className="wins-composer-close"
                onClick={closeComposer}
                aria-label="Close"
              >
                ×
              </button>
            </header>

            <form
              className="wins-form"
              onSubmit={handleSubmit}
            >
              <label className="wins-field">
                <span>Win</span>

                <input
                  type="text"
                  value={draft.title}
                  maxLength={255}
                  onChange={(event) =>
                    updateDraft(
                      "title",
                      event.target.value
                    )
                  }
                  placeholder="What did you achieve?"
                  autoFocus
                />
              </label>

              <label className="wins-field wins-field-description">
                <span>
                  Note
                  <small>
                    optional
                  </small>
                </span>

                <textarea
                  value={
                    draft.description
                  }
                  onChange={(event) =>
                    updateDraft(
                      "description",
                      event.target.value
                    )
                  }
                  placeholder="A detail worth keeping."
                />
              </label>

              <div className="wins-form-row">
                <label className="wins-field">
                  <span>Date</span>

                  <input
                    type="date"
                    value={draft.date}
                    max={today}
                    onChange={(event) =>
                      updateDraft(
                        "date",
                        event.target.value
                      )
                    }
                  />
                </label>

                <fieldset className="wins-size-field">
                  <legend>Size</legend>

                  <div className="wins-size-options">
                    {(
                      [
                        "small",
                        "medium",
                        "large",
                      ] as WinSize[]
                    ).map((item) => (
                      <button
                        key={item}
                        type="button"
                        className={`wins-size-option ${
                          draft.size ===
                          item
                            ? "wins-size-option-active"
                            : ""
                        }`}
                        onClick={() =>
                          updateDraft(
                            "size",
                            item
                          )
                        }
                      >
                        <span />
                        {item}
                      </button>
                    ))}
                  </div>
                </fieldset>
              </div>

              {isEditing &&
                editingWin.source !==
                  "manual" && (
                  <div className="wins-source-note">
                    <span>
                      {getSourceLabel(
                        editingWin.source
                      )}
                    </span>
                  </div>
                )}

              {error && (
                <p
                  className="wins-form-error"
                  role="alert"
                >
                  {error}
                </p>
              )}

              <footer className="wins-form-footer">
                <div className="wins-form-danger">
                  {isEditing &&
                    deleteTarget !==
                      editingWin.id && (
                      <button
                        type="button"
                        onClick={() =>
                          setDeleteTarget(
                            editingWin.id
                          )
                        }
                      >
                        Delete
                      </button>
                    )}

                  {isEditing &&
                    deleteTarget ===
                      editingWin.id && (
                      <div className="wins-delete-confirm">
                        <span>
                          Delete?
                        </span>

                        <button
                          type="button"
                          onClick={() =>
                            setDeleteTarget(
                              null
                            )
                          }
                        >
                          No
                        </button>

                        <button
                          type="button"
                          disabled={
                            requestState !==
                            "idle"
                          }
                          onClick={() =>
                            handleDelete(
                              editingWin.id
                            )
                          }
                        >
                          Yes
                        </button>
                      </div>
                    )}
                </div>

                <button
                  type="submit"
                  className="wins-submit-button"
                  disabled={!canSubmit}
                >
                  {requestState ===
                  "saving"
                    ? "Saving"
                    : isEditing
                      ? "Save"
                      : "Add win"}

                  <span
                    aria-hidden="true"
                  >
                    ↗
                  </span>
                </button>
              </footer>
            </form>
          </aside>
        </div>
      </main>
    </ProtectedLayout>
  );
}
