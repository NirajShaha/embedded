"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { LayoutDashboard, Cpu, ShieldCheck } from "lucide-react";

import { getProject } from "@/lib/api";
import { ThemeToggle } from "@/components/theme-toggle";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar";

function projectIdFromPath(pathname: string): number | null {
  const match = pathname.match(/^\/projects\/(\d+)/);
  return match ? Number(match[1]) : null;
}

function pageNumberFromPath(pathname: string): number | null {
  const match = pathname.match(/\/page\/(\d+)$/);
  return match ? Number(match[1]) : null;
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname();
  const currentProjectId = projectIdFromPath(pathname);
  const currentPage = pageNumberFromPath(pathname);

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ["project", currentProjectId],
    queryFn: () => getProject(currentProjectId as number),
    enabled: currentProjectId !== null,
  });

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href="/">
                <div className="flex aspect-square size-8 items-center justify-center rounded-md bg-primary text-primary-foreground shadow-sm">
                  <ShieldCheck className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold tracking-tight">Embedded Config</span>
                  <span className="truncate text-xs text-muted-foreground">Security setup</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild isActive={pathname === "/"} tooltip="Dashboard">
                <Link href="/">
                  <LayoutDashboard />
                  <span>Dashboard</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>

        {currentProjectId !== null && (
          <>
            <SidebarSeparator />
            <SidebarGroup>
              <SidebarGroupLabel>Current project</SidebarGroupLabel>
              <SidebarMenu>
                <SidebarMenuItem>
                  {projectLoading ? (
                    <div className="flex h-8 items-center gap-2 rounded-md px-2">
                      <Skeleton className="size-4 shrink-0 rounded-md" />
                      <Skeleton className="h-3.5 flex-1 max-w-[70%]" />
                    </div>
                  ) : (
                    <SidebarMenuButton
                      asChild
                      isActive={pathname.includes("/projects/") && !pathname.includes("/page/")}
                      tooltip="ECU details"
                    >
                      <Link href={`/projects/${currentProjectId}/dashboard`}>
                        <Cpu />
                        <span className="truncate">
                          {project?.name ?? `Project #${currentProjectId}`}
                        </span>
                      </Link>
                    </SidebarMenuButton>
                  )}
                </SidebarMenuItem>
                {currentPage !== null && (
                  <SidebarMenuItem>
                    <div className="rounded-md border border-sidebar-border/60 bg-sidebar-accent/30 px-2 py-1.5 text-xs text-sidebar-accent-foreground">
                      <span className="text-muted-foreground">Editing step</span>
                      <span className="ml-1 font-medium">{currentPage} of 4</span>
                    </div>
                  </SidebarMenuItem>
                )}
              </SidebarMenu>
            </SidebarGroup>
          </>
        )}
      </SidebarContent>

      <SidebarFooter>
        <div className="flex items-center justify-between px-1">
          <span className="text-xs text-muted-foreground group-data-[collapsible=icon]:hidden">
            Appearance
          </span>
          <ThemeToggle />
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
