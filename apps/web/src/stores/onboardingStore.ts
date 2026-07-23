import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  order: number;
  completed?: boolean;
  optional?: boolean;
}

export interface OrganizationData {
  name: string;
  slug: string;
  industry?: string;
  company_size?: string;
  website?: string;
}

export interface BrandVoiceData {
  name: string;
  description: string;
  tone_attributes: Record<string, number>;
  vocabulary_preferences: {
    preferred: string[];
    avoid: string[];
  };
  style_guide: string;
  example_content: string;
}

export interface ChannelConnection {
  platform: string;
  connected: boolean;
  account_id?: string;
  account_name?: string;
  access_token?: string;
  expires_at?: string;
}

export interface TeamInvite {
  email: string;
  role: 'admin' | 'member' | 'viewer';
  message?: string;
}

export interface CampaignDraft {
  name: string;
  description: string;
  objective: 'brand_awareness' | 'lead_generation' | 'conversions' | 'traffic' | 'engagement';
  budget_cents: number;
  daily_budget_cents: number;
  platforms: string[];
  target_audience: Record<string, any>;
}

export interface OnboardingState {
  // Current step
  currentStep: string;
  completedSteps: string[];
  
  // Step data
  organization: OrganizationData | null;
  brandVoice: BrandVoiceData | null;
  channels: ChannelConnection[];
  teamInvites: TeamInvite[];
  firstCampaign: CampaignDraft | null;
  
  // Sample data
  sampleDataProvisioned: boolean;
  sampleDataOptions: {
    campaignTypes: string[];
    includeTemplates: boolean;
    includeBrandVoice: boolean;
  };
  
  // Actions
  setCurrentStep: (step: string) => void;
  completeStep: (step: string) => void;
  setOrganization: (data: OrganizationData) => void;
  setBrandVoice: (data: BrandVoiceData) => void;
  addChannel: (channel: ChannelConnection) => void;
  updateChannel: (platform: string, data: Partial<ChannelConnection>) => void;
  addTeamInvite: (invite: TeamInvite) => void;
  removeTeamInvite: (email: string) => void;
  setFirstCampaign: (campaign: CampaignDraft) => void;
  setSampleDataOptions: (options: Partial<OnboardingState['sampleDataOptions']>) => void;
  setSampleDataProvisioned: (provisioned: boolean) => void;
  reset: () => void;
  
  // Computed
  getProgress: () => number;
  getNextStep: () => string | null;
  isStepCompleted: (stepId: string) => boolean;
  isStepAccessible: (stepId: string) => boolean;
}

const ONBOARDING_STEPS: OnboardingStep[] = [
  { id: 'welcome', title: 'Welcome', description: 'Get to know ASTRA OS', order: 1 },
  { id: 'organization', title: 'Organization', description: 'Set up your organization details', order: 2 },
  { id: 'brand', title: 'Brand Voice', description: 'Define your brand personality', order: 3 },
  { id: 'channels', title: 'Connect Channels', description: 'Link your ad accounts and social profiles', order: 4 },
  { id: 'team', title: 'Invite Team', description: 'Add colleagues to collaborate', order: 5 },
  { id: 'first_campaign', title: 'First Campaign', description: 'Create your first AI-assisted campaign', order: 6 },
  { id: 'sample_data', title: 'Try Sample Data', description: 'Explore with pre-built campaigns and templates', order: 7 },
];

const initialState = {
  currentStep: 'welcome',
  completedSteps: [],
  organization: null,
  brandVoice: null,
  channels: [],
  teamInvites: [],
  firstCampaign: null,
  sampleDataProvisioned: false,
  sampleDataOptions: {
    campaignTypes: ['social', 'search', 'email'],
    includeTemplates: true,
    includeBrandVoice: true,
  },
};

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setCurrentStep: (step: string) => set({ currentStep: step }),
      
      completeStep: (step: string) =>
        set((state) => ({
          completedSteps: [...new Set([...state.completedSteps, step])],
          currentStep: get().getNextStep() || step,
        })),
      
      setOrganization: (data: OrganizationData) => set({ organization: data }),
      
      setBrandVoice: (data: BrandVoiceData) => set({ brandVoice: data }),
      
      addChannel: (channel: ChannelConnection) =>
        set((state) => ({
          channels: [...state.channels.filter((c) => c.platform !== channel.platform), channel],
        })),
      
      updateChannel: (platform: string, data: Partial<ChannelConnection>) =>
        set((state) => ({
          channels: state.channels.map((c) =>
            c.platform === platform ? { ...c, ...data } : c
          ),
        })),
      
      addTeamInvite: (invite: TeamInvite) =>
        set((state) => ({
          teamInvites: [...state.teamInvites.filter((i) => i.email !== invite.email), invite],
        })),
      
      removeTeamInvite: (email: string) =>
        set((state) => ({
          teamInvites: state.teamInvites.filter((i) => i.email !== email),
        })),
      
      setFirstCampaign: (campaign: CampaignDraft) => set({ firstCampaign: campaign }),
      
      setSampleDataOptions: (options: Partial<OnboardingState['sampleDataOptions']>) =>
        set((state) => ({
          sampleDataOptions: { ...state.sampleDataOptions, ...options },
        })),
      
      setSampleDataProvisioned: (provisioned: boolean) => set({ sampleDataProvisioned: provisioned }),
      
      reset: () => set(initialState),
      
      getProgress: () => {
        const state = get();
        const totalSteps = ONBOARDING_STEPS.length;
        const completedCount = state.completedSteps.length;
        return Math.round((completedCount / totalSteps) * 100);
      },
      
      getNextStep: () => {
        const state = get();
        const currentIndex = ONBOARDING_STEPS.findIndex((s) => s.id === state.currentStep);
        if (currentIndex >= 0 && currentIndex < ONBOARDING_STEPS.length - 1) {
          const nextStep = ONBOARDING_STEPS[currentIndex + 1];
          if (nextStep) return nextStep.id;
        }
        return null;
      },
      
      isStepCompleted: (stepId: string) => get().completedSteps.includes(stepId),
      
      isStepAccessible: (stepId: string) => {
        const state = get();
        const stepIndex = ONBOARDING_STEPS.findIndex((s) => s.id === stepId);
        const currentIndex = ONBOARDING_STEPS.findIndex((s) => s.id === state.currentStep);
        
        // Allow access to completed steps and current step
        if (stepIndex <= currentIndex) return true;
        
        // Allow access to next step if current is completed
        if (stepIndex === currentIndex + 1 && state.completedSteps.includes(state.currentStep)) {
          return true;
        }
        
        return false;
      },
    }),
    {
      name: 'astra-onboarding',
      partialize: (state) => ({
        currentStep: state.currentStep,
        completedSteps: state.completedSteps,
        organization: state.organization,
        brandVoice: state.brandVoice,
        channels: state.channels,
        teamInvites: state.teamInvites,
        firstCampaign: state.firstCampaign,
        sampleDataOptions: state.sampleDataOptions,
        sampleDataProvisioned: state.sampleDataProvisioned,
      }),
    }
  )
);

// Export step definitions for components
export const onboardingSteps = ONBOARDING_STEPS;