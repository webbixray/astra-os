'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/status-indicator';
import { cn } from '@/lib/utils';

interface WorkflowStep {
  id: string;
  type: 'trigger' | 'action' | 'condition' | 'delay';
  name: string;
  description?: string;
  config?: Record<string, unknown>;
  status?: 'pending' | 'running' | 'completed' | 'failed';
}

interface Workflow {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'active' | 'paused' | 'error';
  steps: WorkflowStep[];
  createdAt: string;
  updatedAt: string;
  lastRun?: string;
  runCount?: number;
  successRate?: number;
}

interface WorkflowStepCardProps {
  step: WorkflowStep;
  index: number;
  isLast: boolean;
  onEdit?: (step: WorkflowStep) => void;
  onDelete?: (step: WorkflowStep) => void;
  className?: string;
}

export function WorkflowStepCard({ step, index, isLast, onEdit, onDelete, className }: WorkflowStepCardProps) {
  const stepIcons: Record<WorkflowStep['type'], string> = {
    trigger: '⚡',
    action: '🎯',
    condition: '🔀',
    delay: '⏱️',
  };

  const stepColors: Record<WorkflowStep['type'], string> = {
    trigger: 'border-l-blue-500',
    action: 'border-l-green-500',
    condition: 'border-l-yellow-500',
    delay: 'border-l-purple-500',
  };

  return (
    <div className={cn('relative', className)}>
      <div className="flex items-start gap-4">
        <div className="flex flex-col items-center">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
            <span className="text-sm">{stepIcons[step.type]}</span>
          </div>
          {!isLast && <div className="mt-2 h-12 w-0.5 bg-gray-200 dark:bg-gray-700" />}
        </div>
        <div className={cn('flex-1 rounded-lg border-l-4 bg-white p-4 shadow-sm dark:bg-gray-900', stepColors[step.type])}>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium">{step.name}</span>
                <Badge variant="secondary" className="text-xs">
                  {step.type}
                </Badge>
                {step.status && <StatusBadge status={step.status} />}
              </div>
              {step.description && (
                <p className="mt-1 text-sm text-gray-500">{step.description}</p>
              )}
            </div>
            <div className="flex gap-1">
              {onEdit && (
                <Button variant="ghost" size="sm" onClick={() => onEdit(step)}>
                  Edit
                </Button>
              )}
              {onDelete && (
                <Button variant="ghost" size="sm" onClick={() => onDelete(step)} className="text-red-600">
                  Delete
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface WorkflowCardProps {
  workflow: Workflow;
  onEdit?: (workflow: Workflow) => void;
  onDelete?: (workflow: Workflow) => void;
  onRun?: (workflow: Workflow) => void;
  onPause?: (workflow: Workflow) => void;
  className?: string;
}

export function WorkflowCard({ workflow, onEdit, onDelete, onRun, onPause, className }: WorkflowCardProps) {
  return (
    <Card className={cn('transition-shadow hover:shadow-md', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg">{workflow.name}</CardTitle>
            {workflow.description && (
              <CardDescription>{workflow.description}</CardDescription>
            )}
          </div>
          <StatusBadge status={workflow.status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>{workflow.steps.length} steps</span>
          {workflow.runCount !== undefined && (
            <span>{workflow.runCount} runs</span>
          )}
          {workflow.successRate !== undefined && (
            <span>{workflow.successRate}% success</span>
          )}
        </div>

        <div className="flex gap-2 pt-2">
          {workflow.status === 'active' && onPause && (
            <Button variant="outline" size="sm" onClick={() => onPause(workflow)}>
              Pause
            </Button>
          )}
          {(workflow.status === 'draft' || workflow.status === 'paused') && onRun && (
            <Button size="sm" onClick={() => onRun(workflow)}>
              Run
            </Button>
          )}
          {onEdit && (
            <Button variant="ghost" size="sm" onClick={() => onEdit(workflow)}>
              Edit
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface WorkflowBuilderProps {
  workflow?: Workflow;
  onSave?: (workflow: Partial<Workflow>) => void;
  onAddStep?: () => void;
  className?: string;
}

export function WorkflowBuilder({ workflow, onSave, onAddStep, className }: WorkflowBuilderProps) {
  const [name, setName] = useState(workflow?.name || '');
  const [description, setDescription] = useState(workflow?.description || '');

  return (
    <div className={cn('space-y-6', className)}>
      <Card>
        <CardHeader>
          <CardTitle>Workflow Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border px-3 py-2"
              placeholder="Enter workflow name"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-md border px-3 py-2"
              placeholder="Enter workflow description"
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Steps</CardTitle>
            {onAddStep && (
              <Button variant="outline" size="sm" onClick={onAddStep}>
                Add Step
              </Button>
            )}
          </div>
          <CardDescription>Build your workflow by adding steps</CardDescription>
        </CardHeader>
        <CardContent>
          {workflow?.steps && workflow.steps.length > 0 ? (
            <div className="space-y-4">
              {workflow.steps.map((step, index) => (
                <WorkflowStepCard
                  key={step.id}
                  step={step}
                  index={index}
                  isLast={index === workflow.steps.length - 1}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-lg border-2 border-dashed p-8 text-center">
              <p className="text-gray-500">No steps yet. Add your first step to get started.</p>
              {onAddStep && (
                <Button variant="outline" className="mt-4" onClick={onAddStep}>
                  Add First Step
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline">Cancel</Button>
        <Button onClick={() => onSave?.({ name, description })}>
          {workflow ? 'Save Changes' : 'Create Workflow'}
        </Button>
      </div>
    </div>
  );
}

interface WorkflowListProps {
  workflows: Workflow[];
  onCreate?: () => void;
  onEdit?: (workflow: Workflow) => void;
  onDelete?: (workflow: Workflow) => void;
  onRun?: (workflow: Workflow) => void;
  onPause?: (workflow: Workflow) => void;
  className?: string;
}

export function WorkflowList({ workflows, onCreate, onEdit, onDelete, onRun, onPause, className }: WorkflowListProps) {
  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Workflows</h2>
          <p className="text-sm text-gray-500">Automate your marketing processes</p>
        </div>
        {onCreate && (
          <Button onClick={onCreate}>
            <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Workflow
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {workflows.map((workflow) => (
          <WorkflowCard
            key={workflow.id}
            workflow={workflow}
            onEdit={onEdit}
            onDelete={onDelete}
            onRun={onRun}
            onPause={onPause}
          />
        ))}
      </div>

      {workflows.length === 0 && (
        <div className="rounded-lg border-2 border-dashed p-12 text-center">
          <h3 className="text-lg font-medium">No workflows yet</h3>
          <p className="mt-2 text-gray-500">Create your first workflow to automate marketing tasks.</p>
          {onCreate && (
            <Button className="mt-4" onClick={onCreate}>
              Create Workflow
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
