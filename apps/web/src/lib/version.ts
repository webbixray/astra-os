const VERSION_KEY = 'astra_version';
const CHECK_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours

interface VersionInfo {
  current: string;
  latest: string;
  updateAvailable: boolean;
  lastChecked: number;
}

function getCurrentVersion(): string {
  return process.env.NEXT_PUBLIC_APP_VERSION || '0.0.1';
}

function getStoredVersionInfo(): VersionInfo | null {
  if (typeof window === 'undefined') return null;
  try {
    const stored = localStorage.getItem(VERSION_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch {
    return null;
  }
  return null;
}

function storeVersionInfo(info: VersionInfo): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(VERSION_KEY, JSON.stringify(info));
}

function shouldCheckForUpdates(): boolean {
  const info = getStoredVersionInfo();
  if (!info) return true;
  return Date.now() - info.lastChecked > CHECK_INTERVAL;
}

export async function checkForUpdates(): Promise<VersionInfo> {
  const current = getCurrentVersion();

  if (!shouldCheckForUpdates()) {
    const stored = getStoredVersionInfo();
    if (stored) {
      return stored;
    }
  }

  try {
    const response = await fetch('https://api.github.com/repos/webbixray/astra-os/releases/latest', {
      headers: { Accept: 'application/vnd.github.v3+json' },
      signal: AbortSignal.timeout(5000),
    });

    if (response.ok) {
      const release = await response.json();
      const latest = release.tag_name?.replace('v', '') || current;

      const info: VersionInfo = {
        current,
        latest,
        updateAvailable: compareVersions(latest, current) > 0,
        lastChecked: Date.now(),
      };

      storeVersionInfo(info);
      return info;
    }
  } catch {
    // Silently fail - offline or rate limited
  }

  const info: VersionInfo = {
    current,
    latest: current,
    updateAvailable: false,
    lastChecked: Date.now(),
  };

  storeVersionInfo(info);
  return info;
}

function compareVersions(a: string, b: string): number {
  const pa = a.split('.').map(Number);
  const pb = b.split('.').map(Number);

  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const na = pa[i] || 0;
    const nb = pb[i] || 0;
    if (na > nb) return 1;
    if (na < nb) return -1;
  }

  return 0;
}

export function getVersionInfo(): VersionInfo | null {
  return getStoredVersionInfo();
}

export const version = {
  current: getCurrentVersion,
  check: checkForUpdates,
  getInfo: getVersionInfo,
};
