"use client";

import "./login.css";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/token/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username,
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert("Invalid username or password.");
        return;
      }

      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);

      router.push("/home");
    } catch (error) {
      console.error(error);
      alert("Unable to connect to the server.");
    }
  }

  return (
    <main className="login-page">
      <div className="login-background" />
      <div className="login-vignette" />

      {/* Header */}

      <header className="login-header">
        <Link
          href="/"
          className="login-logo"
          aria-label="Back to Landing"
        >
          <span className="login-circle" />

          <span className="login-text">
            PROJECT
          </span>

          <span className="login-back">
            ← Back
          </span>
        </Link>
      </header>

      {/* Content */}

      <section className="login-content">

        <h1 className="login-title">
          Welcome back
        </h1>

        <p className="login-description">
          Continue where you left off.
        </p>

        <form
          className="login-form"
          onSubmit={handleSubmit}
        >

          <div className="input-group">

            <input
              id="username"
              className="input"
              type="text"
              placeholder=" "
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />

            <label
              htmlFor="username"
              className="input-label"
            >
              Username
            </label>

          </div>

          <div className="input-group">

            <input
              id="password"
              className="input"
              type="password"
              placeholder=" "
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <label
              htmlFor="password"
              className="input-label"
            >
              Password
            </label>

          </div>

          <button
            type="submit"
            className="login-button"
          >
            Continue
          </button>

        </form>

        <div className="login-footer">
          Don't have an account?{" "}
          <Link href="/register">
            Create account
          </Link>
        </div>

      </section>

    </main>
  );
}