'use client'

import { useState, useRef, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { supabase, db } from '@/lib/supabase'
import { DEMO_PROJECT, DEMO_AGENTS } from '@/lib/demo-data'
import type { Agent, Project } from '@/lib/api'
import Link from 'next/link'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  toolCalls?: ToolCall[]
  permissionChecks?: PermissionCheck[]
}

interface ToolCall {
  id: string
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

function PlaygroundContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const isDemo = searchParams.get('demo') === 'true'
  
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('https://api.openai.com/v1')
  const [showSettings, setShowSettings] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    checkAuthAndLoad()
  }, [isDemo])

  useEffect(() => {
    if (selectedProject) {
      loadAgents()
    }
  }, [selectedProject])

  useEffect(() => {
    // Scroll to bottom of chat container only
    if (messages.length > 0 && chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages])

  const checkAuthAndLoad = async () => {
    // Demo mode - use mock data
    if (isDemo) {
      setIsAuthenticated(false)
      setProjects([DEMO_PROJECT])
      setSelectedProject(DEMO_PROJECT)
      // Filter to dashboard-created agents only (playground needs defined scopes)
      const dashboardAgents = DEMO_AGENTS.filter(a => a.role !== 'sdk')
      setAgents(dashboardAgents)
      if (dashboardAgents.length > 0) {
        setSelectedAgent(dashboardAgents[0])
      }
      return
    }

    // Check authentication
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (user) {
        setIsAuthenticated(true)
        loadProjects()
      } else {
        setIsAuthenticated(false)
        // Auto-enable demo mode for unauthenticated users
        setProjects([DEMO_PROJECT])
        setSelectedProject(DEMO_PROJECT)
        const dashboardAgents = DEMO_AGENTS.filter(a => a.role !== 'sdk')
        setAgents(dashboardAgents)
        if (dashboardAgents.length > 0) {
          setSelectedAgent(dashboardAgents[0])
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      setIsAuthenticated(false)
    }
  }

  const loadProjects = async () => {
    try {
      const data = await db.projects.list()
      setProjects(data)
      if (data.length > 0) {
        setSelectedProject(data[0])
      }
    } catch (error) {
      console.error('Failed to load projects:', error)
    }
  }

  const loadAgents = async () => {
    if (!selectedProject) return
    
    // Demo mode - agents already loaded
    if (isDemo || !isAuthenticated) {
      return
    }
    
    try {
      const data = await db.agents.list(selectedProject.id)
      setAgents(data)
      // Auto-select first non-SDK agent (SDK agents don't have dashboard-defined scopes)
      const dashboardAgents = data.filter(a => a.role !== 'sdk')
      if (dashboardAgents.length > 0) {
        setSelectedAgent(dashboardAgents[0])
      } else {
        setSelectedAgent(null)
      }
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || !selectedAgent || !apiKey) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('/api/playground', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content
          })),
          agentName: selectedAgent.name,
          agentScopes: selectedAgent.scopes,
          apiKey,
          baseUrl
        })
      })

      const data = await response.json()

      if (data.error) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${data.error}`
        }])
      } else {
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.message.content || '',
          toolCalls: data.message.tool_calls,
          permissionChecks: data.permissionChecks
        }
        setMessages(prev => [...prev, assistantMessage])

        // Log events to Supabase for each permission check
        if (data.permissionChecks && selectedProject) {
          for (const check of data.permissionChecks) {
            await logEvent(check)
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Failed to get response. Check your API key and try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const logEvent = async (check: PermissionCheck) => {
    if (!selectedProject || !selectedAgent) return

    try {
      // Use the Edge Function to log the event
      const response = await fetch(
        `https://hosqsdopgfmfzxhjweyt.supabase.co/functions/v1/ingest-event`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': selectedProject.api_key,
            'Authorization': `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`
          },
          body: JSON.stringify({
            agent_id: selectedAgent.id,
            agent_name: selectedAgent.name,
            action: 'permission_check',
            scope: check.scope,
            allowed: check.allowed,
            function_name: check.tool,
            metadata: { 
              source: 'playground',
              reason: check.reason 
            }
          })
        }
      )

      if (!response.ok) {
        console.error('Failed to log event:', await response.text())
      }
    } catch (error) {
      console.error('Failed to log event:', error)
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/login')
  }

  const showDemoMode = isDemo || isAuthenticated === false

  return (
    <div className="min-h-screen bg-background">
      {/* Demo Banner */}
      {showDemoMode && (
        <div className="bg-gradient-to-r from-blue-500/20 via-blue-500/10 to-blue-500/20 border-b border-blue-500/30">
          <div className="container mx-auto px-4 py-2.5 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-blue-200">
              <span className="text-base">🔮</span>
              <span className="text-sm">
                <strong>Preview Mode</strong> — Using sample agents to demonstrate the playground
              </span>
            </div>
            <Link href="/docs" className="text-sm text-blue-200 hover:text-white transition-colors">
              Read the docs →
            </Link>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="border-b border-white/10 bg-black/40 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href={showDemoMode ? "/demo" : "/dashboard"} className="flex items-center gap-2 hover:opacity-80">
              <img src="/agentsudo.png" alt="agentsudo" className="w-6 h-6 invert" />
              <span className="text-xl font-bold text-white">agentsudo</span>
            </Link>
            <Badge variant="secondary" className="bg-green-500/20 text-green-400 border-green-500/30">
              Playground
            </Badge>
            {showDemoMode && (
              <Badge variant="outline" className="text-blue-400 border-blue-400/50 text-xs">
                Preview
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Link href={showDemoMode ? "/demo" : "/dashboard"}>
              <Button variant="outline" size="sm">
                Dashboard
              </Button>
            </Link>
            <Link href="/docs">
              <Button variant="ghost" size="sm">
                Docs
              </Button>
            </Link>
            {isAuthenticated ? (
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            ) : (
              <a href="https://github.com/xywa23/agentsudo" target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="sm">
                  GitHub
                </Button>
              </a>
            )}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Settings Panel */}
          <div className="lg:col-span-1 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  Configuration
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => setShowSettings(!showSettings)}
                  >
                    {showSettings ? 'Hide' : 'Show'}
                  </Button>
                </CardTitle>
                <CardDescription>
                  Test your agents with a real AI before production
                </CardDescription>
              </CardHeader>
              {showSettings && (
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Project</Label>
                    <Select
                      value={selectedProject?.id || ''}
                      onValueChange={(value) => {
                        const project = projects.find(p => p.id === value)
                        setSelectedProject(project || null)
                        setSelectedAgent(null)
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select project" />
                      </SelectTrigger>
                      <SelectContent>
                        {projects.map(project => (
                          <SelectItem key={project.id} value={project.id}>
                            {project.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Agent</Label>
                    <Select
                      value={selectedAgent?.id || ''}
                      onValueChange={(value) => {
                        const agent = agents.find(a => a.id === value)
                        setSelectedAgent(agent || null)
                        clearChat()
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select agent" />
                      </SelectTrigger>
                      <SelectContent>
                        {agents.filter(a => a.role !== 'sdk').map(agent => (
                          <SelectItem key={agent.id} value={agent.id}>
                            {agent.name}
                          </SelectItem>
                        ))}
                        {agents.filter(a => a.role !== 'sdk').length === 0 && (
                          <div className="px-2 py-4 text-sm text-muted-foreground text-center">
                            No agents yet. Create one in the Dashboard.
                          </div>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedAgent && (
                    <div className="space-y-2">
                      <Label>Agent Scopes</Label>
                      <div className="flex flex-wrap gap-1">
                        {selectedAgent.scopes.map((scope, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {scope}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label>OpenAI API Key</Label>
                    <Input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="sk-..."
                    />
                    <p className="text-xs text-muted-foreground">
                      Your key is only used client-side
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label>Base URL</Label>
                    <Input
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      placeholder="https://api.openai.com/v1"
                    />
                  </div>
                </CardContent>
              )}
            </Card>

            {/* Agent's Tools (based on scopes) */}
            {selectedAgent && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Agent Tools</CardTitle>
                  <CardDescription className="text-xs">
                    Tools generated from this agent&apos;s scopes
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-xs">
                    {selectedAgent.scopes.map((scope, i) => {
                      // Generate tool name from scope (must match API logic)
                      const parts = scope.split(':')
                      const action = parts[0]
                      const resource = parts.slice(1).join('_')
                      
                      const actionVerbs: Record<string, string> = {
                        'read': 'get',
                        'write': 'update',
                        'create': 'create',
                        'delete': 'delete',
                        'execute': 'run',
                        'admin': 'manage',
                      }
                      const verb = actionVerbs[action] || action
                      const toolName = `${verb}_${resource}`.replace(/[:.]/g, '_')
                      
                      return (
                        <div key={i} className="flex items-center justify-between gap-2">
                          <span className="font-mono text-gray-300 truncate">{toolName}</span>
                          <Badge 
                            variant="default"
                            className="bg-green-500/20 text-green-400 border-green-500/30 shrink-0"
                          >
                            {scope}
                          </Badge>
                        </div>
                      )
                    })}
                  </div>
                  <p className="text-xs text-muted-foreground mt-4">
                    These tools are auto-generated from scopes. The AI will use them to perform actions.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Chat Panel */}
          <div className="lg:col-span-2">
            <Card className="h-[calc(100vh-12rem)] flex flex-col">
              <CardHeader className="border-b border-white/10">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>
                      {selectedAgent ? `Chat with ${selectedAgent.name}` : 'Select an Agent'}
                    </CardTitle>
                    <CardDescription>
                      Test permission checks in real-time
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={clearChat}>
                    Clear Chat
                  </Button>
                </div>
              </CardHeader>
              
              <CardContent ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                  <div className="h-full flex items-center justify-center text-muted-foreground">
                    <div className="text-center space-y-2">
                      <p>Start a conversation with your AI agent</p>
                      <p className="text-sm">Try: "Can you look up customer #123?"</p>
                      <p className="text-sm">Or: "Deploy the app to production"</p>
                    </div>
                  </div>
                )}

                {messages.map((message, i) => (
                  <div key={i} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === 'user' 
                        ? 'bg-green-500/20 text-green-100' 
                        : 'bg-white/5'
                    }`}>
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      
                      {/* Tool Calls */}
                      {message.toolCalls && message.toolCalls.length > 0 && (
                        <div className="mt-3 space-y-2">
                          <p className="text-xs text-muted-foreground">Tool calls:</p>
                          {message.toolCalls.map((call, j) => (
                            <div key={j} className="bg-black/30 rounded p-2 text-xs font-mono">
                              {call.function.name}({call.function.arguments})
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Permission Checks */}
                      {message.permissionChecks && message.permissionChecks.length > 0 && (
                        <div className="mt-3 space-y-2">
                          <p className="text-xs text-muted-foreground">Permission checks:</p>
                          {message.permissionChecks.map((check, j) => (
                            <div 
                              key={j} 
                              className={`rounded p-2 text-xs ${
                                check.allowed 
                                  ? 'bg-green-500/20 border border-green-500/30' 
                                  : 'bg-red-500/20 border border-red-500/30'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-mono">{check.tool}</span>
                                <Badge variant={check.allowed ? 'default' : 'destructive'}>
                                  {check.allowed ? '✓ Allowed' : '✗ Denied'}
                                </Badge>
                              </div>
                              <div className="mt-1 text-muted-foreground">
                                Scope: {check.scope} • {check.reason}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* No tool called indicator - AI declined due to no matching capability */}
                      {message.role === 'assistant' && 
                       (!message.toolCalls || message.toolCalls.length === 0) && 
                       message.content && 
                       (message.content.toLowerCase().includes("can't") || 
                        message.content.toLowerCase().includes("cannot") ||
                        message.content.toLowerCase().includes("don't have") ||
                        message.content.toLowerCase().includes("unable to") ||
                        message.content.toLowerCase().includes("outside") ||
                        message.content.toLowerCase().includes("not within")) && (
                        <div className="mt-3">
                          <div className="rounded p-2 text-xs bg-yellow-500/20 border border-yellow-500/30">
                            <div className="flex items-center gap-2">
                              <span className="text-yellow-400">⚠</span>
                              <span className="text-yellow-300">No matching tool available for this request</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-white/5 rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-muted-foreground">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}

              </CardContent>

              <div className="p-4 border-t border-white/10">
                <form 
                  onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
                  className="flex gap-2"
                >
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={apiKey ? "Type a message..." : "Enter API key first..."}
                    disabled={!selectedAgent || !apiKey || loading}
                    className="flex-1"
                  />
                  <Button 
                    type="submit" 
                    disabled={!selectedAgent || !apiKey || loading || !input.trim()}
                  >
                    Send
                  </Button>
                </form>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}

export default function PlaygroundPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-xl text-muted-foreground">Loading playground...</div>
      </div>
    }>
      <PlaygroundContent />
    </Suspense>
  )
}
