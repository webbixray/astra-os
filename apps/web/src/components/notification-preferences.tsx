'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface NotificationPreferences {
  email: {
    enabled: boolean;
    frequency: 'realtime' | 'daily' | 'weekly';
    campaigns: boolean;
    analytics: boolean;
    team: boolean;
    system: boolean;
  };
  push: {
    enabled: boolean;
    campaigns: boolean;
    analytics: boolean;
    team: boolean;
    system: boolean;
  };
  inApp: {
    enabled: boolean;
    sound: boolean;
    campaigns: boolean;
    analytics: boolean;
    team: boolean;
    system: boolean;
  };
}

const defaultPreferences: NotificationPreferences = {
  email: {
    enabled: true,
    frequency: 'daily',
    campaigns: true,
    analytics: true,
    team: true,
    system: true,
  },
  push: {
    enabled: true,
    campaigns: true,
    analytics: false,
    team: true,
    system: true,
  },
  inApp: {
    enabled: true,
    sound: true,
    campaigns: true,
    analytics: true,
    team: true,
    system: true,
  },
};

export function NotificationPreferencesComponent() {
  const [preferences, setPreferences] = useState<NotificationPreferences>(defaultPreferences);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Email Notifications</CardTitle>
          <CardDescription>Configure how often you receive email notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="email-enabled">Enable email notifications</Label>
            <Switch
              id="email-enabled"
              checked={preferences.email.enabled}
              onCheckedChange={(checked) =>
                setPreferences({ ...preferences, email: { ...preferences.email, enabled: checked } })
              }
            />
          </div>
          {preferences.email.enabled && (
            <>
              <div className="space-y-2">
                <Label>Frequency</Label>
                <Select
                  value={preferences.email.frequency}
                  onValueChange={(value: 'realtime' | 'daily' | 'weekly') =>
                    setPreferences({ ...preferences, email: { ...preferences.email, frequency: value } })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="realtime">Real-time</SelectItem>
                    <SelectItem value="daily">Daily digest</SelectItem>
                    <SelectItem value="weekly">Weekly digest</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-3">
                <Label>Categories</Label>
                {(['campaigns', 'analytics', 'team', 'system'] as const).map((category) => (
                  <div key={category} className="flex items-center justify-between">
                    <Label htmlFor={`email-${category}`} className="capitalize">
                      {category}
                    </Label>
                    <Switch
                      id={`email-${category}`}
                      checked={preferences.email[category]}
                      onCheckedChange={(checked) =>
                        setPreferences({
                          ...preferences,
                          email: { ...preferences.email, [category]: checked },
                        })
                      }
                    />
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Push Notifications</CardTitle>
          <CardDescription>Configure browser push notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="push-enabled">Enable push notifications</Label>
            <Switch
              id="push-enabled"
              checked={preferences.push.enabled}
              onCheckedChange={(checked) =>
                setPreferences({ ...preferences, push: { ...preferences.push, enabled: checked } })
              }
            />
          </div>
          {preferences.push.enabled && (
            <div className="space-y-3">
              <Label>Categories</Label>
              {(['campaigns', 'analytics', 'team', 'system'] as const).map((category) => (
                <div key={category} className="flex items-center justify-between">
                  <Label htmlFor={`push-${category}`} className="capitalize">
                    {category}
                  </Label>
                  <Switch
                    id={`push-${category}`}
                    checked={preferences.push[category]}
                    onCheckedChange={(checked) =>
                      setPreferences({
                        ...preferences,
                        push: { ...preferences.push, [category]: checked },
                      })
                    }
                  />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>In-App Notifications</CardTitle>
          <CardDescription>Configure notifications within the app</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="inapp-enabled">Enable in-app notifications</Label>
            <Switch
              id="inapp-enabled"
              checked={preferences.inApp.enabled}
              onCheckedChange={(checked) =>
                setPreferences({ ...preferences, inApp: { ...preferences.inApp, enabled: checked } })
              }
            />
          </div>
          {preferences.inApp.enabled && (
            <>
              <div className="flex items-center justify-between">
                <Label htmlFor="inapp-sound">Notification sound</Label>
                <Switch
                  id="inapp-sound"
                  checked={preferences.inApp.sound}
                  onCheckedChange={(checked) =>
                    setPreferences({ ...preferences, inApp: { ...preferences.inApp, sound: checked } })
                  }
                />
              </div>
              <div className="space-y-3">
                <Label>Categories</Label>
                {(['campaigns', 'analytics', 'team', 'system'] as const).map((category) => (
                  <div key={category} className="flex items-center justify-between">
                    <Label htmlFor={`inapp-${category}`} className="capitalize">
                      {category}
                    </Label>
                    <Switch
                      id={`inapp-${category}`}
                      checked={preferences.inApp[category]}
                      onCheckedChange={(checked) =>
                        setPreferences({
                          ...preferences,
                          inApp: { ...preferences.inApp, [category]: checked },
                        })
                      }
                    />
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save Preferences'}
        </Button>
      </div>
    </div>
  );
}
