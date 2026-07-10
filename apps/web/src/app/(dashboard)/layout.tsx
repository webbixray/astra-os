import dynamic from 'next/dynamic';
import { AppShell } from '@/components/app-shell';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const AICommandCenter = dynamic(
  () => import('@/components/ai/ai-command-center').then((mod) => mod.AICommandCenter),
  { ssr: false },
);

const CommandPalette = dynamic(
  () => import('@/components/ui/command-palette').then((mod) => mod.CommandPalette),
  { ssr: false },
);

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <AppShell>
        <ErrorBoundary>{children}</ErrorBoundary>
      </AppShell>
      <AICommandCenter />
      <CommandPalette />
    </>
  );
}
