import Link from "next/link";
import BrandMark from "@/components/BrandMark";

import "./landing.css";

export default function LandingPage() {
  return (
    <main className="landing">
      <div
        className="landing-background"
        aria-hidden="true"
      />

      <div
        className="landing-vignette"
        aria-hidden="true"
      />

      <header className="landing-header">
        <Link
          href="/"
          className="landing-logo"
          aria-label="MIND home"
        >
          <BrandMark className="landing-logo-mark" />

          <span className="landing-logo-text">
            MIND
          </span>
        </Link>
      </header>

      <section className="landing-hero">
        <div className="landing-hero-inner">
          <h1 className="landing-title">
            <span className="landing-title-primary">
              A quiet place
            </span>

            <span className="landing-title-secondary">
              that remembers everything.
            </span>
          </h1>

          <p className="landing-subtitle">
            Your second brain for goals, memories,
            <br />
            habits and progress.
          </p>

          <div className="landing-actions">
            <Link
              href="/login"
              className="landing-button landing-button-primary"
            >
              <span>Continue</span>

              <span
                className="landing-button-arrow"
                aria-hidden="true"
              >
                →
              </span>
            </Link>

            <Link
              href="/register"
              className="landing-button landing-button-secondary"
            >
              Create account
            </Link>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
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
