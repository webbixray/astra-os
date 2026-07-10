'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useCreateCampaign } from '@/features/campaigns/api/useCampaigns';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const CHANNELS = ['email', 'social', 'ads', 'seo', 'content'] as const;
const OBJECTIVES = ['awareness', 'consideration', 'conversion'] as const;

const campaignSchema = z.object({
  name: z.string().min(1, 'Campaign name is required').max(100, 'Name is too long'),
  description: z.string().max(500, 'Description is too long').optional().default(''),
  budget_amount: z.coerce.number().positive('Budget must be positive').optional(),
  budget_currency: z.string().default('USD'),
  start_date: z.string().optional().default(''),
  end_date: z.string().optional().default(''),
  objective: z.string().optional().default(''),
  channels: z.array(z.string()).min(1, 'Select at least one channel'),
});

type FormData = z.infer<typeof campaignSchema>;

interface FieldErrors {
  [key: string]: string | undefined;
}

const CURRENCY_OPTIONS = [
  { value: 'USD', label: 'USD' },
  { value: 'EUR', label: 'EUR' },
  { value: 'GBP', label: 'GBP' },
];


export default function NewCampaignPage() {
  const router = useRouter();
  const { orgId } = useOrg();
  const createCampaign = useCreateCampaign();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    budget_amount: '',
    budget_currency: 'USD',
    start_date: '',
    end_date: '',
    objective: '',
    channels: [] as string[],
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateField = useCallback((field: string, value: string | string[]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  }, []);

  const toggleChannel = useCallback((channel: string) => {
    setFormData((prev) => {
      const channels = prev.channels.includes(channel)
        ? prev.channels.filter((c) => c !== channel)
        : [...prev.channels, channel];
      setErrors((e) => ({ ...e, channels: undefined }));
      return { ...prev, channels };
    });
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = campaignSchema.safeParse({
      ...formData,
      budget_amount: formData.budget_amount ? parseFloat(formData.budget_amount) : undefined,
    });

    if (!result.success) {
      const fieldErrors: FieldErrors = {};
      for (const issue of result.error.issues) {
        const path = issue.path.join('.');
        if (!fieldErrors[path]) fieldErrors[path] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    setIsSubmitting(true);
    try {
      await createCampaign.mutateAsync({
        organization_id: orgId,
        name: result.data.name,
        description: result.data.description || undefined,
        budget_amount: result.data.budget_amount,
        budget_currency: result.data.budget_currency,
        start_date: result.data.start_date || undefined,
        end_date: result.data.end_date || undefined,
        channels: result.data.channels,
        objective: result.data.objective || undefined,
      });
      router.push('/campaigns');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ErrorBoundary>
    <div className="mx-auto max-w-2xl p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">New Campaign</h1>
        <p className="text-sm text-muted-foreground">
          Set up a new marketing campaign
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="name">Campaign Name</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => updateField('name', e.target.value)}
            placeholder="Summer Sale 2026"
          />
          {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => updateField('description', e.target.value)}
            rows={3}
            placeholder="Campaign description..."
          />
          {errors.description && <p className="text-xs text-destructive">{errors.description}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="budget_amount">Budget</Label>
            <Input
              id="budget_amount"
              type="number"
              value={formData.budget_amount}
              onChange={(e) => updateField('budget_amount', e.target.value)}
              placeholder="5000"
            />
            {errors.budget_amount && <p className="text-xs text-destructive">{errors.budget_amount}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="budget_currency">Currency</Label>
            <Select
              id="budget_currency"
              value={formData.budget_currency}
              onChange={(e) => updateField('budget_currency', e.target.value)}
              options={CURRENCY_OPTIONS}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start_date">Start Date</Label>
            <Input
              id="start_date"
              type="date"
              value={formData.start_date}
              onChange={(e) => updateField('start_date', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="end_date">End Date</Label>
            <Input
              id="end_date"
              type="date"
              value={formData.end_date}
              onChange={(e) => updateField('end_date', e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Channels</Label>
          <div className="flex flex-wrap gap-2">
            {CHANNELS.map((channel) => (
              <button
                key={channel}
                type="button"
                onClick={() => toggleChannel(channel)}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                  formData.channels.includes(channel)
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground hover:bg-accent'
                }`}
              >
                {channel}
              </button>
            ))}
          </div>
          {errors.channels && <p className="text-xs text-destructive">{errors.channels}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="objective">Objective</Label>
          <Select
            id="objective"
            value={formData.objective}
            onChange={(e) => updateField('objective', e.target.value)}
            placeholder="Select objective"
            options={OBJECTIVES.map((o) => ({ value: o, label: o.charAt(0).toUpperCase() + o.slice(1) }))}
          />
        </div>

        <div className="flex gap-4 pt-4">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create Campaign'}
          </Button>
          <Button type="button" variant="outline" onClick={() => router.back()}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
    </ErrorBoundary>
  );
}
