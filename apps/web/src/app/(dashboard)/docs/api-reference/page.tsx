'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ChevronRight, Zap, Code, Shield, ExternalLink, Terminal, AlertCircle, CheckCircle, Zap as ZapIcon, Database, Globe, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface CodeExample {
  language: string;
  code: string;
  description: string;
}

const API_ENDPOINTS = [
  {
    category: 'Authentication',
    endpoints: [
      { method: 'POST', path: '/auth/signup', description: 'Register a new user account' },
      { method: 'POST', path: '/auth/signin', description: 'Sign in with email and password' },
      { method: 'POST', path: '/auth/refresh', description: 'Refresh access token' },
      { method: 'POST', path: '/auth/logout', description: 'Sign out and revoke tokens' },
      { method: 'GET', path: '/auth/me', description: 'Get current user profile' },
    ],
  },
  {
    category: 'Organizations',
    endpoints: [
      { method: 'POST', path: '/organizations', description: 'Create a new organization' },
      { method: 'GET', path: '/organizations/my', description: 'List user organizations' },
      { method: 'GET', path: '/organizations/{id}', description: 'Get organization details' },
      { method: 'PATCH', path: '/organizations/{id}', description: 'Update organization' },
    ],
  },
  {
    category: 'Campaigns',
    endpoints: [
      { method: 'POST', path: '/campaigns', description: 'Create a new campaign' },
      { method: 'GET', path: '/campaigns', description: 'List campaigns with filters' },
      { method: 'GET', path: '/campaigns/{id}', description: 'Get campaign details' },
      { method: 'PATCH', path: '/campaigns/{id}', description: 'Update campaign' },
      { method: 'POST', path: '/campaigns/{id}/launch', description: 'Launch a campaign' },
      { method: 'POST', path: '/campaigns/{id}/pause', description: 'Pause a campaign' },
      { method: 'POST', path: '/campaigns/sample', description: 'Create sample campaigns' },
    ],
  },
  {
    category: 'Workflows',
    endpoints: [
      { method: 'POST', path: '/workflows', description: 'Create a workflow' },
      { method: 'GET', path: '/workflows', description: 'List workflows' },
      { method: 'GET', path: '/workflows/{id}', description: 'Get workflow details' },
      { method: 'POST', path: '/workflows/{id}/execute', description: 'Execute a workflow' },
      { method: 'GET', path: '/workflows/{id}/executions', description: 'List executions' },
    ],
  },
  {
    category: 'Shadow Mode',
    endpoints: [
      { method: 'POST', path: '/shadow/organizations/{org}/sessions', description: 'Create shadow session' },
      { method: 'POST', path: '/shadow/sessions/{id}/start', description: 'Start shadow session' },
      { method: 'POST', path: '/shadow/sessions/{id}/pause', description: 'Pause shadow session' },
      { method: 'POST', path: '/shadow/organizations/{org}/sessions/{id}/decisions/agent', description: 'Record agent decision' },
      { method: 'POST', path: '/shadow/decisions/{id}/human', description: 'Record human decision' },
      { method: 'POST', path: '/shadow/sessions/{id}/lift/calculate', description: 'Calculate lift' },
    ],
  },
  {
    category: 'Social Intelligence',
    endpoints: [
      { method: 'GET', path: '/social/organizations/{org}/comments', description: 'List comments' },
      { method: 'POST', path: '/social/organizations/{org}/comments/{id}/reply/generate', description: 'Generate AI reply' },
      { method: 'PATCH', path: '/social/replies/{id}/approve', description: 'Approve auto-reply' },
      { method: 'POST', path: '/social/organizations/{org}/replies/{id}/send', description: 'Send approved reply' },
    ],
  },
  {
    category: 'Observability',
    endpoints: [
      { method: 'GET', path: '/observability/organizations/{org}/metrics/definitions', description: 'List metric definitions' },
      { method: 'POST', path: '/observability/organizations/{org}/metrics/record', description: 'Record metric sample' },
      { method: 'POST', path: '/observability/organizations/{org}/alerts/rules', description: 'Create alert rule' },
      { method: 'GET', path: '/observability/organizations/{org}/alerts', description: 'List alerts' },
      { method: 'POST', path: '/observability/organizations/{org}/costs', description: 'Record cost entry' },
      { method: 'GET', path: '/observability/organizations/{org}/costs/report', description: 'Get cost report' },
      { method: 'POST', path: '/observability/organizations/{org}/slas', description: 'Create SLA definition' },
      { method: 'POST', path: '/observability/organizations/{org}/slas/report', description: 'Generate SLA report' },
    ],
  },
];

