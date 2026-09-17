import * as React from "react";
import { cn } from "@/lib/utils";

interface SectionHeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

/**
 * Unified section header for consistent subsections within pages.
 * Used for grouping related content (e.g., "Your projects", "Test cases").
 * 
 * Usage:
 * <SectionHeader
 *   title="Your projects"
 *   description="Open a project to view its ECU details and security test cases."
 *   action={<Button>New project</Button>}
 * />
 */
export function SectionHeader({
  title,
  description,
  action,
  className,
}: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between", className)}>
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-foreground">{title}</h2>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
