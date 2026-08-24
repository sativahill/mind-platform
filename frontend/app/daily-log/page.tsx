"use client";

import "./daily-log.css";

import {
  FormEvent,
  KeyboardEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { apiFetch } from "@/lib/api";
import ProtectedLayout from "@/components/ProtectedLayout";

interface DailyLog {
  id: number;
  date: string;
  content: string;
  created_at: string;
  updated_at: string;
}

type SuggestionSize =
  | "small"
  | "medium"
  | "large";

interface DailyLogSuggestion {
  id: number;
  daily_log: number;
  suggestion_type: "win";
  type_label: string;
  title: string;
  description: string;
  size: SuggestionSize;
  size_label: string;
  status:
    | "pending"
    | "accepted"
    | "dismissed";
  status_label: string;
  suggestion_key: string;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

interface AnalyzeResponse {
  daily_log: number;
  suggestions: DailyLogSuggestion[];
  suggestions_count: number;
}

interface TimelineEntry {
  date: string;
  log: DailyLog | null;
}

type SaveState =
  | "idle"
  | "saving"
  | "saved"
  | "error";

type AnalysisState =
  | "idle"
  | "loading"
  | "error";

const API_URL =
  "/api/daily-logs/";

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

function getToday() {
  return formatDateForApi(new Date());
}

function formatMainDate(value: string) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    }
  ).format(parseApiDate(value));
}

function formatTimelineDay(value: string) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      day: "2-digit",
    }
  ).format(parseApiDate(value));
}

function formatTimelineMonth(value: string) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "short",
    }
  ).format(parseApiDate(value));
}

function formatTimelineWeekday(
  value: string
) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      weekday: "short",
    }
  ).format(parseApiDate(value));
}

function formatUpdatedTime(
  value: string
) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      hour: "numeric",
      minute: "2-digit",
    }
  ).format(new Date(value));
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

  return "Something went wrong. Please try again.";
}

function shortenText(
  value: string,
  maxLength: number
) {
  const normalized = value
    .trim()
    .replace(/\s+/g, " ");

  if (normalized.length <= maxLength) {
    return normalized;
  }

  return `${normalized
    .slice(0, maxLength)
    .trim()}…`;
}

