"use client";

import * as React from "react";
import {
  ShieldCheck,
  ListChecks,
  CircleCheck,
  ShieldAlert,
  Wrench,
  FileText,
  AlertTriangle,
  Cpu,
  Target,
  Hash,
  Lock,
} from "lucide-react";

import type { TestCase } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

type SeverityRank = 1 | 2 | 3 | 4;

const severityMeta: Record<
  SeverityRank,
  { label: string; color: string; ring: string; icon: React.ElementType }
> = {
  1: {
    label: "Low",
    color: "bg-[var(--severity-low)]/12 text-[var(--severity-low)]",
    ring: "ring-[var(--severity-low)]/30",
    icon: CircleCheck,
  },
  2: {
    label: "Medium",
    color: "bg-[var(--severity-medium)]/15 text-[var(--severity-medium)]",
    ring: "ring-[var(--severity-medium)]/30",
    icon: AlertTriangle,
  },
  3: {
    label: "High",
    color: "bg-[var(--severity-high)]/15 text-[var(--severity-high)]",
    ring: "ring-[var(--severity-high)]/30",
    icon: AlertTriangle,
  },
  4: {
    label: "Critical",
    color: "bg-[var(--severity-critical)]/15 text-[var(--severity-critical)]",
    ring: "ring-[var(--severity-critical)]/40",
    icon: ShieldAlert,
  },
};

function severityFromRank(rank: number | undefined) {
  if (!rank) return null;
  const safe = (rank >= 4 ? 4 : rank <= 1 ? 1 : rank) as SeverityRank;
  return severityMeta[safe];
}

interface TestCaseDetailDialogProps {
  testCase: TestCase | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TestCaseDetailDialog({
  testCase,
  open,
  onOpenChange,
}: TestCaseDetailDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[min(85vh,820px)] w-[min(1400px,calc(100vw-2rem))] max-w-none flex-col gap-0 overflow-hidden p-0 sm:max-w-none">
        {testCase ? (
          <TestCaseDetailBody testCase={testCase} />
        ) : (
          <DialogHeader className="p-6">
            <DialogTitle>Test case</DialogTitle>
            <DialogDescription>No test case selected.</DialogDescription>
          </DialogHeader>
        )}
      </DialogContent>
    </Dialog>
  );
}

