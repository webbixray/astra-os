'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/api';

type SetupStep = 'welcome' | 'account' | 'sample-campaigns' | 'ai-provider' | 'complete';

interface SetupData {
  name: string;
  email: string;
  password: string;
  organizationName: string;
  openaiApiKey: string;
  anthropicApiKey: string;
}

export default function SetupPage() {
  const router = useRouter();
  const [step, setStep] = useState<SetupStep>('welcome');
  const [data, setData] = useState<SetupData>({
      name: '',
      email: '',
      password: '',
      organizationName: '',
      openaiApiKey: '',
      anthropicApiKey: '',
    });
    const [sampleCount, setSampleCount] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updateData = (partial: Partial<SetupData>) => {
    setData((prev) => ({ ...prev, ...partial }));
  };

  const handleAccountSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setError('');
      setLoading(true);

      try {
        const response = await api.post('/auth/signup', {
          name: data.name,
          email: data.email,
          password: data.password,
          organization_name: data.organizationName || `${data.name}'s Organization`,
        });
        // Store organization ID for sample campaigns step
        localStorage.setItem('astra_setup_org_id', response.organization_id);
        setStep('sample-campaigns');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create account');
      } finally {
        setLoading(false);
      }
    };

    const handleSampleCampaignsSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setError('');
      setLoading(true);

      try {
        const orgId = localStorage.getItem('astra_setup_org_id');
        if (!orgId) throw new Error('Organization ID not found');

        await api.post('/campaigns/sample', {
          organization_id: orgId,
          count: sampleCount,
        });
        localStorage.removeItem('astra_setup_org_id');
        setStep('ai-provider');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create sample campaigns');
      } finally {
        setLoading(false);
      }
    };

    const handleAiProviderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (data.openaiApiKey || data.anthropicApiKey) {
        await api.post('/settings/ai-providers', {
          openai_api_key: data.openaiApiKey,
          anthropic_api_key: data.anthropicApiKey,
        });
      }
      setStep('complete');
    } catch (err) {
      setStep('complete');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = () => {
    router.push('/dashboard');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-lg space-y-8 px-4">
        {step === 'welcome' && (
          <div className="space-y-6 text-center">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight">Welcome to Astra OS</h1>
              <p className="text-muted-foreground">
                AI-Native Marketing & Business Growth Operating System
              </p>
            </div>
            <div className="space-y-4 text-left">
              <div className="rounded-lg border p-4">
                <h3 className="font-medium">What you&apos;ll get:</h3>
                <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
                  <li>- AI-powered content generation</li>
                  <li>- Automated campaign management</li>
                  <li>- Multi-channel publishing</li>
                  <li>- Advanced analytics &amp; reporting</li>
                  <li>- Team collaboration tools</li>
                </ul>
              </div>
            </div>
            <Button onClick={() => setStep('account')} className="w-full" size="lg">
              Get Started
            </Button>
          </div>
        )}

        {step === 'account' && (
          <form onSubmit={handleAccountSubmit} className="space-y-6">
            <div className="space-y-2 text-center">
              <h1 className="text-2xl font-semibold tracking-tight">Create Your Account</h1>
              <p className="text-sm text-muted-foreground">
                Set up your admin account to get started
              </p>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  value={data.name}
                  onChange={(e) => updateData({ name: e.target.value })}
                  required
                  placeholder="John Doe"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={data.email}
                  onChange={(e) => updateData({ email: e.target.value })}
                  required
                  placeholder="john@company.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={data.password}
                  onChange={(e) => updateData({ password: e.target.value })}
                  required
                  minLength={8}
                  placeholder="Min. 8 characters"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="org-name">Organization Name</Label>
                <Input
                  id="org-name"
                  value={data.organizationName}
                  onChange={(e) => updateData({ organizationName: e.target.value })}
                  placeholder="My Company (optional)"
                />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Creating account...' : 'Continue'}
              </Button>
            </div>
            <button
              type="button"
              onClick={() => setStep('welcome')}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Back
            </button>
          </form>
        )}

        {step === 'sample-campaigns' && (
          <form onSubmit={handleSampleCampaignsSubmit} className="space-y-6">
            <div className="space-y-2 text-center">
              <h1 className="text-2xl font-semibold tracking-tight">Create Sample Campaigns</h1>
              <p className="text-sm text-muted-foreground">
                We'll set up a few starter campaigns to get you going (you can customize later)
              </p>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="campaign-count">Number of Sample Campaigns</Label>
                <select
                  id="campaign-count"
                  value={sampleCount}
                  onChange={(e) => setSampleCount(Number(e.target.value))}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value={3}>3 Campaigns (Recommended)</option>
                  <option value={5}>5 Campaigns</option>
                  <option value={1}>Just 1</option>
                </select>
                <p className="text-xs text-muted-foreground">
                  Pre-built campaigns for awareness, leads, conversions, and more
                </p>
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Creating campaigns...' : 'Create Sample Campaigns'}
              </Button>
              <button
                type="button"
                onClick={() => setStep('ai-provider')}
                className="w-full text-sm text-muted-foreground hover:text-foreground"
              >
                Skip for now
              </button>
            </div>
            <button
              type="button"
              onClick={() => setStep('account')}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Back
            </button>
          </form>
        )}

        {step === 'ai-provider' && (
          <form onSubmit={handleAiProviderSubmit} className="space-y-6">
            <div className="space-y-2 text-center">
              <h1 className="text-2xl font-semibold tracking-tight">Connect AI Provider</h1>
              <p className="text-sm text-muted-foreground">
                Add at least one AI provider to enable smart features (you can skip this)
              </p>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="openai-key">OpenAI API Key</Label>
                <Input
                  id="openai-key"
                  type="password"
                  value={data.openaiApiKey}
                  onChange={(e) => updateData({ openaiApiKey: e.target.value })}
                  placeholder="sk-..."
                />
                <p className="text-xs text-muted-foreground">
                  For GPT-4o, GPT-4o Mini models
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="anthropic-key">Anthropic API Key</Label>
                <Input
                  id="anthropic-key"
                  type="password"
                  value={data.anthropicApiKey}
                  onChange={(e) => updateData({ anthropicApiKey: e.target.value })}
                  placeholder="sk-ant-..."
                />
                <p className="text-xs text-muted-foreground">
                  For Claude models (alternative to OpenAI)
                </p>
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Saving...' : 'Continue'}
              </Button>
              <button
                type="button"
                onClick={() => setStep('complete')}
                className="w-full text-sm text-muted-foreground hover:text-foreground"
              >
                Skip for now
              </button>
            </div>
            <button
              type="button"
              onClick={() => setStep('account')}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Back
            </button>
          </form>
        )}

        {step === 'complete' && (
          <div className="space-y-6 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
              <span className="text-3xl text-green-600 dark:text-green-400">&#10003;</span>
            </div>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight">You&apos;re All Set!</h1>
              <p className="text-sm text-muted-foreground">
                Your Astra OS instance is ready to use.
              </p>
            </div>
            <div className="space-y-4 text-left">
              <div className="rounded-lg border p-4">
                <h3 className="font-medium">Quick tips:</h3>
                <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
                  <li>- Start by creating your first campaign</li>
                  <li>- Use AI Content to generate marketing copy</li>
                  <li>- Set up your ad accounts in Advertising</li>
                  <li>- Invite team members in Team Settings</li>
                </ul>
              </div>
            </div>
            <Button onClick={handleComplete} className="w-full" size="lg">
              Go to Dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
