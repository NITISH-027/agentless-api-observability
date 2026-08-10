'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api-client';

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [token, setToken] = useState('');
  const [owner, setOwner] = useState('');
  const [repo, setRepo] = useState('');
  const [connectionId, setConnectionId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  async function loadRepositories() {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getRepositories();
      setRepositories(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to fetch connected repositories list.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRepositories();
  }, []);

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !owner || !repo) {
      setError('Please fill in token, owner, and repository fields.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setSuccessMsg(null);

      await apiClient.connectGithub({
        token,
        owner,
        repo,
        connection_id: connectionId || undefined
      });

      setSuccessMsg(`Successfully connected to GitHub repository ${owner}/${repo}.`);
      setToken('');
      setOwner('');
      setRepo('');
      setConnectionId('');
      
      // Reload lists
      await loadRepositories();
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to authenticate and connect to repository.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ padding: '2rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}>GitHub Integration</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Link your GitHub repositories using Personal Access Tokens to map trace exception scopes.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2.5rem', alignItems: 'flex-start' }}>
        {/* Form panel */}
        <div style={{
          backgroundColor: 'var(--panel-bg)',
          border: '1px solid var(--border)',
          padding: '1.5rem',
          borderRadius: '8px'
        }}>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1.25rem' }}>Connect Repository</h2>

          {successMsg && (
            <div style={{
              backgroundColor: 'rgba(16, 185, 129, 0.06)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              color: 'var(--success)',
              padding: '0.75rem',
              borderRadius: '6px',
              marginBottom: '1rem',
              fontSize: '0.8rem'
            }}>
              {successMsg}
            </div>
          )}

          {error && (
            <div style={{
              backgroundColor: 'rgba(244, 63, 94, 0.06)',
              border: '1px solid rgba(244, 63, 94, 0.2)',
              color: 'var(--danger)',
              padding: '0.75rem',
              borderRadius: '6px',
              marginBottom: '1rem',
              fontSize: '0.8rem'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleConnect} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, marginBottom: '0.375rem' }}>
                GitHub Token
              </label>
              <input 
                type="password" 
                placeholder="ghp_..." 
                value={token}
                onChange={(e) => setToken(e.target.value)}
                style={{
                  width: '100%',
                  backgroundColor: 'var(--card-bg)',
                  border: '1px solid var(--border)',
                  borderRadius: '6px',
                  padding: '0.5rem 0.75rem',
                  color: 'var(--foreground)',
                  fontSize: '0.875rem'
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, marginBottom: '0.375rem' }}>
                  Owner
                </label>
                <input 
                  type="text" 
                  placeholder="octocat" 
                  value={owner}
                  onChange={(e) => setOwner(e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '0.5rem 0.75rem',
                    color: 'var(--foreground)',
                    fontSize: '0.875rem'
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, marginBottom: '0.375rem' }}>
                  Repository Name
                </label>
                <input 
                  type="text" 
                  placeholder="hello-world" 
                  value={repo}
                  onChange={(e) => setRepo(e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '0.5rem 0.75rem',
                    color: 'var(--foreground)',
                    fontSize: '0.875rem'
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, marginBottom: '0.375rem' }}>
                Connection ID (Optional)
              </label>
              <input 
                type="text" 
                placeholder="e.g. primary-repo" 
                value={connectionId}
                onChange={(e) => setConnectionId(e.target.value)}
                style={{
                  width: '100%',
                  backgroundColor: 'var(--card-bg)',
                  border: '1px solid var(--border)',
                  borderRadius: '6px',
                  padding: '0.5rem 0.75rem',
                  color: 'var(--foreground)',
                  fontSize: '0.875rem'
                }}
              />
            </div>

            <button type="submit" disabled={submitting} style={{
              backgroundColor: 'var(--primary)',
              color: '#000',
              padding: '0.625rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: 600,
              textAlign: 'center',
              display: 'block',
              width: '100%',
              marginTop: '0.5rem',
              opacity: submitting ? 0.6 : 1
            }}>
              {submitting ? 'Connecting...' : 'Authorize & Connect'}
            </button>
          </form>
        </div>

        {/* Repositories List panel */}
        <div style={{
          backgroundColor: 'var(--panel-bg)',
          border: '1px solid var(--border)',
          padding: '1.5rem',
          borderRadius: '8px'
        }}>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1.25rem' }}>Connected Repositories</h2>

          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading connected repositories...
            </div>
          ) : repositories.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '3rem 2rem',
              color: 'var(--text-muted)',
              border: '1px dashed var(--border)',
              borderRadius: '6px'
            }}>
              No repositories connected yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {repositories.map((repoObj, idx) => (
                <div key={idx} style={{
                  backgroundColor: 'var(--card-bg)',
                  border: '1px solid var(--border)',
                  padding: '1rem',
                  borderRadius: '6px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                      {repoObj.full_name || `${repoObj.owner}/${repoObj.name}`}
                    </h3>
                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      <span>Stars: {repoObj.stargazers_count || 0}</span>
                      <span>Forks: {repoObj.forks_count || 0}</span>
                      {repoObj.connection_id && <span>Connection ID: <strong style={{ color: 'var(--primary)' }}>{repoObj.connection_id}</strong></span>}
                    </div>
                  </div>
                  <span className="badge badge-success">CONNECTED</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
