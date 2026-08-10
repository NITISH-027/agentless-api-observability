'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Incident } from '../types';
import { apiClient } from '../lib/api-client';

export default function OverviewPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadIncidents() {
    try {
      setError(null);
      const data = await apiClient.getIncidents();
      setIncidents(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to connect to backend server. Make sure the FastAPI backend is running on http://localhost:8000.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadIncidents();
  }, []);

  // Compute metrics
  const totalIncidents = incidents.length;
  const activeInvestigations = incidents.filter(i => 
    i.status === 'ANALYZING' || i.status === 'REPRODUCING' || i.status === 'VERIFYING'
  ).length;
  const verifiedFixes = incidents.filter(i => i.status === 'FIXED').length;
  const openPRs = incidents.filter(i => i.pr_result).length;

  const recentIncidents = incidents.slice(0, 5);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'FIXED': return 'var(--success)';
      case 'ANALYZING':
      case 'REPRODUCING':
      case 'VERIFYING': return 'var(--warning)';
      case 'FAILED': return 'var(--danger)';
      default: return 'var(--text-muted)';
    }
  };

  return (
    <div style={{ padding: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}>System Overview</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Automated API failure ingestion and code repair pipeline metrics.</p>
        </div>
        <button onClick={loadIncidents} style={{
          backgroundColor: 'rgba(255,255,255,0.03)',
          border: '1px solid var(--border)',
          color: 'var(--foreground)',
          padding: '0.5rem 1rem',
          borderRadius: '6px',
          fontSize: '0.875rem',
          fontWeight: 500
        }}>
          🔄 Refresh
        </button>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(244, 63, 94, 0.06)',
          border: '1px solid rgba(244, 63, 94, 0.2)',
          color: 'var(--danger)',
          padding: '1rem',
          borderRadius: '6px',
          marginBottom: '2rem',
          fontSize: '0.875rem'
        }}>
          <strong>System Connection Error:</strong> {error}
        </div>
      )}

      {/* Metrics Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2.5rem'
      }}>
        <div style={{
          backgroundColor: 'var(--panel-bg)',
          border: '1px solid var(--border)',
          padding: '1.25rem',
          borderRadius: '8px'
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Ingested</span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 700, marginTop: '0.5rem', color: 'var(--foreground)' }}>{loading ? '...' : totalIncidents}</h2>
        </div>
        
        <div style={{
          backgroundColor: 'var(--panel-bg)',
          border: '1px solid var(--border)',
          padding: '1.25rem',
          borderRadius: '8px'
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Active Investigations</span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 700, marginTop: '0.5rem', color: 'var(--warning)' }}>{loading ? '...' : activeInvestigations}</h2>
        </div>

        <div style={{
          backgroundColor: 'var(--panel-bg)',
          border: '1px solid var(--border)',
          padding: '1.25rem',
          borderRadius: '8px'
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Verified Fixes</span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 700, marginTop: '0.5rem', color: 'var(--success)' }}>{loading ? '...' : verifiedFixes}</h2>
        </div>

        <div style={{
          backgroundColor: 'var(--panel-bg)',
          border: '1px solid var(--border)',
          padding: '1.25rem',
          borderRadius: '8px'
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Open Pull Requests</span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 700, marginTop: '0.5rem', color: 'var(--primary)' }}>{loading ? '...' : openPRs}</h2>
        </div>
      </div>

      {/* Recent Incidents */}
      <div>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)' }}>
          Recent Ingested API Failures
        </h2>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
            Loading system metrics...
          </div>
        ) : recentIncidents.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '4rem 2rem',
            backgroundColor: 'var(--panel-bg)',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            color: 'var(--text-muted)'
          }}>
            <span style={{ fontSize: '2rem', display: 'block', marginBottom: '1rem' }}>📥</span>
            <h3 style={{ color: 'var(--foreground)', marginBottom: '0.5rem', fontSize: '1rem' }}>No incidents yet</h3>
            <p style={{ fontSize: '0.85rem', maxWidth: '360px', margin: '0 auto' }}>
              Your observability environment is empty. Send a JSON payload to <code>POST /logs</code> to trigger ingestion.
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
                  <th style={{ padding: '1rem', fontWeight: 600 }}>Incident ID</th>
                  <th style={{ padding: '1rem', fontWeight: 600 }}>Service</th>
                  <th style={{ padding: '1rem', fontWeight: 600 }}>Endpoint</th>
                  <th style={{ padding: '1rem', fontWeight: 600 }}>Exception</th>
                  <th style={{ padding: '1rem', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '1rem', fontWeight: 600 }}>Ingested At</th>
                  <th style={{ padding: '1rem', fontWeight: 600 }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentIncidents.map((incident) => (
                  <tr key={incident.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '1rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                      {incident.id.slice(0, 12)}
                    </td>
                    <td style={{ padding: '1rem', fontWeight: 600 }}>{incident.service}</td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{
                        color: incident.response_status_code >= 500 ? 'var(--danger)' : 'var(--warning)',
                        fontWeight: 700,
                        marginRight: '0.5rem',
                        fontFamily: 'var(--font-mono)'
                      }}>
                        {incident.request_method}
                      </span>
                      <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{incident.request_path}</span>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--foreground)' }}>{incident.error_type}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '250px' }}>
                        {incident.error_message}
                      </div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span className="badge" style={{
                        color: getStatusColor(incident.status),
                        backgroundColor: `rgba(255,255,255,0.01)`,
                        borderColor: getStatusColor(incident.status)
                      }}>
                        {incident.status}
                      </span>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {new Date(incident.ingested_at).toLocaleString()}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <Link href={`/incidents/${incident.id}`} style={{
                        display: 'inline-block',
                        padding: '0.375rem 0.75rem',
                        backgroundColor: 'rgba(56, 189, 248, 0.05)',
                        color: 'var(--primary)',
                        border: '1px solid rgba(56, 189, 248, 0.2)',
                        borderRadius: '4px',
                        fontSize: '0.8rem',
                        fontWeight: 600
                      }}>
                        Investigate &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
