'use client';

import { useState, useEffect, useMemo } from 'react';
import { z } from 'zod';
import { Sparkles, FileText, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  useBrandVoices,
  useContentTemplates,
  useGenerateContent,
  useRewriteContent,
  useSEOScore,
} from '@/features/ai-content/api/useContentGen';
import { useOrg } from '@/lib/org';
import dynamic from 'next/dynamic';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const ContentSettingsPanel = dynamic(
  () => import('./content-settings-panel').then((m) => ({ default: m.ContentSettingsPanel })),
  { ssr: false, loading: () => <div className="animate-pulse rounded-lg border bg-card p-6 h-96" /> },
);

const ContentResultPanel = dynamic(
  () => import('./content-result-panel').then((m) => ({ default: m.ContentResultPanel })),
  { ssr: false, loading: () => <div className="animate-pulse rounded-lg border bg-card p-6 h-96" /> },
);

const instructionsSchema = z.string().max(1000, 'Instructions too long').optional();

export default function AIContentPage() {
  const { orgId } = useOrg();
  const { data: voices } = useBrandVoices(orgId);
  const { data: templates } = useContentTemplates(orgId);
  const generateMutation = useGenerateContent();
  const rewriteMutation = useRewriteContent();
  const seoMutation = useSEOScore();

  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('');
  const [tone, setTone] = useState('professional');
  const [instructions, setInstructions] = useState('');
  const [instructionsError, setInstructionsError] = useState('');
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [result, setResult] = useState<{
    content: string;
    sections: Record<string, string>;
    template_name: string;
    content_type: string;
  } | null>(null);
  const [editedContent, setEditedContent] = useState('');
  const [seoScore, setSeoScore] = useState<{
    score: number;
    rating: string;
    details: Record<string, unknown>;
  } | null>(null);
  const [mode, setMode] = useState<'compose' | 'rewrite'>('compose');
  const [rewriteInput, setRewriteInput] = useState('');

  const currentTemplate = templates?.find((t) => t.id === selectedTemplate);

  const templateOptions = useMemo(
    () =>
      (templates ?? []).map((t) => ({
        value: t.id,
        label: `${t.name} (${t.content_type})`,
      })),
    [templates],
  );

  const voiceOptions = useMemo(
    () =>
      (voices ?? []).map((v) => ({
        value: v.id,
        label: `${v.name} (${v.tone})`,
      })),
    [voices],
  );

  useEffect(() => {
    const initial: Record<string, string> = {};
    if (currentTemplate) {
      for (const v of currentTemplate.variables) {
        initial[v] = variables[v] || '';
      }
    }
    setVariables(initial);
  }, [selectedTemplate]);

  const handleGenerate = async () => {
    const parsed = instructionsSchema.safeParse(instructions);
    if (!parsed.success) {
      setInstructionsError(parsed.error.issues[0].message);
      return;
    }
    setInstructionsError('');

    if (!selectedTemplate) return;
    const tmpl = templates?.find((t) => t.id === selectedTemplate);
    if (!tmpl) return;

    const filled = Object.fromEntries(
      Object.entries(variables).filter(([, v]) => v.trim()),
    );

    const result = await generateMutation.mutateAsync({
      organization_id: orgId,
      template_id: selectedTemplate,
      variables: filled,
      brand_voice_id: selectedVoice || undefined,
      tone,
      instructions,
    });

    setResult(result);
    setEditedContent(result.content);
    setSeoScore(null);
  };

  const handleRewrite = async () => {
    const parsed = instructionsSchema.safeParse(instructions);
    if (!parsed.success) {
      setInstructionsError(parsed.error.issues[0].message);
      return;
    }
    setInstructionsError('');

    if (!rewriteInput.trim()) return;
    const result = await rewriteMutation.mutateAsync({
      organization_id: orgId,
      content: rewriteInput,
      tone,
      brand_voice_id: selectedVoice || undefined,
      instructions,
    });
    setEditedContent(result.content);
    setSeoScore(null);
  };

  const handleSEOScore = async () => {
    if (!editedContent.trim()) return;
    const result = await seoMutation.mutateAsync({
      content: editedContent,
    });
    setSeoScore(result);
  };

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles className="h-6 w-6" />
          <div>
            <h1 className="text-2xl font-semibold">AI Content Composer</h1>
            <p className="text-sm text-muted-foreground">
              Generate marketing content with AI
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant={mode === 'compose' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setMode('compose')}
          >
            <FileText className="mr-2 h-4 w-4" />
            Compose
          </Button>
          <Button
            variant={mode === 'rewrite' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setMode('rewrite')}
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Rewrite
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <ContentSettingsPanel
          mode={mode}
          selectedTemplate={selectedTemplate}
          onTemplateChange={setSelectedTemplate}
          templateOptions={templateOptions}
          currentTemplate={currentTemplate}
          variables={variables}
          onVariableChange={(key, value) =>
            setVariables((prev) => ({ ...prev, [key]: value }))
          }
          rewriteInput={rewriteInput}
          onRewriteInputChange={setRewriteInput}
          selectedVoice={selectedVoice}
          onVoiceChange={setSelectedVoice}
          voiceOptions={voiceOptions}
          tone={tone}
          onToneChange={setTone}
          instructions={instructions}
          onInstructionsChange={(v) => {
            setInstructions(v);
            if (instructionsError) setInstructionsError('');
          }}
          instructionsError={instructionsError}
          onGenerate={mode === 'compose' ? handleGenerate : handleRewrite}
          isPending={generateMutation.isPending || rewriteMutation.isPending}
        />
        <ContentResultPanel
          mode={mode}
          isPending={generateMutation.isPending || rewriteMutation.isPending}
          result={result}
          editedContent={editedContent}
          onEditedContentChange={setEditedContent}
          seoScore={seoScore}
          onSEOScore={handleSEOScore}
          isSEOPending={seoMutation.isPending}
          onRegenerate={handleGenerate}
        />
      </div>
    </div>
    </ErrorBoundary>
  );
}
