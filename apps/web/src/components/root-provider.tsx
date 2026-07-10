'use client';

import { Providers } from './providers';
import { AuthProvider } from '@/lib/auth';
import { OrgProvider } from '@/lib/org';
import { ThemeProvider } from '@/lib/theme';

export function RootProvider({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <Providers>
        <AuthProvider>
          <OrgProvider>
            {children}
          </OrgProvider>
        </AuthProvider>
      </Providers>
    </ThemeProvider>
  );
}
