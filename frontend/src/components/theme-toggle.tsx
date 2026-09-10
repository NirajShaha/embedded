"use client";

import {
  useEffect,
  useState,
} from "react";
import {
  Moon,
  Sun,
} from "lucide-react";

import {
  useTheme,
} from "@/components/theme-provider";
import {
  Button,
} from "@/components/ui/button";


export function ThemeToggle() {
  const {
    resolvedTheme,
    setTheme,
  } = useTheme();

  const [
    mounted,
    setMounted,
  ] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled
        aria-label="Loading theme"
      >
        <Sun className="size-5" />

        <span className="sr-only">
          Loading theme
        </span>
      </Button>
    );
  }

  const isDark =
    resolvedTheme === "dark";

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={() =>
        setTheme(
          isDark
            ? "light"
            : "dark",
        )
      }
      aria-label={
        isDark
          ? "Switch to light theme"
          : "Switch to dark theme"
      }
      title={
        isDark
          ? "Switch to light theme"
          : "Switch to dark theme"
      }
    >
      {isDark ? (
        <Sun className="size-5" />
      ) : (
        <Moon className="size-5" />
      )}

      <span className="sr-only">
        Toggle theme
      </span>
    </Button>
  );
}