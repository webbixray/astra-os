'use client';

import Link from 'next/link';
import { ChevronRight, Check, Zap, Users, Shield, Code, Terminal, AlertCircle, CheckCircle, Zap as ZapIcon, Database, Globe, ArrowRight } from 'lucide-react';
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

const FIRST_CAMPAIGN_STEPS: Step[] = [
  {
    number: 1,
    title: 'Navigate to Campaigns',
    description: 'Go to the Campaigns page from the main navigation',
    action: 'Go to Campaigns',
    href: '/campaigns',
  },
  {
    number: 2,
    title: 'Click "New Campaign"',
    description: 'Click the "New Campaign" button in the top right',
    action: 'Create Campaign',
    href: '/campaigns/new',
  },
  {
    number: 3,
    title: 'Choose Objective',
    description: 'Select your campaign objective (awareness, leads, conversions, etc.)',
    action: 'Select Objective',
    href: '/campaigns/new',
  },
  {
    number: 4,
    title: 'Define Target Audience',
    description: 'Set demographics, interests, locations, and behaviors',
    action: 'Define Audience',
    href: '/campaigns/new',
  },
  {
    number: 4,
    title: 'Set Budget & Schedule',
    description: 'Define your budget, daily spend limits, and campaign dates',
    action: 'Set Budget',
    href: '/campaigns/new',
  },
  {
    number: 5,
    title: 'Create Ad Creatives',
    description: 'Upload images, write copy, and configure ad formats',
    action: 'Add Creatives',
    href: '/campaigns/new',
  },
  {
    number: 6,
    title: 'Review & Launch',
    description: 'Review all settings and launch your campaign',
    action: 'Launch Campaign',
    href: '/campaigns/new',
  },
];

const CAMPAIGN_TYPES = [
  {
    objective: 'Brand Awareness',
    description: 'Maximize reach and brand recognition',
    bestFor: 'New product launches, brand introductions',
    icon: Zap,
  },
  {
    objective: 'Lead Generation',
    description: 'Capture contact information from prospects',
    bestFor: 'B2B services, high-value products, webinars',
    icon: Users,
  },
  {
    objective: 'Conversions',
    description: 'Drive specific actions (purchases, sign-ups)',
    bestFor: 'E-commerce, app installs, subscriptions',
    icon: ZapIcon,
  },
  {
    objective: 'Engagement',
    description: 'Increase interactions (likes, comments, shares)',
    bestFor: 'Community building, content promotion',
    icon: ZapIcon,
  },
  {
    objective: 'Traffic',
    description: 'Drive clicks to a website or landing page',
    bestFor: 'Content promotion, blog posts, landing pages',
    icon: Globe,
  },
  {
    objective: 'App Installs',
    description: 'Drive mobile app downloads',
    bestFor: 'Mobile apps, games',
    icon: Code,
  },
];

const BUDGET_TIPS = [
  { title: 'Start Small', description: 'Begin with $10-50/day to test creatives and audiences before scaling' },
  { title: 'Use Campaign Budget Optimization', description: 'Let the platform distribute budget across ad sets for best results' },
  { title: 'Set Spend Limits', description: 'Set account-level and campaign-level spend caps to prevent overspending' },
  { title: 'Monitor Daily', description: 'Check performance daily for the first week, then weekly' },
];

const CREATIVE_BEST_PRACTICES = [
  { title: 'Test Multiple Creatives', description: 'Run 3-5 ad variations per ad set to find winners' },
  { title: 'Hook in First 3 Seconds', description: 'Grab attention immediately with strong visual or hook' },
  { title: 'Clear Call-to-Action', description: 'Use action-oriented CTAs: "Shop Now", "Learn More", "Sign Up"' },
  { title: 'Test Multiple Formats', description: 'Try images, videos, carousels, and collections' },
];

