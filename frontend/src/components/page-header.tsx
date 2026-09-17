import * as React from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  badge?: string;
  actions?: React.ReactNode;
  className?: string;
}

/**
 * Unified page header component for consistent visual hierarchy
 * across admin and user sections.
 * 
 * Usage:
 * <PageHeader
 *   title="Test Cases"
 *   description="Manage security test cases"
 *   actions={<Button>Create</Button>}
 * />
 */
export function PageHeader({
  title,
  description,
  icon,
  badge,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between",
        className
      )}
    >
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          {icon && <div className="text-2xl">{icon}</div>}
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              {title}
            </h1>
            {badge && (
              <span className="inline-flex items-center gap-1 rounded-full bg-accent px-3 py-1 text-xs font-medium text-accent-foreground">
                {badge}
              </span>
            )}
          </div>
        </div>
        {description && (
          <p className="max-w-xl text-sm text-muted-foreground sm:text-base">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex shrink-0 items-center gap-2 sm:justify-end">
          {actions}
        </div>
      )}
    </div>
  );
}