function TestCaseDetailBody({ testCase }: { testCase: TestCase }) {
  const sev = severityFromRank(testCase.severity?.severity_rank);
  const SevIcon = sev?.icon;
  const objective = testCase.objective?.name;

  return (
    <>
      <DialogHeader className="shrink-0 gap-3 border-b border-border/60 bg-card/50 p-6">
        <div className="flex flex-wrap items-center gap-2">
          {sev && SevIcon ? (
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${sev.color} ${sev.ring}`}
            >
              <SevIcon className="size-3" />
              {testCase.severity?.name}
            </span>
          ) : null}
          {testCase.category && (
            <Badge variant="secondary">{testCase.category.name}</Badge>
          )}
          {testCase.test_type && (
            <Badge variant="outline">{testCase.test_type.name}</Badge>
          )}
        </div>
        <DialogTitle className="text-xl leading-snug font-semibold tracking-tight">
          {testCase.action_test_case}
        </DialogTitle>
        {objective && (
          <DialogDescription className="text-sm text-muted-foreground">
            <span className="text-muted-foreground">Objective ·</span>{" "}
            <span className="text-foreground">{objective}</span>
          </DialogDescription>
        )}
      </DialogHeader>

      <ScrollArea className="min-h-0 flex-1">
        <div className="grid gap-6 p-6 md:grid-cols-[1.2fr_1fr]">
          {/* Left column: narrative */}
          <div className="space-y-4">
            <DetailSection
              title="Description"
              icon={FileText}
              body={testCase.description}
            />
            <DetailSection
              title="Test steps"
              icon={ListChecks}
              body={testCase.test_steps}
            />
            <DetailSection
              title="Expected output"
              icon={CircleCheck}
              body={testCase.expected_output}
              tone="success"
            />
            {(testCase.attack_path || testCase.attack_feasibility) && (
              <DetailSection
                title="Attack information"
                icon={ShieldAlert}
                tone="danger"
              >
                {testCase.attack_path && (
                  <SubItem label="Attack path" body={testCase.attack_path} />
                )}
                {testCase.attack_feasibility && (
                  <SubItem
                    label="Attack feasibility"
                    body={testCase.attack_feasibility}
                  />
                )}
              </DetailSection>
            )}
          </div>

          {/* Right column: structured facts */}
          <div className="space-y-5">
            <section className="grid grid-cols-2 gap-3">
              <SummaryItem
                icon={Cpu}
                label="Asset"
                value={testCase.asset?.asset_name}
              />
              <SummaryItem
                icon={Target}
                label="Attack vector"
                value={testCase.attack_vector?.name}
              />
              <SummaryItem
                icon={Hash}
                label="Threat"
                value={testCase.threat?.threat_text}
              />
              <SummaryItem
                icon={Lock}
                label="Protocol"
                value={testCase.protocol?.name}
              />
            </section>

            <Separator />

            <section>
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Impact analysis
              </h3>
              <div className="grid grid-cols-1 gap-3">
                <SummaryItem
                  icon={ShieldAlert}
                  label="CIA impact"
                  value={testCase.cia_impact}
                />
                <SummaryItem
                  icon={ShieldCheck}
                  label="Safety impact"
                  value={testCase.safety_impact}
                />
                <SummaryItem
                  icon={Wrench}
                  label="Automation"
                  value={testCase.automation_possible}
                />
              </div>
            </section>

            {testCase.test_case_tools.length > 0 && (
              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Tools used
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {testCase.test_case_tools.map((tool, idx) => (
                    <Badge key={idx} variant="secondary">
                      {tool.tool.tool_name}
                    </Badge>
                  ))}
                </div>
              </section>
            )}

            {testCase.test_case_references.length > 0 && (
              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  References
                </h3>
                <ul className="space-y-2">
                  {testCase.test_case_references.map((ref, idx) => (
                    <li
                      key={idx}
                      className="border-l-2 border-border pl-3 text-sm leading-relaxed text-foreground"
                    >
                      {ref.reference.ref_text}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        </div>
      </ScrollArea>

      <div className="flex shrink-0 items-center justify-between gap-3 border-t border-border/60 bg-card/50 px-6 py-3">
        <span className="text-xs text-muted-foreground font-tabular">
          Test case #{testCase.id}
        </span>
        <DialogClose asChild>
          <Button variant="outline" size="sm">
            Close
          </Button>
        </DialogClose>
      </div>
    </>
  );
}

function SummaryItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value?: string | null;
}) {
  const hasValue = !!value && value.trim().length > 0;
  return (
    <div className="rounded-md border border-border/60 bg-card p-4">
      <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Icon className="size-3.5" />
        {label}
      </div>
      <div
        className={
          hasValue
            ? "mt-1 break-words text-sm text-foreground"
            : "mt-1 text-sm text-muted-foreground"
        }
      >
        {hasValue ? value : "Not specified"}
      </div>
    </div>
  );
}

function DetailSection({
  title,
  icon: Icon,
  body,
  tone,
  children,
}: {
  title: string;
  icon: React.ElementType;
  body?: string | null;
  tone?: "success" | "danger";
  children?: React.ReactNode;
}) {
  const accent =
    tone === "success"
      ? "border-l-[var(--severity-low)]"
      : tone === "danger"
        ? "border-l-[var(--severity-critical)]"
        : "border-l-border";
  const hasContent = !!body || !!children;
  if (!hasContent) return null;
  return (
    <section
      className={`rounded-md border border-border/60 border-l-2 ${accent} bg-card p-4`}
    >
      <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        <Icon className="size-3.5" />
        {title}
      </h3>
      {body ? (
        <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-foreground">
          {body}
        </p>
      ) : null}
      {children}
    </section>
  );
}

function SubItem({ label, body }: { label: string; body: string }) {
  return (
    <div className="mt-2">
      <p className="mb-1 text-xs font-medium text-muted-foreground">
        {label}
      </p>
      <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-foreground">
        {body}
      </p>
    </div>
  );
}