export default function FirstCampaignPage() {
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

  const progress = (completedSteps.size / FIRST_CAMPAIGN_STEPS.length) * 100;

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="mb-8">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
          <Link href="/docs" className="hover:text-foreground">Documentation</Link>
          <ChevronRight className="h-4 w-4" />
          <Link href="/docs/getting-started" className="hover:text-foreground">Getting Started</Link>
          <ChevronRight className="h-4 w-4" />
          <span>First Campaign</span>
        </nav>
        <h1 className="text-3xl font-bold tracking-tight">Create Your First Campaign</h1>
        <p className="mt-2 text-muted-foreground text-lg">
          Step-by-step guide to launching your first marketing campaign in Astra OS.
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Progress</span>
          <span className="text-sm text-muted-foreground">
            {completedSteps.size} of {FIRST_CAMPAIGN_STEPS.length} steps completed
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-muted-foreground text-center">
          {progress === 100 ? '🎉 Campaign ready to launch!' : `${Math.round(progress)}% complete`}
        </p>
      </div>

      {/* Campaign Type Selection */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            Choose Your Campaign Objective
          </CardTitle>
          <CardDescription>Select the goal that matches your marketing goal</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {CAMPAIGN_TYPES.map((type) => (
              <Card key={type.objective} className="h-full transition-shadow hover:shadow-lg">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <type.icon className="h-5 w-5" />
                    </div>
                    <h3 className="font-semibold">{type.objective}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">{type.description}</p>
                  <p className="text-xs text-muted-foreground"><strong>Best for:</strong> {type.bestFor}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Steps */}
      <div className="space-y-6 mb-8">
        {FIRST_CAMPAIGN_STEPS.map((step) => (
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
                  </h3>
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

      {/* Campaign Type Guide */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            Choose the Right Objective
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-muted">
                  <th className="text-left py-2 px-3 font-medium">Objective</th>
                  <th className="text-left py-2 px-3 font-medium">Best For</th>
                  <th className="text-left py-2 px-3 font-medium">Key Metrics</th>
                  <th className="text-left py-2 px-3 font-medium">Typical CTA</th>
                </tr>
              </thead>
              <tbody>
                {CAMPAIGN_TYPES.map((type) => (
                  <tr key={type.objective} className="border-b border-muted/50">
                    <td className="py-3 px-3 font-medium">{type.objective}</td>
                    <td className="py-3 px-3 text-muted-foreground">{type.bestFor}</td>
                    <td className="py-3 px-3 text-muted-foreground">
                      {type.objective === 'Brand Awareness' && 'Impressions, Reach, Frequency'}
                      {type.objective === 'Lead Generation' && 'Leads, CPL, Form Submissions'}
                      {type.objective === 'Conversions' && 'Conversions, CPA, ROAS, Revenue'}
                      {type.objective === 'Engagement' && 'Likes, Comments, Shares, Saves'}
                      {type.objective === 'Traffic' && 'Clicks, CTR, CPC, Landing Page Views'}
                      {type.objective === 'App Installs' && 'Installs, CPI, Cost per Install'}
                    }
                    <td className="py-3 px-3 text-muted-foreground">
                      {type.objective === 'Brand Awareness' && 'Learn More'}
                      {type.objective === 'Lead Generation' && 'Sign Up / Download'}
                      {type.objective === 'Conversions' && 'Buy Now / Get Started'}
                      {type.objective === 'Engagement' && 'Like / Comment / Share'}
                      {type.objective === 'Traffic' && 'Visit Website / Read More'}
                      {type.objective === 'App Installs' && 'Install Now'}
                    }
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Budget Tips */}
      <Card className="mb-8 border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-900/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-amber-500" />
            Budget Tips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {BUDGET_TIPS.map((tip, i) => (
              <li key={i} className="flex items-start gap-2">
                <Zap className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium">{tip.title}</span>
                  <p className="text-sm text-muted-foreground">{tip.description}</p>
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Creative Best Practices */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ZapIcon className="h-5 w-5 text-primary" />
            Creative Best Practices
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {CREATIVE_BEST_PRACTICES.map((tip, i) => (
              <li key={i} className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium">{tip.title}</span>
                  <p className="text-sm text-muted-foreground">{tip.description}</p>
                </div>
              </li>
            ))}
          </ul>
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
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[
              { title: 'Set Up Tracking', href: '/analytics', desc: 'Configure conversion tracking and pixels', icon: Database },
              { title: 'Build Workflows', href: '/workflows/new', desc: 'Automate campaign optimization', icon: Zap },
              { title: 'Invite Team', href: '/team', desc: 'Collaborate with your team', icon: Users },
            ].map((item) => (
              <Link key={item.title} href={item.href} className="flex items-start gap-3 p-4 rounded-lg border hover:bg-accent transition-colors">
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