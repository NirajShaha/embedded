"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";


export type Theme =
  | "light"
  | "dark"
  | "system";


interface ThemeContextValue {
  theme: Theme;
  resolvedTheme:
  | "light"
  | "dark";
  setTheme: (
    theme: Theme,
  ) => void;
}


interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
}


const ThemeContext =
  createContext<
    ThemeContextValue | undefined
  >(undefined);


function isTheme(
  value: string | null,
): value is Theme {
  return (
    value === "light" ||
    value === "dark" ||
    value === "system"
  );
}


function getSystemTheme():
  | "light"
  | "dark" {
  if (
    typeof window !== "undefined" &&
    window.matchMedia(
      "(prefers-color-scheme: dark)",
    ).matches
  ) {
    return "dark";
  }

  return "light";
}


export function ThemeProvider({
  children,
  defaultTheme = "system",
  storageKey = "embedded-config-theme",
}: ThemeProviderProps) {
  const [
    theme,
    setThemeState,
  ] = useState<Theme>(
    defaultTheme,
  );

  const [
    systemTheme,
    setSystemTheme,
  ] = useState<
    "light" | "dark"
  >("light");

  const [
    mounted,
    setMounted,
  ] = useState(false);

  useEffect(() => {
    const storedTheme =
      localStorage.getItem(
        storageKey,
      );

    if (isTheme(storedTheme)) {
      setThemeState(storedTheme);
    }

    setSystemTheme(
      getSystemTheme(),
    );

    setMounted(true);
  }, [storageKey]);

  useEffect(() => {
    const mediaQuery =
      window.matchMedia(
        "(prefers-color-scheme: dark)",
      );

    const handleSystemThemeChange =
      (
        event:
          MediaQueryListEvent,
      ) => {
        setSystemTheme(
          event.matches
            ? "dark"
            : "light",
        );
      };

    mediaQuery.addEventListener(
      "change",
      handleSystemThemeChange,
    );

    return () => {
      mediaQuery.removeEventListener(
        "change",
        handleSystemThemeChange,
      );
    };
  }, []);

  const resolvedTheme =
    theme === "system"
      ? systemTheme
      : theme;

  useEffect(() => {
    if (!mounted) {
      return;
    }

    const root =
      document.documentElement;

    root.classList.remove(
      "light",
      "dark",
    );

    root.classList.add(
      resolvedTheme,
    );

    root.style.colorScheme =
      resolvedTheme;
  }, [
    mounted,
    resolvedTheme,
  ]);

  const setTheme = useCallback(
    (
      nextTheme: Theme,
    ) => {
      setThemeState(
        nextTheme,
      );

      localStorage.setItem(
        storageKey,
        nextTheme,
      );
    },
    [storageKey],
  );

  const contextValue =
    useMemo<
      ThemeContextValue
    >(
      () => ({
        theme,
        resolvedTheme,
        setTheme,
      }),
      [
        theme,
        resolvedTheme,
        setTheme,
      ],
    );

  return (
    <ThemeContext.Provider
      value={contextValue}
    >
      {children}
    </ThemeContext.Provider>
  );
}


export function useTheme() {
  const context =
    useContext(
      ThemeContext,
    );

  if (!context) {
    throw new Error(
      "useTheme must be used within ThemeProvider",
    );
  }

  return context;
}