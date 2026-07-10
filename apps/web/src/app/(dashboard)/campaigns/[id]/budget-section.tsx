'use client';

import { DollarSign, Save, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { UseQueryResult, UseMutationResult } from '@tanstack/react-query';

interface BudgetData {
  currency: string;
  total_budget: number;
  spent: number;
  remaining: number;
  spend_pct: number;
  is_alert_triggered: boolean;
}

interface BudgetSectionProps {
  budget: BudgetData | undefined;
  isLoading: boolean;
  budgetAmount: string;
  onBudgetAmountChange: (v: string) => void;
  threshold: string;
  onThresholdChange: (v: string) => void;
  spendAmount: string;
  onSpendAmountChange: (v: string) => void;
  setBudget: UseMutationResult<unknown, Error, { total_budget: number; alert_threshold: number }>;
  recordSpend: UseMutationResult<unknown, Error, number>;
}

export function BudgetSection({
  budget,
  isLoading,
  budgetAmount,
  onBudgetAmountChange,
  threshold,
  onThresholdChange,
  spendAmount,
  onSpendAmountChange,
  setBudget,
  recordSpend,
}: BudgetSectionProps) {
  return (
    <section className="rounded-lg border bg-card">
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <DollarSign className="h-4 w-4 text-muted-foreground" />
        <h2 className="text-sm font-medium">Budget & Spend</h2>
        {budget?.is_alert_triggered && (
          <span className="ml-auto rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] text-red-500 font-medium">
            ALERT: {budget.spend_pct.toFixed(0)}% spent
          </span>
        )}
      </div>
      <div className="p-4 space-y-4">
        {isLoading ? (
          <Skeleton className="h-16" />
        ) : budget ? (
          <div className="grid gap-4 sm:grid-cols-4">
            <div>
              <p className="text-[11px] text-muted-foreground uppercase">Budget</p>
              <p className="text-xl font-bold">{budget.currency} {budget.total_budget.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[11px] text-muted-foreground uppercase">Spent</p>
              <p className="text-xl font-bold">{budget.currency} {budget.spent.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[11px] text-muted-foreground uppercase">Remaining</p>
              <p className="text-xl font-bold">{budget.currency} {budget.remaining.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[11px] text-muted-foreground uppercase">Spend Rate</p>
              <div className="flex items-center gap-2">
                <div className="h-2 flex-1 rounded-full bg-muted overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all',
                      budget.spend_pct > 90 ? 'bg-red-500' : budget.spend_pct > 70 ? 'bg-yellow-500' : 'bg-green-500',
                    )}
                    style={{ width: `${Math.min(budget.spend_pct, 100)}%` }}
                  />
                </div>
                <span className="text-sm font-medium">{budget.spend_pct.toFixed(0)}%</span>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No budget set</p>
        )}

        <div className="flex flex-wrap gap-3 border-t pt-4">
          <div className="flex items-end gap-2">
            <div>
              <label htmlFor="budget-amount" className="text-xs font-medium text-muted-foreground">Budget amount</label>
              <Input
                id="budget-amount"
                type="number"
                placeholder="Budget"
                value={budgetAmount}
                onChange={(e) => onBudgetAmountChange(e.target.value)}
                className="mt-0.5 w-28"
              />
            </div>
            <div>
              <label htmlFor="alert-threshold" className="text-xs font-medium text-muted-foreground">Alert threshold</label>
              <Input
                id="alert-threshold"
                type="number"
                placeholder="Alert %"
                value={threshold}
                onChange={(e) => onThresholdChange(e.target.value)}
                className="mt-0.5 w-16"
              />
            </div>
            <Button
              size="sm"
              variant="outline"
              disabled={setBudget.isPending || !budgetAmount}
              onClick={() => {
                setBudget.mutate({
                  total_budget: parseFloat(budgetAmount),
                  alert_threshold: parseFloat(threshold),
                });
              }}
            >
              {setBudget.isPending ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <Save className="mr-1 h-3 w-3" />}
              Set Budget
            </Button>
          </div>
          <div className="flex items-end gap-2">
            <div>
              <label htmlFor="spend-amount" className="text-xs font-medium text-muted-foreground">Spend amount</label>
              <Input
                id="spend-amount"
                type="number"
                placeholder="Spend amount"
                value={spendAmount}
                onChange={(e) => onSpendAmountChange(e.target.value)}
                className="mt-0.5 w-24"
              />
            </div>
            <Button
              size="sm"
              variant="outline"
              disabled={recordSpend.isPending || !spendAmount}
              onClick={() => {
                recordSpend.mutate(parseFloat(spendAmount));
                onSpendAmountChange('');
              }}
            >
              Record Spend
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
