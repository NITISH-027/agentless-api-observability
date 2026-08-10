import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agentless API Observability & Debugging Platform",
  description: "Automated API Failure Ingestion, Reproduction, and Patch Verification Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <div className="layout-wrapper">
          <aside className="sidebar" style={{ padding: '1.5rem 1rem', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              {/* Logo */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingLeft: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem' }}>⚡</span>
                <div>
                  <h1 style={{ fontSize: '1rem', fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1 }}>AGENTLESS</h1>
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600 }}>DEBUGGING ENGINE</span>
                </div>
              </div>

              {/* Links */}
              <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                <Link href="/" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.625rem 0.75rem',
                  borderRadius: '6px',
                  color: 'var(--text-dim)',
                  fontSize: '0.875rem',
                  fontWeight: 500
                }}>
                  📊 Overview
                </Link>
                <Link href="/incidents" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.625rem 0.75rem',
                  borderRadius: '6px',
                  color: 'var(--text-dim)',
                  fontSize: '0.875rem',
                  fontWeight: 500
                }}>
                  🚨 Incidents
                </Link>
                <Link href="/repositories" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.625rem 0.75rem',
                  borderRadius: '6px',
                  color: 'var(--text-dim)',
                  fontSize: '0.875rem',
                  fontWeight: 500
                }}>
                  📦 Repositories
                </Link>
                <Link href="/investigations" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.625rem 0.75rem',
                  borderRadius: '6px',
                  color: 'var(--text-dim)',
                  fontSize: '0.875rem',
                  fontWeight: 500
                }}>
                  🔍 Investigations
                </Link>
                <Link href="/pull-requests" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.625rem 0.75rem',
                  borderRadius: '6px',
                  color: 'var(--text-dim)',
                  fontSize: '0.875rem',
                  fontWeight: 500
                }}>
                  🌿 Pull Requests
                </Link>
                <Link href="/settings" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.625rem 0.75rem',
                  borderRadius: '6px',
                  color: 'var(--text-dim)',
                  fontSize: '0.875rem',
                  fontWeight: 500
                }}>
                  ⚙️ Settings
                </Link>
              </nav>
            </div>

            {/* Bottom Status panel */}
            <div style={{
              backgroundColor: 'rgba(255,255,255,0.02)',
              border: '1px solid var(--border)',
              padding: '0.75rem',
              borderRadius: '6px',
              fontSize: '0.75rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.375rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>Backend:</span>
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>ONLINE</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>GitHub Sync:</span>
                <span style={{ color: 'var(--primary)', fontWeight: 600 }}>ACTIVE</span>
              </div>
            </div>
          </aside>

          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
