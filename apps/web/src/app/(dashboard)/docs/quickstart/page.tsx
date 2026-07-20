'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Check, ChevronRight, AlertCircle, CheckCircle, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface Step {
  number: number;
  title: string;
  description: string;
  action: string;
  href: string;
  completed?: boolean;
}

const QUICKSTART_STEPS: Step[] = [
  {
    number: 1,
    title: 'Create Your Account',
    description: 'Sign up for Astra OS and verify your email',
    action: 'Sign Up',
    href: '/setup',
  },
  {
    number: 2,
    title: 'Set Up Your Organization',
    description: 'Create your workspace and invite team members',
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
    title: 'Launch Your First Campaign',
    description: 'Go live and start tracking results',
    action: 'Launch Campaign',
    href: '/campaigns/new',
  },
];

const PREREQUISITES = [
  'A valid email address',
  'A business/organization name',
  'Payment method for ad spend (optional for trial)',
  'OpenAI or Anthropic API key (optional, for AI features)',
];

const NEXT_STEPS = [
  { title: 'Connect Ad Accounts', href: '/advertising', description: 'Link Meta, Google, LinkedIn accounts' },
  { title: 'Set Up Workflows', href: '/workflows', description: 'Automate repetitive tasks' },
  { title: 'Invite Team Members', href: '/team', description: 'Collaborate with your team' },
  { title: 'Explore AI Content', href: '/ai-content', description: 'Generate marketing copy with AI' },
];

export default function QuickstartPage() {
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

  const progress = (completedSteps.size / QUICKSTART_STEPS.length) * 100;

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="mb-8">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
          <Link href="/docs" className="hover:text-foreground">
            Documentation
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span>Quick Start</span>
        </nav>
        <h1 className="text-3xl font-bold tracking-tight">Quick Start Guide</h1>
        <p className="mt-2 text-muted-foreground text-lg">
          Get up and running with Astra OS in 5 minutes.
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Your Progress</span>
          <span className="text-sm text-muted-foreground">
            {completedSteps.size} of {QUICKSTART_STEPS.length} steps completed
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-muted-foreground text-center">
          {progress === 100 ? '🎉 All done! Ready to launch.' : `${Math.round(progress)}% complete`}
        </p>
      </div>

      {/* Prerequisites */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-amber-500" />
            Before You Begin
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {PREREQUISITES.map((item, i) => (
              <li key={i} className="flex items-center gap-2 text-sm">
                <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Steps */}
      <div className="space-y-6 mb-8">
        {QUICKSTART_STEPS.map((step) => (
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
                  onClick={() => toggleStep(step.number)}
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

      {/* Next Steps */}
      <Card className="mb-8 border-primary/20 bg-primary/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            What's Next?
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {NEXT_STEPS.map((step) => (
              <Link
                key={step.title}
                href={step.href}
                className="flex flex-col p-4 rounded-lg border hover:bg-accent transition-colors"
              >
                <h4 className="font-medium">{step.title}</h4>
                <p className="text-sm text-muted-foreground mt-1">{step.description}</p>
                <span className="mt-2 text-sm text-primary flex items-center gap-1">
                  Continue <ChevronRight className="h-3 w-3" />
                </span>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Tips */}
      <Card className="border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-900/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-amber-500" />
            Pro Tips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <Zap className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <span>Start with sample campaigns to see results immediately, then customize.</span>
            </li>
            <li className="flex items-start gap-2">
              <Zap className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <span>Connect AI providers early to unlock content generation and optimization.</span>
            </li>
            <li className="flex items-start gap-2">
              <Zap className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <span>Set up workflows early to automate repetitive tasks from day one.</span>
            </li>
            <li className="flex items-start gap-2">
              <Zap className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <span>Invite team members early to establish collaboration workflows.</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
