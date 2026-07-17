'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { LegacySelect as Select } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { config, type AstraConfig } from '@/lib/config';

export function UserPreferences() {
  const { addToast } = useToast();
  const [prefs, setPrefs] = useState<AstraConfig>(() => config.get());
  const [saving, setSaving] = useState(false);

  const updatePrefs = (partial: Partial<AstraConfig>) => {
    setPrefs((prev) => ({ ...prev, ...partial }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      config.set(prefs);
      config.theme.apply(prefs.theme);
      addToast({
        type: 'success',
        title: 'Preferences saved',
        description: 'Your settings have been updated.',
      });
    } catch {
      addToast({
        type: 'error',
        title: 'Failed to save',
        description: 'Could not save your preferences.',
      });
    } finally {
      setSaving(false);
    }
  };

  const timezones = [
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Australia/Sydney',
    'Pacific/Auckland',
  ];

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-medium">Preferences</h3>
        <p className="text-sm text-muted-foreground">
          Customize your Astra OS experience
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <Label>Theme</Label>
          <Select
            options={[
              { value: 'light', label: 'Light' },
              { value: 'dark', label: 'Dark' },
              { value: 'system', label: 'System' },
            ]}
            value={prefs.theme}
            onChange={(e) => updatePrefs({ theme: e.target.value as AstraConfig['theme'] })}
          />
        </div>

        <div className="space-y-2">
          <Label>Timezone</Label>
          <Select
            options={timezones.map((tz) => ({
              value: tz,
              label: tz.replace(/_/g, ' '),
            }))}
            value={prefs.timezone}
            onChange={(e) => updatePrefs({ timezone: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label>Default View</Label>
          <Select
            options={[
              { value: 'dashboard', label: 'Dashboard' },
              { value: 'campaigns', label: 'Campaigns' },
              { value: 'content', label: 'Content' },
            ]}
            value={prefs.defaultView}
            onChange={(e) => updatePrefs({ defaultView: e.target.value as AstraConfig['defaultView'] })}
          />
        </div>

        <div className="space-y-2">
          <Label>Email Digest</Label>
          <Select
            options={[
              { value: 'daily', label: 'Daily' },
              { value: 'weekly', label: 'Weekly' },
              { value: 'none', label: 'None' },
            ]}
            value={prefs.emailDigest}
            onChange={(e) => updatePrefs({ emailDigest: e.target.value as AstraConfig['emailDigest'] })}
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="notifications"
            checked={prefs.notificationsEnabled}
            onChange={(e) => updatePrefs({ notificationsEnabled: e.target.checked })}
            className="rounded"
          />
          <Label htmlFor="notifications">Enable notifications</Label>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="sidebar"
            checked={prefs.sidebarCollapsed}
            onChange={(e) => updatePrefs({ sidebarCollapsed: e.target.checked })}
            className="rounded"
          />
          <Label htmlFor="sidebar">Collapse sidebar by default</Label>
        </div>
      </div>

      <div className="flex gap-2">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Preferences'}
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            config.reset();
            setPrefs(config.get());
            addToast({
              type: 'info',
              title: 'Preferences reset',
              description: 'All settings have been reset to defaults.',
            });
          }}
        >
          Reset to Defaults
        </Button>
      </div>
    </div>
  );
}
