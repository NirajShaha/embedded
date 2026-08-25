"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderPlus } from "lucide-react";

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

  const { data: projects, isLoading, isError, error } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  const handleCreated = (projectId: number) => {
    setDialogOpen(false);
    queryClient.invalidateQueries({ queryKey: ["projects"] });
    router.push(`/projects/${projectId}/page/1`);
  };

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8">
      <section className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          Good day, {APP_USER_NAME}
        </h1>
        <p className="text-muted-foreground">
          Pick up where you left off, or start a new project configuration.
        </p>
      </section>

      <section className="flex items-center justify-between">
        <h2 className="text-xl font-medium">Your projects</h2>
        <Button onClick={() => setDialogOpen(true)}>
          <FolderPlus />
          New project
        </Button>
      </section>

      {isLoading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-44 rounded-xl" />
          ))}
        </div>
      ) : isError ? (
        <p className="text-destructive">
          Failed to load projects: {error instanceof Error ? error.message : "unknown error"}
        </p>
      ) : projects && projects.length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed py-16 text-center">
          <FolderPlus className="size-10 text-muted-foreground" />
          <div>
            <p className="font-medium">No projects yet</p>
            <p className="text-sm text-muted-foreground">
              Create your first project to start the setup wizard.
            </p>
          </div>
          <Button onClick={() => setDialogOpen(true)}>
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