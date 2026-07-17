'use client';

import { Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { LegacySelect as Select } from '@/components/ui/select';
import { cn } from '@/lib/utils';

const TONES = [
  'professional',
  'casual',
  'funny',
  'formal',
  'friendly',
  'authoritative',
];

const TONE_EMOJIS: Record<string, string> = {
  professional: '\u{1F4BC}',
  casual: '\u{1F60A}',
  funny: '\u{1F602}',
  formal: '\u{1F3A9}',
  friendly: '\u{1F91D}',
  authoritative: '\u{1F4CA}',
};

interface ContentSettingsPanelProps {
  mode: 'compose' | 'rewrite';
  selectedTemplate: string;
  onTemplateChange: (v: string) => void;
  templateOptions: { value: string; label: string }[];
  currentTemplate: { variables: string[] } | undefined;
  variables: Record<string, string>;
  onVariableChange: (key: string, value: string) => void;
  rewriteInput: string;
  onRewriteInputChange: (v: string) => void;
  selectedVoice: string;
  onVoiceChange: (v: string) => void;
  voiceOptions: { value: string; label: string }[];
  tone: string;
  onToneChange: (t: string) => void;
  instructions: string;
  onInstructionsChange: (v: string) => void;
  instructionsError: string;
  onGenerate: () => void;
  isPending: boolean;
}

export function ContentSettingsPanel({
  mode,
  selectedTemplate,
  onTemplateChange,
  templateOptions,
  currentTemplate,
  variables,
  onVariableChange,
  rewriteInput,
  onRewriteInputChange,
  selectedVoice,
  onVoiceChange,
  voiceOptions,
  tone,
  onToneChange,
  instructions,
  onInstructionsChange,
  instructionsError,
  onGenerate,
  isPending,
}: ContentSettingsPanelProps) {
  return (
    <div className="col-span-1 space-y-4">
      <div className="rounded-lg border bg-card p-4">
        <h2 className="mb-3 text-sm font-medium">
          {mode === 'compose' ? 'Content Settings' : 'Rewrite Settings'}
        </h2>

        {mode === 'compose' && (
          <div className="space-y-3">
            <div className="space-y-1">
              <Label className="text-xs">Template</Label>
              <Select
                value={selectedTemplate}
                onChange={(e) => onTemplateChange(e.target.value)}
                options={[
                  { value: '', label: 'Select template...' },
                  ...templateOptions,
                ]}
              />
            </div>

            {currentTemplate && currentTemplate.variables.length > 0 && (
              <div className="space-y-2">
                <Label className="text-xs">Variables</Label>
                {currentTemplate.variables.map((v) => (
                  <Input
                    key={v}
                    placeholder={v.replace('_', ' ')}
                    value={variables[v] || ''}
                    onChange={(e) => onVariableChange(v, e.target.value)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {mode === 'rewrite' && (
          <Textarea
            placeholder="Paste content to rewrite..."
            className="h-32"
            aria-label="Content to rewrite"
            value={rewriteInput}
            onChange={(e) => onRewriteInputChange(e.target.value)}
          />
        )}

        <div className="mt-3 space-y-3">
          <div className="space-y-1">
            <Label className="text-xs">Brand Voice</Label>
            <Select
              value={selectedVoice}
              onChange={(e) => onVoiceChange(e.target.value)}
              options={[
                { value: '', label: 'Default tone' },
                ...voiceOptions,
              ]}
            />
          </div>

          <div className="space-y-1">
            <Label className="text-xs">Tone</Label>
            <div className="mt-1 grid grid-cols-2 gap-1">
              {TONES.map((t) => (
                <button
                  key={t}
                  onClick={() => onToneChange(t)}
                  className={cn(
                    'rounded-md px-2 py-1.5 text-xs font-medium transition-colors',
                    tone === t
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-accent',
                  )}
                >
                  {TONE_EMOJIS[t]} {t}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <Label className="text-xs">Instructions</Label>
            <Textarea
              placeholder="Additional instructions..."
              className="h-20"
              value={instructions}
              onChange={(e) => onInstructionsChange(e.target.value)}
              error={instructionsError}
            />
            {instructionsError && (
              <p className="text-xs text-destructive">{instructionsError}</p>
            )}
          </div>

          <Button
            className="w-full"
            onClick={onGenerate}
            disabled={isPending}
          >
            {isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            {mode === 'compose' ? 'Generate' : 'Rewrite'}
          </Button>
        </div>
      </div>
    </div>
  );
}
