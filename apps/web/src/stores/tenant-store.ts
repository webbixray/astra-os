import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { OrganizationResponse } from '@/lib/api/generated';

interface TenantState {
  currentTenant: OrganizationResponse | null;
  availableTenants: OrganizationResponse[];
  isLoading: boolean;
  error: string | null;

  // Actions
  setCurrentTenant: (tenant: OrganizationResponse | null) => void;
  setAvailableTenants: (tenants: OrganizationResponse[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  switchTenant: (tenantId: string) => Promise<void>;
  fetchTenants: () => Promise<void>;
  clearError: () => void;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set, get) => ({
      currentTenant: null,
      availableTenants: [],
      isLoading: false,
      error: null,

      setCurrentTenant: (tenant) => set({ currentTenant: tenant }),

      setAvailableTenants: (tenants) => set({ availableTenants: tenants }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      clearError: () => set({ error: null }),

      switchTenant: async (tenantId: string) => {
        const { availableTenants } = get();
        const tenant = availableTenants.find(t => t.id === tenantId);

        if (!tenant) {
          set({ error: 'Tenant not found' });
          return;
        }

        set({ currentTenant: tenant, error: null });

        // Update the X-Tenant-ID header for subsequent API calls
        // This will be picked up by the axios interceptor
        document.cookie = `astra_current_tenant=${tenantId}; path=/; max-age=31536000; SameSite=Lax`;

        // Reload the page to apply new tenant context
        window.location.reload();
      },

      fetchTenants: async () => {
        set({ isLoading: true, error: null });

        try {
          // Dynamic import to avoid circular dependencies
          const { OrganizationsService } = await import('@/lib/api/generated');

          const response = await OrganizationsService.getOrganizations();

          if (response.data && response.data.data) {
            set({ availableTenants: response.data.data, isLoading: false });

            // If no current tenant but we have tenants, set the first one
            const { currentTenant } = get();
            if (!currentTenant && response.data.data.length > 0) {
              get().switchTenant(response.data.data[0].id);
            }
          }
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to fetch tenants';
          set({ error: errorMessage, isLoading: false });
        }
      },
    }),
    {
      name: 'astra-tenant-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentTenant: state.currentTenant,
        availableTenants: state.availableTenants,
      }),
    }
  )
);

// Helper hook for easy access to current tenant ID
export const useCurrentTenantId = () => {
  const currentTenant = useTenantStore((state) => state.currentTenant);
  return currentTenant?.id ?? null;
};

// Helper hook for checking if user has access to a tenant
export const useHasTenantAccess = (tenantId: string) => {
  const availableTenants = useTenantStore((state) => state.availableTenants);
  return availableTenants.some(t => t.id === tenantId);
};