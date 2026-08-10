'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Incident } from '../../types';
import { apiClient } from '../../lib/api-client';

export default function PullRequestsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadPullRequests() {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getIncidents();
      setIncidents(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load pull requests list.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPullRequests();
  }, []);

  const prIncidents = incidents.filter(i => i.pr_result);

  return (
    <div style={{ padding: '2rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}>Automated Pull Requests</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Review pull requests proposed by the platform to fix experimentally validated exception paths.</p>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(244, 63, 94, 0.05)',
          border: '1px solid var(--danger)',
          color: 'var(--danger)',
          padding: '1rem',
          borderRadius: '6px',
          marginBottom: '2rem',
          fontSize: '0.875rem'
        }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
          Loading pull requests records...
        </div>
      ) : prIncidents.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '5rem 2rem',
          backgroundColor: 'var(--panel-bg)',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          color: 'var(--text-muted)'
        }}>
          <span style={{ fontSize: '2rem', display: 'block', marginBottom: '1rem' }}>🌿</span>
          <h3 style={{ color: 'var(--foreground)', marginBottom: '0.5rem' }}>No pull requests created yet</h3>
          <p style={{ fontSize: '0.875rem', maxWidth: '400px', margin: '0 auto' }}>
            Pull requests are generated after a hypothesis patch has been experimentally verified. Run the pipeline on an incident to start!
          </p>
        </div>
      ) : (
        <div style={{
          backgroundColor: 'var(--panel-bg)',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          overflow: 'hidden'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'rgba(255,255,255,0.01)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '1rem' }}>PR Number</th>
                <th style={{ padding: '1rem' }}>Repository</th>
                <th style={{ padding: '1rem' }}>Target Branch / Base</th>
                <th style={{ padding: '1rem' }}>Link</th>
                <th style={{ padding: '1rem' }}>Related Incident</th>
                <th style={{ padding: '1rem' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {prIncidents.map((incident) => {
                const pr = incident.pr_result;
                return (
                  <tr key={incident.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '1rem', fontWeight: 'bold' }}>
                      #{pr.pr_number}
                    </td>
                    <td style={{ padding: '1rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {incident.github_owner}/{incident.github_repo}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{
                        backgroundColor: 'rgba(56, 189, 248, 0.05)',
                        border: '1px solid rgba(56, 189, 248, 0.1)',
                        padding: '0.2rem 0.4rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: 'var(--primary)',
                        fontFamily: 'var(--font-mono)'
                      }}>
                        {pr.head_branch}
                      </span>
                      <span style={{ margin: '0 0.5rem', color: 'var(--text-muted)' }}>&rarr;</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {incident.github_branch || 'main'}
                      </span>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <a href={pr.pr_url} target="_blank" rel="noreferrer" style={{ fontWeight: 600 }}>
                        Open in GitHub &nearr;
                      </a>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <Link href={`/incidents/${incident.id}`} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                        {incident.id.slice(0, 12)}
                      </Link>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span className="badge badge-success">FIXED</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
