import { createContext } from "react";

export const AUTH_STORAGE_KEY = "food-ad-review:authenticated";
export const AUTH_DEPARTMENT_STORAGE_KEY = "food-ad-review:department";

export type AuthDepartment = "marketing" | "legal";

export interface AuthContextValue {
  isAuthenticated: boolean;
  department: AuthDepartment;
  login: (department: AuthDepartment) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