const AUTH_EXAMPLES: CodeExample[] = [
  {
    language: 'bash',
    description: 'Sign up for a new account',
    code: `curl -X POST https://api.astra-os.com/api/v1/auth/signup \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@company.com",
    "password": "SecurePass123!",
    "name": "John Doe",
    "organization_name": "Acme Corp"
  }'`,
  },
  {
    language: 'bash',
    description: 'Sign in and get access token',
    code: `curl -X POST https://api.astra-os.com/api/v1/auth/signin \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@company.com",
    "password": "SecurePass123!"
  }'`,
  },
  {
    language: 'bash',
    description: 'Use access token for authenticated requests',
    code: `curl -X GET https://api.astra-os.com/api/v1/campaigns \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json"`,
  },
  {
    language: 'javascript',
    description: 'JavaScript fetch example',
    code: `const response = await fetch('https://api.astra-os.com/api/v1/campaigns', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer ' + accessToken,
    'Content-Type': 'application/json',
  },
});

const data = await response.json();`,
  },
];

const CAMPAIGN_EXAMPLES: CodeExample[] = [
  {
    language: 'bash',
    description: 'Create a new campaign',
    code: `curl -X POST https://api.astra-os.com/api/v1/campaigns \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "organization_id": "org-uuid",
    "name": "Q4 Holiday Campaign",
    "objective": "conversions",
    "budget": 10000,
    "target_audience": {
      "age_min": 25,
      "age_max": 55,
      "interests": ["technology", "business"]
    }
  }'`,
  },
  {
    language: 'bash',
    description: 'Launch a campaign',
    code: `curl -X POST https://api.astra-os.com/api/v1/campaigns/{campaign_id}/launch \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
  },
  {
    language: 'bash',
    description: 'Create sample campaigns for onboarding',
    code: `curl -X POST https://api.astra-os.com/api/v1/campaigns/sample \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "organization_id": "org-uuid",
    "count": 3
  }'`,
  },
];

const SHADOW_MODE_EXAMPLES: CodeExample[] = [
  {
    language: 'bash',
    description: 'Record an agent decision in shadow mode',
    code: `curl -X POST https://api.astra-os.com/api/v1/shadow/organizations/{org_id}/sessions/{session_id}/decisions/agent \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "decision_type": "bid_optimization",
    "context": {"campaign_id": "camp-123", "current_roas": 3.2},
    "entity_id": "campaign-123",
    "entity_type": "campaign",
    "agent_decision": {"action": "increase_bid", "amount": 1.5},
    "agent_confidence": 0.85,
    "agent_reasoning": "Strong conversion rate trend",
    "agent_model": "gpt-4o"
  }'`,
  },
  {
    language: 'bash',
    description: 'Submit human decision for comparison',
    code: `curl -X POST https://api.astra-os.com/api/v1/shadow/decisions/{decision_id}/human \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "human_decision": {"action": "increase_bid", "amount": 1.2},
    "human_confidence": 0.9,
    "human_reasoning": "Conservative increase due to seasonality"
  }'`,
  },
  {
    language: 'bash',
    description: 'Calculate lift for a metric',
    code: `curl -X POST https://api.astra-os.com/api/v1/shadow/organizations/{org_id}/sessions/{session_id}/lift/calculate \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "metric_name": "roas",
    "period_start": "2024-01-01T00:00:00Z",
    "period_end": "2024-01-31T23:59:59Z",
    "baseline_value": 2.8,
    "agent_value": 3.5,
    "campaigns": ["camp-uuid-1", "camp-uuid-2"],
    "decision_types": ["bid_optimization", "budget_adjustment"]
  }'`,
  },
];

