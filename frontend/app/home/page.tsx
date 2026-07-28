"use client";

import "./home.css";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "@/lib/api";
import ProtectedLayout from "@/components/ProtectedLayout";

interface LastDailyLog {
  date: string;
  content: string;
}

interface LastWin {
  title: string;
  size: string;
}

interface PrimaryGoal {
  id: number;
  title: string;
  progress: number;
}

interface GoalsData {
  active_count: number;
  primary: PrimaryGoal | null;
}

interface LatestHabit {
  id: number;
  title: string;
  streak: number;
}

interface HabitsData {
  active_count: number;
  completed_today: number;
  highest_streak: number;
  latest: LatestHabit | null;
}

interface HomeData {
  brain: Record<string, unknown>;
  daily_logs_count: number;
  wins_count: number;
  last_daily_log: LastDailyLog | null;
  last_win: LastWin | null;
  goals: GoalsData;
  habits: HabitsData;
}

interface BrainNode {
  href: string;
  title: string;
  value: string;
  detail: string;
  position:
    | "top-left"
    | "top-right"
    | "bottom-left"
    | "bottom-right";
}

function shortenText(value: string, maxLength: number) {
  const normalized = value.trim().replace(/\s+/g, " ");

  if (normalized.length <= maxLength) {
    return normalized;
  }

  return `${normalized.slice(0, maxLength).trim()}…`;
}

