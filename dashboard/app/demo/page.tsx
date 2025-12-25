'use client';

import { useState } from 'react';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { type Project, type Agent, type Event, type Analytics } from '@/lib/api';
import { DEMO_PROJECT, DEMO_AGENTS, DEMO_EVENTS, DEMO_ANALYTICS } from '@/lib/demo-data';
import Link from 'next/link';

export default function DemoDashboardPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'overview' | 'agents' | 'events'>('overview');

  // Use demo data
  const selectedProject: Project = DEMO_PROJECT;
  const agents: Agent[] = DEMO_AGENTS;
  const analytics: Analytics = DEMO_ANALYTICS;
  const recentEvents: Event[] = DEMO_EVENTS;

  // Activity Feed filters
  const [statusFilter, setStatusFilter] = useState<'all' | 'allowed' | 'denied'>('all');
  const [agentFilter, setAgentFilter] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest');
  const [currentPage, setCurrentPage] = useState(1);
  const eventsPerPage = 20;

  // Show API key state (always masked in demo)
  const [showApiKey, setShowApiKey] = useState(false);

  // Toast for demo mode actions
  const showDemoToast = () => {
    alert('This is a preview. The hosted dashboard is coming soon!');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Demo Banner */}
      <div className="bg-gradient-to-r from-blue-500/20 via-blue-500/10 to-blue-500/20 border-b border-blue-500/30">
        <div className="container mx-auto px-4 py-2.5 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-blue-200">
            <span className="text-base">🔮</span>
            <span className="text-sm">
              <strong>Dashboard Preview</strong> — See what&apos;s possible with AgentSudo telemetry
            </span>
          </div>
          <Link href="/docs" className="text-sm text-blue-200 hover:text-white transition-colors">
            Read the docs →
          </Link>
        </div>
      </div>

      {/* Header */}
      <header className="border-b border-white/10 bg-black/40 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2">
              <img src="/agentsudo.png" alt="agentsudo" className="w-6 h-6 invert" />
              <span className="text-xl font-bold text-white">agentsudo</span>
            </Link>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg">
              <span className="text-sm text-white font-medium">{selectedProject.name}</span>
              <Badge variant="outline" className="text-blue-400 border-blue-400/50 text-xs">
                Preview
              </Badge>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/playground?demo=true">
              <Button 
                variant="outline" 
                size="sm" 
                className="border-green-500/30 text-green-400 hover:bg-green-500/10"
              >
                🧪 Playground
              </Button>
            </Link>
            <Link href="/docs">
              <Button variant="ghost" size="sm">
                Docs
              </Button>
            </Link>
            <a href="https://github.com/xywa23/agentsudo" target="_blank" rel="noopener noreferrer">
              <Button variant="ghost" size="sm">
                GitHub
              </Button>
            </a>
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
        {activeTab === 'overview' && (
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
                      value={selectedProject.api_key}
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
                    Sample API key for preview. Hosted dashboard coming soon.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Last 60 minutes (sample data)</CardDescription>
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
              <Button onClick={showDemoToast} className="opacity-75">
                Create Agent
              </Button>
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
                          onClick={showDemoToast}
                          className="text-red-500 hover:text-red-600 opacity-75"
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
                            No events match filters
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

      {/* Footer CTA */}
      <div className="border-t border-white/10 bg-gradient-to-r from-green-500/10 via-green-500/5 to-green-500/10">
        <div className="container mx-auto px-4 py-8 text-center">
          <h3 className="text-xl font-bold text-white mb-2">Ready to secure your AI agents?</h3>
          <p className="text-gray-400 mb-4">Get started with the SDK in under 5 minutes. Works 100% locally.</p>
          <div className="flex justify-center gap-3">
            <Link href="/docs/getting-started">
              <Button className="bg-green-500 hover:bg-green-600">
                Get Started
              </Button>
            </Link>
            <a href="https://github.com/xywa23/agentsudo" target="_blank" rel="noopener noreferrer">
              <Button variant="outline">
                ⭐ Star on GitHub
              </Button>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
