"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ShieldCheck,
  ListChecks,
  CircleCheck,
  ShieldAlert,
  Wrench,
  FileText,
  AlertTriangle,
  AlertCircle,
  Cpu,
  Target,
  Hash,
  Lock,
  Pencil,
  RotateCcw,
  Save,
} from "lucide-react";

import {
  listReferences,
  listTools,
  resetTestCaseOverride,
  updateTestCaseOverride,
  type TestCase,
  type TestCaseOverridePayload,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

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

const TEXT_FIELDS = [
  { key: "action_test_case", label: "Action / test case", long: true, required: true },
  { key: "description", label: "Description", long: true, required: false },
  { key: "test_steps", label: "Test steps", long: true, required: false },
  { key: "expected_output", label: "Expected output", long: true, required: false },
  { key: "attack_path", label: "Attack path", long: true, required: false },
  { key: "attack_feasibility", label: "Attack feasibility", long: false, required: false },
  { key: "source_scope_status", label: "Source scope status", long: false, required: false },
  { key: "cia_impact", label: "CIA impact", long: false, required: false },
  { key: "safety_impact", label: "Safety impact", long: false, required: false },
  { key: "automation_possible", label: "Automation possible", long: false, required: false },
] as const;

type TextFieldKey = (typeof TEXT_FIELDS)[number]["key"];

type FormState = Record<TextFieldKey, string>;

function toFormState(testCase: TestCase): FormState {
  return {
    action_test_case: testCase.action_test_case ?? "",
    description: testCase.description ?? "",
    test_steps: testCase.test_steps ?? "",
    expected_output: testCase.expected_output ?? "",
    attack_path: testCase.attack_path ?? "",
    attack_feasibility: testCase.attack_feasibility ?? "",
    source_scope_status: testCase.source_scope_status ?? "",
    cia_impact: testCase.cia_impact ?? "",
    safety_impact: testCase.safety_impact ?? "",
    automation_possible: testCase.automation_possible ?? "",
  };
}

function sameIds(a: number[], b: number[]) {
  if (a.length !== b.length) return false;
  const sortedA = [...a].sort((x, y) => x - y);
  const sortedB = [...b].sort((x, y) => x - y);
  return sortedA.every((value, index) => value === sortedB[index]);
}

interface TestCaseDetailDialogProps {
  testCase: TestCase | null;
  projectId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TestCaseDetailDialog({
  testCase,
  projectId,
  open,
  onOpenChange,
}: TestCaseDetailDialogProps) {
  const [isEditing, setIsEditing] = React.useState(false);

  const handleOpenChange = React.useCallback(
    (nextOpen: boolean) => {
      if (!nextOpen) {
        setIsEditing(false);
      }
      onOpenChange(nextOpen);
    },
    [onOpenChange],
  );

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="flex h-[min(85vh,820px)] max-h-[min(85vh,820px)] w-[min(1400px,calc(100vw-2rem))] max-w-none flex-col gap-0 overflow-hidden p-0 sm:max-w-none">
        {testCase ? (
          <TestCaseDetailBody
            key={testCase.id}
            testCase={testCase}
            projectId={projectId}
            isEditing={isEditing}
            onStartEditing={() => setIsEditing(true)}
            onCancelEditing={() => setIsEditing(false)}
          />
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

function TestCaseEditFields({
  form,
  onChange,
}: {
  form: FormState;
  onChange: (field: TextFieldKey, value: string) => void;
}) {
  return (
    <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {TEXT_FIELDS.map((field) => (
        <FormField
          key={field.key}
          id={field.key}
          label={field.label}
          required={field.required}
          fullWidth={field.long}
        >
          {field.long ? (
            <Textarea
              id={field.key}
              value={form[field.key]}
              onChange={(e) => onChange(field.key, e.target.value)}
              required={field.required}
              rows={5}
              className="field-sizing-content max-h-72 min-h-24 resize-y"
            />
          ) : (
            <Input
              id={field.key}
              value={form[field.key]}
              onChange={(e) => onChange(field.key, e.target.value)}
            />
          )}
        </FormField>
      ))}
    </section>
  );
}

function TestCaseDetailBody({
  testCase,
  projectId,
  isEditing,
  onStartEditing,
  onCancelEditing,
}: {
  testCase: TestCase;
  projectId: number;
  isEditing: boolean;
  onStartEditing: () => void;
  onCancelEditing: () => void;
}) {
  const queryClient = useQueryClient();

  const [error, setError] = React.useState<string | null>(null);
  const [isResetOpen, setIsResetOpen] = React.useState(false);
  const [form, setForm] = React.useState<FormState>(() => toFormState(testCase));
  const [baseline, setBaseline] = React.useState<FormState>(() =>
    toFormState(testCase),
  );
  const [selectedTools, setSelectedTools] = React.useState<number[]>(() =>
    testCase.test_case_tools.map((item) => item.tool.id),
  );
  const [baselineTools, setBaselineTools] = React.useState<number[]>(() =>
    testCase.test_case_tools.map((item) => item.tool.id),
  );
  const [selectedReferences, setSelectedReferences] = React.useState<number[]>(
    () => testCase.test_case_references.map((item) => item.reference.id),
  );
  const [baselineReferences, setBaselineReferences] = React.useState<number[]>(
    () => testCase.test_case_references.map((item) => item.reference.id),
  );

  const toolsQuery = useQuery({
    queryKey: ["test-case-tools"],
    queryFn: listTools,
    enabled: isEditing,
  });

  const referencesQuery = useQuery({
    queryKey: ["test-case-references"],
    queryFn: listReferences,
    enabled: isEditing,
  });

  const invalidate = React.useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["test-cases"] });
  }, [queryClient]);

  const saveMutation = useMutation({
    mutationFn: (payload: TestCaseOverridePayload) =>
      updateTestCaseOverride(projectId, testCase.id, payload),
    onSuccess: () => {
      setError(null);
      onCancelEditing();
      invalidate();
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Failed to save changes");
    },
  });

  const resetMutation = useMutation({
    mutationFn: () => resetTestCaseOverride(projectId, testCase.id),
    onSuccess: () => {
      setError(null);
      onCancelEditing();
      setIsResetOpen(false);
      invalidate();
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Failed to reset changes");
    },
  });

  const isBusy = saveMutation.isPending || resetMutation.isPending;

  // Seed the form from the current (already merged) test case whenever we enter
  // edit mode, so a save or reset is always diffed against fresh values.
  const startEditing = React.useCallback(() => {
    try {
      const next = toFormState(testCase);
      const tools = testCase.test_case_tools.map((item) => item.tool.id);
      const references = testCase.test_case_references.map(
        (item) => item.reference.id,
      );
      setForm(next);
      setBaseline(next);
      setSelectedTools(tools);
      setBaselineTools(tools);
      setSelectedReferences(references);
      setBaselineReferences(references);
      setError(null);
      onStartEditing();
    } catch (err) {
      setError(
        "Could not open the editor: " +
          (err instanceof Error ? err.message : "unknown error"),
      );
    }
  }, [testCase, onStartEditing]);

  const handleChange = React.useCallback(
    (field: TextFieldKey, value: string) => {
      setForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const toggleTool = React.useCallback((id: number) => {
    setSelectedTools((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, []);

  const toggleReference = React.useCallback((id: number) => {
    setSelectedReferences((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, []);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const payload: TestCaseOverridePayload = {};

    for (const field of TEXT_FIELDS) {
      if (form[field.key] !== baseline[field.key]) {
        payload[field.key] = form[field.key];
      }
    }

    if (!sameIds(selectedTools, baselineTools)) {
      payload.tools = selectedTools;
    }

    if (!sameIds(selectedReferences, baselineReferences)) {
      payload.references = selectedReferences;
    }

    if (Object.keys(payload).length === 0) {
      onCancelEditing();
      return;
    }

    saveMutation.mutate(payload);
  };

  const sev = severityFromRank(testCase.severity?.severity_rank);
  const SevIcon = sev?.icon;
  const objective = testCase.objective?.name;

  return (
    <>
      <DialogHeader
        data-editing={isEditing ? "true" : "false"}
        className="relative z-10 shrink-0 gap-3 border-b border-border/60 bg-card p-6"
      >
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
          {testCase.is_overridden && (
            <Badge variant="secondary">Edited for this project</Badge>
          )}
        </div>
        <DialogTitle className="text-xl leading-snug font-semibold tracking-tight">
          {isEditing ? form.action_test_case || "Edit test case" : testCase.action_test_case}
        </DialogTitle>
        {objective && (
          <DialogDescription className="text-sm text-muted-foreground">
            <span className="text-muted-foreground">Objective ·</span>{" "}
            <span className="text-foreground">{objective}</span>
          </DialogDescription>
        )}
      </DialogHeader>

      {isEditing ? (
        <form
          onSubmit={handleSubmit}
          className="flex min-h-0 flex-1 flex-col overflow-hidden bg-popover"
          id="test-case-edit-form"
        >
          <DialogTitle className="sr-only">Edit test case</DialogTitle>
          <DialogDescription className="sr-only">
            Edit this project&apos;s copy of the test case. The master catalogue
            is not modified.
          </DialogDescription>
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
            <div className="space-y-6 p-6">
              <TestCaseEditFields form={form} onChange={handleChange} />

              <Separator />

              <section>
                <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Classification
                </h3>
                <p className="mb-3 text-xs text-muted-foreground">
                  Category, objective, type, severity and the other classifications
                  come from the master catalogue and cannot be edited here.
                </p>
                <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
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
                </div>
              </section>

              <Separator />

              <section>
                <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <Wrench className="size-3.5" />
                  Tools used
                </h3>
                <p className="mb-2 text-xs text-muted-foreground">
                  Selecting tools replaces the master list for this project only.
                </p>
                {toolsQuery.isLoading ? (
                  <Skeleton className="h-10 w-full" />
                ) : (
                  <ToggleList
                    options={(toolsQuery.data ?? []).map((tool) => ({
                      id: tool.id,
                      label: tool.tool_name,
                    }))}
                    selected={selectedTools}
                    onToggle={toggleTool}
                    emptyLabel="No tools available"
                  />
                )}
              </section>

              <section>
                <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <FileText className="size-3.5" />
                  References
                </h3>
                <p className="mb-2 text-xs text-muted-foreground">
                  Selecting references replaces the master list for this project only.
                </p>
                {referencesQuery.isLoading ? (
                  <Skeleton className="h-10 w-full" />
                ) : (
                  <ToggleList
                    options={(referencesQuery.data ?? []).map((reference) => ({
                      id: reference.id,
                      label: reference.ref_text,
                    }))}
                    selected={selectedReferences}
                    onToggle={toggleReference}
                    emptyLabel="No references available"
                  />
                )}
              </section>
            </div>
          </div>

          <div className="relative z-10 shrink-0 space-y-3 border-t border-border/60 bg-card/50 p-6">
            {error && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <p>{error}</p>
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={onCancelEditing}
                disabled={isBusy}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isBusy}>
                <Save className="size-4" />
                {saveMutation.isPending ? "Saving…" : "Save changes"}
              </Button>
            </DialogFooter>
          </div>
        </form>
      ) : (
        <>
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

          <div className="relative z-10 flex shrink-0 flex-col gap-3 border-t border-border/60 bg-card/50 px-6 py-3">
            {error && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <p>{error}</p>
              </div>
            )}

            <div className="flex items-center justify-between gap-3">
              <span className="text-xs text-muted-foreground font-tabular">
                Test case #{testCase.id}
              </span>
              <div className="flex items-center gap-2">
                {testCase.is_overridden && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsResetOpen(true)}
                    disabled={isBusy}
                    className="gap-2"
                  >
                    <RotateCcw className="size-4" />
                    Reset to original
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={startEditing}
                  disabled={isBusy}
                  className="gap-2"
                >
                  <Pencil className="size-4" />
                  Edit
                </Button>
                <DialogClose asChild>
                  <Button variant="outline" size="sm">
                    Close
                  </Button>
                </DialogClose>
              </div>
            </div>
          </div>
        </>
      )}

      <AlertDialog open={isResetOpen} onOpenChange={setIsResetOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reset to original?</AlertDialogTitle>
            <AlertDialogDescription>
              This discards the edits made for this project and restores the original
              master test case. Other projects are not affected.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={resetMutation.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(event) => {
                event.preventDefault();
                resetMutation.mutate();
              }}
              disabled={resetMutation.isPending}
            >
              {resetMutation.isPending ? "Resetting…" : "Reset"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

function ToggleList({
  options,
  selected,
  onToggle,
  emptyLabel,
}: {
  options: Array<{ id: number; label: string }>;
  selected: number[];
  onToggle: (id: number) => void;
  emptyLabel: string;
}) {
  if (options.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyLabel}</p>;
  }

  return (
    <div className="max-h-56 space-y-1 overflow-y-auto rounded-md border border-border/60 p-2">
      {options.map((option) => {
        const isSelected = selected.includes(option.id);
        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onToggle(option.id)}
            aria-pressed={isSelected}
            className={
              isSelected
                ? "block w-full rounded border border-primary/40 bg-primary/10 px-2.5 py-1.5 text-left text-sm text-foreground"
                : "block w-full rounded border border-transparent px-2.5 py-1.5 text-left text-sm text-muted-foreground hover:bg-muted"
            }
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

function FormField({
  id,
  label,
  required,
  fullWidth,
  children,
}: {
  id: string;
  label: string;
  required?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={`space-y-1.5 ${fullWidth ? "lg:col-span-2" : ""}`}>
      <Label htmlFor={id} className="text-sm">
        {label}
        {required && <span className="ml-0.5 text-destructive">*</span>}
      </Label>
      {children}
    </div>
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
