import { useCallback, useEffect, useState, type ReactNode } from "react";
import { createRestClient } from "../api/apiConfig";
import type { Account } from "../types/domain";
import { RestAuthApi, type AuthApi, type LoginInput } from "./authApi";
import { AUTH_DEPARTMENT_STORAGE_KEY, AUTH_STORAGE_KEY, AuthContext, type AuthDepartment } from "./context";

interface AuthProviderProps {
  children: ReactNode;
  api?: AuthApi | null;
  useFixtures?: boolean;
}

function readDepartment(): AuthDepartment {
  try {
    return sessionStorage.getItem(AUTH_DEPARTMENT_STORAGE_KEY) === "legal" ? "legal" : "marketing";
  } catch {
    return "marketing";
  }
}

function createFixtureUser(department: AuthDepartment): Account {
  return {
    userId: "fixture-user",
    name: department === "legal" ? "법무 담당자" : "마케팅 담당자",
    email: `${department}@adguard.local`,
    department,
    role: "reviewer",
    needsPasswordChange: false,
  };
}

export function AuthProvider({ children, api, useFixtures }: AuthProviderProps) {
  const demoMode = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("demo") === "true";
  const fixtureMode = useFixtures ?? (api === undefined && (import.meta.env.VITE_USE_FIXTURES !== "false" || demoMode));
  const [authApi] = useState<AuthApi | null>(() => {
    if (fixtureMode) return null;
    if (api !== undefined) return api;
    const client = createRestClient();
    return client ? new RestAuthApi(client) : null;
  });
  const [user, setUser] = useState<Account | null>(() => {
    if (!fixtureMode) return null;
    try {
      return sessionStorage.getItem(AUTH_STORAGE_KEY) === "true" ? createFixtureUser(readDepartment()) : null;
    } catch {
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState(!fixtureMode);

  useEffect(() => {
    if (fixtureMode || !authApi) {
      setIsLoading(false);
      return;
    }

    let active = true;
    void authApi.me().then((account) => {
      if (active) setUser(account);
    }).catch(() => {
      if (active) setUser(null);
    }).finally(() => {
      if (active) setIsLoading(false);
    });
    return () => {
      active = false;
    };
  }, [authApi, fixtureMode]);

  const login = useCallback(async (input: LoginInput & { department?: AuthDepartment }) => {
    if (fixtureMode || !authApi) {
      const department = input.department ?? (input.loginType === "ADMIN" ? "marketing" : readDepartment());
      try {
        sessionStorage.setItem(AUTH_STORAGE_KEY, "true");
        sessionStorage.setItem(AUTH_DEPARTMENT_STORAGE_KEY, department);
      } catch {
        // Keep the fixture login usable when storage is unavailable.
      }
      setUser(createFixtureUser(department));
      return;
    }

    setIsLoading(true);
    try {
      setUser(await authApi.login(input));
    } finally {
      setIsLoading(false);
    }
  }, [authApi, fixtureMode]);

  const logout = useCallback(async () => {
    try {
      if (!fixtureMode && authApi) await authApi.logout();
    } finally {
      try {
        sessionStorage.removeItem(AUTH_STORAGE_KEY);
        sessionStorage.removeItem(AUTH_DEPARTMENT_STORAGE_KEY);
      } catch {
        // Keep logout usable when storage is unavailable.
      }
      setUser(null);
    }
  }, [authApi, fixtureMode]);

  const department = user?.department === "marketing" || user?.department === "legal" ? user.department : null;
  return <AuthContext.Provider value={{ isAuthenticated: user !== null, isLoading, department, user, login, logout }}>{children}</AuthContext.Provider>;
}
