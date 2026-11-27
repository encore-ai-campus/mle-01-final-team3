import { createContext } from "react";
import type { Account } from "../types/domain";
import type { LoginInput } from "./authApi";

export const AUTH_STORAGE_KEY = "food-ad-review:authenticated";
export const AUTH_DEPARTMENT_STORAGE_KEY = "food-ad-review:department";

export type AuthDepartment = "marketing" | "legal";

export interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  department: AuthDepartment | null;
  user: Account | null;
  login: (input: LoginInput & { department?: AuthDepartment }) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
