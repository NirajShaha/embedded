import * as React from "react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

/**
 * Unified empty state component for consistent appearance
 * when there's no data to display.
 * 
 * Usage:
 * <EmptyState
 *   icon={<FileIcon />}
 *   title="No projects yet"
 *   description="Create your first project to get started"
 *   action={<Button>Create Project</Button>}
 * />
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border bg-card/50 px-6 py-20 text-center",
        className
      )}
    >
      <div className="flex size-12 items-center justify-center rounded-full bg-accent/10 text-accent">
        {icon}
      </div>
      <div className="space-y-2">
        <p className="text-base font-semibold text-foreground">{title}</p>
        {description && (
          <p className="mx-auto max-w-sm text-sm text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
}
