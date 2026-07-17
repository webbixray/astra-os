'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/lib/auth';

const PASSWORD_MIN_LENGTH = 8;

function getPasswordStrength(password: string): {
  score: number;
  label: string;
  color: string;
  checks: { label: string; met: boolean }[];
} {
  const checks = [
    { label: 'At least 8 characters', met: password.length >= PASSWORD_MIN_LENGTH },
    { label: 'Uppercase letter', met: /[A-Z]/.test(password) },
    { label: 'Lowercase letter', met: /[a-z]/.test(password) },
    { label: 'Number', met: /\d/.test(password) },
    { label: 'Special character', met: /[!@#$%^&*()\-_=+{}[\]|;:',.<>?/~`]/.test(password) },
  ];
  const score = checks.filter((c) => c.met).length;
  if (score <= 2) return { score, label: 'Weak', color: 'text-red-500', checks };
  if (score <= 3) return { score, label: 'Fair', color: 'text-yellow-500', checks };
  if (score <= 4) return { score, label: 'Good', color: 'text-blue-500', checks };
  return { score, label: 'Strong', color: 'text-green-500', checks };
}

export default function SignupPage() {
  const router = useRouter();
  const { signup } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showChecks, setShowChecks] = useState(false);

  const strength = useMemo(() => getPasswordStrength(password), [password]);
  const isPasswordValid = password.length >= PASSWORD_MIN_LENGTH && strength.score >= 4;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!isPasswordValid) {
      setError('Please meet all password requirements.');
      return;
    }
    setLoading(true);
    try {
      await signup(email, password, name);
      router.push('/dashboard');
    } catch {
      setError('Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-6 px-4">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">Create an account</h1>
          <p className="text-sm text-muted-foreground">Get started with ASTRA OS</p>
        </div>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="Your name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="name@example.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onFocus={() => setShowChecks(true)}
              required
              placeholder="••••••••"
            />
            {showChecks && password.length > 0 && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Strength:</span>
                  <span className={strength.color}>{strength.label}</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full transition-all ${
                      strength.score <= 2
                        ? 'bg-red-500'
                        : strength.score <= 3
                          ? 'bg-yellow-500'
                          : strength.score <= 4
                            ? 'bg-blue-500'
                            : 'bg-green-500'
                    }`}
                    style={{ width: `${(strength.score / 5) * 100}%` }}
                  />
                </div>
                <ul className="mt-1 space-y-0.5">
                  {strength.checks.map((check) => (
                    <li
                      key={check.label}
                      className={`text-xs ${check.met ? 'text-green-500' : 'text-muted-foreground'}`}
                    >
                      {check.met ? '✓' : '○'} {check.label}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading || !isPasswordValid}>
            {loading ? 'Creating account...' : 'Create Account'}
          </Button>
        </div>
        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <a href="/login" className="text-foreground underline underline-offset-4 hover:text-primary">
            Sign in
          </a>
        </p>
      </form>
    </div>
  );
}
