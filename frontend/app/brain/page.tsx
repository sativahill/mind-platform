"use client";

import "./brain.css";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import ProtectedLayout from "@/components/ProtectedLayout";
import { apiFetch } from "@/lib/api";


const BRAIN_API_URL = "/api/brain/";
const ARRAY_PREVIEW_LIMIT = 3;
const NESTED_FIELD_LIMIT = 6;
const MAX_RENDER_DEPTH = 3;
const FIELD_PRIORITY = [
  "title",
  "name",
  "identity",
  "status",
  "progress",
  "streak",
  "today_status",
  "date",
  "due_date",
  "completed_at",
  "content",
  "description",
  "why_it_matters",
  "trigger",
  "action",
  "reward",
  "priority",
  "source",
];


interface BrainResponse {
  id: number;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}


interface BrainSection {
  key: string;
  title: string;
  description: string;
  value: unknown;
}


function isRecord(
  value: unknown
): value is Record<string, unknown> {
  return (
    typeof value === "object"
    && value !== null
    && !Array.isArray(value)
  );
}


function isBrainResponse(
  value: unknown
): value is BrainResponse {
  return (
    isRecord(value)
    && typeof value.id === "number"
    && isRecord(value.data)
    && typeof value.created_at === "string"
    && typeof value.updated_at === "string"
  );
}


function hasReadableValue(
  value: unknown
): boolean {
  if (value === null || value === undefined) {
    return false;
  }

  if (typeof value === "string") {
    return value.trim().length > 0;
  }

  if (Array.isArray(value)) {
    return value.some(hasReadableValue);
  }

  if (isRecord(value)) {
    return Object.values(value)
      .some(hasReadableValue);
  }

  return true;
}


function formatLabel(key: string) {
  const normalized = key
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\bv\d+$/i, "")
    .trim();

  if (!normalized) {
    return "Detail";
  }

  return normalized
    .split(/\s+/)
    .map((word, index) => {
      if (word.toLowerCase() === "ai") {
        return "AI";
      }

      if (index === 0) {
        return (
          word.charAt(0).toUpperCase()
          + word.slice(1)
        );
      }

      return word.toLowerCase();
    })
    .join(" ");
}


function formatScalar(value: unknown) {
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "number") {
    return new Intl.NumberFormat("en-US")
      .format(value);
  }

  if (typeof value === "string") {
    const normalized = value.trim();

    if (
      /^[a-z][a-z0-9_]*$/.test(normalized)
      && normalized.includes("_")
    ) {
      return formatLabel(normalized);
    }

    if (normalized.length > 260) {
      return `${normalized.slice(0, 257).trim()}…`;
    }

    return normalized;
  }

  return String(value);
}


function isTechnicalKey(key: string) {
  return (
    key === "id"
    || key === "event_key"
    || key === "sort_order"
    || key === "position"
    || key.endsWith("_id")
    || key.endsWith("_ids")
  );
}


function getReadableEntries(
  value: Record<string, unknown>
) {
  const entries = Object.entries(value)
    .filter(([, entryValue]) => (
      hasReadableValue(entryValue)
    ));

  const nonTechnicalEntries = entries
    .filter(([key]) => !isTechnicalKey(key));

  const readableEntries = nonTechnicalEntries.length > 0
    ? nonTechnicalEntries
    : entries;

  return readableEntries
    .map((entry, index) => ({
      entry,
      index,
      priority: FIELD_PRIORITY.indexOf(
        entry[0]
      ),
    }))
    .sort((left, right) => {
      const leftPriority = left.priority < 0
        ? Number.MAX_SAFE_INTEGER
        : left.priority;
      const rightPriority = right.priority < 0
        ? Number.MAX_SAFE_INTEGER
        : right.priority;

      return (
        leftPriority - rightPriority
        || left.index - right.index
      );
    })
    .map(({ entry }) => entry);
}


function ReadableValue({
  value,
  depth = 0,
}: {
  value: unknown;
  depth?: number;
}) {
  if (
    typeof value === "string"
    || typeof value === "number"
    || typeof value === "boolean"
  ) {
    return (
      <span className="brain-scalar">
        {formatScalar(value)}
      </span>
    );
  }

  if (Array.isArray(value)) {
    const readableItems = value
      .filter(hasReadableValue);

    if (readableItems.length === 0) {
      return null;
    }

    if (depth >= MAX_RENDER_DEPTH) {
      return (
        <span className="brain-summary">
          {readableItems.length}{" "}
          {readableItems.length === 1
            ? "entry"
            : "entries"}
        </span>
      );
    }

    const visibleItems = readableItems
      .slice(0, ARRAY_PREVIEW_LIMIT);
    const remainingCount =
      readableItems.length
      - visibleItems.length;

    return (
      <div className="brain-array">
        {visibleItems.map((item, index) => (
          <div
            className="brain-array-item"
            key={index}
          >
            <ReadableValue
              value={item}
              depth={depth + 1}
            />
          </div>
        ))}

        {remainingCount > 0 && (
          <span className="brain-more">
            +{remainingCount} more
          </span>
        )}
      </div>
    );
  }

  if (isRecord(value)) {
    const entries = getReadableEntries(value);

    if (entries.length === 0) {
      return null;
    }

    if (depth >= MAX_RENDER_DEPTH) {
      return (
        <span className="brain-summary">
          {entries.length}{" "}
          {entries.length === 1
            ? "detail"
            : "details"}
          {" "}recorded
        </span>
      );
    }

    const limit = depth >= 2
      ? NESTED_FIELD_LIMIT
      : entries.length;
    const visibleEntries = entries
      .slice(0, limit);
    const remainingCount =
      entries.length
      - visibleEntries.length;

    return (
      <dl className="brain-fields">
        {visibleEntries.map(([
          key,
          entryValue,
        ]) => {
          const isNested = (
            Array.isArray(entryValue)
            || isRecord(entryValue)
          );

          return (
            <div
              className={`brain-field ${
                isNested
                  ? "brain-field-nested"
                  : ""
              }`}
              key={key}
            >
              <dt>{formatLabel(key)}</dt>

              <dd>
                <ReadableValue
                  value={entryValue}
                  depth={depth + 1}
                />
              </dd>
            </div>
          );
        })}

        {remainingCount > 0 && (
          <div className="brain-field brain-field-more">
            <dt>Additional</dt>
            <dd>
              +{remainingCount} more details
            </dd>
          </div>
        )}
      </dl>
    );
  }

  return null;
}


