export type InvestigationStatus = 'RECEIVED' | 'ANALYZING' | 'REPRODUCING' | 'VERIFYING' | 'FIXED' | 'FAILED';

export interface RequestInfo {
  method: string;
  path: string;
  query?: Record<string, any>;
  headers?: Record<string, string>;
  body?: any;
}

export interface ResponseInfo {
  status_code: number;
  body?: any;
}

export interface ErrorInfo {
  type: string;
  message: string;
  stack_trace: string;
}

export interface IncidentMetadata {
  request_id?: string;
  deployment_id?: string;
  git_commit?: string;
}

export interface Incident {
  id: string;
  fingerprint: string;
  service: string;
  environment: string;
  timestamp: string;
  ingested_at: string;
  status: InvestigationStatus;
  request_method: string;
  request_path: string;
  request_query?: Record<string, any>;
  request_headers?: Record<string, string>;
  request_body?: any;
  response_status_code: number;
  response_body?: any;
  error_type: string;
  error_message: string;
  error_stack_trace: string;
  metadata_json?: IncidentMetadata;
  
  // Repository association
  github_owner?: string;
  github_repo?: string;
  github_commit_sha?: string;
  github_branch?: string;
  github_repo_url?: string;
  
  // Pipeline analysis logs
  traceback_analysis?: any;
  hypotheses?: any[];
  reproduction_result?: any;
  verification_results?: any;
  patch_result?: any;
  pr_result?: any;
}
