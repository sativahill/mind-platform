"use client";

import "./login.css";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/token/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username: username.trim(),
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError("The username or password is incorrect.");
        return;
      }

      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);

      router.replace("/home");
    } catch (error) {
      console.error("Login error:", error);

      setError(
        "Unable to connect to the server. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page auth-page">
      <div
        className="login-background"
        aria-hidden="true"
      />

      <div
        className="login-vignette"
        aria-hidden="true"
      />

      <header className="login-header">
        <Link
          href="/"
          className="login-logo"
          aria-label="Return to the landing page"
        >
          <span className="login-circle" />

          <span className="login-text">
            PROJECT
          </span>
        </Link>
      </header>

      <section className="login-content auth-content">
        <div className="login-heading auth-heading">
          <h1 className="login-title auth-title">
            Welcome Back
          </h1>

          <p className="login-description auth-description">
            Everything you have built is still here.
          </p>
        </div>

        <form
          className="login-form auth-form"
          onSubmit={handleSubmit}
          noValidate
        >
          <div className="input-group">
            <label
              htmlFor="username"
              className="input-label"
            >
              Username
            </label>

            <input
              id="username"
              className="input"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => {
                setUsername(event.target.value);
                setError("");
              }}
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="input-group">
            <label
              htmlFor="password"
              className="input-label"
            >
              Password
            </label>

            <div className="password-field">
              <input
                id="password"
                className="input password-input"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setError("");
                }}
                disabled={isSubmitting}
                required
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() => {
                  setShowPassword((current) => !current);
                }}
                aria-label={
                  showPassword
                    ? "Hide password"
                    : "Show password"
                }
                aria-pressed={showPassword}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <div
            className={`login-error ${
              error ? "login-error-visible" : ""
            }`}
            role="alert"
            aria-live="polite"
          >
            {error}
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={
              isSubmitting ||
              !username.trim() ||
              !password
            }
          >
            <span>
              {isSubmitting
                ? "Signing in"
                : "Continue"}
            </span>

            <span
              className="login-button-arrow"
              aria-hidden="true"
            >
              →
            </span>
          </button>
        </form>

        <p className="login-footer">
          New to PROJECT?{" "}
          <Link href="/register">
            Create an account
          </Link>
        </p>
      </section>

      <footer className="login-legal">
        <Link href="/privacy">
          Privacy
        </Link>

        <span aria-hidden="true">
          •
        </span>

        <Link href="/terms">
          Terms
        </Link>
      </footer>
    </main>
  );
}
