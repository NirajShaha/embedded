"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import { API_URL } from "@/config";

export type UserRole = "ADMIN" | "USER";

export interface AuthUser {
  id: number;
  username: string;
  role: UserRole;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;

  login: (username: string, password: string) => Promise<void>;

  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function isValidAuthUser(value: unknown): value is AuthUser {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Partial<AuthUser>;

  return (
    typeof candidate.id === "number" &&
    Number.isFinite(candidate.id) &&
    typeof candidate.username === "string" &&
    candidate.username.trim().length > 0 &&
    (candidate.role === "ADMIN" || candidate.role === "USER")
  );
}

function clearStoredAuthentication() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

function readStoredAuthentication(): AuthUser | null {
  const token = localStorage.getItem("token");

  const storedUser = localStorage.getItem("user");

  if (!token || !storedUser) {
    clearStoredAuthentication();
    return null;
  }

  try {
    const parsedUser: unknown = JSON.parse(storedUser);

    if (!isValidAuthUser(parsedUser)) {
      clearStoredAuthentication();
      return null;
    }

    return parsedUser;
  } catch {
    clearStoredAuthentication();
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();

  /*
   * These initial values must be identical
   * during server rendering and the browser's
   * first hydration render.
   *
   * Do not read localStorage in useState.
   */
  const [user, setUser] = useState<AuthUser | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  const authenticationChangedRef = useRef(false);

  /*
   * localStorage is accessed only after
   * hydration has completed in the browser.
   */
  useEffect(() => {
    if (authenticationChangedRef.current) {
      setIsLoading(false);
      return;
    }

    const storedUser = readStoredAuthentication();

    setUser(storedUser);
    setIsLoading(false);
  }, []);

  /*
   * The shared API client dispatches this
   * event when the backend returns 401.
   */
  useEffect(() => {
    const handleUnauthorized = () => {
      clearStoredAuthentication();
      setUser(null);
      setIsLoading(false);

      router.replace("/login");
      router.refresh();
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);

    return () => {
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, [router]);

  /*
   * Keep authentication synchronized between
   * multiple tabs and browser windows.
   */
  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key !== "token" && event.key !== "user" && event.key !== null) {
        return;
      }

      const storedUser = readStoredAuthentication();

      setUser(storedUser);
      setIsLoading(false);

      if (!storedUser) {
        router.replace("/login");
        router.refresh();
      }
    };

    window.addEventListener("storage", handleStorageChange);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, [router]);

  const login = useCallback(
    async (username: string, password: string) => {
      const normalizedUsername = username.trim();

      if (!normalizedUsername) {
        throw new Error("Username is required.");
      }

      if (!password) {
        throw new Error("Password is required.");
      }

      setIsLoading(true);

      try {
        const response = await fetch(`${API_URL}/auth/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username: normalizedUsername,
            password,
          }),
        });

        if (!response.ok) {
          let message = "Invalid username or password";

          try {
            const responseBody = (await response.json()) as {
              detail?: string;
            };

            if (
              typeof responseBody.detail === "string" &&
              responseBody.detail.trim().length > 0
            ) {
              message = responseBody.detail;
            }
          } catch {
            /*
             * Keep the default login error
             * when the response is not JSON.
             */
          }

          throw new Error(message);
        }

        const data = (await response.json()) as LoginResponse;

        if (!data.access_token || !isValidAuthUser(data.user)) {
          throw new Error("The login response is invalid.");
        }

        localStorage.setItem("token", data.access_token);

        localStorage.setItem("user", JSON.stringify(data.user));

        authenticationChangedRef.current = true;
        setUser(data.user);

        window.location.assign(data.user.role === "ADMIN" ? "/admin" : "/");
      } finally {
        setIsLoading(false);
      }
    },
    [router],
  );

  const logout = useCallback(() => {
    authenticationChangedRef.current = true;
    clearStoredAuthentication();

    setUser(null);
    setIsLoading(false);

    router.replace("/login");
    router.refresh();
  }, [router]);

  const contextValue = useMemo<AuthContextValue>(
    () => ({
      user,

      isAuthenticated: user !== null,

      isAdmin: user?.role === "ADMIN",

      isLoading,

      login,
      logout,
    }),
    [user, isLoading, login, logout],
  );

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
