'use client';

import { Button } from '@/components/ui/button';

interface SettingsProfileTabProps {
  user: any;
  onLogout: () => void;
}

export function SettingsProfileTab({ user, onLogout }: SettingsProfileTabProps) {
  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Profile</h2>
        <p className="text-sm text-muted-foreground">Your account details</p>
      </div>

      <div className="rounded-lg border bg-card p-4">
        <div className="space-y-3 text-sm">
          <div><span className="text-muted-foreground">Name</span><p className="font-medium">{user?.name ?? 'Not set'}</p></div>
          <div><span className="text-muted-foreground">Email</span><p className="font-medium">{user?.email ?? 'Not set'}</p></div>
        </div>
      </div>

      <div className="rounded-lg border border-destructive/20 bg-card p-4">
        <h3 className="mb-2 text-sm font-medium text-destructive">Danger Zone</h3>
        <p className="mb-3 text-sm text-muted-foreground">Sign out of your account</p>
        <Button variant="destructive" size="sm" onClick={onLogout}>Sign Out</Button>
      </div>
    </div>
  );
}
