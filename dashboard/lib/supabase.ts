import { createClient } from '@supabase/supabase-js'
import type { Project, Agent, Event } from './api'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Analytics functions (call PostgreSQL functions via RPC)
export const analytics = {
  async getSummary(projectId: string, days: number = 7) {
    const { data, error } = await supabase.rpc('get_analytics_summary', {
      p_project_id: projectId,
      p_days: days
    })
    if (error) throw error
    return data
  },

  async getAgentActivity(projectId: string, days: number = 7, limit: number = 10) {
    const { data, error } = await supabase.rpc('get_agent_activity', {
      p_project_id: projectId,
      p_days: days,
      p_limit: limit
    })
    if (error) throw error
    return data || []
  },

  async getScopeUsage(projectId: string, days: number = 7, limit: number = 20) {
    const { data, error } = await supabase.rpc('get_scope_usage', {
      p_project_id: projectId,
      p_days: days,
      p_limit: limit
    })
    if (error) throw error
    return data || []
  }
}

// Helper functions for CRUD operations with RLS
export const db = {
  // Projects
  projects: {
    async list(): Promise<Project[]> {
      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .order('created_at', { ascending: false })
      
      if (error) throw error
      return data as Project[]
    },

    async create(name: string, description?: string): Promise<Project> {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) throw new Error('Not authenticated')

      const { data, error } = await supabase
        .from('projects')
        .insert({
          user_id: user.id,
          name,
          description,
          api_key: `as_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`
        })
        .select()
        .single()
      
      if (error) throw error
      return data as Project
    },

    async update(id: string, updates: { name?: string; description?: string }): Promise<Project> {
      const { data, error } = await supabase
        .from('projects')
        .update(updates)
        .eq('id', id)
        .select()
        .single()
      
      if (error) throw error
      return data as Project
    },

    async delete(id: string): Promise<void> {
      const { error } = await supabase
        .from('projects')
        .delete()
        .eq('id', id)
      
      if (error) throw error
    },

    async regenerateApiKey(id: string): Promise<Project> {
      const newApiKey = `as_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`
      const { data, error } = await supabase
        .from('projects')
        .update({ api_key: newApiKey })
        .eq('id', id)
        .select()
        .single()
      
      if (error) throw error
      return data as Project
    },
  },

  // Agents
  agents: {
    async list(projectId: string): Promise<Agent[]> {
      const { data, error } = await supabase
        .from('agents')
        .select('*')
        .eq('project_id', projectId)
        .order('created_at', { ascending: false })
      
      if (error) throw error
      return data as Agent[]
    },

    async create(projectId: string, agent: {
      name: string
      scopes: string[]
      role?: string
      session_ttl?: number
    }): Promise<Agent> {
      const { data, error } = await supabase
        .from('agents')
        .insert({
          project_id: projectId,
          name: agent.name,
          scopes: agent.scopes,
          role: agent.role || 'worker',
          session_ttl: agent.session_ttl || 3600,
        })
        .select()
        .single()
      
      if (error) throw error
      return data as Agent
    },

    async update(id: string, updates: {
      name?: string
      scopes?: string[]
      role?: string
      session_ttl?: number
    }): Promise<Agent> {
      const { data, error} = await supabase
        .from('agents')
        .update(updates)
        .eq('id', id)
        .select()
        .single()
      
      if (error) throw error
      return data as Agent
    },

    async delete(id: string): Promise<void> {
      const { error } = await supabase
        .from('agents')
        .delete()
        .eq('id', id)
      
      if (error) throw error
    },
  },

  // Events
  events: {
    async list(projectId: string, limit: number = 100): Promise<Event[]> {
      const { data, error } = await supabase
        .from('events')
        .select('*')
        .eq('project_id', projectId)
        .order('timestamp', { ascending: false })
        .limit(limit)
      
      if (error) throw error
      return data as Event[]
    },

    async getRecent(projectId: string, limit: number = 100): Promise<Event[]> {
      const { data, error } = await supabase
        .from('events')
        .select('*')
        .eq('project_id', projectId)
        .order('timestamp', { ascending: false })
        .limit(limit)
      
      if (error) throw error
      return data as Event[]
    },
  },
}
