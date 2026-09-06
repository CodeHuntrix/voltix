import { create } from "zustand";
import { persist } from "zustand/middleware";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  siteId: string | null;
  orgId: string | null;
  setTokens: (access: string, refresh: string) => void;
  setContext: (orgId: string, siteId: string) => void;
  logout: () => void;
};

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      siteId: null,
      orgId: null,
      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      setContext: (orgId, siteId) => set({ orgId, siteId }),
      logout: () =>
        set({ accessToken: null, refreshToken: null, siteId: null, orgId: null }),
    }),
    { name: "voltix-auth" },
  ),
);
