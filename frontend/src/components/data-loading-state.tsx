import * as React from "react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface DataLoadingStateProps {
  isLoading: boolean;
  isEmpty: boolean;
  isError: boolean;
  error?: Error | null;
  children: React.ReactNode;
  loadingContent?: React.ReactNode;
  emptyContent?: React.ReactNode;
  errorContent?: React.ReactNode;
  className?: string;
}

/**
 * Unified data loading state component that handles:
 * - Loading skeleton display
 * - Empty state display
 * - Error state display
 * - Success state display (children)
 * 
 * Usage:
 * <DataLoadingState
 *   isLoading={isLoading}
 *   isEmpty={!data || data.length === 0}
 *   isError={isError}
 *   error={error}
 *   loadingContent={<Skeleton className="h-44 rounded-xl" />}
 *   emptyContent={<EmptyState ... />}
 *   errorContent={<Alert variant="destructive" ... />}
 * >
 *   <DataGrid data={data} />
 * </DataLoadingState>
 */
export function DataLoadingState({
  isLoading,
  isEmpty,
  isError,
  error,
  children,
  loadingContent,
  emptyContent,
  errorContent,
  className,
}: DataLoadingStateProps) {
  if (isLoading) {
    return (
      <div className={cn("w-full", className)}>
        {loadingContent}
      </div>
    );
  }

  if (isError) {
    return (
      <div className={cn("w-full", className)}>
        {errorContent || (
          <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
            <p className="text-sm text-destructive">
              Failed to load data: {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        )}
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className={cn("w-full", className)}>
        {emptyContent}
      </div>
    );
  }

  return (
    <div className={cn("w-full", className)}>
      {children}
    </div>
  );
}
