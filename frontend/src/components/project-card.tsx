"use client";

import Link from "next/link";
import { Layers } from "lucide-react";

import type { Project } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function ProjectCard({ project }: { project: Project }) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-row items-start justify-between space-y-0">
        <CardTitle className="text-lg">{project.name}</CardTitle>
        <Badge variant="secondary">
          <Layers className="mr-1 size-3" />
          Configure
        </Badge>
      </CardHeader>
      <CardContent className="flex-1">
        <CardDescription className="line-clamp-3">
          {project.description ?? "No description provided."}
        </CardDescription>
        <p className="mt-3 text-xs text-muted-foreground">
          Created {new Date(project.created_at).toLocaleDateString()}
        </p>
      </CardContent>
      <CardFooter>
        <Button asChild variant="default" className="w-full">
          <Link href={`/projects/${project.id}/page/1`}>Continue setup</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}