function BrainVisual() {
  return (
    <div
      className="brain-visual"
      aria-hidden="true"
    >
      <div className="brain-glow brain-glow-one" />
      <div className="brain-glow brain-glow-two" />

      <svg
        className="brain-svg"
        viewBox="0 0 360 320"
        role="presentation"
      >
        <defs>
          <linearGradient
            id="brainStroke"
            x1="70"
            y1="30"
            x2="290"
            y2="290"
            gradientUnits="userSpaceOnUse"
          >
            <stop
              offset="0"
              stopColor="#d6cbff"
              stopOpacity="0.96"
            />
            <stop
              offset="0.5"
              stopColor="#9278f5"
              stopOpacity="0.88"
            />
            <stop
              offset="1"
              stopColor="#6248d0"
              stopOpacity="0.52"
            />
          </linearGradient>

          <radialGradient
            id="brainFill"
            cx="0"
            cy="0"
            r="1"
            gradientTransform="translate(180 152) rotate(90) scale(145 128)"
            gradientUnits="userSpaceOnUse"
          >
            <stop
              stopColor="#8b70f2"
              stopOpacity="0.16"
            />
            <stop
              offset="0.7"
              stopColor="#493783"
              stopOpacity="0.05"
            />
            <stop
              offset="1"
              stopColor="#15121d"
              stopOpacity="0"
            />
          </radialGradient>

          <filter
            id="brainBlur"
            x="-50%"
            y="-50%"
            width="200%"
            height="200%"
          >
            <feGaussianBlur stdDeviation="5" />
          </filter>
        </defs>

        <path
          className="brain-shape"
          d="
            M178 40
            C162 20 132 18 112 34
            C91 32 72 45 66 65
            C43 69 28 89 31 112
            C14 128 16 156 34 170
            C24 192 35 217 57 225
            C57 249 76 267 100 267
            C111 289 139 298 158 282
            C167 291 174 294 180 294

            M182 40
            C198 20 228 18 248 34
            C269 32 288 45 294 65
            C317 69 332 89 329 112
            C346 128 344 156 326 170
            C336 192 325 217 303 225
            C303 249 284 267 260 267
            C249 289 221 298 202 282
            C193 291 186 294 180 294
          "
          fill="none"
          stroke="url(#brainStroke)"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        <path
          className="brain-fill"
          d="
            M178 40
            C162 20 132 18 112 34
            C91 32 72 45 66 65
            C43 69 28 89 31 112
            C14 128 16 156 34 170
            C24 192 35 217 57 225
            C57 249 76 267 100 267
            C111 289 139 298 158 282
            C167 291 174 294 180 294
            C186 294 193 291 202 282
            C221 298 249 289 260 267
            C284 267 303 249 303 225
            C325 217 336 192 326 170
            C344 156 346 128 329 112
            C332 89 317 69 294 65
            C288 45 269 32 248 34
            C228 18 198 20 182 40
            Z
          "
          fill="url(#brainFill)"
        />

        <path
          className="brain-center-line"
          d="
            M180 42
            C170 60 171 82 180 98
            C171 114 172 136 180 152
            C171 170 172 194 180 212
            C171 231 172 257 180 292
          "
        />

        <g className="brain-folds">
          <path d="M112 36 C138 43 148 60 145 80" />
          <path d="M66 66 C94 64 113 78 111 100" />
          <path d="M32 112 C59 106 84 121 87 144" />
          <path d="M34 170 C58 156 84 164 94 185" />
          <path d="M57 225 C80 205 108 209 121 231" />
          <path d="M100 267 C111 245 135 239 151 253" />

          <path d="M248 36 C222 43 212 60 215 80" />
          <path d="M294 66 C266 64 247 78 249 100" />
          <path d="M328 112 C301 106 276 121 273 144" />
          <path d="M326 170 C302 156 276 164 266 185" />
          <path d="M303 225 C280 205 252 209 239 231" />
          <path d="M260 267 C249 245 225 239 209 253" />

          <path d="M145 80 C125 92 126 115 148 124" />
          <path d="M111 100 C94 113 97 136 117 145" />
          <path d="M94 185 C115 174 132 187 130 208" />
          <path d="M151 253 C151 232 140 218 121 213" />

          <path d="M215 80 C235 92 234 115 212 124" />
          <path d="M249 100 C266 113 263 136 243 145" />
          <path d="M266 185 C245 174 228 187 230 208" />
          <path d="M209 253 C209 232 220 218 239 213" />
        </g>

        <path
          className="brain-outline-glow"
          d="
            M178 40
            C162 20 132 18 112 34
            C91 32 72 45 66 65
            C43 69 28 89 31 112
            C14 128 16 156 34 170
            C24 192 35 217 57 225
            C57 249 76 267 100 267
            C111 289 139 298 158 282
            C167 291 174 294 180 294

            M182 40
            C198 20 228 18 248 34
            C269 32 288 45 294 65
            C317 69 332 89 329 112
            C346 128 344 156 326 170
            C336 192 325 217 303 225
            C303 249 284 267 260 267
            C249 289 221 298 202 282
            C193 291 186 294 180 294
          "
          fill="none"
          stroke="#8268f2"
          strokeOpacity="0.4"
          strokeWidth="8"
          filter="url(#brainBlur)"
        />

        <g className="brain-signals">
          <circle cx="112" cy="36" r="3" />
          <circle cx="32" cy="112" r="3" />
          <circle cx="100" cy="267" r="3" />
          <circle cx="248" cy="36" r="3" />
          <circle cx="328" cy="112" r="3" />
          <circle cx="260" cy="267" r="3" />
        </g>
      </svg>

      <span className="brain-status-label">
        Brain
      </span>

      <span className="brain-status-value">
        Listening
      </span>
    </div>
  );
}

