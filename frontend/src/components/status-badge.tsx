import * as React from "react";
import { cn } from "@/lib/utils";

type StatusType = "critical" | "high" | "medium" | "low" | "info" | "success" | "warning";

const statusConfig: Record<StatusType, { bg: string; text: string; label: string }> = {
  critical: {
    bg: "bg-red-100 dark:bg-red-950",
    text: "text-red-700 dark:text-red-200",
    label: "Critical",
  },
  high: {
    bg: "bg-orange-100 dark:bg-orange-950",
    text: "text-orange-700 dark:text-orange-200",
    label: "High",
  },
  medium: {
    bg: "bg-yellow-100 dark:bg-yellow-950",
    text: "text-yellow-700 dark:text-yellow-200",
    label: "Medium",
  },
  low: {
    bg: "bg-green-100 dark:bg-green-950",
    text: "text-green-700 dark:text-green-200",
    label: "Low",
  },
  info: {
    bg: "bg-blue-100 dark:bg-blue-950",
    text: "text-blue-700 dark:text-blue-200",
    label: "Info",
  },
  success: {
    bg: "bg-emerald-100 dark:bg-emerald-950",
    text: "text-emerald-700 dark:text-emerald-200",
    label: "Success",
  },
  warning: {
    bg: "bg-amber-100 dark:bg-amber-950",
    text: "text-amber-700 dark:text-amber-200",
    label: "Warning",
  },
};

interface StatusBadgeProps {
  status: StatusType;
  customLabel?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

/**
 * Unified status badge for consistent severity/status indicators.
 * Used throughout the application for test cases, alerts, etc.
 * 
 * Usage:
 * <StatusBadge status="critical" />
 * <StatusBadge status="high" customLabel="High Priority" />
 */
export function StatusBadge({
  status,
  customLabel,
  size = "md",
  className,
}: StatusBadgeProps) {
  const config = statusConfig[status];
  const label = customLabel || config.label;

  const sizeClasses = {
    sm: "px-2 py-1 text-xs",
    md: "px-2.5 py-1.5 text-sm",
    lg: "px-3 py-2 text-base",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-medium rounded-full",
        config.bg,
        config.text,
        sizeClasses[size],
        className
      )}
    >
      <span className={cn("h-2 w-2 rounded-full", config.text.replace("text-", "bg-"))} />
      {label}
    </span>
  );
}
