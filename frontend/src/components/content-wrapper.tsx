import * as React from "react";
import { cn } from "@/lib/utils";

interface ContentWrapperProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Unified content wrapper for consistent max-width and padding
 * across all pages. Provides a unified container experience.
 * 
 * Usage:
 * <ContentWrapper>
 *   <PageHeader ... />
 *   <div>Page content</div>
 * </ContentWrapper>
 */
export function ContentWrapper({ children, className }: ContentWrapperProps) {
  return (
    <div className={cn("flex flex-col gap-10 w-full", className)}>
      {children}
    </div>
  );
}
