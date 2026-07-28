"use client";

import "./navbar.css";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

interface NavigationItem {
  href: string;
  label: string;
}

const navigationItems: NavigationItem[] = [
  {
    href: "/home",
    label: "Home",
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

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  const [isMenuOpen, setIsMenuOpen] =
    useState(false);

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
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    setIsMenuOpen(false);

    router.replace("/login");
  }

  return (
    <header className="app-navbar">
      <div className="app-navbar-inner">
        <Link
          href="/home"
          className="app-navbar-logo"
          aria-label="PROJECT home"
          onClick={closeMenu}
        >
          <span className="app-navbar-logo-circle" />

          <span className="app-navbar-logo-text">
            PROJECT
          </span>
        </Link>

        <nav
          className={`app-navbar-navigation ${
            isMenuOpen
              ? "app-navbar-navigation-open"
              : ""
          }`}
          aria-label="Main navigation"
        >
          {navigationItems.map((item) => {
            const active = isActiveRoute(
              item.href
            );

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
                  active ? "page" : undefined
                }
                onClick={closeMenu}
              >
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