-- AgentSudo Database Schema
-- Exported from Supabase project: hosqsdopgfmfzxhjweyt
-- This migration creates all tables needed for the AgentSudo dashboard

-- =============================================================================
-- EXTENSIONS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;

-- =============================================================================
-- TABLES
-- =============================================================================

-- Projects table
-- Each user can have multiple projects, each with its own API key
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    description TEXT,
    api_key VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agents table
-- AI agents belong to a project and have specific scopes/permissions
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    role VARCHAR NOT NULL DEFAULT 'worker',
    session_ttl INTEGER NOT NULL DEFAULT 3600,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Events table
-- Permission check events from the SDK
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL,
    agent_name VARCHAR NOT NULL,
    action VARCHAR NOT NULL,
    scope VARCHAR,
    allowed BOOLEAN NOT NULL,
    function_name VARCHAR,
    metadata JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions table
-- Track agent sessions for analytics
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_project_id ON agents(project_id);
CREATE INDEX IF NOT EXISTS idx_events_project_id ON events(project_id);
CREATE INDEX IF NOT EXISTS idx_events_agent_id ON events(agent_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_project_id ON sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_sessions_agent_id ON sessions(agent_id);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Projects: Users can only access their own projects
CREATE POLICY projects_select_own ON projects
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY projects_insert_own ON projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY projects_update_own ON projects
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY projects_delete_own ON projects
    FOR DELETE USING (auth.uid() = user_id);

-- Agents: Users can only access agents in their projects
CREATE POLICY agents_select_own ON agents
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = agents.project_id
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY agents_insert_own ON agents
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = agents.project_id
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY agents_update_own ON agents
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = agents.project_id
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY agents_delete_own ON agents
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = agents.project_id
            AND projects.user_id = auth.uid()
        )
    );

-- Events: Users can view their own events, service role can insert
CREATE POLICY events_select_own ON events
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = events.project_id
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY events_insert_service ON events
    FOR INSERT WITH CHECK (true);

-- Sessions: Users can view their own sessions, service role can insert
CREATE POLICY sessions_select_own ON sessions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = sessions.project_id
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY sessions_insert_service ON sessions
    FOR INSERT WITH CHECK (true);

-- =============================================================================
-- FUNCTIONS FOR ANALYTICS (called via RPC)
-- =============================================================================

-- Get analytics summary for a project
CREATE OR REPLACE FUNCTION get_analytics_summary(p_project_id UUID, p_days INTEGER DEFAULT 7)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
  time_threshold TIMESTAMPTZ;
BEGIN
  time_threshold := NOW() - (p_days || ' days')::INTERVAL;
  
  SELECT json_build_object(
    'total_events', COALESCE((
      SELECT COUNT(*) FROM events 
      WHERE project_id = p_project_id AND timestamp >= time_threshold
    ), 0),
    'total_agents', COALESCE((
      SELECT COUNT(*) FROM agents WHERE project_id = p_project_id
    ), 0),
    'total_sessions', COALESCE((
      SELECT COUNT(*) FROM sessions 
      WHERE project_id = p_project_id AND started_at >= time_threshold
    ), 0),
    'permission_denials', COALESCE((
      SELECT COUNT(*) FROM events 
      WHERE project_id = p_project_id AND allowed = FALSE AND timestamp >= time_threshold
    ), 0),
    'permission_grants', COALESCE((
      SELECT COUNT(*) FROM events 
      WHERE project_id = p_project_id AND allowed = TRUE AND timestamp >= time_threshold
    ), 0),
    'denial_rate', COALESCE(
      ROUND(
        (SELECT COUNT(*)::NUMERIC FROM events WHERE project_id = p_project_id AND allowed = FALSE AND timestamp >= time_threshold) /
        NULLIF((SELECT COUNT(*)::NUMERIC FROM events WHERE project_id = p_project_id AND timestamp >= time_threshold), 0) * 100
      , 2)
    , 0)
  ) INTO result;
  
  RETURN result;
END;
$$;

-- Get agent activity for a project
CREATE OR REPLACE FUNCTION get_agent_activity(p_project_id UUID, p_days INTEGER DEFAULT 7, p_limit INTEGER DEFAULT 10)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
  time_threshold TIMESTAMPTZ;
BEGIN
  time_threshold := NOW() - (p_days || ' days')::INTERVAL;
  
  SELECT COALESCE(json_agg(activity ORDER BY event_count DESC), '[]'::JSON)
  INTO result
  FROM (
    SELECT 
      a.id as agent_id,
      a.name as agent_name,
      COUNT(e.id) as event_count,
      COUNT(e.id) FILTER (WHERE e.allowed = FALSE) as denial_count,
      MAX(e.timestamp) as last_active
    FROM agents a
    LEFT JOIN events e ON e.agent_id = a.id AND e.timestamp >= time_threshold
    WHERE a.project_id = p_project_id
    GROUP BY a.id, a.name
    HAVING COUNT(e.id) > 0
    LIMIT p_limit
  ) activity;
  
  RETURN result;
END;
$$;

-- Get scope usage for a project
CREATE OR REPLACE FUNCTION get_scope_usage(p_project_id UUID, p_days INTEGER DEFAULT 7, p_limit INTEGER DEFAULT 20)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
  time_threshold TIMESTAMPTZ;
BEGIN
  time_threshold := NOW() - (p_days || ' days')::INTERVAL;
  
  SELECT COALESCE(json_agg(usage ORDER BY request_count DESC), '[]'::JSON)
  INTO result
  FROM (
    SELECT 
      scope,
      COUNT(*) as request_count,
      COUNT(*) FILTER (WHERE allowed = FALSE) as denial_count,
      COUNT(DISTINCT agent_id) as agents_using
    FROM events
    WHERE project_id = p_project_id 
      AND timestamp >= time_threshold
      AND scope IS NOT NULL
    GROUP BY scope
    LIMIT p_limit
  ) usage;
  
  RETURN result;
END;
$$;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
