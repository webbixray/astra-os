'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useOnboardingStore, onboardingSteps } from '@/stores/onboardingStore';
import { Check, ChevronRight, Sparkles, Users, Megaphone, BarChart2, Gift, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';

const stepIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  welcome: Sparkles,
  organization: Users,
  brand: Megaphone,
  channels: BarChart2,
  team: Users,
  first_campaign: BarChart2,
  sample_data: Gift,
};

export default function OnboardingPage() {
  const router = useRouter();
  const {
    currentStep,
    setCurrentStep,
    completeStep,
    organization,
    setOrganization,
    brandVoice,
    setBrandVoice,
    channels,
    addChannel,
    updateChannel,
    teamInvites,
    addTeamInvite,
    removeTeamInvite,
    firstCampaign,
    setFirstCampaign,
    sampleDataOptions,
    setSampleDataOptions,
    sampleDataProvisioned,
    setSampleDataProvisioned,
    getProgress,
    getNextStep,
    isStepAccessible,
    isStepCompleted,
  } = useOnboardingStore();

  const [mounted, setMounted] = useState(false);
  const [organizationForm, setOrganizationForm] = useState({
    name: organization?.name || '',
    slug: organization?.slug || '',
    industry: organization?.industry || '',
    company_size: organization?.company_size || '',
    website: organization?.website || '',
  });
  const [brandForm, setBrandForm] = useState({
    name: brandVoice?.name || '',
    description: brandVoice?.description || '',
    tone_attributes: brandVoice?.tone_attributes || {},
    vocabulary_preferences: brandVoice?.vocabulary_preferences || { preferred: [], avoid: [] },
    style_guide: brandVoice?.style_guide || '',
    example_content: brandVoice?.example_content || '',
  });
  const [campaignForm, setCampaignForm] = useState({
    name: firstCampaign?.name || '',
    description: firstCampaign?.description || '',
    objective: firstCampaign?.objective || 'brand_awareness',
    budget_cents: firstCampaign?.budget_cents || 100000,
    daily_budget_cents: firstCampaign?.daily_budget_cents || 5000,
    platforms: firstCampaign?.platforms || ['meta'],
    target_audience: firstCampaign?.target_audience || {},
  });
  const [newInviteEmail, setNewInviteEmail] = useState('');
  const [newInviteRole, setNewInviteRole] = useState<'admin' | 'member' | 'viewer'>('member');

  useEffect(() => {
    setMounted(true);
  }, []);

  const progress = getProgress();

  const handleNext = () => {
    completeStep(currentStep);
    const nextStep = getNextStep();
    if (nextStep) {
      setCurrentStep(nextStep);
    } else {
      router.push('/dashboard');
    }
  };

  const handleBack = () => {
    const currentIndex = onboardingSteps.findIndex((s) => s.id === currentStep);
    if (currentIndex > 0) {
      const prevStep = onboardingSteps[currentIndex - 1];
      if (prevStep) {
        setCurrentStep(prevStep.id);
      }
    }
  };

  const currentStepData = onboardingSteps.find((s) => s.id === currentStep);

  if (!mounted) return null;
  if (!currentStepData) return null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-muted/30 to-background">
      {/* Progress Bar */}
      <div className="sticky top-0 z-10 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto max-w-4xl px-4 py-3">
          <Progress value={progress} className="h-2" />
          <div className="flex justify-between mt-2 text-xs text-muted-foreground">
            {onboardingSteps.map((step) => (
              <span
                key={step.id}
                className={`flex items-center gap-1 ${
                  isStepCompleted(step.id)
                    ? 'text-primary'
                    : step.id === currentStep
                    ? 'text-foreground font-medium'
                    : isStepAccessible(step.id)
                    ? 'text-muted-foreground'
                    : 'text-muted-foreground/50'
                }`}
              >
                {isStepCompleted(step.id) && <Check className="h-3 w-3" />}
                {step.title}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-4xl px-4 py-8">
        {/* Step Indicator */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            {(() => {
              const Icon = stepIcons[currentStep];
              if (!Icon) return null;
              return <Icon className="h-10 w-10 text-primary" />;
            })()}
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{currentStepData.title}</h1>
              <p className="text-muted-foreground">{currentStepData.description}</p>
            </div>
          </div>
        </div>

        {/* Step Content */}
        <div className="space-y-6">
          {currentStep === 'welcome' && <WelcomeStep onNext={handleNext} />}
          {currentStep === 'organization' && (
            <OrganizationStep
              formData={organizationForm}
              onChange={setOrganizationForm}
              onSave={(data) => {
                setOrganization(data);
                handleNext();
              }}
            />
          )}
          {currentStep === 'brand' && (
            <BrandVoiceStep
              formData={brandForm}
              onChange={setBrandForm}
              onSave={(data) => {
                setBrandVoice(data);
                handleNext();
              }}
            />
          )}
          {currentStep === 'channels' && (
            <ChannelsStep
              channels={channels}
              onAddChannel={addChannel}
              onUpdateChannel={updateChannel}
              onNext={handleNext}
            />
          )}
          {currentStep === 'team' && (
            <TeamStep
              invites={teamInvites}
              newInviteEmail={newInviteEmail}
              setNewInviteEmail={setNewInviteEmail}
              newInviteRole={newInviteRole}
              setNewInviteRole={setNewInviteRole}
              onAddInvite={addTeamInvite}
              onRemoveInvite={removeTeamInvite}
              onNext={handleNext}
            />
          )}
          {currentStep === 'first_campaign' && (
            <FirstCampaignStep
              formData={campaignForm}
              onChange={setCampaignForm}
              onSave={(data) => {
                setFirstCampaign(data);
                handleNext();
              }}
            />
          )}
          {currentStep === 'sample_data' && (
            <SampleDataStep
              options={sampleDataOptions}
              onChange={setSampleDataOptions}
              provisioned={sampleDataProvisioned}
              onProvision={() => setSampleDataProvisioned(true)}
              onNext={handleNext}
            />
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-6 border-t">
          <Button variant="outline" onClick={handleBack} disabled={currentStep === 'welcome'}>
            <ChevronRight className="mr-2 h-4 w-4 rotate-180" />
            Back
          </Button>
          <div className="flex gap-3">
            {currentStep !== 'welcome' && (
              <Button variant="outline" onClick={handleBack}>
                <ChevronRight className="mr-2 h-4 w-4 rotate-180" />
                Back
              </Button>
            )}
            <Button
              onClick={handleNext}
              disabled={currentStep !== 'welcome' && !isStepCompleted(currentStep)}
            >
              {getNextStep() ? 'Continue' : 'Get Started'}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="space-y-8">
      <Card>
        <CardContent className="pt-6">
          <div className="text-center space-y-6">
            <Sparkles className="h-16 w-16 text-primary mx-auto" />
            <h2 className="text-2xl font-bold">Welcome to ASTRA OS</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              The AI-native marketing operating system that helps you plan, execute, and optimize
              campaigns with hierarchical AI agents — all with human governance built in.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
              <FeatureCard
                icon={Users}
                title="Agent Workforce"
                description="CEO → Directors → Specialists hierarchy for end-to-end campaign execution"
              />
              <FeatureCard
                icon={Megaphone}
                title="Brand Memory"
                description="Persistent knowledge graph with brand voice, guidelines, and campaign history"
              />
              <FeatureCard
                icon={BarChart2}
                title="Governed Autonomy"
                description="Advisory → Semi-auto → Full-auto with approval gates and audit trails"
              />
            </div>

            <div className="mt-8 p-4 bg-primary/5 rounded-lg border border-primary/20">
              <h3 className="font-semibold mb-2">What you'll set up in the next few minutes:</h3>
              <ul className="text-sm text-muted-foreground space-y-1 text-left max-w-md mx-auto">
                <li>• Your organization profile</li>
                <li>• Brand voice and guidelines</li>
                <li>• Ad platform connections (Meta, Google, LinkedIn, etc.)</li>
                <li>• Team invitations</li>
                <li>• Your first AI-assisted campaign</li>
                <li>• Optional sample data to explore</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="text-center">
        <Button size="lg" onClick={onNext} className="w-full max-w-md">
          Let's Get Started
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, description }: { icon: React.ComponentType<{ className?: string }>; title: string; description: string }) {
  return (
    <Card className="h-full">
      <CardContent className="pt-6 text-center">
        <Icon className="h-10 w-10 text-primary mx-auto mb-3" />
        <h3 className="font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground mt-1">{description}</p>
      </CardContent>
    </Card>
  );
}

function OrganizationStep({
  formData,
  onChange,
  onSave,
}: {
  formData: any;
  onChange: (data: any) => void;
  onSave: (data: any) => void;
}) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const slug = formData.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
    onSave({ ...formData, slug });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Organization Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Organization Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => onChange({ ...formData, name: e.target.value })}
                placeholder="Acme Marketing"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="slug">Slug *</Label>
              <Input
                id="slug"
                value={formData.slug}
                onChange={(e) => onChange({ ...formData, slug: e.target.value })}
                placeholder="acme-marketing"
                required
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Select value={formData.industry} onValueChange={(value) => onChange({ ...formData, industry: value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select industry" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="technology">Technology</SelectItem>
                  <SelectItem value="ecommerce">E-commerce</SelectItem>
                  <SelectItem value="finance">Financial Services</SelectItem>
                  <SelectItem value="healthcare">Healthcare</SelectItem>
                  <SelectItem value="education">Education</SelectItem>
                  <SelectItem value="media">Media & Entertainment</SelectItem>
                  <SelectItem value="real_estate">Real Estate</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="company_size">Company Size</Label>
              <Select value={formData.company_size} onValueChange={(value) => onChange({ ...formData, company_size: value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select size" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1-10">1-10 employees</SelectItem>
                  <SelectItem value="11-50">11-50 employees</SelectItem>
                  <SelectItem value="51-200">51-200 employees</SelectItem>
                  <SelectItem value="201-500">201-500 employees</SelectItem>
                  <SelectItem value="501-1000">501-1000 employees</SelectItem>
                  <SelectItem value="1000+">1000+ employees</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="website">Website (optional)</Label>
            <Input
              id="website"
              type="url"
              value={formData.website}
              onChange={(e) => onChange({ ...formData, website: e.target.value })}
              placeholder="https://acme.com"
            />
          </div>
        </CardContent>
      </Card>

      <div className="text-center">
        <Button type="submit" size="lg" className="w-full max-w-md">
          Save & Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}

function BrandVoiceStep({
  formData,
  onChange,
  onSave,
}: {
  formData: any;
  onChange: (data: any) => void;
  onSave: (data: any) => void;
}) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  const toneAttributes = [
    { key: 'professional', label: 'Professional', description: 'Formal, authoritative, trustworthy' },
    { key: 'friendly', label: 'Friendly', description: 'Warm, approachable, conversational' },
    { key: 'innovative', label: 'Innovative', description: 'Forward-thinking, cutting-edge, bold' },
    { key: 'empathetic', label: 'Empathetic', description: 'Understanding, caring, human-centric' },
    { key: 'witty', label: 'Witty', description: 'Clever, humorous, engaging' },
    { key: 'direct', label: 'Direct', description: 'Clear, concise, no-nonsense' },
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Define Your Brand Voice</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="brand_name">Brand Voice Name *</Label>
            <Input
              id="brand_name"
              value={formData.name}
              onChange={(e) => onChange({ ...formData, name: e.target.value })}
              placeholder="Acme Professional Voice"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => onChange({ ...formData, description: e.target.value })}
              placeholder="A professional yet approachable voice that builds trust through expertise..."
              required
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label>Tone Attributes (0-100)</Label>
            <p className="text-sm text-muted-foreground">
              Adjust sliders to define your brand's personality. Higher values = more of that trait.
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              {toneAttributes.map((attr) => (
                <div key={attr.key} className="space-y-2">
                  <div className="flex justify-between">
                    <span className="font-medium">{attr.label}</span>
                    <span className="text-muted-foreground">{formData.tone_attributes[attr.key] || 50}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={formData.tone_attributes[attr.key] || 50}
                    onChange={(e) =>
                      onChange({
                        ...formData,
                        tone_attributes: {
                          ...formData.tone_attributes,
                          [attr.key]: parseInt(e.target.value),
                        },
                      })
                    }
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground">{attr.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="style_guide">Style Guide (optional)</Label>
            <Textarea
              id="style_guide"
              value={formData.style_guide}
              onChange={(e) => onChange({ ...formData, style_guide: e.target.value })}
              placeholder="Oxford comma required. Use active voice. Avoid jargon. Max 2 emojis per post..."
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="example_content">Example Content (optional)</Label>
            <Textarea
              id="example_content"
              value={formData.example_content}
              onChange={(e) => onChange({ ...formData, example_content: e.target.value })}
              placeholder="Paste a piece of content that perfectly represents your brand voice..."
              rows={4}
            />
          </div>
        </CardContent>
      </Card>

      <div className="text-center">
        <Button type="submit" size="lg" className="w-full max-w-md">
          Save & Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}

function ChannelsStep({
  channels,
  onAddChannel,
  onUpdateChannel,
  onNext,
}: {
  channels: any[];
  onAddChannel: (channel: any) => void;
  onUpdateChannel: (platform: string, data: any) => void;
  onNext: () => void;
}) {
  const platforms = [
    { id: 'meta', name: 'Meta (Facebook/Instagram)', icon: '📘' },
    { id: 'google', name: 'Google Ads', icon: '🔍' },
    { id: 'linkedin', name: 'LinkedIn Ads', icon: '💼' },
    { id: 'tiktok', name: 'TikTok Ads', icon: '🎵' },
    { id: 'twitter', name: 'X (Twitter) Ads', icon: '🐦' },
    { id: 'snapchat', name: 'Snapchat Ads', icon: '👻' },
  ];

  const connectedPlatforms = channels.filter((c) => c.connected).map((c) => c.platform);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Connect Your Ad Platforms</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            Connect your ad accounts to enable AI-powered campaign management, optimization, and reporting.
            You can skip this and connect later.
          </p>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {platforms.map((platform) => {
              const channel = channels.find((c) => c.platform === platform.id);
              const isConnected = channel?.connected;
              
              return (
                <Card
                  key={platform.id}
                  className={`relative cursor-pointer transition-all ${
                    isConnected ? 'ring-2 ring-primary border-primary' : ''
                  }`}
                  onClick={() => {
                    if (!isConnected) {
                      onAddChannel({ platform: platform.id, connected: true });
                    }
                  }}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-3xl">{platform.icon}</span>
                      {isConnected && <Check className="h-5 w-5 text-primary" />}
                    </div>
                    <h3 className="font-medium">{platform.name}</h3>
                    {isConnected && channel && (
                      <p className="text-sm text-muted-foreground mt-1">
                        {channel.account_name || `Account ${channel.account_id?.slice(0, 8)}...`}
                      </p>
                    )}
                    {!isConnected && (
                      <Button variant="outline" className="mt-3 w-full" size="sm" onClick={(e) => e.stopPropagation()}>
                        Connect
                      </Button>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {connectedPlatforms.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Connected Accounts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {channels.filter((c) => c.connected).map((channel) => {
                const platform = platforms.find((p) => p.id === channel.platform);
                return (
                  <div key={channel.platform} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{platform?.icon}</span>
                      <div>
                        <p className="font-medium">{platform?.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {channel.account_name || channel.account_id}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => onUpdateChannel(channel.platform, { connected: false })}>
                      Disconnect
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="text-center">
        <Button size="lg" onClick={onNext} className="w-full max-w-md">
          Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
        <p className="mt-3 text-sm text-muted-foreground">
          You can connect more platforms later from Settings → Integrations
        </p>
      </div>
    </div>
  );
}

function TeamStep({
  invites,
  newInviteEmail,
  setNewInviteEmail,
  newInviteRole,
  setNewInviteRole,
  onAddInvite,
  onRemoveInvite,
  onNext,
}: {
  invites: any[];
  newInviteEmail: string;
  setNewInviteEmail: (email: string) => void;
  newInviteRole: 'admin' | 'member' | 'viewer';
  setNewInviteRole: (role: 'admin' | 'member' | 'viewer') => void;
  onAddInvite: (invite: any) => void;
  onRemoveInvite: (email: string) => void;
  onNext: () => void;
}) {
  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (newInviteEmail && !invites.some((i) => i.email === newInviteEmail)) {
      onAddInvite({ email: newInviteEmail, role: newInviteRole as any });
      setNewInviteEmail('');
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Invite Your Team</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <p className="text-muted-foreground">
            Add team members who will collaborate on campaigns. They'll receive an email invitation.
          </p>

          <form onSubmit={handleAdd} className="flex gap-2">
            <div className="flex-1 space-y-2">
              <Label htmlFor="invite_email">Email Address</Label>
              <Input
                id="invite_email"
                type="email"
                value={newInviteEmail}
                onChange={(e) => setNewInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite_role">Role</Label>
              <Select value={newInviteRole} onValueChange={(value) => setNewInviteRole(value as 'admin' | 'member' | 'viewer')}>
                <SelectTrigger id="invite_role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="member">Member</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button type="submit" className="h-10">
              Add
            </Button>
          </form>

          {invites.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium">Invited Team Members</h4>
              {invites.map((invite) => (
                <div key={invite.email} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <span className="text-primary font-medium">
                        {invite.email.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium">{invite.email}</p>
                      <p className="text-sm text-muted-foreground capitalize">{invite.role}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => onRemoveInvite(invite.email)}>
                    Remove
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="text-center">
        <Button size="lg" onClick={onNext} className="w-full max-w-md">
          Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
        <p className="mt-3 text-sm text-muted-foreground">
          {invites.length === 0 ? 'Skip for now' : 'Invitations will be sent after setup'}
        </p>
      </div>
    </div>
  );
}

function FirstCampaignStep({
  formData,
  onChange,
  onSave,
}: {
  formData: any;
  onChange: (data: any) => void;
  onSave: (data: any) => void;
}) {
  const objectives = [
    { value: 'brand_awareness', label: 'Brand Awareness', description: 'Reach new audiences and increase brand recognition' },
    { value: 'lead_generation', label: 'Lead Generation', description: 'Capture qualified leads for your sales team' },
    { value: 'conversions', label: 'Conversions', description: 'Drive purchases, sign-ups, or other valuable actions' },
    { value: 'traffic', label: 'Website Traffic', description: 'Send visitors to your website or landing page' },
    { value: 'engagement', label: 'Engagement', description: 'Increase likes, comments, shares, and video views' },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Create Your First Campaign</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="campaign_name">Campaign Name *</Label>
            <Input
              id="campaign_name"
              value={formData.name}
              onChange={(e) => onChange({ ...formData, name: e.target.value })}
              placeholder="Q1 Brand Launch Campaign"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => onChange({ ...formData, description: e.target.value })}
              placeholder="Launch campaign for our new product line across social and search..."
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label>Campaign Objective *</Label>
            <div className="grid gap-3 md:grid-cols-2">
              {objectives.map((obj) => (
                <label
                  key={obj.value}
                  className={`relative cursor-pointer p-4 border rounded-lg transition-all ${
                    formData.objective === obj.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <input
                    type="radio"
                    name="objective"
                    value={obj.value}
                    checked={formData.objective === obj.value}
                    onChange={(e) => onChange({ ...formData, objective: e.target.value })}
                    className="sr-only"
                  />
                  <div className="font-medium">{obj.label}</div>
                  <div className="text-sm text-muted-foreground mt-1">{obj.description}</div>
                </label>
              ))}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="total_budget">Total Budget (USD)</Label>
              <Input
                id="total_budget"
                type="number"
                value={formData.budget_cents / 100}
                onChange={(e) => onChange({ ...formData, budget_cents: parseFloat(e.target.value) * 100 })}
                placeholder="1000"
                min="100"
                step="100"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="daily_budget">Daily Budget (USD)</Label>
              <Input
                id="daily_budget"
                type="number"
                value={formData.daily_budget_cents / 100}
                onChange={(e) => onChange({ ...formData, daily_budget_cents: parseFloat(e.target.value) * 100 })}
                placeholder="50"
                min="10"
                step="10"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Platforms</Label>
            <div className="flex flex-wrap gap-2">
              {['meta', 'google', 'linkedin', 'tiktok'].map((platform) => (
                <label
                  key={platform}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm cursor-pointer transition-colors ${
                    formData.platforms.includes(platform)
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={formData.platforms.includes(platform)}
                    onChange={(e) =>
                      onChange({
                        ...formData,
                        platforms: e.target.checked
                          ? [...formData.platforms, platform]
                          : formData.platforms.filter((p: string) => p !== platform),
                      })
                    }
                    className="sr-only"
                  />
                  {platform.charAt(0).toUpperCase() + platform.slice(1)}
                </label>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="text-center">
        <Button type="submit" size="lg" className="w-full max-w-md">
          Create Campaign
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}

function SampleDataStep({
  options,
  onChange,
  provisioned,
  onProvision,
  onNext,
}: {
  options: any;
  onChange: (options: any) => void;
  provisioned: boolean;
  onProvision: () => void;
  onNext: () => void;
}) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Explore with Sample Data</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <p className="text-muted-foreground">
            Provision sample campaigns, templates, and brand voice examples to explore ASTRA OS features
            before creating your own. This data is completely separate from your real data.
          </p>

          <div className="space-y-4">
            {[
              { key: 'includeTemplates', label: 'Campaign Templates', description: 'Pre-built campaign structures for common objectives' },
              { key: 'includeBrandVoice', label: 'Sample Brand Voices', description: 'Example brand voice configurations for different industries' },
            ].map((item) => (
              <label key={item.key} className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-muted/50">
                <input
                  type="checkbox"
                  checked={options[item.key]}
                  onChange={(e) => onChange({ [item.key]: e.target.checked })}
                  className="h-4 w-4 rounded border-input"
                />
                <div>
                  <p className="font-medium">{item.label}</p>
                  <p className="text-sm text-muted-foreground">{item.description}</p>
                </div>
              </label>
            ))}

            <div className="space-y-2">
              <Label>Campaign Types to Include</Label>
              <div className="flex flex-wrap gap-2">
                {['social', 'search', 'email', 'display', 'video'].map((type) => (
                  <label key={type} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm cursor-pointer bg-muted hover:bg-muted/80">
                    <input
                      type="checkbox"
                      checked={options.campaignTypes.includes(type)}
                      onChange={(e) =>
                        onChange({
                          campaignTypes: e.target.checked
                            ? [...options.campaignTypes, type]
                            : options.campaignTypes.filter((t: string) => t !== type),
                        })
                      }
                      className="sr-only"
                    />
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </label>
                ))}
              </div>
            </div>
          </div>

          {!provisioned ? (
            <Button onClick={onProvision} className="w-full" size="lg">
              Provision Sample Data
            </Button>
          ) : (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
              ✓ Sample data provisioned successfully! You can now explore the dashboard.
            </div>
          )}
        </CardContent>
      </Card>

      <div className="text-center">
        <Button size="lg" onClick={onNext} className="w-full max-w-md">
          {provisioned ? 'Enter Dashboard' : 'Skip & Enter Dashboard'}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}