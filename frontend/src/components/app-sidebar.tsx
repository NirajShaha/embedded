"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { LayoutDashboard, Layers, Settings2 } from "lucide-react";

import { totalPages } from "@/lib/navigation";
import { getProject } from "@/lib/api";
import { ThemeToggle } from "@/components/theme-toggle";
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

  const { data: project } = useQuery({
    queryKey: ["project", currentProjectId],
    queryFn: () => getProject(currentProjectId as number),
    enabled: currentProjectId !== null,
  });

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg">
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <Settings2 className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">Embedded Config</span>
                <span className="truncate text-xs">Setup wizard</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild isActive={pathname === "/"}>
                <Link href="/">
                  <LayoutDashboard />
                  <span>Dashboard</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div className="flex items-center justify-between px-2">
          <ThemeToggle />
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
