'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { type Project, type Agent, type Event, type Analytics } from '@/lib/api';
import { supabase, db, analytics as analyticsApi } from '@/lib/supabase';

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [recentEvents, setRecentEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'agents' | 'events'>('overview');

  // Modal states
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showCreateAgent, setShowCreateAgent] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  // Activity Feed filters
  const [statusFilter, setStatusFilter] = useState<'all' | 'allowed' | 'denied'>('all');
  const [agentFilter, setAgentFilter] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest');
  const [currentPage, setCurrentPage] = useState(1);
  const eventsPerPage = 20;

  useEffect(() => {
    checkAuthAndLoadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadProjectData();
    }
  }, [selectedProject]);

  const checkAuthAndLoadProjects = async () => {
    try {
      // Check if user is authenticated first
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        router.push('/login');
        return;
      }

      // User is authenticated, load projects
      const data = await db.projects.list();
      setProjects(data);
      if (data.length > 0 && !selectedProject) {
        setSelectedProject(data[0]);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
      router.push('/login');
    } finally {
      setLoading(false);
    }
  };

  const loadProjectData = async () => {
    if (!selectedProject) return;

    try {
      const [agentsData, analyticsData, eventsData] = await Promise.all([
        db.agents.list(selectedProject.id),
        analyticsApi.getSummary(selectedProject.id, 7),
        db.events.getRecent(selectedProject.id, 100),
      ]);

      setAgents(agentsData);
      setAnalytics(analyticsData as Analytics);
      setRecentEvents(eventsData);
    } catch (error) {
      console.error('Failed to load project data:', error);
    }
  };

  const handleCreateProject = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const name = formData.get('name') as string;
    const description = formData.get('description') as string;

    try {
      const newProject = await db.projects.create(name, description);
      setProjects([...projects, newProject]);
      setSelectedProject(newProject);
      setShowCreateProject(false);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to create project');
    }
  };

  const handleCreateAgent = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedProject) return;

    const formData = new FormData(e.currentTarget);
    const name = formData.get('name') as string;
    const scopesStr = formData.get('scopes') as string;
    const scopes = scopesStr.split(',').map(s => s.trim()).filter(Boolean);
    const role = formData.get('role') as string;
    const session_ttl = parseInt(formData.get('session_ttl') as string);

    try {
      const newAgent = await db.agents.create(selectedProject.id, {
        name,
        scopes,
        role,
        session_ttl,
      });
      setAgents([...agents, newAgent]);
      setShowCreateAgent(false);
      loadProjectData();
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to create agent');
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;

    try {
      await db.agents.delete(agentId);
      setAgents(agents.filter(a => a.id !== agentId));
      loadProjectData();
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to delete agent');
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle>Welcome to AgentSudo</CardTitle>
            <CardDescription>Create your first project to get started</CardDescription>
          </CardHeader>
          <CardContent>
            <Dialog open={showCreateProject} onOpenChange={setShowCreateProject}>
              <DialogTrigger asChild>
                <Button className="w-full">Create Project</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Project</DialogTitle>
                  <DialogDescription>Create a new project to manage your AI agents</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateProject} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Project Name</Label>
                    <Input id="name" name="name" placeholder="My Project" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Description (optional)</Label>
                    <Textarea id="description" name="description" placeholder="Project description..." />
                  </div>
                  <div className="flex gap-3">
                    <Button type="button" variant="outline" onClick={() => setShowCreateProject(false)} className="flex-1">
                      Cancel
                    </Button>
                    <Button type="submit" className="flex-1">Create</Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/40 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <img src="/agentsudo.png" alt="agentsudo" className="w-6 h-6 invert" />
              <span className="text-xl font-bold text-white">agentsudo</span>
            </div>
            <Select
              value={selectedProject?.id || ''}
              onValueChange={(value) => {
                const project = projects.find(p => p.id === value);
                setSelectedProject(project || null);
              }}
            >
              <SelectTrigger className="w-[200px]">
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
          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => router.push('/playground')}
              className="border-green-500/30 text-green-400 hover:bg-green-500/10"
            >
              🧪 Playground
            </Button>
            <Dialog open={showCreateProject} onOpenChange={setShowCreateProject}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">New Project</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Project</DialogTitle>
                  <DialogDescription>Create a new project to manage your AI agents</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateProject} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Project Name</Label>
                    <Input id="name" name="name" placeholder="My Project" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Description (optional)</Label>
                    <Textarea id="description" name="description" placeholder="Project description..." />
                  </div>
                  <div className="flex gap-3">
                    <Button type="button" variant="outline" onClick={() => setShowCreateProject(false)} className="flex-1">
                      Cancel
                    </Button>
                    <Button type="submit" className="flex-1">Create</Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
            <Button variant="ghost" size="sm" onClick={() => router.push('/profile')}>
              Profile
            </Button>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="flex gap-4 mb-8 border-b">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'overview'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('agents')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'agents'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Agents
          </button>
          <button
            onClick={() => setActiveTab('events')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'events'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Activity Feed
          </button>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && analytics && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Total Events</CardDescription>
                  <CardTitle className="text-3xl">{analytics.total_events.toLocaleString()}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Active Agents</CardDescription>
                  <CardTitle className="text-3xl">{analytics.total_agents}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Sessions</CardDescription>
                  <CardTitle className="text-3xl">{analytics.total_sessions.toLocaleString()}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Denial Rate</CardDescription>
                  <CardTitle className="text-3xl text-red-500">{analytics.denial_rate}%</CardTitle>
                </CardHeader>
              </Card>
            </div>

            {/* API Key Section */}
            <Card>
              <CardHeader>
                <CardTitle>API Configuration</CardTitle>
                <CardDescription>Use this API key in your Python SDK</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Label>Project API Key</Label>
                  <div className="flex gap-2">
                    <Input
                      type={showApiKey ? 'text' : 'password'}
                      value={selectedProject?.api_key || ''}
                      readOnly
                      className="font-mono text-sm"
                    />
                    <Button
                      variant="outline"
                      onClick={() => setShowApiKey(!showApiKey)}
                    >
                      {showApiKey ? 'Hide' : 'Show'}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Use this API key in your Python SDK to send telemetry to the dashboard
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Last 60 minutes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {recentEvents.slice(0, 10).map(event => (
                    <div key={event.id} className="flex items-center justify-between py-3 border-b last:border-0">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${event.allowed ? 'bg-green-500' : 'bg-red-500'}`} />
                        <div>
                          <div className="font-medium text-sm">{event.agent_name}</div>
                          <div className="text-xs text-muted-foreground">
                            {event.action} {event.scope && `• ${event.scope}`}
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                  {recentEvents.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      No recent activity
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Agents Tab */}
        {activeTab === 'agents' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Agents</h2>
              <Dialog open={showCreateAgent} onOpenChange={setShowCreateAgent}>
                <DialogTrigger asChild>
                  <Button>Create Agent</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Create Agent</DialogTitle>
                    <DialogDescription>Create a new AI agent with specific permissions</DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleCreateAgent} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="agent-name">Agent Name</Label>
                      <Input id="agent-name" name="name" placeholder="SupportBot" required />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="scopes">Scopes (comma-separated)</Label>
                      <Input id="scopes" name="scopes" placeholder="read:orders, write:refunds" required />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="role">Role</Label>
                      <Input id="role" name="role" defaultValue="worker" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="session_ttl">Session TTL (seconds)</Label>
                      <Input id="session_ttl" name="session_ttl" type="number" defaultValue={3600} min={60} max={86400} />
                    </div>
                    <div className="flex gap-3">
                      <Button type="button" variant="outline" onClick={() => setShowCreateAgent(false)} className="flex-1">
                        Cancel
                      </Button>
                      <Button type="submit" className="flex-1">Create</Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.map(agent => (
                <Card key={agent.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-lg">{agent.name}</CardTitle>
                          <Badge 
                            variant="outline" 
                            className={agent.role === 'sdk' 
                              ? 'text-blue-400 border-blue-400/50 text-xs' 
                              : 'text-green-400 border-green-400/50 text-xs'
                            }
                          >
                            {agent.role === 'sdk' ? 'SDK' : 'Dashboard'}
                          </Badge>
                        </div>
                        <CardDescription>{agent.role === 'sdk' ? 'Auto-created from SDK events' : agent.role}</CardDescription>
                      </div>
                      {agent.role !== 'sdk' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteAgent(agent.id)}
                          className="text-red-500 hover:text-red-600"
                        >
                          Delete
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <div className="text-xs text-muted-foreground mb-2">
                        {agent.role === 'sdk' ? 'Observed Scopes' : 'Scopes'}
                      </div>
                      {agent.scopes.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {agent.scopes.map((scope, i) => (
                            <Badge key={i} variant="secondary">{scope}</Badge>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground italic">
                          {agent.role === 'sdk' ? 'Scopes defined in your code' : 'No scopes defined'}
                        </p>
                      )}
                    </div>
                    {agent.role !== 'sdk' && (
                      <div>
                        <div className="text-xs text-muted-foreground">Session TTL</div>
                        <div className="text-sm">{agent.session_ttl}s</div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Events Tab */}
        {activeTab === 'events' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold">Activity Feed</h2>
              <div className="flex items-center gap-3">
                {/* Status Filter */}
                <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v as 'all' | 'allowed' | 'denied'); setCurrentPage(1); }}>
                  <SelectTrigger className="w-[130px]">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="allowed">Allowed</SelectItem>
                    <SelectItem value="denied">Denied</SelectItem>
                  </SelectContent>
                </Select>

                {/* Agent Filter */}
                <Select value={agentFilter} onValueChange={(v) => { setAgentFilter(v); setCurrentPage(1); }}>
                  <SelectTrigger className="w-[160px]">
                    <SelectValue placeholder="Agent" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Agents</SelectItem>
                    {[...new Set(recentEvents.map(e => e.agent_name))].map(name => (
                      <SelectItem key={name} value={name}>{name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Sort Order */}
                <Select value={sortOrder} onValueChange={(v) => setSortOrder(v as 'newest' | 'oldest')}>
                  <SelectTrigger className="w-[130px]">
                    <SelectValue placeholder="Sort" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="newest">Newest First</SelectItem>
                    <SelectItem value="oldest">Oldest First</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Status</TableHead>
                    <TableHead>Agent</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Scope</TableHead>
                    <TableHead>Function</TableHead>
                    <TableHead>Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(() => {
                    const filteredEvents = recentEvents
                      .filter(event => {
                        if (statusFilter === 'allowed' && !event.allowed) return false;
                        if (statusFilter === 'denied' && event.allowed) return false;
                        if (agentFilter !== 'all' && event.agent_name !== agentFilter) return false;
                        return true;
                      })
                      .sort((a, b) => {
                        const dateA = new Date(a.timestamp).getTime();
                        const dateB = new Date(b.timestamp).getTime();
                        return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
                      });
                    
                    const startIndex = (currentPage - 1) * eventsPerPage;
                    const paginatedEvents = filteredEvents.slice(startIndex, startIndex + eventsPerPage);
                    
                    if (filteredEvents.length === 0) {
                      return (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                            {recentEvents.length === 0 ? 'No events yet' : 'No events match filters'}
                          </TableCell>
                        </TableRow>
                      );
                    }
                    
                    return paginatedEvents.map(event => (
                      <TableRow key={event.id}>
                        <TableCell>
                          <Badge variant={event.allowed ? 'default' : 'destructive'}>
                            {event.allowed ? 'Allowed' : 'Denied'}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-medium">{event.agent_name}</TableCell>
                        <TableCell>{event.action}</TableCell>
                        <TableCell className="font-mono text-sm">{event.scope || '-'}</TableCell>
                        <TableCell>{event.function_name || '-'}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(event.timestamp).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ));
                  })()}
                </TableBody>
              </Table>
            </Card>
            
            {/* Pagination */}
            {(() => {
              const filteredCount = recentEvents.filter(event => {
                if (statusFilter === 'allowed' && !event.allowed) return false;
                if (statusFilter === 'denied' && event.allowed) return false;
                if (agentFilter !== 'all' && event.agent_name !== agentFilter) return false;
                return true;
              }).length;
              const totalPages = Math.ceil(filteredCount / eventsPerPage);
              
              if (totalPages <= 1) return null;
              
              return (
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Showing {((currentPage - 1) * eventsPerPage) + 1}-{Math.min(currentPage * eventsPerPage, filteredCount)} of {filteredCount} events
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </main>
    </div>
  );
}
