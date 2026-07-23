import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { ToastProvider } from '@/components/ui/toast';
import React from 'react';
import { vi } from 'vitest';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
}

function AllProviders({ children, queryClient }: { children: React.ReactNode; queryClient: QueryClient }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
        <ToastProvider>{children}</ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export function customRender(ui: React.ReactElement, options: CustomRenderOptions = {}): ReturnType<typeof render> & { queryClient: QueryClient } {
  const { queryClient = createTestQueryClient(), ...renderOptions } = options;

  function Wrapper({ children }: { children: React.ReactNode }) {
    return <AllProviders queryClient={queryClient}>{children}</AllProviders>;
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

export const mockUser = {
  id: 'test-user-id',
  email: 'test@astra.dev',
  name: 'Test User',
  role: 'admin',
  avatar_url: null,
};

export const mockOrganization = {
  id: 'test-org-id',
  name: 'Test Organization',
  slug: 'test-org',
  plan: 'professional',
};

export function createMockFetch(responses: Record<string, unknown>) {
  const mockFn = vi.fn((url: string): Promise<{ ok: boolean; json: () => Promise<unknown> }> => {
    const key = Object.keys(responses).find((k) => url.includes(k));
    if (key) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(responses[key]),
      });
    }
    return Promise.resolve({
      ok: false,
      json: () => Promise.resolve({ error: 'Not found' }),
    });
  });
  return mockFn;
}

export function setupIntersectionObserverMock() {
  const mockIntersectionObserver = vi.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  });
  window.IntersectionObserver = mockIntersectionObserver as unknown as typeof IntersectionObserver;
}

export function setupResizeObserverMock() {
  class MockResizeObserver {
    callback: ResizeObserverCallback;
    constructor(callback: ResizeObserverCallback) {
      this.callback = callback;
    }
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
  }
  window.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;
}

export function mockClipboard() {
  Object.assign(navigator, {
    clipboard: {
      writeText: vi.fn(),
      readText: vi.fn(),
    },
  });
}

export function mockLocalStorage() {
  const store: Record<string, string> = {};

  vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => store[key as string] || null);
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation((key, value) => {
    store[key as string] = value;
  });
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation((key) => {
    store[key as string] = undefined as unknown as string;
  });
  vi.spyOn(Storage.prototype, 'clear').mockImplementation(() => {
    Object.keys(store).forEach((key) => { store[key] = undefined as unknown as string; });
  });

  return store;
}
