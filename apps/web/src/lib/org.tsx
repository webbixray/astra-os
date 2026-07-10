'use client';

import { createContext, useContext, useState, useEffect, useCallback, useRef, type ReactNode } from 'react';
import { useAuth } from './auth';
import { api } from './api';

interface OrgInfo {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  role: string;
}

interface OrgContextType {
  orgId: string;
  orgs: OrgInfo[];
  currentOrg: OrgInfo | null;
  setOrgId: (id: string) => void;
  isLoading: boolean;
  refresh: () => Promise<void>;
}

const OrgContext = createContext<OrgContextType | null>(null);

export function OrgProvider({ children }: { children: ReactNode }) {
  const { user, isAuthenticated } = useAuth();
  const [orgs, setOrgs] = useState<OrgInfo[]>([]);
  const [orgId, setOrgId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const fetchedRef = useRef(false);

  const fetchOrgs = useCallback(async () => {
    if (!isAuthenticated || !user) return;
    setIsLoading(true);
    try {
      const data = await api.get<OrgInfo[]>('/organizations/my');
      setOrgs(data);
      if (data.length > 0 && data[0]) {
        setOrgId((prev) => prev || data[0]!.id);
      }
    } catch {
      // Not critical - default org will be used
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    if (isAuthenticated && !fetchedRef.current) {
      fetchedRef.current = true;
      fetchOrgs();
    }
  }, [isAuthenticated, fetchOrgs]);

  const currentOrg = orgs.find((o) => o.id === orgId) || orgs[0] || null;

  return (
    <OrgContext.Provider value={{ orgId, orgs, currentOrg, setOrgId, isLoading, refresh: fetchOrgs }}>
      {children}
    </OrgContext.Provider>
  );
}

export function useOrg(): OrgContextType {
  const context = useContext(OrgContext);
  if (!context) {
    throw new Error('useOrg must be used within an OrgProvider');
  }
  return context;
}
