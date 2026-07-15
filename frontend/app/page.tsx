import Link from "next/link";
import "./landing.css";

export default function LandingPage() {
  return (
    <main className="landing">

      {/* Background */}

      <div className="background" />
      <div className="vignette" />

      {/* Header */}

      <header className="header">
        <Link
          href="/"
          className="logo"
          aria-label="PROJECT"
        >
          <span className="logo-circle" />
          <span className="logo-text">
            PROJECT
          </span>
        </Link>
      </header>

      {/* Hero */}

      <section className="hero">

        <div className="hero-inner">

          <h1 className="hero-title hero-light">
            A quiet place
          </h1>

          <h2 className="hero-title hero-muted">
            that remembers
          </h2>

          <h3 className="hero-title hero-muted">
            everything
          </h3>

          <p className="subtitle">
            Your second brain for goals, memories,
            <br />
            habits and progress.
          </p>

          <div className="buttons">

            <Link
              href="/login"
              className="button button-primary"
            >
              Continue
            </Link>

            <Link
              href="/register"
              className="button button-secondary"
            >
              Create account
            </Link>

          </div>

        </div>

      </section>

      {/* Footer */}

      <footer className="footer">

        <Link href="/privacy">
          Privacy
        </Link>

        <span>•</span>

        <Link href="/terms">
          Terms
        </Link>

      </footer>

    </main>
  );
}