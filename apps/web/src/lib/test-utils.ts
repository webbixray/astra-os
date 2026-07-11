import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { ToastProvider } from '@/components/ui/toast';
import React from 'react';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
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

export function customRender(ui: React.ReactElement, options: CustomRenderOptions = {}) {
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
  return jest.fn().mockImplementation((url: string) => {
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
}

export function setupIntersectionObserverMock() {
  const mockIntersectionObserver = jest.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  });
  window.IntersectionObserver = mockIntersectionObserver;
}

export function setupResizeObserverMock() {
  class MockResizeObserver {
    callback: ResizeObserverCallback;
    constructor(callback: ResizeObserverCallback) {
      this.callback = callback;
    }
    observe = jest.fn();
    unobserve = jest.fn();
    disconnect = jest.fn();
  }
  window.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;
}

export function mockClipboard() {
  Object.assign(navigator, {
    clipboard: {
      writeText: jest.fn(),
      readText: jest.fn(),
    },
  });
}

export function mockLocalStorage() {
  const store: Record<string, string> = {};

  jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => store[key as string] || null);
  jest.spyOn(Storage.prototype, 'setItem').mockImplementation((key, value) => {
    store[key as string] = value;
  });
  jest.spyOn(Storage.prototype, 'removeItem').mockImplementation((key) => {
    delete store[key as string];
  });
  jest.spyOn(Storage.prototype, 'clear').mockImplementation(() => {
    Object.keys(store).forEach((key) => delete store[key]);
  });

  return store;
}
