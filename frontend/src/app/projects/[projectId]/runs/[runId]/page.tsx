"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ContentWrapper } from "@/components/content-wrapper";
import { PageHeader } from "@/components/page-header";
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
    <ContentWrapper>
      <PageHeader
        title={`Run #${Number.isFinite(runId) ? runId : "…"}`}
        description="Configure the Vector bus, start the trace, then run each test case. Live output and script status stream on the right."
        badge="Live execution"
        actions={
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
        }
      />
      <Separator />
      {runQuery.isLoading ? (
        <div className="flex items-center justify-center gap-2 py-24 text-sm text-muted-foreground">
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
          projectId={projectId}
          runId={runId}
          initialRun={runQuery.data.run}
          initialCases={runQuery.data.cases}
        />
      )}
    </ContentWrapper>
  );
}
