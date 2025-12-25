import { NextRequest, NextResponse } from 'next/server'

// Generate a tool definition from a scope
function generateToolFromScope(scope: string): { name: string; description: string; scope: string } {
  const parts = scope.split(':')
  const action = parts[0]
  const resource = parts.slice(1).join('_')
  
  // Generate descriptive tool name and description based on action type
  const actionDescriptions: Record<string, { verb: string; desc: string }> = {
    'read': { verb: 'get', desc: 'Retrieve' },
    'write': { verb: 'update', desc: 'Create or update' },
    'create': { verb: 'create', desc: 'Create new' },
    'delete': { verb: 'delete', desc: 'Delete' },
    'execute': { verb: 'run', desc: 'Execute' },
    'admin': { verb: 'manage', desc: 'Administer' },
  }
  
  const actionInfo = actionDescriptions[action] || { verb: action, desc: action }
  const toolName = `${actionInfo.verb}_${resource}`.replace(/[:.]/g, '_')
  const resourceReadable = resource.replace(/_/g, ' ').replace(/:/g, ' ')
  
  return {
    name: toolName,
    description: `${actionInfo.desc} ${resourceReadable} data`,
    scope: scope
  }
}

interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
  tool_calls?: ToolCall[]
  tool_call_id?: string
}

interface ToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string
  }
}

interface PermissionCheck {
  tool: string
  scope: string
  allowed: boolean
  reason: string
}

// Check if a scope is allowed based on agent's scopes
function checkPermission(requiredScope: string, agentScopes: string[]): { allowed: boolean; reason: string } {
  // Direct match
  if (agentScopes.includes(requiredScope)) {
    return { allowed: true, reason: 'Scope directly granted' }
  }

  // Check for wildcard patterns (e.g., "read:*" matches "read:customers")
  const [action, resource] = requiredScope.split(':')
  
  // Check for action wildcard (e.g., "*:customers")
  if (agentScopes.includes(`*:${resource}`)) {
    return { allowed: true, reason: 'Wildcard resource match' }
  }
  
  // Check for resource wildcard (e.g., "read:*")
  if (agentScopes.includes(`${action}:*`)) {
    return { allowed: true, reason: 'Wildcard action match' }
  }
  
  // Check for full wildcard
  if (agentScopes.includes('*') || agentScopes.includes('*:*')) {
    return { allowed: true, reason: 'Full wildcard access' }
  }

  // Check for hierarchical scopes (e.g., "write:refunds" matches "write:refunds:small")
  for (const scope of agentScopes) {
    if (requiredScope.startsWith(scope + ':')) {
      return { allowed: true, reason: `Hierarchical match: ${scope}` }
    }
  }

  return { allowed: false, reason: `Missing scope: ${requiredScope}` }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { 
      messages, 
      agentName, 
      agentScopes, 
      apiKey,
      baseUrl = 'https://api.chatanywhere.org/v1'
    } = body

    if (!messages || !agentName || !agentScopes || !apiKey) {
      return NextResponse.json(
        { error: 'Missing required fields: messages, agentName, agentScopes, apiKey' },
        { status: 400 }
      )
    }

    // Generate tools dynamically from agent's scopes
    type GeneratedTool = { name: string; description: string; scope: string }
    const generatedTools: GeneratedTool[] = agentScopes.map((scope: string) => generateToolFromScope(scope))
    
    // Add common tools that users might ask for (to demonstrate denied permissions)
    const commonTools: GeneratedTool[] = [
      { name: 'send_email', description: 'Send an email to a user', scope: 'write:emails' },
      { name: 'delete_account', description: 'Delete a user account permanently', scope: 'delete:users' },
      { name: 'process_payment', description: 'Process a payment transaction', scope: 'write:payments' },
      { name: 'export_all_data', description: 'Export all system data', scope: 'admin:export' },
      { name: 'access_logs', description: 'Access system audit logs', scope: 'read:logs' },
    ]
    
    // Combine agent tools with common tools (avoiding duplicates)
    const agentToolNames = new Set(generatedTools.map(t => t.name))
    const allTools = [
      ...generatedTools,
      ...commonTools.filter(t => !agentToolNames.has(t.name))
    ]
    
    const tools = allTools.map((tool: GeneratedTool) => ({
      type: 'function' as const,
      function: {
        name: tool.name,
        description: tool.description,
        parameters: {
          type: 'object',
          properties: {
            id: { type: 'string', description: 'The ID or identifier to operate on' },
            data: { type: 'object', description: 'Additional data for the operation' }
          }
        }
      }
    }))

    // Build a tools description for the system prompt
    const toolsList = allTools.map((t: GeneratedTool) => `- ${t.name}: ${t.description} (requires: ${t.scope})`).join('\n')

    // System prompt that instructs the AI about its role and available tools
    const systemPrompt = `You are an AI agent named "${agentName}" in a permission testing playground.

You have access to the following tools based on your permission scopes:
${toolsList}

IMPORTANT RULES:
1. When the user asks you to perform an action that matches one of your tools, you MUST call that tool.
2. If the user asks for something you DON'T have a tool for, politely explain that this action is outside your permitted capabilities and list what you CAN do instead.
3. Always be helpful and suggest alternatives when you can't perform a requested action.

Examples:
- User: "get employee 123" → Call get_employees with id="123"
- User: "read the analytics" → Call get_analytics
- User: "process a refund" (but you don't have refund tools) → Explain you can't do refunds and list your actual capabilities

Your capabilities are limited to the tools listed above. Be transparent about what you can and cannot do.`

    // Call the LLM
    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages
        ],
        tools,
        tool_choice: 'auto',
        max_tokens: 1000
      })
    })

    if (!response.ok) {
      const error = await response.text()
      console.error('LLM API error:', error)
      return NextResponse.json(
        { error: `LLM API error: ${response.status}` },
        { status: 500 }
      )
    }

    const data = await response.json()
    const assistantMessage = data.choices[0].message

    // Check permissions for any tool calls
    const permissionChecks: PermissionCheck[] = []
    
    if (assistantMessage.tool_calls) {
      for (const toolCall of assistantMessage.tool_calls) {
        const tool = allTools.find((t: GeneratedTool) => t.name === toolCall.function.name)
        if (tool) {
          const { allowed, reason } = checkPermission(tool.scope, agentScopes)
          permissionChecks.push({
            tool: toolCall.function.name,
            scope: tool.scope,
            allowed,
            reason
          })
        }
      }
    }

    return NextResponse.json({
      message: assistantMessage,
      permissionChecks,
      usage: data.usage
    })

  } catch (error) {
    console.error('Playground error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
