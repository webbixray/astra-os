'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Check, CheckCircle, ChevronRight, Code, Terminal, Shield, Zap, AlertCircle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface Step {
  number: number;
  title: string;
  description: string;
  action: string;
  href: string;
}

const SETUP_STEPS: Step[] = [
  {
    number: 1,
    title: 'Create Your Account',
    description: 'Sign up with your email and create a secure password',
    action: 'Create Account',
    href: '/setup?step=account',
  },
  {
    number: 2,
    title: 'Set Up Your Organization',
    description: 'Name your workspace and configure basic settings',
    action: 'Configure Org',
    href: '/setup',
  },
  {
    number: 3,
    title: 'Create Sample Campaigns',
    description: 'Launch pre-built campaigns to see results fast',
    action: 'Add Campaigns',
    href: '/setup',
  },
  {
    number: 4,
    title: 'Connect AI Provider',
    description: 'Add OpenAI or Anthropic API keys for AI features',
    action: 'Connect AI',
    href: '/setup',
  },
  {
    number: 5,
    title: 'Complete Setup',
    description: 'Review and finalize your configuration',
    action: 'Finish Setup',
    href: '/setup',
  },
];

const TEAM_INVITE_STEPS = [
  'Navigate to Team Settings from the sidebar',
  'Click "Invite Member" and enter their email',
  'Assign role: Admin, Member, or Viewer',
  'Send invitation - they\'ll receive an email',
  'They accept and join your workspace',
];

export default function AccountSetupPage() {
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (step: number) => {
    const newSet = new Set(completedSteps);
    if (newSet.has(step)) {
      newSet.delete(step);
    } else {
      newSet.add(step);
    }
    setCompletedSteps(newSet);
  };

  const progress = (completedSteps.size / SETUP_STEPS.length) * 100;

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="mb-8">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
          <Link href="/docs" className="hover:text-foreground">
            Documentation
          </Link>
          <ChevronRight className="h-4 w-4" />
          <Link href="/docs/getting-started" className="hover:text-foreground">
            Getting Started
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span>Account Setup</span>
        </nav>
        <h1 className="text-3xl font-bold tracking-tight">Account Setup Guide</h1>
        <p className="mt-2 text-muted-foreground text-lg">
          Complete your Astra OS account setup in 5 steps.
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Setup Progress</span>
          <span className="text-sm text-muted-foreground">
            {completedSteps.size} of {SETUP_STEPS.length} steps completed
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-muted-foreground text-center">
          {progress === 100 ? '🎉 Setup complete! Ready to launch.' : `${Math.round(progress)}% complete`}
        </p>
      </div>

      {/* Steps */}
      <div className="space-y-6 mb-8">
        {SETUP_STEPS.map((step) => (
          <Card
            key={step.number}
            className={cn(
              'overflow-hidden transition-all duration-200',
              completedSteps.has(step.number)
                ? 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10'
                : ''
            )}
          >
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div
                  className={cn(
                    'flex h-12 w-12 shrink-0 items-center justify-center rounded-full font-bold text-lg transition-all',
                    completedSteps.has(step.number)
                      ? 'bg-green-500 text-white'
                      : 'bg-muted text-muted-foreground'
                  )}
                  onClick={() => {
                    const newSet = new Set(completedSteps);
                    if (newSet.has(step.number)) {
                      newSet.delete(step.number);
                    } else {
                      newSet.add(step.number);
                    }
                    setCompletedSteps(newSet);
                  }}
                  style={{ cursor: 'pointer' }}
                >
                  {completedSteps.has(step.number) ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <span className="font-bold">{step.number}</span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{step.title}</h3>
                    {completedSteps.has(step.number) && (
                      <span className="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                        <CheckCircle className="h-3 w-3" />
                        Completed
                      </span>
                    )}
                  </div>
                  <p className="text-muted-foreground mb-4">{step.description}</p>
                  <Link
                    href={step.href}
                    className={cn(
                      'inline-flex items-center gap-1 text-sm font-medium transition-colors',
                      completedSteps.has(step.number)
                        ? 'text-green-600 hover:text-green-700'
                        : 'text-primary hover:text-primary/80'
                    )}
                  >
                    {step.action}
                    <ChevronRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Team Invitations */}
      <Card className="mb-8 border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-500" />
            Invite Your Team
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-3">
            {TEAM_INVITE_STEPS.map((step, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-sm font-medium">
                  {i + 1}
                </span>
                <span className="text-sm pt-0.5">{step}</span>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>

      {/* Next Steps */}
      <Card className="border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            What's Next?
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[
              { title: 'Connect Ad Accounts', href: '/advertising', desc: 'Link Meta, Google, LinkedIn accounts', icon: Zap },
              { title: 'Create First Campaign', href: '/campaigns/new', desc: 'Launch your first marketing campaign', icon: Zap },
              { title: 'Build a Workflow', href: '/workflows/new', desc: 'Automate marketing tasks', icon: Sparkles },
              { title: 'Invite Team', href: '/team', desc: 'Collaborate with your team', icon: Users },
            ].map((item) => (
              <Link
                key={item.title}
                href={item.href}
                className="flex items-start gap-3 p-4 rounded-lg border hover:bg-accent transition-colors"
              >
                <item.icon className="h-5 w-5 text-primary mt-0.5" />
                <div>
                  <p className="font-medium">{item.title}</p>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}