function addValueToGroup(
  group: Record<string, unknown>,
  key: string,
  value: unknown
) {
  if (!hasReadableValue(value)) {
    return;
  }

  if (isRecord(value)) {
    Object.assign(group, value);
    return;
  }

  group[key] = value;
}


function buildBrainSections(
  data: Record<string, unknown>
): BrainSection[] {
  const progress: Record<string, unknown> = {};
  const recentMemory: Record<string, unknown> = {};

  addValueToGroup(
    progress,
    "progress",
    data.progress
  );

  if (hasReadableValue(data.habits)) {
    progress.habits = data.habits;
  }

  addValueToGroup(
    recentMemory,
    "history",
    data.history
  );

  const groupedKeys = new Set([
    "user",
    "context",
    "progress",
    "habits",
    "patterns",
    "history",
  ]);

  Object.entries(data).forEach(([
    key,
    value,
  ]) => {
    if (
      !groupedKeys.has(key)
      && hasReadableValue(value)
      && !(key in recentMemory)
    ) {
      recentMemory[key] = value;
    }
  });

  return [
    {
      key: "identity",
      title: "Identity",
      description: (
        "Details you have shared with PROJECT."
      ),
      value: data.user,
    },
    {
      key: "focus",
      title: "Current focus",
      description: (
        "The context guiding your next steps."
      ),
      value: data.context,
    },
    {
      key: "progress",
      title: "Progress",
      description: (
        "Goals, tasks, habits and wins in motion."
      ),
      value: progress,
    },
    {
      key: "patterns",
      title: "Patterns",
      description: (
        "Signals PROJECT has retained over time."
      ),
      value: data.patterns,
    },
    {
      key: "memory",
      title: "Recent memory",
      description: (
        "A concise view of recent events and activity."
      ),
      value: recentMemory,
    },
  ].filter((section) => (
    hasReadableValue(section.value)
  ));
}


export default function BrainPage() {
  const [brain, setBrain] =
    useState<BrainResponse | null>(null);
  const [isLoading, setIsLoading] =
    useState(true);
  const [error, setError] =
    useState("");
  const requestIdRef = useRef(0);

  const loadBrain = useCallback(async () => {
    const requestId =
      requestIdRef.current + 1;
    requestIdRef.current = requestId;

    setIsLoading(true);
    setError("");

    try {
      const response = await apiFetch(
        BRAIN_API_URL
      );

      if (!response.ok) {
        throw new Error(
          "Brain request failed."
        );
      }

      const payload: unknown =
        await response.json();

      if (!isBrainResponse(payload)) {
        throw new Error(
          "Brain response was invalid."
        );
      }

      if (requestId !== requestIdRef.current) {
        return;
      }

      setBrain(payload);
    } catch (loadError) {
      if (requestId !== requestIdRef.current) {
        return;
      }

      console.error(
        "Brain loading error:",
        loadError
      );
      setError(
        "Brain could not be loaded right now."
      );
    } finally {
      if (requestId === requestIdRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    let active = true;

    void Promise.resolve().then(() => {
      if (active) {
        void loadBrain();
      }
    });

    return () => {
      active = false;
      requestIdRef.current += 1;
    };
  }, [loadBrain]);

  const sections = useMemo(
    () => buildBrainSections(
      brain?.data ?? {}
    ),
    [brain]
  );

  return (
    <ProtectedLayout>
      <div className="brain-page">
        <div
          className="brain-page-background"
          aria-hidden="true"
        />

        <div className="brain-shell">
          <header className="brain-header">
            <div className="brain-heading">
              <span className="brain-heading-mark" />

              <div>
                <h1>Brain</h1>
                <p>
                  What the system currently knows
                  about you
                </p>
              </div>
            </div>

          </header>

          {isLoading ? (
            <section
              className="brain-loading"
              aria-label="Loading Brain"
              aria-live="polite"
            >
              {[0, 1, 2].map((item) => (
                <div
                  className="brain-loading-row"
                  key={item}
                >
                  <span />
                  <div>
                    <i />
                    <i />
                  </div>
                </div>
              ))}
            </section>
          ) : error ? (
            <section
              className="brain-error"
              role="alert"
            >
              <span className="brain-state-mark" />
              <h2>Memory is unavailable</h2>
              <p>{error}</p>
              <button
                type="button"
                onClick={loadBrain}
              >
                Try again
              </button>
            </section>
          ) : sections.length === 0 ? (
            <section className="brain-empty">
              <span className="brain-state-mark" />
              <h2>Your Brain is taking shape</h2>
              <p>
                It will fill as you use Daily Log,
                Goals, Habits and Board.
              </p>
            </section>
          ) : (
            <div className="brain-sections">
              {sections.map((section) => (
                <section
                  className="brain-section"
                  key={section.key}
                >
                  <header>
                    <span>{section.title}</span>
                    <p>{section.description}</p>
                  </header>

                  <div className="brain-section-content">
                    <ReadableValue
                      value={section.value}
                    />
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedLayout>
  );
}
