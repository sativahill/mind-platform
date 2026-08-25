"use client";

import "./navbar.css";

import Link from "next/link";
import {
  useEffect,
  useState,
} from "react";
import {
  usePathname,
  useRouter,
} from "next/navigation";
import BrandMark from "./BrandMark";
import BrainIcon from "./BrainIcon";

interface NavigationItem {
  href: string;
  label: string;
  icon?: "brain";
}

const navigationItems: NavigationItem[] = [
  {
    href: "/home",
    label: "Home",
  },
  {
    href: "/brain",
    label: "Brain",
    icon: "brain",
  },
  {
    href: "/daily-log",
    label: "Daily Log",
  },
  {
    href: "/wins",
    label: "Wins",
  },
  {
    href: "/chat",
    label: "Chat",
  },
  {
    href: "/goals",
    label: "Goals",
  },
  {
    href: "/board",
    label: "Board",
  },
  {
    href: "/habits",
    label: "Habits",
  },
];

function getGreeting() {
  const hour = new Date().getHours();

  if (hour < 12) {
    return "Good morning";
  }

  if (hour < 18) {
    return "Good afternoon";
  }

  return "Good evening";
}

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  const [isMenuOpen, setIsMenuOpen] =
    useState(false);

  const [greeting, setGreeting] =
    useState(getGreeting);

  useEffect(() => {
    function updateGreeting() {
      setGreeting(getGreeting());
    }

    updateGreeting();

    const intervalId = window.setInterval(
      updateGreeting,
      60_000
    );

    return () => {
      window.clearInterval(intervalId);
    };
  }, []);

  function isActiveRoute(href: string) {
    return (
      pathname === href ||
      pathname.startsWith(`${href}/`)
    );
  }

  function closeMenu() {
    setIsMenuOpen(false);
  }

  function logout() {
    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "refresh_token"
    );

    setIsMenuOpen(false);

    router.replace("/login");
  }

  function toggleTheme() {
    const root = document.documentElement;
    const nextTheme =
      root.dataset.theme === "light"
        ? "dark"
        : "light";

    root.dataset.theme = nextTheme;
    root.style.colorScheme = nextTheme;

    try {
      localStorage.setItem(
        "mind-theme",
        nextTheme
      );
    } catch {
      // The visual switch still works when storage is blocked.
    }
  }

  return (
    <header className="app-navbar">
      <div className="app-navbar-inner">
        <div className="app-navbar-identity">
          <Link
            href="/home"
            className="app-navbar-logo"
            aria-label="MIND home"
            onClick={closeMenu}
          >
            <BrandMark className="app-navbar-logo-mark" />

            <span className="app-navbar-logo-text">
              MIND
            </span>
          </Link>

          <span
            className="app-navbar-greeting"
            aria-label={greeting}
          >
            {greeting}.
          </span>
        </div>

        <nav
          className={`app-navbar-navigation ${
            isMenuOpen
              ? "app-navbar-navigation-open"
              : ""
          }`}
          aria-label="Main navigation"
        >
          {navigationItems.map((item) => {
            const active =
              isActiveRoute(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`app-navbar-link ${
                  active
                    ? "app-navbar-link-active"
                    : ""
                }`}
                aria-current={
                  active
                    ? "page"
                    : undefined
                }
                onClick={closeMenu}
              >
                {item.icon === "brain" && (
                  <BrainIcon className="app-navbar-brain-icon" />
                )}

                {item.label}
              </Link>
            );
          })}

          <button
            type="button"
            className="app-navbar-mobile-logout"
            onClick={logout}
          >
            Sign out
          </button>
        </nav>

        <div className="app-navbar-actions">
          <button
            type="button"
            className="app-navbar-theme"
            onClick={toggleTheme}
            aria-label="Toggle color theme"
            title="Toggle color theme"
          >
            <svg
              className="app-navbar-theme-sun"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="3.25" />
              <path d="M12 2.75v2M12 19.25v2M2.75 12h2M19.25 12h2M5.45 5.45l1.4 1.4M17.15 17.15l1.4 1.4M18.55 5.45l-1.4 1.4M6.85 17.15l-1.4 1.4" />
            </svg>

            <svg
              className="app-navbar-theme-moon"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M19.2 15.35A7.65 7.65 0 0 1 8.65 4.8 7.65 7.65 0 1 0 19.2 15.35Z" />
            </svg>
          </button>

          <button
            type="button"
            className="app-navbar-logout"
            onClick={logout}
          >
            Sign out
          </button>

          <button
            type="button"
            className={`app-navbar-menu-button ${
              isMenuOpen
                ? "app-navbar-menu-button-open"
                : ""
            }`}
            onClick={() => {
              setIsMenuOpen(
                (current) => !current
              );
            }}
            aria-label={
              isMenuOpen
                ? "Close navigation menu"
                : "Open navigation menu"
            }
            aria-expanded={isMenuOpen}
          >
            <span />
            <span />
          </button>
        </div>
      </div>
    </header>
  );
}
