// Demo data for the read-only demo dashboard
// This provides realistic mock data to showcase the dashboard without authentication

import type { Project, Agent, Event, Analytics } from './api'

// Generate timestamps for the last 24 hours
const now = new Date()
const generateTimestamp = (minutesAgo: number) => {
  const date = new Date(now.getTime() - minutesAgo * 60 * 1000)
  return date.toISOString()
}

export const DEMO_PROJECT: Project = {
  id: 'demo-project-id',
  user_id: 'demo-user-id',
  name: 'E-Commerce Platform',
  description: 'Production AI agents for customer support and order management',
  api_key: 'as_demo_xxxxxxxxxxxx',
  created_at: '2024-11-01T00:00:00.000Z',
  updated_at: generateTimestamp(60),
}

export const DEMO_AGENTS: Agent[] = [
  // SDK-created agents (auto-discovered from telemetry)
  {
    id: 'agent-1',
    project_id: 'demo-project-id',
    name: 'SupportBot',
    scopes: ['read:orders', 'read:customers', 'write:refunds', 'write:tickets'],
    role: 'sdk',
    session_ttl: 3600,
    created_at: '2024-11-15T00:00:00.000Z',
    updated_at: generateTimestamp(30),
  },
  {
    id: 'agent-2',
    project_id: 'demo-project-id',
    name: 'AnalyticsBot',
    scopes: ['read:orders', 'read:customers', 'read:analytics'],
    role: 'sdk',
    session_ttl: 7200,
    created_at: '2024-11-20T00:00:00.000Z',
    updated_at: generateTimestamp(120),
  },
  {
    id: 'agent-3',
    project_id: 'demo-project-id',
    name: 'InventoryAgent',
    scopes: ['read:inventory', 'write:inventory', 'read:orders'],
    role: 'sdk',
    session_ttl: 1800,
    created_at: '2024-12-01T00:00:00.000Z',
    updated_at: generateTimestamp(45),
  },
  // Dashboard-created agents (manually configured)
  {
    id: 'agent-4',
    project_id: 'demo-project-id',
    name: 'EmailBot',
    scopes: ['read:customers', 'write:emails'],
    role: 'worker',
    session_ttl: 3600,
    created_at: '2024-12-03T00:00:00.000Z',
    updated_at: generateTimestamp(200),
  },
  {
    id: 'agent-5',
    project_id: 'demo-project-id',
    name: 'PaymentProcessor',
    scopes: ['read:orders', 'write:payments', 'read:customers'],
    role: 'worker',
    session_ttl: 1800,
    created_at: '2024-12-04T00:00:00.000Z',
    updated_at: generateTimestamp(90),
  },
  {
    id: 'agent-6',
    project_id: 'demo-project-id',
    name: 'ReportGenerator',
    scopes: ['read:orders', 'read:analytics', 'read:inventory', 'write:reports'],
    role: 'worker',
    session_ttl: 7200,
    created_at: '2024-12-05T00:00:00.000Z',
    updated_at: generateTimestamp(15),
  },
]

// Generate realistic events
const eventTemplates = [
  { agent_name: 'SupportBot', action: 'permission_check', scope: 'read:orders', allowed: true, function_name: 'get_order_details' },
  { agent_name: 'SupportBot', action: 'permission_check', scope: 'write:refunds', allowed: true, function_name: 'process_refund' },
  { agent_name: 'SupportBot', action: 'permission_check', scope: 'write:inventory', allowed: false, function_name: 'update_stock' },
  { agent_name: 'SupportBot', action: 'permission_check', scope: 'read:customers', allowed: true, function_name: 'fetch_customer' },
  { agent_name: 'AnalyticsBot', action: 'permission_check', scope: 'read:orders', allowed: true, function_name: 'aggregate_orders' },
  { agent_name: 'AnalyticsBot', action: 'permission_check', scope: 'read:analytics', allowed: true, function_name: 'get_metrics' },
  { agent_name: 'AnalyticsBot', action: 'permission_check', scope: 'write:refunds', allowed: false, function_name: 'issue_refund' },
  { agent_name: 'InventoryAgent', action: 'permission_check', scope: 'read:inventory', allowed: true, function_name: 'check_stock' },
  { agent_name: 'InventoryAgent', action: 'permission_check', scope: 'write:inventory', allowed: true, function_name: 'restock_item' },
  { agent_name: 'InventoryAgent', action: 'permission_check', scope: 'write:orders', allowed: false, function_name: 'cancel_order' },
  { agent_name: 'EmailBot', action: 'permission_check', scope: 'write:emails', allowed: true, function_name: 'send_notification' },
  { agent_name: 'EmailBot', action: 'permission_check', scope: 'read:customers', allowed: true, function_name: 'get_email_list' },
  { agent_name: 'EmailBot', action: 'permission_check', scope: 'write:refunds', allowed: false, function_name: 'refund_and_notify' },
]

export const DEMO_EVENTS: Event[] = Array.from({ length: 100 }, (_, i) => {
  const template = eventTemplates[i % eventTemplates.length]
  const minutesAgo = Math.floor(i * 2.5) + Math.random() * 5
  
  return {
    id: `event-${i + 1}`,
    project_id: 'demo-project-id',
    agent_id: DEMO_AGENTS.find(a => a.name === template.agent_name)?.id || 'agent-1',
    agent_name: template.agent_name,
    action: template.action,
    scope: template.scope,
    allowed: template.allowed,
    function_name: template.function_name,
    metadata: {
      source: 'sdk',
      action_type: 'permission_check',
    },
    timestamp: generateTimestamp(minutesAgo),
  }
})

// Calculate analytics from events
const totalEvents = DEMO_EVENTS.length
const deniedEvents = DEMO_EVENTS.filter(e => !e.allowed).length
const allowedEvents = totalEvents - deniedEvents

export const DEMO_ANALYTICS: Analytics = {
  total_events: totalEvents,
  total_agents: DEMO_AGENTS.length,
  total_sessions: 47,
  permission_denials: deniedEvents,
  permission_grants: allowedEvents,
  denial_rate: Math.round((deniedEvents / totalEvents) * 100),
}
