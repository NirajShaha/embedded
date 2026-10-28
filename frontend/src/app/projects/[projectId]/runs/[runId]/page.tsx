"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getExecutionRun } from "@/lib/execution";
import { ScriptRunDashboard } from "@/components/execution/script-run-dashboard";

export default function RunPage() {
  const params = useParams<{ projectId: string; runId: string }>();
  const projectId = Number(params.projectId);
  const runId = Number(params.runId);

  const runQuery = useQuery({
    queryKey: ["execution-run", runId],
    queryFn: () => getExecutionRun(runId),
    refetchOnWindowFocus: false,
    retry: 1,
  });

  return (
    <div className="flex flex-col gap-4 lg:h-[calc(100dvh-7.5rem)]">
      {/* Compact header so the dashboard below gets the screen */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <h1 className="text-xl font-semibold tracking-tight">
            Run #{Number.isFinite(runId) ? runId : "…"}
          </h1>
          <Badge variant="secondary" className="gap-1.5">
            <span className="inline-flex size-1.5 rounded-full bg-[var(--signal)]" />
            Live execution
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline" size="sm">
            <Link href={`/projects/${projectId}/dashboard`}>
              <ChevronLeft />
              Test cases
            </Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link href={`/projects/${projectId}/runs/${runId}/report`}>
              Report
              <ChevronRight />
            </Link>
          </Button>
        </div>
      </div>

      {runQuery.isLoading ? (
        <div className="flex flex-1 items-center justify-center gap-2 py-24 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading run snapshot…
        </div>
      ) : runQuery.isError || !runQuery.data ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center text-sm">
          <p className="font-medium text-destructive">Could not load this run</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {runQuery.error instanceof Error ? runQuery.error.message : "Unknown error"}
          </p>
          <Button asChild variant="outline" size="sm" className="mt-4">
            <Link href={`/projects/${projectId}/dashboard`}>Back to test cases</Link>
          </Button>
        </div>
      ) : (
        <ScriptRunDashboard
          className="lg:min-h-0 lg:flex-1"
          projectId={projectId}
          runId={runId}
          initialRun={runQuery.data.run}
          initialCases={runQuery.data.cases}
        />
      )}
    </div>
  );
}
