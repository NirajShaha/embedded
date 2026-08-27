import Link from "next/link";
import { ChevronLeft } from "lucide-react";

import { EcuDetailForm } from "@/components/ecu-detail-form";
import { TestCasesDashboard } from "@/components/test-cases-dashboard";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

type Params = { projectId: string };

export default async function ProjectDashboardPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { projectId } = await params;
  const projectIdNum = Number(projectId);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Project
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Dashboard
          </h1>
          <p className="max-w-xl text-sm text-muted-foreground">
            Manage ECU hardware details and review the security test cases that
            apply to this configuration.
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link href="/">
            <ChevronLeft />
            All projects
          </Link>
        </Button>
      </div>

      <Separator />

      <div className="flex flex-col gap-8">
        <EcuDetailForm projectId={projectIdNum} />
        <TestCasesDashboard projectId={projectIdNum} />
      </div>
    </div>
  );
}
