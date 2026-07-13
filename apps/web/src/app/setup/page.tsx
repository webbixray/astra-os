'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { api } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Check } from 'lucide-react';

type SetupStep = 'welcome' | 'account' | 'organization' | 'sample-campaigns' | 'ai-provider' | 'complete';

interface SetupData {
  name: string;
  email: string;
  password: string;
  organizationName: string;
  openaiApiKey: string;
  anthropicApiKey: string;
}

const STEP_LABELS = {
  welcome: 'Welcome',
  account: 'Account',
  organization: 'Organization',
  'sample-campaigns': 'Sample Campaigns',
  'ai-provider': 'AI Provider',
  complete: 'Complete',
};

const STEP_ORDER: SetupStep[] = [
  'welcome',
  'account',
  'organization',
  'sample-campaigns',
  'ai-provider',
  'complete',
];

const SAMPLE_CAMPAIGN_OPTIONS = [
  { value: 1, label: '1 Campaign (Quick Start)' },
  { value: 3, label: '3 Campaigns (Recommended)' },
  { value: 5, label: '5 Campaigns (Full Suite)' },
];

const SAMPLE_CAMPAIGN_PREVIEWS = [
  { name: 'Brand Awareness Launch', objective: 'Brand Awareness', budget: 5000, desc: 'Introduce your brand to new audiences' },
  { name: 'Lead Generation Campaign', objective: 'Lead Generation', budget: 3000, desc: 'Generate qualified leads through targeted content' },
  { name: 'Product Launch Campaign', objective: 'Conversions', budget: 4000, desc: 'Drive conversions for new product launch' },
  { name: 'Retargeting Campaign', objective: 'Conversions', budget: 2000, desc: 'Retarget website visitors with personalized offers' },
  { name: 'Thought Leadership Content', objective: 'Brand Awareness', budget: 1500, desc: 'Establish brand authority through educational content' },
];

