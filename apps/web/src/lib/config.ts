const CONFIG_KEY = 'astra_config';

interface AstraConfig {
  theme: 'light' | 'dark' | 'system';
  sidebarCollapsed: boolean;
  defaultView: 'dashboard' | 'campaigns' | 'content';
  notificationsEnabled: boolean;
  emailDigest: 'daily' | 'weekly' | 'none';
  language: string;
  timezone: string;
}

const defaultConfig: AstraConfig = {
  theme: 'system',
  sidebarCollapsed: false,
  defaultView: 'dashboard',
  notificationsEnabled: true,
  emailDigest: 'weekly',
  language: 'en',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
};

function getConfig(): AstraConfig {
  if (typeof window === 'undefined') return defaultConfig;
  try {
    const stored = localStorage.getItem(CONFIG_KEY);
    if (stored) {
      return { ...defaultConfig, ...JSON.parse(stored) };
    }
  } catch {
    return defaultConfig;
  }
  return defaultConfig;
}

function setConfig(partial: Partial<AstraConfig>): void {
  if (typeof window === 'undefined') return;
  const current = getConfig();
  const updated = { ...current, ...partial };
  localStorage.setItem(CONFIG_KEY, JSON.stringify(updated));
}

function resetConfig(): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(CONFIG_KEY, JSON.stringify(defaultConfig));
}

function getTheme(): AstraConfig['theme'] {
  return getConfig().theme;
}

function setTheme(theme: AstraConfig['theme']): void {
  setConfig({ theme });
  applyTheme(theme);
}

function applyTheme(theme: AstraConfig['theme']): void {
  if (typeof window === 'undefined') return;
  const root = document.documentElement;

  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.classList.toggle('dark', prefersDark);
  } else {
    root.classList.toggle('dark', theme === 'dark');
  }
}

function getTimezone(): string {
  return getConfig().timezone;
}

function setTimezone(timezone: string): void {
  setConfig({ timezone });
}

export const config = {
  get: getConfig,
  set: setConfig,
  reset: resetConfig,
  theme: {
    get: getTheme,
    set: setTheme,
    apply: applyTheme,
  },
  timezone: {
    get: getTimezone,
    set: setTimezone,
  },
};

export type { AstraConfig };
