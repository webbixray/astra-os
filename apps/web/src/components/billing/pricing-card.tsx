'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';

interface Plan {
  id: string;
  name: string;
  description: string;
  price: number;
  period: 'monthly' | 'yearly';
  features: { name: string; included: boolean; limit?: string }[];
  popular?: boolean;
  current?: boolean;
}

interface PricingCardProps {
  plan: Plan;
  onSelect?: (plan: Plan) => void;
  className?: string;
}

export function PricingCard({ plan, onSelect, className }: PricingCardProps) {
  return (
    <Card
      className={cn(
        'relative transition-shadow hover:shadow-md',
        plan.popular && 'border-blue-500 shadow-md',
        plan.current && 'border-green-500',
        className,
      )}
    >
      {plan.popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge className="bg-blue-600 text-white">Most Popular</Badge>
        </div>
      )}
      {plan.current && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge className="bg-green-600 text-white">Current Plan</Badge>
        </div>
      )}
      <CardHeader>
        <CardTitle>{plan.name}</CardTitle>
        <CardDescription>{plan.description}</CardDescription>
        <div className="mt-4">
          <span className="text-4xl font-bold">${plan.price}</span>
          <span className="text-gray-500">/{plan.period === 'monthly' ? 'mo' : 'yr'}</span>
        </div>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {plan.features.map((feature) => (
            <li key={feature.name} className="flex items-center gap-2">
              {feature.included ? (
                <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="h-5 w-5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
              <span className={cn('text-sm', !feature.included && 'text-gray-400')}>
                {feature.name}
                {feature.limit && (
                  <span className="text-gray-500"> ({feature.limit})</span>
                )}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
      <CardFooter>
        <Button
          className="w-full"
          variant={plan.current ? 'outline' : plan.popular ? 'default' : 'outline'}
          disabled={plan.current}
          onClick={() => onSelect?.(plan)}
        >
          {plan.current ? 'Current Plan' : 'Upgrade'}
        </Button>
      </CardFooter>
    </Card>
  );
}

interface PricingSectionProps {
  plans: Plan[];
  annual?: boolean;
  onToggleAnnual?: (annual: boolean) => void;
  onSelectPlan?: (plan: Plan) => void;
  className?: string;
}

export function PricingSection({ plans, annual, onToggleAnnual, onSelectPlan, className }: PricingSectionProps) {
  return (
    <div className={cn('space-y-8', className)}>
      <div className="text-center">
        <h2 className="text-3xl font-bold">Simple, transparent pricing</h2>
        <p className="mt-2 text-gray-500">Choose the plan that's right for your team</p>
        {onToggleAnnual && (
          <div className="mt-6 flex items-center justify-center gap-3">
            <span className={!annual ? 'font-medium' : 'text-gray-500'}>Monthly</span>
            <Switch checked={annual} onCheckedChange={onToggleAnnual} />
            <span className={annual ? 'font-medium' : 'text-gray-500'}>
              Annual
              <Badge variant="secondary" className="ml-2 bg-green-100 text-green-800">
                Save 20%
              </Badge>
            </span>
          </div>
        )}
      </div>
      <div className="grid gap-6 md:grid-cols-3">
        {plans.map((plan) => (
          <PricingCard key={plan.id} plan={plan} onSelect={onSelectPlan} />
        ))}
      </div>
    </div>
  );
}

interface Invoice {
  id: string;
  date: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed';
  description: string;
}

interface BillingHistoryProps {
  invoices: Invoice[];
  className?: string;
}

export function BillingHistory({ invoices, className }: BillingHistoryProps) {
  const statusColors: Record<Invoice['status'], string> = {
    paid: 'bg-green-100 text-green-800',
    pending: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Billing History</CardTitle>
        <CardDescription>Your recent invoices</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {invoices.map((invoice) => (
            <div key={invoice.id} className="flex items-center justify-between rounded-lg border p-4">
              <div>
                <div className="font-medium">{invoice.description}</div>
                <div className="text-sm text-gray-500">
                  {new Date(invoice.date).toLocaleDateString()}
                </div>
              </div>
              <div className="flex items-center gap-4">
                <Badge variant="secondary" className={statusColors[invoice.status]}>
                  {invoice.status}
                </Badge>
                <span className="font-medium">${invoice.amount.toFixed(2)}</span>
                <Button variant="ghost" size="sm">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface SubscriptionStatusProps {
  plan: string;
  nextBillingDate: string;
  amount: number;
  paymentMethod?: { brand: string; last4: string; expMonth: number; expYear: number };
  className?: string;
}

export function SubscriptionStatus({ plan, nextBillingDate, amount, paymentMethod, className }: SubscriptionStatusProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Current Subscription</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-lg font-bold">{plan}</div>
            <div className="text-sm text-gray-500">
              ${amount}/month · Renews {new Date(nextBillingDate).toLocaleDateString()}
            </div>
          </div>
          <Button variant="outline">Manage</Button>
        </div>
        {paymentMethod && (
          <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-16 items-center justify-center rounded bg-white dark:bg-gray-700">
                <span className="text-sm font-bold uppercase">{paymentMethod.brand}</span>
              </div>
              <div>
                <div className="text-sm font-medium">
                  •••• •••• •••• {paymentMethod.last4}
                </div>
                <div className="text-xs text-gray-500">
                  Expires {paymentMethod.expMonth}/{paymentMethod.expYear}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