export default function SetupPage() {
  const router = useRouter();
  const [step, setStep] = useState<SetupStep>('welcome');
  const [sampleCount, setSampleCount] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState({
    name: '',
    email: '',
    password: '',
    organizationName: '',
    openaiApiKey: '',
    anthropicApiKey: '',
  });
  const [createdOrgId, setCreatedOrgId] = useState<string | null>(null);
  const [sampleCampaignsCreated, setSampleCampaignsCreated] = useState<{ id: string; name: string; objective: string; budget: number }[]>([]);

  const updateData = (partial: Partial<typeof data>) => {
    setData((prev) => ({ ...prev, ...partial }));
  };

  const nextStep = () => {
    const currentIndex = STEP_ORDER.indexOf(step);
    if (currentIndex < STEP_ORDER.length - 1) {
      setStep(STEP_ORDER[currentIndex + 1]);
    }
  };

  const prevStep = () => {
    const currentIndex = STEP_ORDER.indexOf(step);
    if (currentIndex > 0) {
      setStep(STEP_ORDER[currentIndex - 1]);
    }
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
      localStorage.setItem('astra_setup_org_id', response.organization_id);
      nextStep();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  const handleOrgSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      nextStep();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create organization');
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

      const response = await api.post('/campaigns/sample', {
        organization_id: orgId,
        count: sampleCount,
      });

      setSampleCampaignsCreated(response.campaigns);
      localStorage.removeItem('astra_setup_org_id');
      nextStep();
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
      nextStep();
    } catch (err) {
      console.warn('AI provider setup skipped:', err);
      nextStep();
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = () => {
    router.push('/dashboard');
  };

  const canGoNext = () => {
    switch (step) {
      case 'account':
        return data.name.length > 0 && data.email.length > 0 && data.password.length >= 8;
      case 'organization':
        return data.organizationName.length > 0;
      case 'sample-campaigns':
        return sampleCount > 0;
      case 'ai-provider':
        return true;
      default:
        return true;
    }
  };

  const progress = ((STEP_ORDER.indexOf(step) + 1) / STEP_ORDER.length) * 100;

  return (
    <div className="flex min-h-screen bg-background">
      <div className="fixed top-0 left-0 right-0 h-1 bg-muted z-50">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <div className="w-full max-w-2xl space-y-8">
          <div className="flex items-center justify-between mb-8">
            {STEP_ORDER.map((s, i) => (
              <div key={s} className="flex flex-col items-center flex-1">
                <div
                  className={`relative flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all ${
                    i < STEP_ORDER.indexOf(step)
                      ? 'bg-primary border-primary text-primary-foreground'
                      : i === STEP_ORDER.indexOf(step)
                      ? 'border-primary bg-background text-primary'
                      : 'border-muted text-muted-foreground bg-background'
                  }`}
                >
                  {i < STEP_ORDER.indexOf(step) ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <span className="text-sm font-medium">{i + 1}</span>
                  )}
                </div>
                <span
                  className={`mt-2 text-xs font-medium text-center transition-colors ${
                    i <= STEP_ORDER.indexOf(step)
                      ? 'text-foreground'
                      : 'text-muted-foreground'
                  }`}
                >
                  {STEP_LABELS[s]}
                </span>
                {i < STEP_ORDER.length - 1 && (
                  <div
                    className="absolute top-5 left-1/2 w-full h-0.5 bg-muted"
                    style={{ width: '50%' }}
                  />
                )}
              </div>
            ))}
          </div>

          <div className="bg-card border rounded-xl p-8 shadow-sm">
            {step === 'welcome' && (
              <div className="space-y-8 text-center">
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">Welcome to Astra OS</h1>
                  <p className="mt-2 text-muted-foreground text-lg">
                    AI-Native Marketing & Business Growth Operating System
                  </p>
                </div>
                <Card>
                  <CardHeader>
                    <CardTitle>What you'll get:</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3 text-left text-muted-foreground">
                      <li className="flex items-center gap-2"><Check className="h-4 w-4 text-primary" /> AI-powered content generation</li>
                      <li className="flex items-center gap-2"><Check className="h-4 w-4 text-primary" /> Automated campaign management</li>
                      <li className="flex items-center gap-2"><Check className="h-4 w-4 text-primary" /> Multi-channel publishing</li>
                      <li className="flex items-center gap-2"><Check className="h-4 w-4 text-primary" /> Advanced analytics & reporting</li>
                      <li className="flex items-center gap-2"><Check className="h-4 w-4 text-primary" /> Team collaboration tools</li>
                      <li className="flex items-center gap-2"><Check className="h-4 w-4 text-primary" /> Shadow mode for safe AI adoption</li>
                    </ul>
                  </CardContent>
                </Card>
                <Button onClick={() => setStep('account')} className="w-full" size="lg">
                  Get Started
                </Button>
              </div>
            )}

            {step === 'account' && (
              <form onSubmit={handleAccountSubmit} className="space-y-6">
                <div className="space-y-2 text-center">
                  <h1 className="text-2xl font-semibold tracking-tight">Create Your Account</h1>
                  <p className="text-sm text-muted-foreground">Set up your admin account to get started</p>
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
                  {error && <p className="text-sm text-destructive">{error}</p>}
                  <Button type="submit" className="w-full" disabled={loading || !canGoNext()}>
                    {loading ? 'Creating account...' : 'Continue'}
                  </Button>
                </div>
                <button
                  type="button"
                  onClick={prevStep}
                  className="text-sm text-muted-foreground hover:text-foreground w-full mt-4"
                >
                  Back
                </button>
              </form>
            )}

            {step === 'organization' && (
              <form onSubmit={handleOrgSubmit} className="space-y-6">
                <div className="space-y-2 text-center">
                  <h1 className="text-2xl font-semibold tracking-tight">Organization Details</h1>
                  <p className="text-sm text-muted-foreground">
                    Set up your organization (optional - we created one for you)
                  </p>
                </div>
                <div className="space-y-4">
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
                  <Button type="submit" className="w-full" disabled={loading || !canGoNext()}>
                    {loading ? 'Creating organization...' : 'Continue'}
                  </Button>
                </div>
                <button
                  type="button"
                  onClick={prevStep}
                  className="text-sm text-muted-foreground hover:text-foreground w-full mt-4"
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
                    <Select value={sampleCount} onValueChange={(v) => setSampleCount(Number(v))}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select count" />
                      </SelectTrigger>
                      <SelectContent>
                        {SAMPLE_CAMPAIGN_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={String(opt.value)}>{opt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      You'll get the first {sampleCount} campaigns from our curated list
                    </p>
                  </div>

                  <div className="space-y-3">
                    <h4 className="font-medium">Campaigns that will be created:</h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {SAMPLE_CAMPAIGN_PREVIEWS.slice(0, sampleCount).map((campaign, i) => (
                        <Card key={i} className="bg-muted/50">
                          <CardContent className="pt-3 pb-3">
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <p className="font-medium">{campaign.name}</p>
                                <p className="text-sm text-muted-foreground">{campaign.desc}</p>
                              </div>
                              <div className="flex flex-col items-end gap-1">
                                <span className="text-xs text-muted-foreground uppercase">{campaign.objective}</span>
                                <span className="font-medium">${campaign.budget.toLocaleString()}</span>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>

                  {error && <p className="text-sm text-destructive">{error}</p>}
                  <Button type="submit" className="w-full" disabled={loading || !canGoNext()}>
                    {loading ? 'Creating campaigns...' : 'Create Sample Campaigns'}
                  </Button>
                  <button
                    type="button"
                    onClick={() => nextStep()}
                    className="w-full text-sm text-muted-foreground hover:text-foreground"
                  >
                    Skip for now
                  </button>
                </div>
                <button
                  type="button"
                  onClick={prevStep}
                  className="text-sm text-muted-foreground hover:text-foreground w-full mt-4"
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
                    Add your API keys to enable AI content generation (optional - you can add later)
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
                    <p className="text-xs text-muted-foreground">For GPT-4o, GPT-4o Mini models</p>
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
                    <p className="text-xs text-muted-foreground">For Claude models (alternative to OpenAI)</p>
                  </div>
                  {error && <p className="text-sm text-destructive">{error}</p>}
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? 'Saving...' : 'Continue'}
                  </Button>
                  <button
                    type="button"
                    onClick={() => nextStep()}
                    className="w-full text-sm text-muted-foreground hover:text-foreground"
                  >
                    Skip for now
                  </button>
                </div>
                <button
                  type="button"
                  onClick={prevStep}
                  className="text-sm text-muted-foreground hover:text-foreground w-full mt-4"
                >
                  Back
                </button>
              </form>
            )}

            {step === 'complete' && (
              <div className="space-y-6 text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                  <Check className="h-8 w-8 text-green-600 dark:text-green-400" />
                </div>
                <div className="space-y-2">
                  <h1 className="text-2xl font-semibold tracking-tight">You're All Set!</h1>
                  <p className="text-sm text-muted-foreground">
                    Your Astra OS instance is ready to use. Let's start growing your business.
                  </p>
                </div>
                <div className="rounded-lg border p-4 text-left space-y-2">
                  <h4 className="font-medium">What's ready:</h4>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>Account & organization created</li>
                    {sampleCampaignsCreated.length > 0 && <li>{sampleCampaignsCreated.length} sample campaigns created</li>}
                    {(data.openaiApiKey || data.anthropicApiKey) && <li>AI provider configured</li>}
                    <li>Ready to create your first campaign</li>
                  </ul>
                </div>
                <Button onClick={handleComplete} className="w-full" size="lg">
                  Go to Dashboard
                </Button>
              </div>
            )}
          </div>

          <div className="flex justify-between pt-4">
            <button
              onClick={prevStep}
              disabled={step === 'welcome'}
              className="text-sm text-muted-foreground hover:text-foreground disabled:opacity-50"
            >
              Back
            </button>
            <div className="text-xs text-muted-foreground">
              Step {STEP_ORDER.indexOf(step) + 1} of {STEP_ORDER.length}
            </div>
            <button
              onClick={nextStep}
              disabled={step === 'complete' || !canGoNext()}
              className="text-sm text-muted-foreground hover:text-foreground disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}