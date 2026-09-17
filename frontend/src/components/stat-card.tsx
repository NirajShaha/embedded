import * as React from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: number | string;
  subLabel?: string;
  icon?: React.ElementType;
  iconBg?: string;
  iconColor?: string;
  isLoading?: boolean;
  trend?: {
    value: string;
    direction: "up" | "down" | "neutral";
  };
  className?: string;
}

/**
 * Unified stat card component for displaying metrics.
 * Works for both admin and user dashboards.
 * 
 * Usage:
 * <StatCard
 *   label="Projects"
 *   value={12}
 *   subLabel="Active projects"
 *   icon={FolderIcon}
 *   iconBg="bg-blue-100"
 *   iconColor="text-blue-600"
 * />
 */
export function StatCard({
  label,
  value,
  subLabel,
  icon: Icon,
  iconBg = "bg-accent/10",
  iconColor = "text-accent",
  isLoading = false,
  trend,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-4 rounded-xl border bg-card p-5 shadow-sm transition-shadow hover:shadow-md",
        className
      )}
    >
      {Icon && (
        <div className={cn("flex size-12 shrink-0 items-center justify-center rounded-xl", iconBg)}>
          <Icon className={cn("size-6", iconColor)} />
        </div>
      )}
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </p>
        <p className="mt-0.5 text-3xl font-bold tabular-nums text-foreground">
          {isLoading ? (
            <span className="inline-block h-8 w-16 animate-pulse rounded-md bg-muted" />
          ) : (
            value
          )}
        </p>
        {subLabel && (
          <p className="mt-0.5 text-xs text-muted-foreground flex items-center gap-1">
            {subLabel}
            {trend && (
              <span
                className={cn(
                  "text-xs font-medium",
                  trend.direction === "up" && "text-green-600",
                  trend.direction === "down" && "text-red-600",
                  trend.direction === "neutral" && "text-muted-foreground"
                )}
              >
                {trend.value}
              </span>
            )}
          </p>
        )}
      </div>
    </div>
  );
}
