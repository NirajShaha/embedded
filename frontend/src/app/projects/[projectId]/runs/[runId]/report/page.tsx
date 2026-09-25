"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  CheckCircle2,
  ChevronLeft,
  Clock3,
  Loader2,
  Timer,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ContentWrapper } from "@/components/content-wrapper";
import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { ReportCharts } from "@/components/execution/report-charts";
import {
  formatDurationMs,
  getRunReport,
  notifyRunFinished,
} from "@/lib/execution";

export default function RunReportPage() {
  const params = useParams<{ projectId: string; runId: string }>();
  const projectId = Number(params.projectId);
  const runId = Number(params.runId);
  const notifiedRef = React.useRef(false);

  const reportQuery = useQuery({
    queryKey: ["execution-report", runId],
    queryFn: () => getRunReport(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.run.status;
      return status === "running" || status === "paused" ? 5000 : false;
    },
    refetchOnWindowFocus: false,
    retry: 1,
  });

  const report = reportQuery.data;

  React.useEffect(() => {
    if (!report || notifiedRef.current) return;
    if (["completed", "failed", "cancelled"].includes(report.run.status)) {
      notifiedRef.current = true;
      notifyRunFinished(report.run, report.summary);
    }
  }, [report]);

  React.useEffect(() => {
    if (reportQuery.isError) {
      toast.error(
        reportQuery.error instanceof Error
          ? reportQuery.error.message
          : "Could not load the report",
      );
    }
  }, [reportQuery.isError, reportQuery.error]);

  return (
    <ContentWrapper>
      <PageHeader
        title={`Report · Run #${Number.isFinite(runId) ? runId : "…"}`}
        description="Execution results with frame-accurate charts built from the recorded stream."
        badge="Execution report"
        actions={
          <div className="flex items-center gap-2">
            <Button asChild variant="outline" size="sm">
              <Link href={`/projects/${projectId}/runs/${runId}`}>
                <ChevronLeft />
                Live run
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href={`/projects/${projectId}/dashboard`}>Test cases</Link>
            </Button>
          </div>
        }
      />
      <Separator />

      {reportQuery.isLoading ? (
        <div className="flex items-center justify-center gap-2 py-24 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading report…
        </div>
      ) : !report ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center text-sm">
          <p className="font-medium text-destructive">Could not load this report</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Cases passed"
              value={`${report.summary.passed_cases}/${report.summary.total_cases}`}
              subLabel={`${report.summary.failed_cases} failed · ${report.summary.by_status.skipped ?? 0} skipped`}
              icon={report.summary.failed_cases > 0 ? XCircle : CheckCircle2}
              iconBg={report.summary.failed_cases > 0 ? "bg-red-100 dark:bg-red-950" : "bg-emerald-100 dark:bg-emerald-950"}
              iconColor={report.summary.failed_cases > 0 ? "text-red-600 dark:text-red-200" : "text-emerald-600 dark:text-emerald-200"}
            />
            <StatCard
              label="Frame ACK rate"
              value={`${report.summary.ack_rate_pct}%`}
              subLabel={`${report.summary.packets_acked.toLocaleString()} / ${report.summary.packets_sent.toLocaleString()} frames`}
              icon={Activity}
              iconBg="bg-blue-100 dark:bg-blue-950"
              iconColor="text-blue-600 dark:text-blue-200"
            />
            <StatCard
              label="Total time"
              value={formatDurationMs(report.summary.total_duration_ms)}
              subLabel={report.run.status}
              icon={Timer}
              iconBg="bg-amber-100 dark:bg-amber-950"
              iconColor="text-amber-600 dark:text-amber-200"
            />
            <StatCard
              label="Mean RTT"
              value={report.summary.avg_rtt_ms !== null ? `${report.summary.avg_rtt_ms} ms` : "—"}
              subLabel="Across finished cases"
              icon={Clock3}
              iconBg="bg-violet-100 dark:bg-violet-950"
              iconColor="text-violet-600 dark:text-violet-200"
            />
          </div>

          <ReportCharts
            summary={report.summary}
            cases={report.cases}
            buckets={report.buckets}
            events={report.events}
          />
        </div>
      )}
    </ContentWrapper>
  );
}
