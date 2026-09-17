"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderPlus, Plus, LayoutGrid } from "lucide-react";

import { APP_USER_NAME } from "@/config";
import { listProjects } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CreateProjectDialog } from "@/components/create-project-dialog";
import { ProjectCard } from "@/components/project-card";
import { PageHeader } from "@/components/page-header";
import { SectionHeader } from "@/components/section-header";
import { ContentWrapper } from "@/components/content-wrapper";
import { EmptyState } from "@/components/empty-state";
import { DataLoadingState } from "@/components/data-loading-state";
import { StatCard } from "@/components/stat-card";

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const { user, logout } = useAuth();

  const {
    data: projects,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  const handleCreated = (projectId: number) => {
    setDialogOpen(false);
    queryClient.invalidateQueries({ queryKey: ["projects"] });
    router.push(`/projects/${projectId}/dashboard`);
  };

  const projectCount = projects?.length ?? 0;
  const greeting = React.useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 5) return "Working late";
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  }, []);

  return (
    <ContentWrapper>
      {/* Page Header */}
      <PageHeader
        title={APP_USER_NAME}
        description="Configure ECUs, walk through the four-step setup, and run security test coverage. Pick up a project below or start fresh."
        badge={greeting}
      />

      {/* Statistics Section */}
      <div className="grid gap-4 sm:grid-cols-2">
        <StatCard
          label="Projects"
          value={isLoading ? "—" : projectCount}
          subLabel="Active projects"
          icon={LayoutGrid}
          iconBg="bg-blue-100 dark:bg-blue-950"
          iconColor="text-blue-600 dark:text-blue-200"
          isLoading={isLoading}
        />
        <StatCard
          label="Setup Steps"
          value="4"
          subLabel="Per project"
          icon={LayoutGrid}
          iconBg="bg-emerald-100 dark:bg-emerald-950"
          iconColor="text-emerald-600 dark:text-emerald-200"
        />
      </div>

      {/* Projects Section */}
      <div className="space-y-6">
        <SectionHeader
          title="Your projects"
          description="Open a project to view its ECU details and security test cases."
          action={
            <Button onClick={() => setDialogOpen(true)} className="gap-1.5">
              <Plus className="h-4 w-4" />
              New project
            </Button>
          }
        />

        <DataLoadingState
          isLoading={isLoading}
          isEmpty={!projects || projects.length === 0}
          isError={isError}
          error={error}
          loadingContent={
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-44 rounded-xl" />
              ))}
            </div>
          }
          emptyContent={
            <EmptyState
              icon={<FolderPlus className="h-6 w-6" />}
              title="No projects yet"
              description="Create your first project to start the four-step setup wizard and unlock security test coverage."
              action={
                <Button onClick={() => setDialogOpen(true)} className="gap-1.5">
                  <Plus className="h-4 w-4" />
                  Create your first project
                </Button>
              }
            />
          }
        >
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {projects?.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </DataLoadingState>
      </div>

      <CreateProjectDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onCreated={(project) => handleCreated(project.id)}
      />
    </ContentWrapper>
  );
}
