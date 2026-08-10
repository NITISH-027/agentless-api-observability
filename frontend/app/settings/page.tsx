'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api-client';

export default function SettingsPage() {
  const [status, setStatus] = useState<string>('UNKNOWN');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkHealth() {
      try {
        const resp = await apiClient.getHealth();
        setStatus(resp.status || 'OK');
      } catch (e) {
        setStatus('OFFLINE');
      } finally {
        setLoading(false);
      }
    }
    checkHealth();
  }, []);

  return (
    <div style={{ padding: '2rem', maxWidth: '800px' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}>System Settings</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Configure environment settings, LLM providers, and check system status.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Status Card */}
        <div style={{
          backgroundColor: 'var(--panel-bg)',
          border: '1px solid var(--border)',
          padding: '1.5rem',
          borderRadius: '8px'
        }}>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Platform Status</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem', fontSize: '0.9rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>FastAPI Engine:</span>
            <span style={{ 
              fontWeight: 700, 
              color: status === 'OFFLINE' ? 'var(--danger)' : 'var(--success)'
            }}>
              {loading ? 'CHECKING...' : status}
            </span>

            <span style={{ color: 'var(--text-muted)' }}>Database Integrations:</span>
            <span style={{ color: 'var(--foreground)' }}>Supabase PostgreSQL</span>

            <span style={{ color: 'var(--text-muted)' }}>Sandbox Isolation:</span>
            <span style={{ color: 'var(--foreground)' }}>Docker Context</span>
          </div>
        </div>

        {/* Configuration Guidelines Card */}
        <div style={{
          backgroundColor: 'var(--panel-bg)',
          border: '1px solid var(--border)',
          padding: '1.5rem',
          borderRadius: '8px'
        }}>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Environment Configuration</h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-dim)', marginBottom: '1rem', lineHeight: '1.5' }}>
            System configuration parameters are resolved from the backend <code>.env</code> file. Exposing these variables directly to the client bundle is blocked for security.
          </p>

          <pre style={{
            backgroundColor: 'var(--card-bg)',
            padding: '1rem',
            borderRadius: '6px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8rem',
            border: '1px solid var(--border)',
            color: 'var(--text-dim)',
            lineHeight: '1.6'
          }}>
{`# Backend .env configuration checklist:
GITHUB_TOKEN=ghp_...
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-...
SANDBOX_IMAGE=python:3.10-slim
DATABASE_URL=sqlite:///./sql_app.db`}
          </pre>
        </div>
      </div>
    </div>
  );
}
