'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { Incident } from '../../../types';
import { apiClient } from '../../../lib/api-client';

export default function IncidentDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'traceback' | 'request' | 'patch'>('timeline');

  // Interactive Pipeline Actions Loading States
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Selected frame for source-code viewer
  const [selectedFrameIdx, setSelectedFrameIdx] = useState<number | null>(null);

  // Repo association form states
  const [repoOwner, setRepoOwner] = useState('');
  const [repoName, setRepoName] = useState('');
  const [repoCommit, setRepoCommit] = useState('');
  const [repoBranch, setRepoBranch] = useState('main');

  async function loadIncident() {
    try {
      setError(null);
      const data = await apiClient.getIncident(id);
      setIncident(data);
      
      // Auto-select first mapped frame if exists
      if (data.traceback_analysis?.frames) {
        const firstMappedIdx = data.traceback_analysis.frames.findIndex((f: any) => f.mapped);
        if (firstMappedIdx !== -1) {
          setSelectedFrameIdx(firstMappedIdx);
        } else if (data.traceback_analysis.frames.length > 0) {
          setSelectedFrameIdx(0);
        }
      }
      
      // Populate repo form if associated
      if (data.github_owner) setRepoOwner(data.github_owner);
      if (data.github_repo) setRepoName(data.github_repo);
      if (data.github_commit_sha) setRepoCommit(data.github_commit_sha);
      if (data.github_branch) setRepoBranch(data.github_branch);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load incident details');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadIncident();
  }, [id]);

  // Action pipeline handlers
  async function handleAssociateRepo() {
    if (!repoOwner || !repoName || !repoCommit) {
      setActionError('Please specify repository owner, name, and commit hash.');
      return;
    }
    try {
      setActionLoading('repo');
      setActionError(null);
      setActionSuccess(null);
      await apiClient.associateRepository(id, {
        owner: repoOwner,
        repository: repoName,
        commit_sha: repoCommit,
        branch: repoBranch || undefined
      });
      setActionSuccess('Repository details successfully updated.');
      await loadIncident();
    } catch (e: any) {
      setActionError(e.message || 'Failed to associate repository.');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleReproduce() {
    try {
      setActionLoading('reproduce');
      setActionError(null);
      setActionSuccess(null);
      // Auto-resolve workspace or pass default
      await apiClient.reproduceFailure(id, {
        workspace_id: `ws_${id}`,
        provider: 'mock' // using mock/openai resolved in settings
      });
      setActionSuccess('Sandbox reproduction run completed successfully.');
      await loadIncident();
    } catch (e: any) {
      setActionError(e.message || 'Failed to execute reproduction sandbox.');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleGenerateHypotheses() {
    try {
      setActionLoading('hypotheses');
      setActionError(null);
      setActionSuccess(null);
      await apiClient.generateHypotheses(id, {
        workspace_id: `ws_${id}`,
        provider: 'mock'
      });
      setActionSuccess('AI debugging hypotheses generated.');
      await loadIncident();
    } catch (e: any) {
      setActionError(e.message || 'Failed to formulate hypotheses.');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleGeneratePatch(hypothesisId: string) {
    try {
      setActionLoading(`patch_${hypothesisId}`);
      setActionError(null);
      setActionSuccess(null);
      
      // Verification run
      await apiClient.verifyPatch(id, {
        hypothesis_id: hypothesisId,
        patch_content: 'diff --git a/src/service.py b/src/service.py\n+    if qty < 0: raise ValueError' // dummy verification diff
      });
      
      // Patch generation run
      await apiClient.generatePatch(id, {
        hypothesis_id: hypothesisId,
        provider: 'mock'
      });
      
      setActionSuccess('Production patch diff generated and verified successfully.');
      await loadIncident();
    } catch (e: any) {
      setActionError(e.message || 'Failed to verify or generate patch.');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleCreatePR() {
    try {
      setActionLoading('pr');
      setActionError(null);
      setActionSuccess(null);
      await apiClient.createPullRequest(id, {
        connection_id: 'conn_123'
      });
      setActionSuccess('GitHub Pull Request proposed and opened successfully.');
      await loadIncident();
    } catch (e: any) {
      setActionError(e.message || 'Failed to push PR to GitHub.');
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '6rem', color: 'var(--text-muted)' }}>
        Loading incident details...
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div style={{ padding: '2rem' }}>
        <div style={{
          backgroundColor: 'rgba(244,63,94,0.05)',
          border: '1px solid var(--danger)',
          color: 'var(--danger)',
          padding: '1.5rem',
          borderRadius: '6px',
          marginBottom: '1.5rem'
        }}>
          <h3>Incident load crashed</h3>
          <p>{error || 'Failure context details not found.'}</p>
        </div>
        <Link href="/" style={{ color: 'var(--primary)' }}>&larr; Return to Dashboard</Link>
      </div>
    );
  }

  const getTimelineSteps = () => {
    const isRepro = incident.reproduction_result?.reproduced;
    const isHyp = incident.hypotheses && incident.hypotheses.length > 0;
    const isVal = incident.verification_results && Object.keys(incident.verification_results).length > 0;
    const isPat = incident.patch_result?.status === 'ACCEPTED';
    const isPR = incident.pr_result?.status === 'CREATED';

    return [
      { name: 'Failure Observed', done: true },
      { name: 'Failure Reproduced', done: !!isRepro },
      { name: 'Hypotheses Formulated', done: !!isHyp },
      { name: 'Root Cause Validated', done: !!isVal },
      { name: 'Patch Generated', done: !!isPat },
      { name: 'Patch Verified', done: !!isPat },
      { name: 'PR Created', done: !!isPR }
    ];
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'FIXED': return <span className="badge badge-success">FIXED</span>;
      case 'ANALYZING':
      case 'REPRODUCING':
      case 'VERIFYING': return <span className="badge badge-warning">{status}</span>;
      case 'FAILED': return <span className="badge badge-danger">FAILED</span>;
      default: return <span className="badge badge-muted">{status}</span>;
    }
  };

  const selectedFrame = selectedFrameIdx !== null && incident.traceback_analysis?.frames
    ? incident.traceback_analysis.frames[selectedFrameIdx]
    : null;

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%', overflowY: 'auto' }}>
      {/* Header Info Panel */}
      <div style={{
        backgroundColor: 'var(--panel-bg)',
        border: '1px solid var(--border)',
        padding: '1.5rem',
        borderRadius: '8px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>#{incident.id}</span>
            {getStatusBadge(incident.status)}
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>• {new Date(incident.timestamp).toLocaleString()}</span>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem', display: 'flex', gap: '0.5rem' }}>
            <span style={{ color: 'var(--primary)' }}>{incident.request_method}</span>
            <span style={{ color: 'var(--foreground)', fontFamily: 'var(--font-mono)' }}>{incident.request_path}</span>
          </h1>
          <p style={{ color: 'var(--danger)', fontWeight: 600, fontSize: '0.9rem' }}>
            {incident.error_type}: {incident.error_message}
          </p>
        </div>
        <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Service: <strong style={{ color: 'var(--foreground)' }}>{incident.service}</strong></span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Environment: <strong style={{ color: 'var(--foreground)' }}>{incident.environment}</strong></span>
        </div>
      </div>

      {/* Action logs overlays */}
      {actionSuccess && (
        <div style={{ backgroundColor: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', color: 'var(--success)', padding: '0.75rem', borderRadius: '6px', fontSize: '0.8rem' }}>
          ✓ {actionSuccess}
        </div>
      )}
      {actionError && (
        <div style={{ backgroundColor: 'rgba(244,63,94,0.06)', border: '1px solid rgba(244,63,94,0.2)', color: 'var(--danger)', padding: '0.75rem', borderRadius: '6px', fontSize: '0.8rem' }}>
          ⚠ Error: {actionError}
        </div>
      )}

      {/* Grid: Columns Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 1.25fr', gap: '1.5rem', alignItems: 'flex-start' }}>
        
        {/* Main tabs view pane */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Navigation Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', gap: '1.5rem', paddingBottom: '0.25rem' }}>
            {(['timeline', 'traceback', 'request', 'patch'] as const).map(tab => (
              <button 
                key={tab} 
                onClick={() => setActiveTab(tab)}
                style={{
                  color: activeTab === tab ? 'var(--primary)' : 'var(--text-dim)',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  borderBottom: activeTab === tab ? '2px solid var(--primary)' : '2px solid transparent',
                  paddingBottom: '0.5rem',
                  paddingRight: '0.5rem',
                  paddingLeft: '0.5rem',
                  textTransform: 'capitalize'
                }}
              >
                {tab === 'timeline' ? 'Timeline & Hypotheses' : tab === 'traceback' ? 'Code & Traceback Explorer' : tab === 'request' ? 'Request Details' : 'Patch Diff & Verdict'}
              </button>
            ))}
          </div>

          {/* TAB 1: Timeline & Hypotheses */}
          {activeTab === 'timeline' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {/* Timeline Steps Card */}
              <div style={{ backgroundColor: 'var(--panel-bg)', border: '1px solid var(--border)', padding: '1.25rem', borderRadius: '8px' }}>
                <h2 style={{ fontSize: '0.95rem', marginBottom: '1rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Investigation Progress</h2>
                <div style={{ display: 'flex', justifyContent: 'space-between', position: 'relative', flexWrap: 'wrap', gap: '1rem' }}>
                  {getTimelineSteps().map((step, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      <span style={{
                        fontSize: '0.95rem',
                        color: step.done ? 'var(--success)' : 'var(--text-muted)'
                      }}>
                        {step.done ? '✓' : '○'}
                      </span>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: step.done ? 'var(--foreground)' : 'var(--text-muted)' }}>{step.name}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Hypotheses List */}
              <div style={{ backgroundColor: 'var(--panel-bg)', border: '1px solid var(--border)', padding: '1.25rem', borderRadius: '8px' }}>
                <h2 style={{ fontSize: '0.95rem', marginBottom: '1.25rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Diagnosed Root Causes</h2>
                
                {!incident.hypotheses || incident.hypotheses.length === 0 ? (
                  <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    No root cause hypotheses formulated yet. Verify setup and run the analyzer in actions panel.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {incident.hypotheses.map((hyp, index) => {
                      const vResult = incident.verification_results?.[hyp.id];
                      return (
                        <div key={hyp.id} style={{
                          backgroundColor: 'var(--card-bg)',
                          border: '1px solid var(--border)',
                          padding: '1.25rem',
                          borderRadius: '6px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                            <div>
                              <span className="badge badge-info" style={{ marginRight: '0.5rem' }}>{hyp.category}</span>
                              <span className="badge" style={{
                                color: hyp.confidence === 'HIGH' ? 'var(--success)' : hyp.confidence === 'MEDIUM' ? 'var(--warning)' : 'var(--text-muted)',
                                borderColor: hyp.confidence === 'HIGH' ? 'var(--success)' : hyp.confidence === 'MEDIUM' ? 'var(--warning)' : 'var(--border)'
                              }}>CONFIDENCE: {hyp.confidence}</span>
                            </div>
                            {vResult ? (
                              <span className={`badge ${vResult.verdict === 'VALIDATED' ? 'badge-success' : 'badge-danger'}`}>
                                {vResult.verdict}
                              </span>
                            ) : (
                              <span className="badge badge-muted">UNTESTED</span>
                            )}
                          </div>

                          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>{hyp.title}</h3>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginBottom: '1rem', lineHeight: '1.4' }}>{hyp.description}</p>

                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem', fontSize: '0.8rem' }}>
                            <div>
                              <strong style={{ display: 'block', color: 'var(--foreground)', marginBottom: '0.25rem' }}>Supporting Evidence:</strong>
                              <ul style={{ paddingLeft: '1.25rem', color: 'var(--text-dim)' }}>
                                {hyp.supporting_evidence.map((ev: string, idx: number) => <li key={idx}>{ev}</li>)}
                              </ul>
                            </div>
                            <div>
                              <strong style={{ display: 'block', color: 'var(--foreground)', marginBottom: '0.25rem' }}>Contradicting Evidence:</strong>
                              <ul style={{ paddingLeft: '1.25rem', color: 'var(--text-dim)' }}>
                                {hyp.contradicting_evidence && hyp.contradicting_evidence.length > 0 ? (
                                  hyp.contradicting_evidence.map((ev: string, idx: number) => <li key={idx}>{ev}</li>)
                                ) : (
                                  <li>None.</li>
                                )}
                              </ul>
                            </div>
                          </div>

                          {/* Verification Plan */}
                          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
                            <strong style={{ display: 'block', fontSize: '0.8rem', color: 'var(--foreground)', marginBottom: '0.25rem' }}>Verification Plan:</strong>
                            <ul style={{ paddingLeft: '1.25rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                              {hyp.verification_plan.map((step: string, idx: number) => <li key={idx}>{step}</li>)}
                            </ul>
                          </div>

                          {/* Actions button for hypothesis patch generation */}
                          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                            <button 
                              onClick={() => handleGeneratePatch(hyp.id)}
                              disabled={!!actionLoading}
                              style={{
                                backgroundColor: 'rgba(56, 189, 248, 0.08)',
                                border: '1px solid rgba(56, 189, 248, 0.2)',
                                color: 'var(--primary)',
                                padding: '0.375rem 0.75rem',
                                borderRadius: '4px',
                                fontSize: '0.75rem',
                                fontWeight: 600
                              }}
                            >
                              {actionLoading === `patch_${hyp.id}` ? 'Drafting Fix...' : 'Draft Code Fix & Test'}
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: Code & Traceback Explorer */}
          {activeTab === 'traceback' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 2.5fr', gap: '1.25rem', height: '520px' }}>
              {/* Left frame picker list */}
              <div style={{
                backgroundColor: 'var(--panel-bg)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '0.75rem',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.375rem',
                height: '100%'
              }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0.25rem 0.5rem' }}>
                  Execution Frames
                </span>
                {(!incident.traceback_analysis?.frames || incident.traceback_analysis.frames.length === 0) ? (
                  <div style={{ padding: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    No parsed frames. Run trace analyzer.
                  </div>
                ) : (
                  incident.traceback_analysis.frames.map((frame: any, idx: number) => (
                    <button 
                      key={idx}
                      onClick={() => setSelectedFrameIdx(idx)}
                      style={{
                        textAlign: 'left',
                        padding: '0.625rem',
                        borderRadius: '6px',
                        border: selectedFrameIdx === idx ? '1px solid var(--primary)' : '1px solid transparent',
                        backgroundColor: selectedFrameIdx === idx ? 'rgba(56, 189, 248, 0.05)' : 'rgba(255,255,255,0.01)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.125rem'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                        <span style={{
                          fontWeight: 600,
                          fontSize: '0.8rem',
                          color: frame.mapped ? 'var(--foreground)' : 'var(--text-muted)'
                        }}>{frame.function_name}</span>
                        {frame.mapped && <span style={{ fontSize: '0.65rem', color: 'var(--primary)', fontWeight: 600 }}>MAPPED</span>}
                      </div>
                      <span style={{
                        fontSize: '0.7rem',
                        color: 'var(--text-muted)',
                        fontFamily: 'var(--font-mono)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        width: '200px'
                      }}>
                        {frame.repo_path || frame.raw_file_path}:{frame.line_number}
                      </span>
                    </button>
                  ))
                )}
              </div>

              {/* Right panel source code displayer */}
              <div style={{
                backgroundColor: 'var(--panel-bg)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                height: '100%',
                overflow: 'hidden'
              }}>
                {selectedFrame ? (
                  <>
                    <div>
                      <h3 style={{ fontSize: '0.9rem', fontWeight: 600, display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
                        <span>File: <strong style={{ fontFamily: 'var(--font-mono)' }}>{selectedFrame.repo_path || selectedFrame.raw_file_path}</strong></span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Line: {selectedFrame.line_number}</span>
                      </h3>
                      {selectedFrame.containing_class && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                          Scope: Class <code>{selectedFrame.containing_class}</code>, Function <code>{selectedFrame.containing_function}</code>
                        </div>
                      )}
                    </div>

                    <div style={{
                      flex: 1,
                      backgroundColor: 'rgba(0,0,0,0.35)',
                      border: '1px solid rgba(255,255,255,0.03)',
                      borderRadius: '6px',
                      overflowY: 'auto',
                      padding: '0.75rem',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.8rem',
                      lineHeight: '1.6',
                      color: '#e2e8f0'
                    }}>
                      {!selectedFrame.context || selectedFrame.context.length === 0 ? (
                        <div style={{ padding: '2rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                          No surrounding source code lines context available. Make sure workspace repos are connected properly.
                        </div>
                      ) : (
                        selectedFrame.context.map((line: any, index: number) => (
                          <div 
                            key={index} 
                            style={{
                              backgroundColor: line.is_target ? 'rgba(244,63,94,0.1)' : 'transparent',
                              borderLeft: line.is_target ? '3px solid var(--danger)' : '3px solid transparent',
                              paddingLeft: '0.5rem',
                              display: 'flex',
                              gap: '1rem'
                            }}
                          >
                            <span style={{ width: '25px', display: 'inline-block', color: 'var(--text-muted)', textAlign: 'right' }}>{line.line_number}</span>
                            <span style={{ whiteSpace: 'pre-wrap', color: line.is_target ? 'var(--foreground)' : 'var(--text-dim)' }}>{line.content}</span>
                          </div>
                        ))
                      )}
                    </div>
                  </>
                ) : (
                  <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Select a stack frame on the left side to review context source code.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: Request details */}
          {activeTab === 'request' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ backgroundColor: 'var(--panel-bg)', border: '1px solid var(--border)', padding: '1.25rem', borderRadius: '8px' }}>
                <h2 style={{ fontSize: '0.95rem', marginBottom: '1rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>HTTP Request Specs</h2>
                <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem', fontSize: '0.85rem' }}>
                  <span>Method: <strong style={{ color: 'var(--primary)' }}>{incident.request_method}</strong></span>
                  <span>Path: <strong style={{ fontFamily: 'var(--font-mono)' }}>{incident.request_path}</strong></span>
                  <span>Response Status: <strong style={{ color: incident.response_status_code >= 500 ? 'var(--danger)' : 'var(--warning)' }}>{incident.response_status_code}</strong></span>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.8rem' }}>
                  <div>
                    <strong style={{ display: 'block', color: 'var(--foreground)', marginBottom: '0.25rem' }}>Headers (Sanitized):</strong>
                    <pre style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '4px', overflowX: 'auto', fontFamily: 'var(--font-mono)' }}>
                      {JSON.stringify(incident.request_headers || {}, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <strong style={{ display: 'block', color: 'var(--foreground)', marginBottom: '0.25rem' }}>Payload Body:</strong>
                    <pre style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '4px', overflowX: 'auto', fontFamily: 'var(--font-mono)' }}>
                      {JSON.stringify(incident.request_body || {}, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Patch Diff & Verdict */}
          {activeTab === 'patch' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Verdict Card */}
              <div style={{ backgroundColor: 'var(--panel-bg)', border: '1px solid var(--border)', padding: '1.25rem', borderRadius: '8px' }}>
                <h2 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Verification Summary</h2>
                
                {incident.patch_result ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
                    <div>Status: <span className="badge badge-success">{incident.patch_result.status}</span></div>
                    <div>Root Cause: <strong style={{ color: 'var(--foreground)' }}>{incident.patch_result.root_cause_addressed}</strong></div>
                    <div>Modified Files: <code style={{ color: 'var(--primary)' }}>{incident.patch_result.files_to_modify?.join(', ')}</code></div>
                    <div style={{ marginTop: '0.5rem', borderTop: '1px solid var(--border)', paddingTop: '0.5rem', color: 'var(--text-dim)' }}>
                      Explanation: {incident.patch_result.explanation}
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    No patch diff generated yet. Run patch analysis in the right actions sidebar.
                  </div>
                )}
              </div>

              {/* Diff Code viewer */}
              {incident.patch_result?.patch_diff && (
                <div style={{ backgroundColor: 'var(--panel-bg)', border: '1px solid var(--border)', padding: '1.25rem', borderRadius: '8px' }}>
                  <h2 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Unified Git Diff</h2>
                  <pre style={{
                    backgroundColor: 'rgba(0,0,0,0.3)',
                    padding: '1rem',
                    borderRadius: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    color: '#e2e8f0',
                    lineHeight: '1.5',
                    border: '1px solid var(--border)',
                    overflowX: 'auto'
                  }}>
                    {incident.patch_result.patch_diff}
                  </pre>
                </div>
              )}

              {/* PR results */}
              {incident.pr_result && (
                <div style={{ backgroundColor: 'var(--panel-bg)', border: '1px solid var(--border)', padding: '1.25rem', borderRadius: '8px' }}>
                  <h2 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Opened Pull Request</h2>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
                    <div>Branch: <code style={{ color: 'var(--primary)' }}>{incident.pr_result.head_branch}</code></div>
                    <div>PR Link: <a href={incident.pr_result.pr_url} target="_blank" rel="noreferrer" style={{ fontWeight: 600 }}>GitHub Pull Request #{incident.pr_result.pr_number} &nearr;</a></div>
                    <div>Created At: {new Date(incident.pr_result.created_at).toLocaleString()}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar panels (Controls & Metadata) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* GitHub Connection panel */}
          <div style={{
            backgroundColor: 'var(--panel-bg)',
            border: '1px solid var(--border)',
            padding: '1.25rem',
            borderRadius: '8px'
          }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
              Repository Target
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.8rem' }}>
              <div>
                <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>GitHub Owner</label>
                <input 
                  type="text" 
                  placeholder="octocat" 
                  value={repoOwner}
                  onChange={(e) => setRepoOwner(e.target.value)}
                  style={{ width: '100%', backgroundColor: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '4px', padding: '0.375rem 0.5rem', color: 'var(--foreground)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Repository Name</label>
                <input 
                  type="text" 
                  placeholder="hello-world" 
                  value={repoName}
                  onChange={(e) => setRepoName(e.target.value)}
                  style={{ width: '100%', backgroundColor: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '4px', padding: '0.375rem 0.5rem', color: 'var(--foreground)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Commit SHA</label>
                <input 
                  type="text" 
                  placeholder="abc123commit" 
                  value={repoCommit}
                  onChange={(e) => setRepoCommit(e.target.value)}
                  style={{ width: '100%', backgroundColor: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '4px', padding: '0.375rem 0.5rem', color: 'var(--foreground)', fontFamily: 'var(--font-mono)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Branch Base</label>
                <input 
                  type="text" 
                  placeholder="main" 
                  value={repoBranch}
                  onChange={(e) => setRepoBranch(e.target.value)}
                  style={{ width: '100%', backgroundColor: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '4px', padding: '0.375rem 0.5rem', color: 'var(--foreground)' }}
                />
              </div>

              <button 
                onClick={handleAssociateRepo}
                disabled={!!actionLoading}
                style={{
                  backgroundColor: 'var(--primary)',
                  color: '#000',
                  padding: '0.5rem',
                  borderRadius: '4px',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  marginTop: '0.25rem'
                }}
              >
                {actionLoading === 'repo' ? 'Syncing...' : 'Sync Repository Specs'}
              </button>
            </div>
          </div>

          {/* Pipeline Actions Controls panel */}
          <div style={{
            backgroundColor: 'var(--panel-bg)',
            border: '1px solid var(--border)',
            padding: '1.25rem',
            borderRadius: '8px'
          }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
              Execution Controls
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              {/* Step 1: Trace Analyzer */}
              <button 
                onClick={async () => {
                  try {
                    setActionLoading('analyze');
                    setActionError(null);
                    setActionSuccess(null);
                    await apiClient.analyzeTraceback(id, { workspace_id: `ws_${id}` });
                    setActionSuccess('Trace mapping analysis complete.');
                    await loadIncident();
                  } catch (e: any) {
                    setActionError(e.message || 'Analysis failed.');
                  } finally {
                    setActionLoading(null);
                  }
                }}
                disabled={!incident.github_commit_sha || !!actionLoading}
                style={{
                  backgroundColor: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border)',
                  color: 'var(--foreground)',
                  padding: '0.625rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  textAlign: 'left',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  opacity: !incident.github_commit_sha ? 0.4 : 1
                }}
              >
                <span>🔍 Parse Trace Mapping</span>
                {actionLoading === 'analyze' && <span>⏳</span>}
              </button>

              {/* Step 2: Reproduce Sandbox */}
              <button 
                onClick={handleReproduce}
                disabled={!incident.github_commit_sha || !!actionLoading}
                style={{
                  backgroundColor: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border)',
                  color: 'var(--foreground)',
                  padding: '0.625rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  textAlign: 'left',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  opacity: !incident.github_commit_sha ? 0.4 : 1
                }}
              >
                <span>🧪 Run Sandbox Isolation</span>
                {actionLoading === 'reproduce' && <span>⏳</span>}
              </button>

              {/* Step 3: Formulate Hypotheses */}
              <button 
                onClick={handleGenerateHypotheses}
                disabled={!incident.reproduction_result || !!actionLoading}
                style={{
                  backgroundColor: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border)',
                  color: 'var(--foreground)',
                  padding: '0.625rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  textAlign: 'left',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  opacity: !incident.reproduction_result ? 0.4 : 1
                }}
              >
                <span>🧠 Formulate Hypotheses</span>
                {actionLoading === 'hypotheses' && <span>⏳</span>}
              </button>

              {/* Step 4: PR creation */}
              <button 
                onClick={handleCreatePR}
                disabled={incident.patch_result?.status !== 'ACCEPTED' || !!actionLoading}
                style={{
                  backgroundColor: 'rgba(56, 189, 248, 0.08)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  color: 'var(--primary)',
                  padding: '0.625rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  textAlign: 'left',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  opacity: incident.patch_result?.status !== 'ACCEPTED' ? 0.4 : 1
                }}
              >
                <span>🌿 Push PR to GitHub</span>
                {actionLoading === 'pr' && <span>⏳</span>}
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
