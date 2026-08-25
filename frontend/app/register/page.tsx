"use client";

import "./register.css";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { apiUrl } from "@/lib/api";
import BrandMark from "@/components/BrandMark";

type RegisterErrorResponse = {
  username?: string[];
  email?: string[];
  password?: string[];
  detail?: string;
  non_field_errors?: string[];
};

export default function RegisterPage() {
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] =
    useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirmation, setShowPasswordConfirmation] =
    useState(false);

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function getErrorMessage(data: RegisterErrorResponse) {
    if (data.username?.length) {
      return data.username[0];
    }

    if (data.email?.length) {
      return data.email[0];
    }

    if (data.password?.length) {
      return data.password[0];
    }

    if (data.non_field_errors?.length) {
      return data.non_field_errors[0];
    }

    if (data.detail) {
      return data.detail;
    }

    return "Unable to create your account. Please try again.";
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    setError("");

    if (password !== passwordConfirmation) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(
        apiUrl("/api/register/"),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username: username.trim(),
            email: email.trim(),
            password,
          }),
        }
      );

      const data: RegisterErrorResponse =
        await response.json();

      if (!response.ok) {
        setError(getErrorMessage(data));
        return;
      }

      router.replace("/login");
    } catch (error) {
      console.error("Registration error:", error);

      setError(
        "Unable to connect to the server. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="register-page auth-page">
      <div
        className="register-background"
        aria-hidden="true"
      />

      <div
        className="register-vignette"
        aria-hidden="true"
      />

      <header className="register-header">
        <Link
          href="/"
          className="register-logo"
          aria-label="Return to the landing page"
        >
          <BrandMark className="register-logo-mark" />

          <span className="register-text">
            MIND
          </span>
        </Link>
      </header>

      <section className="register-content auth-content">
        <div className="register-heading auth-heading">
          <h1 className="register-title auth-title">
            Take Action 
          </h1>

          <p className="register-description auth-description">
            A place for your goals, habits and progress.
          </p>
        </div>

        <form
          className="register-form auth-form"
          onSubmit={handleSubmit}
          noValidate
        >
          <div className="register-input-group">
            <label
              htmlFor="username"
              className="register-input-label"
            >
              Username
            </label>

            <input
              id="username"
              className="register-input"
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

          <div className="register-input-group">
            <label
              htmlFor="email"
              className="register-input-label"
            >
              Email
            </label>

            <input
              id="email"
              className="register-input"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                setError("");
              }}
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="register-input-group">
            <label
              htmlFor="password"
              className="register-input-label"
            >
              Password
            </label>

            <div className="register-password-field">
              <input
                id="password"
                className="register-input register-password-input"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
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
                className="register-password-toggle"
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

          <div className="register-input-group">
            <label
              htmlFor="password-confirmation"
              className="register-input-label"
            >
              Confirm password
            </label>

            <div className="register-password-field">
              <input
                id="password-confirmation"
                className="register-input register-password-input"
                type={
                  showPasswordConfirmation
                    ? "text"
                    : "password"
                }
                autoComplete="new-password"
                value={passwordConfirmation}
                onChange={(event) => {
                  setPasswordConfirmation(
                    event.target.value
                  );
                  setError("");
                }}
                disabled={isSubmitting}
                required
              />

              <button
                type="button"
                className="register-password-toggle"
                onClick={() => {
                  setShowPasswordConfirmation(
                    (current) => !current
                  );
                }}
                aria-label={
                  showPasswordConfirmation
                    ? "Hide password confirmation"
                    : "Show password confirmation"
                }
                aria-pressed={showPasswordConfirmation}
              >
                {showPasswordConfirmation
                  ? "Hide"
                  : "Show"}
              </button>
            </div>
          </div>

          <div
            className={`register-error ${
              error ? "register-error-visible" : ""
            }`}
            role="alert"
            aria-live="polite"
          >
            {error}
          </div>

          <button
            type="submit"
            className="register-button"
            disabled={
              isSubmitting ||
              !username.trim() ||
              !email.trim() ||
              !password ||
              !passwordConfirmation
            }
          >
            <span>
              {isSubmitting
                ? "Creating account"
                : "Create account"}
            </span>

            <span
              className="register-button-arrow"
              aria-hidden="true"
            >
              →
            </span>
          </button>
        </form>

        <p className="register-footer">
          Already have an account?{" "}
          <Link href="/login">
            Sign in
          </Link>
        </p>
      </section>

      <footer className="register-legal">
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
