"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Navbar() {
  const router = useRouter();

  function logout() {
    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "refresh_token"
    );

    router.push("/login");
  }

  return (
    <nav className="border-b p-4">
      <div className="flex gap-4 items-center">
        <Link href="/home">
          Home
        </Link>

        <Link href="/daily-log">
          Daily Log
        </Link>

        <Link href="/wins">
          Wins
        </Link>

        <Link href="/chat">
          Chat
        </Link>

        <Link href="/goals">
          Goals
        </Link>

        <Link href="/board">
          Board
        </Link>

        <Link href="/habits">
          Habits
        </Link>

        <button
          onClick={logout}
          className="ml-auto border rounded px-3 py-1"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}