export default function DailyLogPage() {
  const today = useMemo(
    () => getToday(),
    []
  );

  const [selectedDate, setSelectedDate] =
    useState(today);

  const [currentLog, setCurrentLog] =
    useState<DailyLog | null>(null);

  const [logs, setLogs] = useState<
    DailyLog[]
  >([]);

  const [content, setContent] =
    useState("");

  const [
    originalContent,
    setOriginalContent,
  ] = useState("");

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    isHistoryLoading,
    setIsHistoryLoading,
  ] = useState(true);

  const [saveState, setSaveState] =
    useState<SaveState>("idle");

  const [error, setError] =
    useState("");

  const [
    showDeleteConfirm,
    setShowDeleteConfirm,
  ] = useState(false);

  const [
    suggestions,
    setSuggestions,
  ] = useState<DailyLogSuggestion[]>(
    []
  );

  const [
    analysisState,
    setAnalysisState,
  ] = useState<AnalysisState>("idle");

  const [
    analysisError,
    setAnalysisError,
  ] = useState("");

  const [
    resolvingSuggestionId,
    setResolvingSuggestionId,
  ] = useState<number | null>(null);

  const hasUnsavedChanges =
    content !== originalContent;

  const isToday =
    selectedDate === today;

  const characterCount =
    content.length;

  const wordCount = content
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;

  const timelineEntries =
    useMemo<TimelineEntry[]>(() => {
      const todayLog =
        logs.find(
          (log) => log.date === today
        ) ?? null;

      const otherLogs = logs
        .filter(
          (log) => log.date !== today
        )
        .map((log) => ({
          date: log.date,
          log,
        }));

      return [
        {
          date: today,
          log: todayLog,
        },
        ...otherLogs,
      ];
    }, [logs, today]);

  const loadHistory = useCallback(
    async () => {
      try {
        setIsHistoryLoading(true);

        const response = await apiFetch(
          API_URL
        );

        const data: unknown =
          await response.json();

        if (!response.ok) {
          throw new Error(
            getErrorMessage(data)
          );
        }

        if (Array.isArray(data)) {
          setLogs(data as DailyLog[]);
        }
      } catch (loadError) {
        console.error(
          "Daily Log history error:",
          loadError
        );
      } finally {
        setIsHistoryLoading(false);
      }
    },
    []
  );

  const loadSuggestions = useCallback(
    async (logId: number) => {
      try {
        setAnalysisError("");

        const response = await apiFetch(
          `${API_URL}?id=${logId}&action=suggestions`
        );

        const data: unknown =
          await response.json();

        if (!response.ok) {
          throw new Error(
            getErrorMessage(data)
          );
        }

        setSuggestions(
          Array.isArray(data)
            ? (data as DailyLogSuggestion[])
            : []
        );
      } catch (loadError) {
        console.error(
          "Daily Log suggestions error:",
          loadError
        );

        setSuggestions([]);
        setAnalysisError(
          loadError instanceof Error
            ? loadError.message
            : "Unable to load suggestions."
        );
      }
    },
    []
  );

  const analyzeLog = useCallback(
    async (logId: number) => {
      try {
        setAnalysisState("loading");
        setAnalysisError("");

        const response = await apiFetch(
          `${API_URL}?id=${logId}&action=analyze`,
          {
            method: "POST",
          }
        );

        const data: unknown =
          await response.json();

        if (!response.ok) {
          throw new Error(
            getErrorMessage(data)
          );
        }

        const result =
          data as AnalyzeResponse;

        setSuggestions(
          Array.isArray(
            result.suggestions
          )
            ? result.suggestions
            : []
        );

        setAnalysisState("idle");
      } catch (analysisRequestError) {
        console.error(
          "Daily Log analysis error:",
          analysisRequestError
        );

        setAnalysisState("error");
        setAnalysisError(
          analysisRequestError instanceof Error
            ? analysisRequestError.message
            : "Analysis is temporarily unavailable."
        );
      }
    },
    []
  );

  const loadSelectedLog = useCallback(
    async (date: string) => {
      try {
        setIsLoading(true);
        setError("");
        setSaveState("idle");
        setShowDeleteConfirm(false);
        setSuggestions([]);
        setAnalysisState("idle");
        setAnalysisError("");
        setResolvingSuggestionId(null);

        const response = await apiFetch(
          `${API_URL}?date=${date}`
        );

        if (response.status === 404) {
          setCurrentLog(null);
          setContent("");
          setOriginalContent("");
          return;
        }

        const data: unknown =
          await response.json();

        if (!response.ok) {
          throw new Error(
            getErrorMessage(data)
          );
        }

        const log = data as DailyLog;

        setCurrentLog(log);
        setContent(log.content);
        setOriginalContent(
          log.content
        );

        await loadSuggestions(
          log.id
        );
      } catch (loadError) {
        console.error(
          "Daily Log loading error:",
          loadError
        );

        setError(
          loadError instanceof Error
            ? loadError.message
            : "Unable to load this entry."
        );
      } finally {
        setIsLoading(false);
      }
    },
    [loadSuggestions]
  );

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    loadSelectedLog(selectedDate);
  }, [
    selectedDate,
    loadSelectedLog,
  ]);

  useEffect(() => {
    function handleBeforeUnload(
      event: BeforeUnloadEvent
    ) {
      if (!hasUnsavedChanges) {
        return;
      }

      event.preventDefault();
      event.returnValue = "";
    }

    window.addEventListener(
      "beforeunload",
      handleBeforeUnload
    );

    return () => {
      window.removeEventListener(
        "beforeunload",
        handleBeforeUnload
      );
    };
  }, [hasUnsavedChanges]);

  function changeDate(nextDate: string) {
    if (
      nextDate === selectedDate
    ) {
      return;
    }

    if (
      hasUnsavedChanges &&
      !window.confirm(
        "You have unsaved changes. Leave this entry?"
      )
    ) {
      return;
    }

    setSelectedDate(nextDate);
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (
      saveState === "saving" ||
      !content.trim() ||
      !hasUnsavedChanges
    ) {
      return;
    }

    try {
      setError("");
      setSaveState("saving");

      const isEditing =
        currentLog !== null;

      const response = await apiFetch(
        isEditing
          ? `${API_URL}?id=${currentLog.id}`
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
            date: selectedDate,
            content,
          }),
        }
      );

      const data: unknown =
        await response.json();

      if (!response.ok) {
        setError(
          getErrorMessage(data)
        );
        setSaveState("error");
        return;
      }

      const savedLog =
        data as DailyLog;

      setCurrentLog(savedLog);
      setContent(savedLog.content);
      setOriginalContent(
        savedLog.content
      );
      setSaveState("saved");

      await loadHistory();

      await analyzeLog(
        savedLog.id
      );

      window.setTimeout(() => {
        setSaveState((state) =>
          state === "saved"
            ? "idle"
            : state
        );
      }, 1800);
    } catch (saveError) {
      console.error(
        "Daily Log save error:",
        saveError
      );

      setError(
        "Unable to save your entry."
      );

      setSaveState("error");
    }
  }

  async function handleDelete() {
    if (!currentLog) {
      return;
    }

    try {
      setError("");

      const response = await apiFetch(
        `${API_URL}?id=${currentLog.id}`,
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

      setCurrentLog(null);
      setContent("");
      setOriginalContent("");
      setSaveState("idle");
      setShowDeleteConfirm(false);
      setSuggestions([]);
      setAnalysisState("idle");
      setAnalysisError("");
      setResolvingSuggestionId(null);

      await loadHistory();
    } catch (deleteError) {
      console.error(
        "Daily Log delete error:",
        deleteError
      );

      setError(
        "Unable to delete this entry."
      );
    }
  }

  async function handleSuggestionAction(
    suggestionId: number,
    action: "accept" | "dismiss"
  ) {
    try {
      setResolvingSuggestionId(
        suggestionId
      );
      setAnalysisError("");

      const response = await apiFetch(
        `${API_URL}?suggestion_id=${suggestionId}&action=${action}`,
        {
          method: "POST",
        }
      );

      let data: unknown = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data)
        );
      }

      setSuggestions((current) =>
        current.filter(
          (suggestion) =>
            suggestion.id !==
            suggestionId
        )
      );
    } catch (actionError) {
      console.error(
        "Daily Log suggestion action error:",
        actionError
      );

      setAnalysisError(
        actionError instanceof Error
          ? actionError.message
          : "Unable to update this suggestion."
      );
    } finally {
      setResolvingSuggestionId(
        null
      );
    }
  }

  function handleEditorKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (
      (event.ctrlKey ||
        event.metaKey) &&
      event.key === "Enter"
    ) {
      event.preventDefault();

      event.currentTarget
        .form
        ?.requestSubmit();
    }
  }

  return (
    <ProtectedLayout>
      <main className="daily-log-page">
        <div
          className="daily-log-background"
          aria-hidden="true"
        />

        <div className="daily-log-shell">
          <header className="daily-log-topbar">
            <div className="daily-log-brand">
              <span className="daily-log-brand-dot" />

              <h1>Daily Log</h1>
            </div>

            <p className="daily-log-selected-date">
              {formatMainDate(
                selectedDate
              )}
            </p>
          </header>

          <section className="daily-log-journal">
            <form
              className="daily-log-editor"
              onSubmit={handleSubmit}
            >
              <div className="daily-log-editor-top">
                <div>
                  <span className="daily-log-entry-label">
                    {isToday
                      ? "Today"
                      : formatTimelineMonth(
                          selectedDate
                        )}
                  </span>

                  <h2>
                    {isToday
                      ? "What happened today?"
                      : "What do you remember?"}
                  </h2>
                </div>

                <div
                  className={`daily-log-status daily-log-status-${saveState}`}
                >
                  {saveState ===
                    "saving" &&
                    "Saving"}

                  {saveState ===
                    "saved" &&
                    "Saved"}

                  {saveState ===
                    "error" &&
                    "Not saved"}

                  {saveState ===
                    "idle" &&
                    hasUnsavedChanges &&
                    "Unsaved"}

                  {saveState ===
                    "idle" &&
                    !hasUnsavedChanges &&
                    currentLog &&
                    `Updated ${formatUpdatedTime(
                      currentLog.updated_at
                    )}`}
                </div>
              </div>

              <div className="daily-log-writing-area">
                {isLoading ? (
                  <div className="daily-log-editor-loading">
                    <span />
                    <span />
                    <span />
                  </div>
                ) : (
                  <textarea
                    className="daily-log-textarea"
                    value={content}
                    onChange={(event) => {
                      setContent(
                        event.target.value
                      );

                      setError("");
                      setSaveState("idle");

                      if (
                        suggestions.length > 0
                      ) {
                        setSuggestions([]);
                      }

                      setAnalysisError("");
                      setAnalysisState("idle");
                    }}
                    onKeyDown={
                      handleEditorKeyDown
                    }
                    placeholder="Start writing…"
                    aria-label="Daily Log content"
                    spellCheck={false}
                  />
                )}
              </div>

              <footer className="daily-log-editor-footer">
                <div className="daily-log-meta">
                  <span>
                    {wordCount}{" "}
                    {wordCount === 1
                      ? "word"
                      : "words"}
                  </span>

                  <span>
                    {characterCount} chars
                  </span>
                </div>

                <div className="daily-log-actions">
                  {currentLog &&
                    !showDeleteConfirm && (
                      <button
                        type="button"
                        className="daily-log-delete-button"
                        onClick={() =>
                          setShowDeleteConfirm(
                            true
                          )
                        }
                      >
                        Delete
                      </button>
                    )}

                  {currentLog &&
                    showDeleteConfirm && (
                      <div className="daily-log-delete-confirm">
                        <span>
                          Delete?
                        </span>

                        <button
                          type="button"
                          onClick={() =>
                            setShowDeleteConfirm(
                              false
                            )
                          }
                        >
                          No
                        </button>

                        <button
                          type="button"
                          onClick={handleDelete}
                        >
                          Yes
                        </button>
                      </div>
                    )}

                  <button
                    type="submit"
                    className="daily-log-save-button"
                    disabled={
                      isLoading ||
                      saveState ===
                        "saving" ||
                      !content.trim() ||
                      !hasUnsavedChanges
                    }
                  >
                    {saveState ===
                    "saving"
                      ? "Saving"
                      : currentLog
                        ? "Save"
                        : "Create"}

                    <span
                      aria-hidden="true"
                    >
                      ↗
                    </span>
                  </button>
                </div>
              </footer>

              {!isLoading &&
                currentLog &&
                !hasUnsavedChanges && (
                  <section
                    className="daily-log-suggestions"
                    aria-label="Daily Log suggestions"
                  >
                    {analysisState ===
                      "loading" && (
                      <div className="daily-log-analysis-status">
                        <span className="daily-log-analysis-pulse" />

                        <div>
                          <strong>
                            Looking through the entry
                          </strong>

                          <span>
                            Checking for completed wins.
                          </span>
                        </div>
                      </div>
                    )}

                    {analysisState !==
                      "loading" &&
                      suggestions.length >
                        0 && (
                        <div className="daily-log-suggestion-list">
                          <div className="daily-log-suggestion-heading">
                            <span>
                              Found in this entry
                            </span>

                            <strong>
                              {
                                suggestions.length
                              }
                            </strong>
                          </div>

                          {suggestions.map(
                            (suggestion) => {
                              const isResolving =
                                resolvingSuggestionId ===
                                suggestion.id;

                              return (
                                <article
                                  key={
                                    suggestion.id
                                  }
                                  className={`daily-log-suggestion daily-log-suggestion-${suggestion.size}`}
                                >
                                  <span className="daily-log-suggestion-mark">
                                    Win
                                  </span>

                                  <div className="daily-log-suggestion-copy">
                                    <h3>
                                      {
                                        suggestion.title
                                      }
                                    </h3>

                                    {suggestion.description && (
                                      <p>
                                        {
                                          suggestion.description
                                        }
                                      </p>
                                    )}

                                    <span className="daily-log-suggestion-size">
                                      {
                                        suggestion.size_label
                                      }
                                    </span>
                                  </div>

                                  <div className="daily-log-suggestion-actions">
                                    <button
                                      type="button"
                                      className="daily-log-suggestion-dismiss"
                                      disabled={
                                        isResolving
                                      }
                                      onClick={() =>
                                        handleSuggestionAction(
                                          suggestion.id,
                                          "dismiss"
                                        )
                                      }
                                    >
                                      Dismiss
                                    </button>

                                    <button
                                      type="button"
                                      className="daily-log-suggestion-accept"
                                      disabled={
                                        isResolving
                                      }
                                      onClick={() =>
                                        handleSuggestionAction(
                                          suggestion.id,
                                          "accept"
                                        )
                                      }
                                    >
                                      {isResolving
                                        ? "Working"
                                        : "Add to My Wins"}
                                    </button>
                                  </div>
                                </article>
                              );
                            }
                          )}
                        </div>
                      )}

                    {analysisState !==
                      "loading" &&
                      suggestions.length ===
                        0 && (
                        <div className="daily-log-analysis-empty">
                          <span>
                            {analysisState ===
                            "error"
                              ? analysisError
                              : "No pending win suggestions."}
                          </span>

                          <button
                            type="button"
                            onClick={() =>
                              analyzeLog(
                                currentLog.id
                              )
                            }
                          >
                            {analysisState ===
                            "error"
                              ? "Try again"
                              : "Check entry"}
                          </button>
                        </div>
                      )}

                    {analysisError &&
                      analysisState !==
                        "error" && (
                        <p
                          className="daily-log-analysis-error"
                          role="alert"
                        >
                          {analysisError}
                        </p>
                      )}
                  </section>
                )}

              {error && (
                <p
                  className="daily-log-error"
                  role="alert"
                >
                  {error}
                </p>
              )}
            </form>

            <aside className="daily-log-timeline">
              <div className="daily-log-timeline-header">
                <span>Days</span>

                <strong>
                  {logs.length}
                </strong>
              </div>

              <div className="daily-log-timeline-scroll">
                {isHistoryLoading ? (
                  <div className="daily-log-timeline-loading">
                    <span />
                    <span />
                    <span />
                    <span />
                  </div>
                ) : (
                  <div className="daily-log-timeline-list">
                    {timelineEntries.map(
                      (
                        entry,
                        index
                      ) => {
                        const isActive =
                          entry.date ===
                          selectedDate;

                        const entryIsToday =
                          entry.date ===
                          today;

                        return (
                          <button
                            key={
                              entry.date
                            }
                            type="button"
                            className={`daily-log-timeline-item ${
                              isActive
                                ? "daily-log-timeline-item-active"
                                : ""
                            }`}
                            onClick={() =>
                              changeDate(
                                entry.date
                              )
                            }
                          >
                            <span className="daily-log-timeline-rail">
                              <span className="daily-log-timeline-dot" />

                              {index <
                                timelineEntries.length -
                                  1 && (
                                <span className="daily-log-timeline-line" />
                              )}
                            </span>

                            <span className="daily-log-timeline-date">
                              <strong>
                                {formatTimelineDay(
                                  entry.date
                                )}
                              </strong>

                              <span>
                                {formatTimelineMonth(
                                  entry.date
                                )}
                              </span>
                            </span>

                            <span className="daily-log-timeline-copy">
                              <strong>
                                {entryIsToday
                                  ? "Today"
                                  : formatTimelineWeekday(
                                      entry.date
                                    )}
                              </strong>

                              <span>
                                {entry.log
                                  ? shortenText(
                                      entry.log
                                        .content,
                                      58
                                    )
                                  : "Empty day"}
                              </span>
                            </span>
                          </button>
                        );
                      }
                    )}
                  </div>
                )}
              </div>
            </aside>
          </section>
        </div>
      </main>
    </ProtectedLayout>
  );
}
