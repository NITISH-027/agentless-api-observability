'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Incident } from '../../types';
import { apiClient } from '../../lib/api-client';

export default function InvestigationsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadInvestigations() {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getIncidents();
      setIncidents(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load investigations.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInvestigations();
  }, []);

  const activeInvestigations = incidents.filter(i => 
    i.status === 'ANALYZING' || i.status === 'REPRODUCING' || i.status === 'VERIFYING'
  );

  const completedInvestigations = incidents.filter(i => 
    i.status === 'FIXED' || i.status === 'FAILED'
  );

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
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}>Active Investigations</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Monitor the pipeline state of current failure isolation, code repair, and test loops.</p>
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
          Loading active pipelines...
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2.5rem', alignItems: 'flex-start' }}>
          {/* Active section */}
          <div style={{
            backgroundColor: 'var(--panel-bg)',
            border: '1px solid var(--border)',
            padding: '1.5rem',
            borderRadius: '8px'
          }}>
            <h2 style={{ fontSize: '1.1rem', marginBottom: '1.25rem', color: 'var(--warning)' }}>Running Pipelines ({activeInvestigations.length})</h2>

            {activeInvestigations.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '3rem 2rem',
                color: 'var(--text-muted)',
                border: '1px dashed var(--border)',
                borderRadius: '6px'
              }}>
                No running debugging tasks.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {activeInvestigations.map(i => (
                  <div key={i.id} style={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--border)',
                    padding: '1rem',
                    borderRadius: '6px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>#{i.id.slice(0, 12)}</span>
                      <span className="badge badge-warning">{i.status}</span>
                    </div>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.25rem' }}>{i.service}</h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '0.75rem' }}>
                      {i.request_method} {i.request_path}
                    </p>
                    <Link href={`/incidents/${i.id}`} style={{
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      color: 'var(--primary)'
                    }}>
                      View Progress Live &rarr;
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Completed section */}
          <div style={{
            backgroundColor: 'var(--panel-bg)',
            border: '1px solid var(--border)',
            padding: '1.5rem',
            borderRadius: '8px'
          }}>
            <h2 style={{ fontSize: '1.1rem', marginBottom: '1.25rem', color: 'var(--success)' }}>Completed Pipelines ({completedInvestigations.length})</h2>

            {completedInvestigations.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '3rem 2rem',
                color: 'var(--text-muted)',
                border: '1px dashed var(--border)',
                borderRadius: '6px'
              }}>
                No completed pipeline runs.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {completedInvestigations.map(i => (
                  <div key={i.id} style={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--border)',
                    padding: '1rem',
                    borderRadius: '6px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>#{i.id.slice(0, 12)}</span>
                      <span className="badge" style={{
                        color: getStatusColor(i.status),
                        borderColor: getStatusColor(i.status),
                        backgroundColor: 'rgba(255,255,255,0.01)'
                      }}>{i.status}</span>
                    </div>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.25rem' }}>{i.service}</h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '0.75rem' }}>
                      {i.request_method} {i.request_path}
                    </p>
                    <Link href={`/incidents/${i.id}`} style={{
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      color: 'var(--primary)'
                    }}>
                      View Details &rarr;
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