export default function HomePage() {
  const [data, setData] = useState<HomeData | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadHome() {
      try {
        setError("");

        const response = await apiFetch(
          "http://127.0.0.1:8000/api/home/"
        );

        if (!response.ok) {
          throw new Error(
            `Home request failed with status ${response.status}`
          );
        }

        const result: HomeData = await response.json();

        if (isMounted) {
          setData(result);
        }
      } catch (loadError) {
        console.error("Home loading error:", loadError);

        if (isMounted) {
          setError("Your home could not be loaded.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadHome();

    return () => {
      isMounted = false;
    };
  }, []);

  const nodes = useMemo<BrainNode[]>(() => {
    const latestLog = data?.last_daily_log;
    const primaryGoal = data?.goals.primary;
    const latestWin = data?.last_win;
    const latestHabit = data?.habits.latest;

    return [
      {
        href: "/daily-log",
        title: "Daily Log",
        value: `${data?.daily_logs_count ?? 0} ${
          data?.daily_logs_count === 1
            ? "entry"
            : "entries"
        }`,
        detail: latestLog
          ? shortenText(latestLog.content, 44)
          : "Nothing written yet",
        position: "top-left",
      },
      {
        href: "/goals",
        title: "Goals",
        value: `${data?.goals.active_count ?? 0} active`,
        detail: primaryGoal
          ? `${primaryGoal.title} · ${primaryGoal.progress}%`
          : "No active goal",
        position: "top-right",
      },
      {
        href: "/wins",
        title: "My Wins",
        value: `${data?.wins_count ?? 0} recorded`,
        detail: latestWin
          ? latestWin.title
          : "No win recorded yet",
        position: "bottom-left",
      },
      {
        href: "/habits",
        title: "Habits",
        value: `${data?.habits.completed_today ?? 0}/${
          data?.habits.active_count ?? 0
        } today`,
        detail: latestHabit
          ? `${latestHabit.title} · ${latestHabit.streak} day streak`
          : "No active habit",
        position: "bottom-right",
      },
    ];
  }, [data]);

  return (
    <ProtectedLayout>
      <main className="home-page">
        <div
          className="home-background"
          aria-hidden="true"
        />

        <div
          className="home-vignette"
          aria-hidden="true"
        />

        <div className="home-container">
          {isLoading ? (
            <section
              className="home-loading"
              aria-label="Loading home"
            >
              <div className="home-loading-brain">
                <BrainVisual />
              </div>
            </section>
          ) : error ? (
            <section
              className="home-error"
              role="alert"
            >
              <p>{error}</p>

              <button
                type="button"
                onClick={() => window.location.reload()}
              >
                Try again
              </button>
            </section>
          ) : (
            <section
              className="brain-system"
              aria-label="Your connected system"
            >
              <svg
                className="brain-connections"
                viewBox="0 0 1200 720"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <defs>
                  <linearGradient
                    id="connectionGradientLeft"
                    x1="600"
                    y1="360"
                    x2="160"
                    y2="150"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop
                      offset="0"
                      stopColor="#876bf0"
                      stopOpacity="0.55"
                    />

                    <stop
                      offset="1"
                      stopColor="#ffffff"
                      stopOpacity="0.06"
                    />
                  </linearGradient>

                  <linearGradient
                    id="connectionGradientRight"
                    x1="600"
                    y1="360"
                    x2="1040"
                    y2="150"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop
                      offset="0"
                      stopColor="#876bf0"
                      stopOpacity="0.55"
                    />

                    <stop
                      offset="1"
                      stopColor="#ffffff"
                      stopOpacity="0.06"
                    />
                  </linearGradient>
                </defs>

                <path
                  d="M480 255 C415 225 345 165 245 145"
                  stroke="url(#connectionGradientLeft)"
                />

                <path
                  d="M720 255 C785 225 855 165 955 145"
                  stroke="url(#connectionGradientRight)"
                />

                <path
                  d="M480 465 C415 495 345 555 245 575"
                  stroke="url(#connectionGradientLeft)"
                />

                <path
                  d="M720 465 C785 495 855 555 955 575"
                  stroke="url(#connectionGradientRight)"
                />

                <circle cx="480" cy="255" r="3" />
                <circle cx="720" cy="255" r="3" />
                <circle cx="480" cy="465" r="3" />
                <circle cx="720" cy="465" r="3" />
              </svg>

              <div className="brain-core">
                <BrainVisual />
              </div>

              {nodes.map((node) => (
                <Link
                  key={node.href}
                  href={node.href}
                  className={`brain-node brain-node-${node.position}`}
                >
                  <div className="brain-node-heading">
                    <h2>{node.title}</h2>

                    <span aria-hidden="true">
                      ↗
                    </span>
                  </div>

                  <strong>
                    {node.value}
                  </strong>

                  <p>
                    {node.detail}
                  </p>
                </Link>
              ))}
            </section>
          )}
        </div>
      </main>
    </ProtectedLayout>
  );
}
