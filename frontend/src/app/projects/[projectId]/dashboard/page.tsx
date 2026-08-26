import Link from "next/link";

import { EcuDetailForm } from "@/components/ecu-detail-form";
import { TestCasesDashboard } from "@/components/test-cases-dashboard";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";

type Params = { projectId: string };

export default async function ProjectDashboardPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { projectId } = await params;
  const projectIdNum = Number(projectId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            Project Dashboard
          </h1>
          <p className="text-muted-foreground mt-2">
            Manage ECU details and view security test cases
          </p>
        </div>
        <Link href="/">
          <Button variant="outline">
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back to Projects
          </Button>
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <EcuDetailForm projectId={projectIdNum} />
        </div>

        <div className="lg:col-span-3">
          <TestCasesDashboard projectId={projectIdNum} />
        </div>
      </div>
    </div>
  );
}
