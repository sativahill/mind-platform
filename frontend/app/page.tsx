import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold mb-4">
          PROJECT
        </h1>

        <p className="text-zinc-400 text-lg mb-8">
          Personal AI Platform
        </p>

        <div className="flex gap-4 justify-center">
          <Link
            href="/login"
            className="border rounded px-6 py-3"
          >
            Login
          </Link>

          <Link
            href="/register"
            className="border rounded px-6 py-3"
          >
            Create Account
          </Link>
        </div>
      </div>
    </main>
  );
}