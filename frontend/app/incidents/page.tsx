'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Incident } from '../../types';
import { apiClient } from '../../lib/api-client';

export default function IncidentsListPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [filteredIncidents, setFilteredIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [serviceFilter, setServiceFilter] = useState('ALL');
  const [envFilter, setEnvFilter] = useState('ALL');

  async function loadIncidents() {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getIncidents();
      setIncidents(data);
      setFilteredIncidents(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to fetch incidents list.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadIncidents();
  }, []);

  // Filter application trigger
  useEffect(() => {
    let filtered = [...incidents];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(i => 
        i.id.toLowerCase().includes(query) || 
        i.service.toLowerCase().includes(query) || 
        i.error_type.toLowerCase().includes(query) || 
        i.error_message.toLowerCase().includes(query) ||
        i.request_path.toLowerCase().includes(query)
      );
    }

    if (statusFilter !== 'ALL') {
      filtered = filtered.filter(i => i.status === statusFilter);
    }

    if (serviceFilter !== 'ALL') {
      filtered = filtered.filter(i => i.service === serviceFilter);
    }

    if (envFilter !== 'ALL') {
      filtered = filtered.filter(i => i.environment === envFilter);
    }

    setFilteredIncidents(filtered);
  }, [searchQuery, statusFilter, serviceFilter, envFilter, incidents]);

  // Extract unique filter categories
  const servicesList = Array.from(new Set(incidents.map(i => i.service)));
  const envsList = Array.from(new Set(incidents.map(i => i.environment)));

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
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}>Incidents Inventory</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Filter, inspect, and trace all failure logs recorded from active integrations.</p>
      </div>

      {/* Filters Bar */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem',
        alignItems: 'center',
        padding: '1.25rem',
        backgroundColor: 'var(--panel-bg)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        marginBottom: '2rem'
      }}>
        {/* Search */}
        <div style={{ flex: 1, minWidth: '220px' }}>
          <input 
            type="text" 
            placeholder="Search by ID, exception, route, message..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
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

        {/* Status Filter */}
        <div>
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--card-bg)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '0.5rem 1.5rem 0.5rem 0.75rem',
              color: 'var(--foreground)',
              fontSize: '0.875rem',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="RECEIVED">RECEIVED</option>
            <option value="ANALYZING">ANALYZING</option>
            <option value="REPRODUCING">REPRODUCING</option>
            <option value="VERIFYING">VERIFYING</option>
            <option value="FIXED">FIXED</option>
            <option value="FAILED">FAILED</option>
          </select>
        </div>

        {/* Service Filter */}
        <div>
          <select 
            value={serviceFilter} 
            onChange={(e) => setServiceFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--card-bg)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '0.5rem 1.5rem 0.5rem 0.75rem',
              color: 'var(--foreground)',
              fontSize: '0.875rem',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Services</option>
            {servicesList.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {/* Environment Filter */}
        <div>
          <select 
            value={envFilter} 
            onChange={(e) => setEnvFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--card-bg)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '0.5rem 1.5rem 0.5rem 0.75rem',
              color: 'var(--foreground)',
              fontSize: '0.875rem',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Environments</option>
            {envsList.map(env => <option key={env} value={env}>{env}</option>)}
          </select>
        </div>
      </div>

      {/* List content */}
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
          Loading incident records...
        </div>
      ) : filteredIncidents.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '5rem 2rem',
          backgroundColor: 'var(--panel-bg)',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          color: 'var(--text-muted)'
        }}>
          <h3 style={{ color: 'var(--foreground)', marginBottom: '0.5rem' }}>No matching records</h3>
          <p style={{ fontSize: '0.875rem' }}>Try clearing filters or queries to broaden search boundaries.</p>
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
                <th style={{ padding: '1rem' }}>Incident ID</th>
                <th style={{ padding: '1rem' }}>Service</th>
                <th style={{ padding: '1rem' }}>Environment</th>
                <th style={{ padding: '1rem' }}>Endpoint</th>
                <th style={{ padding: '1rem' }}>Exception / Message</th>
                <th style={{ padding: '1rem' }}>Status</th>
                <th style={{ padding: '1rem' }}>Ingested At</th>
                <th style={{ padding: '1rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredIncidents.map((incident) => (
                <tr key={incident.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '1rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                    {incident.id}
                  </td>
                  <td style={{ padding: '1rem', fontWeight: 600 }}>{incident.service}</td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{
                      backgroundColor: 'rgba(255,255,255,0.03)',
                      border: '1px solid var(--border)',
                      padding: '0.2rem 0.4rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      color: 'var(--text-dim)'
                    }}>{incident.environment}</span>
                  </td>
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
                      borderColor: getStatusColor(incident.status),
                      backgroundColor: 'rgba(255,255,255,0.01)'
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
                      Investigate
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
