"use client";

import AuthGuard from "./AuthGuard";
import Navbar from "./Navbar";

interface ProtectedLayoutProps {
  children: React.ReactNode;
}

export default function ProtectedLayout({
  children,
}: ProtectedLayoutProps) {
  return (
    <AuthGuard>
      <Navbar />

      <main>
        {children}
      </main>
    </AuthGuard>
  );
}