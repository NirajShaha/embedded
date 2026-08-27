"use client";

import Link from "next/link";
import { ArrowUpRight, Cpu } from "lucide-react";

import type { Project } from "@/lib/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function ProjectCard({ project }: { project: Project }) {
  const formatted = new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(project.created_at));

  return (
    <Card className="group relative transition-all hover:-translate-y-0.5 hover:border-foreground/20 hover:shadow-md">
      <Link
        href={`/projects/${project.id}/dashboard`}
        className="absolute inset-0 z-10"
        aria-label={`Open project ${project.name}`}
      >
        <span className="sr-only">Open project</span>
      </Link>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-accent text-accent-foreground">
            <Cpu className="size-4" />
          </div>
          <ArrowUpRight className="size-4 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-foreground" />
        </div>
        <CardTitle className="mt-3 text-base font-semibold leading-snug">
          {project.name}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col justify-between gap-4">
        <CardDescription className="line-clamp-3 text-sm leading-relaxed">
          {project.description ?? "No description provided."}
        </CardDescription>
        <div className="flex items-center justify-between border-t border-border/60 pt-3 text-xs text-muted-foreground">
          <span className="font-tabular">{formatted}</span>
          <span>Project #{project.id}</span>
        </div>
      </CardContent>
    </Card>
  );
}
