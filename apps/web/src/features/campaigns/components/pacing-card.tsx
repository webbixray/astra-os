'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, TrendingUp, TrendingDown, CheckCircle, PauseCircle } from 'lucide-react';

interface PacingData {
  strategy: string;
  status: string;
  daily_target: number;
  total_budget: number;
  total_spent: number;
  remaining_budget: number;
  days_elapsed: number;
  days_remaining: number;
  percent_time_elapsed: number;
  percent_budget_spent: number;
  pace_ratio: number;
  recommended_daily_limit: number;
  should_pause: boolean;
  alert_message: string | null;
}

const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  on_track: {
    color: 'bg-green-100 text-green-800',
    icon: <CheckCircle className="h-4 w-4" />,
    label: 'On Track',
  },
  ahead: {
    color: 'bg-yellow-100 text-yellow-800',
    icon: <TrendingUp className="h-4 w-4" />,
    label: 'Ahead of Pace',
  },
  behind: {
    color: 'bg-orange-100 text-orange-800',
    icon: <TrendingDown className="h-4 w-4" />,
    label: 'Behind Pace',
  },
  overspend_risk: {
    color: 'bg-red-100 text-red-800',
    icon: <AlertTriangle className="h-4 w-4" />,
    label: 'Overspend Risk',
  },
  underspend_risk: {
    color: 'bg-blue-100 text-blue-800',
    icon: <TrendingDown className="h-4 w-4" />,
    label: 'Underspend Risk',
  },
  completed: {
    color: 'bg-gray-100 text-gray-800',
    icon: <PauseCircle className="h-4 w-4" />,
    label: 'Completed',
  },
};

interface PacingCardProps {
  data: PacingData;
}

export function PacingCard({ data }: PacingCardProps) {
  const config = STATUS_CONFIG[data.status] || STATUS_CONFIG.on_track;
  const progressValue = Math.min(data.percent_budget_spent, 100);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Budget Pacing</CardTitle>
          <Badge className={config.color}>
            {config.icon}
            <span className="ml-1">{config.label}</span>
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Budget: {data.percent_budget_spent.toFixed(1)}%</span>
            <span>Time: {data.percent_time_elapsed.toFixed(1)}%</span>
          </div>
          <Progress value={progressValue} className="h-2" />
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-muted-foreground">Daily Target</p>
            <p className="text-sm font-semibold">${data.daily_target.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Spent</p>
            <p className="text-sm font-semibold">${data.total_spent.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Remaining</p>
            <p className="text-sm font-semibold">${data.remaining_budget.toLocaleString()}</p>
          </div>
        </div>

        {/* Pace ratio */}
        <div className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
          <span className="text-xs text-muted-foreground">Pace Ratio</span>
          <span className={`text-sm font-medium ${
            data.pace_ratio > 1.15 ? 'text-red-600' :
            data.pace_ratio > 1.05 ? 'text-yellow-600' :
            data.pace_ratio < 0.7 ? 'text-blue-600' :
            data.pace_ratio < 0.95 ? 'text-orange-600' :
            'text-green-600'
          }`}>
            {(data.pace_ratio * 100).toFixed(0)}%
          </span>
        </div>

        {/* Days info */}
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{data.days_elapsed} days elapsed</span>
          <span>{data.days_remaining} days remaining</span>
        </div>

        {/* Alert */}
        {data.alert_message && (
          <div className={`rounded-lg px-3 py-2 text-xs ${
            data.should_pause ? 'bg-red-50 text-red-700 border border-red-200' :
            'bg-yellow-50 text-yellow-700 border border-yellow-200'
          }`}>
            {data.alert_message}
          </div>
        )}

        {/* Recommended limit */}
        {data.recommended_daily_limit > 0 && (
          <div className="text-xs text-muted-foreground">
            Recommended daily limit: <span className="font-medium">${data.recommended_daily_limit.toLocaleString()}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
