'use client';

import { useEffect, useState } from 'react';
import { version } from '@/lib/version';

interface VersionInfo {
  current: string;
  latest: string;
  updateAvailable: boolean;
}

export function VersionBanner() {
  const [info, setInfo] = useState<VersionInfo | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const checkVersion = async () => {
      const versionInfo = await version.check();
      setInfo(versionInfo);
    };
    checkVersion();
  }, []);

  if (!info || !info.updateAvailable || dismissed) {
    return null;
  }

  return (
    <div className="rounded-lg border border-blue-500/50 bg-blue-50 p-4 dark:bg-blue-950">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <span className="text-lg text-blue-600">{'\u2139'}</span>
          <div>
            <h3 className="font-medium text-blue-900 dark:text-blue-100">
              Update Available
            </h3>
            <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
              Version {info.latest} is available (current: {info.current})
            </p>
            <a
              href="https://github.com/webbixray/astra-os/releases"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-block text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
            >
              View Release Notes
            </a>
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="text-blue-500 hover:text-blue-700"
          aria-label="Dismiss"
        >
          &times;
        </button>
      </div>
    </div>
  );
}
