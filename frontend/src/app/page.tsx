"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderPlus, Plus } from "lucide-react";

import { APP_USER_NAME } from "@/config";
import { listProjects } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CreateProjectDialog } from "@/components/create-project-dialog";
import { ProjectCard } from "@/components/project-card";

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = React.useState(false);

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
    <div className="flex flex-col gap-10">
      <section className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{greeting},</p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            {APP_USER_NAME}
          </h1>
          <p className="max-w-xl text-sm text-muted-foreground sm:text-base">
            Configure ECUs, walk through the four-step setup, and run security
            test coverage. Pick up a project below or start fresh.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3 rounded-lg border border-border/60 bg-card px-4 py-3 shadow-sm">
          <div className="flex flex-col">
            <span className="text-xs uppercase tracking-wider text-muted-foreground">
              Projects
            </span>
            <span className="text-2xl font-semibold tabular-nums text-foreground">
              {isLoading ? "—" : projectCount}
            </span>
          </div>
          <div className="h-10 w-px bg-border" />
          <div className="flex flex-col">
            <span className="text-xs uppercase tracking-wider text-muted-foreground">
              Setup steps
            </span>
            <span className="text-2xl font-semibold tabular-nums text-foreground">4</span>
          </div>
        </div>
      </section>

      <section className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Your projects</h2>
          <p className="text-sm text-muted-foreground">
            Open a project to view its ECU details and security test cases.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus />
          New project
        </Button>
      </section>

      {isLoading ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-44 rounded-xl" />
          ))}
        </div>
      ) : isError ? (
        <p className="text-sm text-destructive">
          Failed to load projects:{" "}
          {error instanceof Error ? error.message : "unknown error"}
        </p>
      ) : projects && projects.length > 0 ? (
        <div className="stagger-in grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border bg-card/50 px-6 py-20 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
            <FolderPlus className="size-5" />
          </div>
          <div className="space-y-1">
            <p className="text-base font-semibold">No projects yet</p>
            <p className="mx-auto max-w-sm text-sm text-muted-foreground">
              Create your first project to start the four-step setup wizard and
              unlock security test coverage.
            </p>
          </div>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus />
            Create your first project
          </Button>
        </div>
      )}

      <CreateProjectDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onCreated={(project) => handleCreated(project.id)}
      />
    </div>
  );
}
