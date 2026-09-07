"use client";

import { ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoading } = useAuth();

  // Don't show layout on login page
  if (pathname === "/login") {
    return <>{children}</>;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="space-y-4">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
        </div>
      </div>
    );
  }

  if (!user) {
    router.push("/login");
    return null;
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="surface-grain">
        <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-3 border-b border-border/60 bg-background/80 px-5 backdrop-blur-md">
          <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-foreground" />
          <div className="h-5 w-px bg-border" />
          <div className="flex flex-1 items-center gap-2 text-sm">
            <span className="text-muted-foreground">Signed in as</span>
            <span className="font-medium text-foreground">{user.username}</span>
            <span className="text-xs text-muted-foreground">({user.role})</span>
            <span className="ml-2 inline-flex h-1.5 w-1.5 rounded-full bg-[var(--signal)] shadow-[0_0_0_3px_oklch(0.62_0.13_215/0.18)]" />
          </div>
          <div className="hidden items-center gap-1.5 rounded-full border border-border/60 bg-card/60 px-2.5 py-1 text-xs text-muted-foreground sm:flex">
            <kbd className="rounded border border-border/80 bg-background px-1 font-mono text-[10px]">⌘</kbd>
            <kbd className="rounded border border-border/80 bg-background px-1 font-mono text-[10px]">B</kbd>
            <span className="ml-1">Toggle sidebar</span>
          </div>
        </header>
        <main className="flex-1 overflow-auto">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