export default function ApiReferencePage() {
  const [activeTab, setActiveTab] = useState('endpoints');

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="mb-8">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
          <Link href="/docs" className="hover:text-foreground">Documentation</Link>
          <ChevronRight className="h-4 w-4" />
          <span>API Reference</span>
        </nav>
        <h1 className="text-3xl font-bold tracking-tight">API Reference</h1>
        <p className="mt-2 text-muted-foreground text-lg">
          Complete REST API documentation for Astra OS. All endpoints require authentication via Bearer token.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="auth">Authentication</TabsTrigger>
          <TabsTrigger value="examples">Code Examples</TabsTrigger>
          <TabsTrigger value="webhooks">Webhooks</TabsTrigger>
        </TabsList>

        <TabsContent value="endpoints" className="mt-6 space-y-8">
          {API_ENDPOINTS.map((group) => (
            <div key={group.category}>
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                {group.category}
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-muted">
                      <th className="text-left py-2 px-3 font-medium">Method</th>
                      <th className="text-left py-2 px-3 font-medium">Endpoint</th>
                      <th className="text-left py-2 px-3 font-medium">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.endpoints.map((ep) => (
                      <tr key={ep.path} className="border-b border-muted/50">
                        <td className="py-3 px-3">
                          <code className={cn(
                            'px-2 py-1 rounded text-xs font-mono',
                            ep.method === 'GET' && 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
                            ep.method === 'POST' && 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
                            ep.method === 'PATCH' && 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
                            ep.method === 'DELETE' && 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                          )}>
                            {ep.method}
                          </code>
                        </td>
                        <td className="py-3 px-3 font-mono text-sm">
                          <code>/api/v1{ep.path}</code>
                        </td>
                        <td className="py-3 px-3 text-muted-foreground">{ep.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </TabsContent>

        <TabsContent value="auth" className="mt-6 space-y-6">
          <h2 className="text-xl font-semibold">Authentication</h2>
          <p className="text-muted-foreground mb-6">
            Astra OS uses JWT-based authentication with short-lived access tokens (15 min) and long-lived refresh tokens (7 days).
            Include the access token in the Authorization header for all authenticated requests.
          </p>
          <div className="space-y-4">
            <h3 className="font-semibold">Request Format</h3>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto"><code>Authorization: Bearer {access_token}</code></pre>
            <h3 className="font-semibold">Token Expiry</h3>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground">
              <li>Access Token: 15 minutes</li>
              <li>Refresh Token: 7 days</li>
              <li>Tokens rotate on refresh</li>
            </ul>
          </div>
        </TabsContent>

        <TabsContent value="examples" className="mt-6 space-y-8">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="auth">Authentication</TabsTrigger>
              <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
              <TabsTrigger value="shadow">Shadow Mode</TabsTrigger>
            </TabsList>

            <TabsContent value="auth" className="mt-4 space-y-6">
              {AUTH_EXAMPLES.map((ex, i) => (
                <div key={i} className="space-y-2">
                  <p className="text-sm font-medium">{ex.description}</p>
                  <pre className="bg-muted p-4 rounded-lg overflow-x-auto"><code className="language-{ex.language}">{ex.code}</code></pre>
                </div>
              ))}
            </TabsContent>

            <TabsContent value="campaigns" className="mt-4 space-y-6">
              {CAMPAIGN_EXAMPLES.map((ex, i) => (
                <div key={i} className="space-y-2">
                  <p className="text-sm font-medium">{ex.description}</p>
                  <pre className="bg-muted p-4 rounded-lg overflow-x-auto"><code className="language-{ex.language}">{ex.code}</code></pre>
                </div>
              ))}
            </TabsContent>

            <TabsContent value="shadow" className="mt-4 space-y-6">
              {SHADOW_MODE_EXAMPLES.map((ex, i) => (
                <div key={i} className="space-y-2">
                  <p className="text-sm font-medium">{ex.description}</p>
                  <pre className="bg-muted p-4 rounded-lg overflow-x-auto"><code className="language-{ex.language}">{ex.code}</code></pre>
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </TabsContent>

        <TabsContent value="webhooks" className="mt-6 space-y-6">
          <h2 className="text-xl font-semibold">Webhook Events</h2>
          <p className="text-muted-foreground mb-6">
            Configure webhooks in Organization Settings to receive real-time events.
          </p>
          <div className="space-y-2">
            {[
              'campaign.created',
              'campaign.updated',
              'campaign.launched',
              'campaign.paused',
              'workflow.created',
              'workflow.executed',
              'workflow.completed',
              'agent.task_completed',
              'agent.task_failed',
              'shadow.decision_made',
              'shadow.decision_compared',
              'alert.fired',
              'alert.resolved',
              'budget.warning',
              'budget.critical',
            ].map((event) => (
              <div key={event} className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <code className="text-sm font-mono text-primary">{event}</code>
                <span className="text-sm text-muted-foreground">Triggered when {event.replace('.', ' ').replace('_', ' ')}</span>
              </div>
            ))}
          </div>
          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h3 className="font-semibold mb-2">Webhook Security</h3>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              <li>Verify webhook signatures using the X-Signature header</li>
              <li>Respond with 2xx within 10 seconds</li>
              <li>Retry with exponential backoff on failure</li>
              <li>Idempotency keys provided in X-Idempotency-Key header</li>
            </ul>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}