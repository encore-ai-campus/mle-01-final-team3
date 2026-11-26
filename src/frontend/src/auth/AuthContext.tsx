import { useCallback, useState, type ReactNode } from "react";
import { AUTH_DEPARTMENT_STORAGE_KEY, AUTH_STORAGE_KEY, AuthContext, type AuthDepartment } from "./context";

function readAuthentication(): boolean {
  try {
    return sessionStorage.getItem(AUTH_STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function readDepartment(): AuthDepartment {
  try {
    return sessionStorage.getItem(AUTH_DEPARTMENT_STORAGE_KEY) === "legal" ? "legal" : "marketing";
  } catch {
    return "marketing";
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(readAuthentication);
  const [department, setDepartment] = useState<AuthDepartment>(readDepartment);
  const login = useCallback((nextDepartment: AuthDepartment) => {
    try {
      sessionStorage.setItem(AUTH_STORAGE_KEY, "true");
      sessionStorage.setItem(AUTH_DEPARTMENT_STORAGE_KEY, nextDepartment);
    } catch {
      // The in-memory state still supports the beta flow if storage is unavailable.
    }
    setDepartment(nextDepartment);
    setIsAuthenticated(true);
  }, []);
  const logout = useCallback(() => {
    try {
      sessionStorage.removeItem(AUTH_STORAGE_KEY);
      sessionStorage.removeItem(AUTH_DEPARTMENT_STORAGE_KEY);
    } catch {
      // Keep logout usable when storage is unavailable.
    }
    setIsAuthenticated(false);
  }, []);

  return <AuthContext.Provider value={{ isAuthenticated, department, login, logout }}>{children}</AuthContext.Provider>;
}

