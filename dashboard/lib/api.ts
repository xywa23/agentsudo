// Type definitions for AgentSudo
// All data operations now go through Supabase directly (see supabase.ts)

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  api_key: string;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  project_id: string;
  name: string;
  scopes: string[];
  role: string;
  session_ttl: number;
  created_at: string;
  updated_at: string;
}

export interface Event {
  id: string;
  project_id: string;
  agent_id: string;
  agent_name: string;
  action: string;
  scope?: string;
  allowed: boolean;
  function_name?: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface Analytics {
  total_events: number;
  total_agents: number;
  total_sessions: number;
  permission_denials: number;
  permission_grants: number;
  denial_rate: number;
}

export interface AgentActivity {
  agent_id: string;
  agent_name: string;
  event_count: number;
  denial_count: number;
  last_active: string;
}

export interface ScopeUsage {
  scope: string;
  request_count: number;
  denial_count: number;
  agents_using: number;
}
