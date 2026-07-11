export interface FeatureFlag {
  key: string;
  enabled: boolean;
  description?: string;
  rolloutPercentage?: number;
  allowedUsers?: string[];
  allowedRoles?: string[];
  startDate?: string;
  endDate?: string;
}

export interface FeatureFlagOptions {
  defaultEnabled?: boolean;
  rolloutPercentage?: number;
  allowedUsers?: string[];
  allowedRoles?: string[];
}

class FeatureFlagManager {
  private flags = new Map<string, FeatureFlag>();
  private userContext?: { id: string; role?: string };

  setFlags(flags: FeatureFlag[]): void {
    flags.forEach((flag) => {
      this.flags.set(flag.key, flag);
    });
  }

  setFlag(key: string, flag: FeatureFlag): void {
    this.flags.set(key, flag);
  }

  setUserContext(context: { id: string; role?: string }): void {
    this.userContext = context;
  }

  isEnabled(key: string, options?: FeatureFlagOptions): boolean {
    const flag = this.flags.get(key);

    if (!flag) {
      return options?.defaultEnabled ?? false;
    }

    if (!flag.enabled) return false;

    if (flag.startDate && new Date(flag.startDate) > new Date()) {
      return false;
    }

    if (flag.endDate && new Date(flag.endDate) < new Date()) {
      return false;
    }

    if (flag.allowedUsers && flag.allowedUsers.length > 0) {
      if (!this.userContext || !flag.allowedUsers.includes(this.userContext.id)) {
        return false;
      }
    }

    if (flag.allowedRoles && flag.allowedRoles.length > 0) {
      if (!this.userContext?.role || !flag.allowedRoles.includes(this.userContext.role)) {
        return false;
      }
    }

    if (flag.rolloutPercentage !== undefined && flag.rolloutPercentage < 100) {
      const hash = this.hashString(`${key}:${this.userContext?.id || 'anonymous'}`);
      const bucket = hash % 100;
      if (bucket >= flag.rolloutPercentage) {
        return false;
      }
    }

    return true;
  }

  getFlag(key: string): FeatureFlag | undefined {
    return this.flags.get(key);
  }

  getAllFlags(): FeatureFlag[] {
    return Array.from(this.flags.values());
  }

  getEnabledFlags(): FeatureFlag[] {
    return this.getAllFlags().filter((f) => this.isEnabled(f.key));
  }

  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash |= 0;
    }
    return Math.abs(hash);
  }
}

export const featureFlags = new FeatureFlagManager();

export function isFeatureEnabled(key: string, options?: FeatureFlagOptions): boolean {
  return featureFlags.isEnabled(key, options);
}

export function withFeatureFlag<T>(
  key: string,
  enabledComponent: T,
  disabledComponent: T,
): T {
  return featureFlags.isEnabled(key) ? enabledComponent : disabledComponent;
}

export const DEFAULT_FLAGS: FeatureFlag[] = [
  {
    key: 'ai-content-generation',
    enabled: true,
    description: 'Enable AI-powered content generation',
  },
  {
    key: 'advanced-analytics',
    enabled: true,
    description: 'Enable advanced analytics features',
  },
  {
    key: 'beta-features',
    enabled: false,
    description: 'Enable beta features',
    rolloutPercentage: 10,
  },
  {
    key: 'new-dashboard',
    enabled: false,
    description: 'Enable new dashboard design',
    rolloutPercentage: 25,
  },
  {
    key: 'real-time-collaboration',
    enabled: false,
    description: 'Enable real-time collaboration features',
    allowedRoles: ['admin', 'owner'],
  },
];

featureFlags.setFlags(DEFAULT_FLAGS);
