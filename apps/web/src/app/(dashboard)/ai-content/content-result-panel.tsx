'use client';

import {
  Sparkles,
  RotateCcw,
  FileText,
  Send,
  BarChart3,
  Check,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

const scoreColor = (score: number) => {
  if (score >= 70) return 'text-green-500';
  if (score >= 50) return 'text-yellow-500';
  return 'text-red-500';
};

interface ContentResultPanelProps {
  mode: 'compose' | 'rewrite';
  isPending: boolean;
  result: { content: string; sections: Record<string, string>; template_name: string; content_type: string } | null;
  editedContent: string;
  onEditedContentChange: (v: string) => void;
  seoScore: { score: number; rating: string; details: Record<string, unknown> } | null;
  onSEOScore: () => void;
  isSEOPending: boolean;
  onRegenerate: () => void;
}

export function ContentResultPanel({
  mode,
  isPending,
  result,
  editedContent,
  onEditedContentChange,
  seoScore,
  onSEOScore,
  isSEOPending,
  onRegenerate,
}: ContentResultPanelProps) {
  return (
    <div className="col-span-2 space-y-4">
      {isPending && (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">
              Generating content...
            </p>
          </div>
        </div>
      )}

      {result && !isPending && (
        <div className="rounded-lg border bg-card">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">
                {result.template_name}
              </span>
              <span className="text-xs text-muted-foreground">
                ({result.content_type})
              </span>
            </div>
            <div className="flex gap-1">
              <Button
                size="sm"
                variant="outline"
                onClick={onSEOScore}
                disabled={isSEOPending}
              >
                <BarChart3 className="mr-1 h-3 w-3" />
                SEO Score
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  navigator.clipboard.writeText(editedContent);
                }}
              >
                <Send className="mr-1 h-3 w-3" />
                Copy
              </Button>
            </div>
          </div>

          {seoScore && (
            <div className="flex items-center gap-4 border-b bg-muted/30 px-4 py-2 text-xs">
              <span className="flex items-center gap-1">
                SEO Score:
                <span className={cn('font-semibold', scoreColor(seoScore.score))}>
                  {seoScore.score}/100 ({seoScore.rating})
                </span>
              </span>
              <span className="text-muted-foreground">
                {seoScore.details?.word_count
                  ? `${(seoScore.details as Record<string, unknown>).word_count as number} words`
                  : ''}
              </span>
              {seoScore.details?.has_headings !== undefined && (
                <span className="text-muted-foreground">
                  {(seoScore.details as Record<string, unknown>).has_headings
                    ? 'Has headings'
                    : 'No headings'}
                </span>
              )}
            </div>
          )}

          <div className="p-4">
            {result.sections &&
              Object.entries(result.sections).map(([name, content]) => (
                <div key={name} className="mb-4">
                  <h3 className="mb-1 text-xs font-medium uppercase text-muted-foreground">
                    {name}
                  </h3>
                  <p className="whitespace-pre-wrap text-sm">{content}</p>
                </div>
              ))}

            {Object.keys(result.sections || {}).length === 0 && (
              <Textarea
                className="min-h-64"
                value={editedContent}
                onChange={(e) => onEditedContentChange(e.target.value)}
              />
            )}
          </div>

          <div className="flex items-center gap-2 border-t px-4 py-3">
            <Button
              size="sm"
              onClick={onRegenerate}
              disabled={isPending}
            >
              <RotateCcw className="mr-1 h-3 w-3" />
              Regenerate
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                navigator.clipboard.writeText(editedContent);
              }}
            >
              <Check className="mr-1 h-3 w-3" />
              Copy All
            </Button>
          </div>
        </div>
      )}

      {!result && !isPending && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-20 text-center">
          <Sparkles className="mb-4 h-12 w-12 text-muted-foreground" />
          <p className="text-lg text-muted-foreground">
            {mode === 'compose'
              ? 'Select a template and generate content'
              : 'Paste content to rewrite'}
          </p>
          <p className="text-sm text-muted-foreground">
            Choose settings on the left and click{' '}
            {mode === 'compose' ? 'Generate' : 'Rewrite'}
          </p>
        </div>
      )}

      {mode === 'rewrite' && editedContent && !isPending && (
        <div className="rounded-lg border bg-card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-medium">Rewritten Content</h2>
            <Button
              size="sm"
              variant="outline"
              onClick={onSEOScore}
              disabled={isSEOPending}
            >
              <BarChart3 className="mr-1 h-3 w-3" />
              SEO Score
            </Button>
          </div>
          {seoScore && (
            <div className="mb-3 flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1">
                SEO Score:
                <span className={cn('font-semibold', scoreColor(seoScore.score))}>
                  {seoScore.score}/100 ({seoScore.rating})
                </span>
              </span>
            </div>
          )}
          <Textarea
            className="min-h-48"
            value={editedContent}
            onChange={(e) => onEditedContentChange(e.target.value)}
          />
        </div>
      )}
    </div>
  );
}
