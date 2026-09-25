"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import {
  CheckCircle,
  ChevronDown,
  CircleAlert,
  Download,
  Eye,
  Play,
  Search,
  ShieldAlert,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  Wrench,
  X,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { toast } from "sonner";

import {
  downloadTestCasesPDF,
  getCategories,
  getTestTypes,
  listTestCases,
  type Category,
  type TestCase,
  type TestType,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/ui/data-table";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Pagination } from "@/components/pagination";
import { TestCaseDetailDialog } from "@/components/test-case-detail-dialog";

interface TestCasesDashboardProps {
  projectId: number;
}

type SeverityRank = 1 | 2 | 3 | 4;

interface SeverityMeta {
  label: string;
  color: string;
  ring: string;
  icon: LucideIcon;
}

const severityMeta: Record<SeverityRank, SeverityMeta> = {
  1: {
    label: "Low",
    color: "bg-[var(--severity-low)]/12 text-[var(--severity-low)]",
    ring: "ring-[var(--severity-low)]/30",
    icon: CheckCircle,
  },
  2: {
    label: "Medium",
    color: "bg-[var(--severity-medium)]/15 text-[var(--severity-medium)]",
    ring: "ring-[var(--severity-medium)]/30",
    icon: Zap,
  },
  3: {
    label: "High",
    color: "bg-[var(--severity-high)]/15 text-[var(--severity-high)]",
    ring: "ring-[var(--severity-high)]/30",
    icon: CircleAlert,
  },
  4: {
    label: "Critical",
    color: "bg-[var(--severity-critical)]/15 text-[var(--severity-critical)]",
    ring: "ring-[var(--severity-critical)]/40",
    icon: ShieldAlert,
  },
};

function severityFromRank(rank: number | undefined): SeverityMeta | null {
  if (!rank) {
    return null;
  }

  const safeRank = (rank >= 4 ? 4 : rank <= 1 ? 1 : rank) as SeverityRank;

  return severityMeta[safeRank];
}

interface MultiFilterDropdownProps<
  T extends {
    id: number;
    name: string;
  },
> {
  label: string;
  items: T[] | undefined;
  selected: number[];
  onToggle: (id: number) => void;
  onClear: () => void;
  icon: LucideIcon;
  allLabel: string;
}

function MultiFilterDropdown<
  T extends {
    id: number;
    name: string;
  },
>({
  label,
  items,
  selected,
  onToggle,
  onClear,
  icon: Icon,
  allLabel,
}: MultiFilterDropdownProps<T>) {
  const selectedItems =
    items?.filter((item) => selected.includes(item.id)) ?? [];

  const triggerLabel =
    selectedItems.length === 0
      ? allLabel
      : selectedItems.length === 1
        ? selectedItems[0].name
        : `${selectedItems.length} selected`;

  return (
    <div className="flex min-w-[12rem] flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              "w-full justify-between font-normal",
              selectedItems.length > 0 &&
                "border-primary/40 bg-primary/5 text-foreground",
            )}
          >
            <span className="flex min-w-0 items-center gap-2 truncate">
              <Icon className="size-3.5 shrink-0 text-muted-foreground" />

              <span className="truncate">{triggerLabel}</span>
            </span>

            <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="start" className="w-64">
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>{label}</span>

            {selectedItems.length > 0 && (
              <button
                type="button"
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  onClear();
                }}
                className="text-xs font-normal text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            )}
          </DropdownMenuLabel>

          <DropdownMenuSeparator />

          {items?.map((item) => {
            const isChecked = selected.includes(item.id);

            return (
              <DropdownMenuCheckboxItem
                key={item.id}
                checked={isChecked}
                onCheckedChange={() => onToggle(item.id)}
                onSelect={(event) => {
                  event.preventDefault();
                }}
                className="justify-between"
              >
                <span className="truncate">{item.name}</span>
              </DropdownMenuCheckboxItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

const PAGE_SIZE_DEFAULT = 10;

export function TestCasesDashboard({ projectId }: TestCasesDashboardProps) {
  const router = useRouter();
  const [selectedCategories, setSelectedCategories] = React.useState<number[]>(
    [],
  );

  const [selectedTestTypes, setSelectedTestTypes] = React.useState<number[]>(
    [],
  );

  const [selectedSeverities, setSelectedSeverities] = React.useState<number[]>(
    [],
  );

  const [search, setSearch] = React.useState("");

  const [page, setPage] = React.useState(1);

  const [pageSize, setPageSize] = React.useState(PAGE_SIZE_DEFAULT);
  const [activeTestCaseId, setActiveTestCaseId] = React.useState<number | null>(
    null,
  );

  const [isPdfLoading, setIsPdfLoading] = React.useState(false);

  const [pdfError, setPdfError] = React.useState<string | null>(null);

  const [isRunStarting, setIsRunStarting] = React.useState(false);

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ["categories"],
    queryFn: getCategories,
  });

  const { data: testTypes, isLoading: testTypesLoading } = useQuery({
    queryKey: ["test-types"],
    queryFn: getTestTypes,
  });

  const { data: testCases, isLoading: casesLoading } = useQuery({
    queryKey: [
      "test-cases",
      projectId,
      selectedCategories
        .slice()
        .sort((first, second) => first - second)
        .join(","),
      selectedTestTypes
        .slice()
        .sort((first, second) => first - second)
        .join(","),
    ],
    queryFn: () =>
      listTestCases(
        selectedCategories.length > 0 ? selectedCategories : undefined,
        selectedTestTypes.length > 0 ? selectedTestTypes : undefined,
        projectId,
      ),
  });

  // Derive the open test case from the query data so edits saved through the
  // dialog immediately flow back into the row and the detail view.
  const activeTestCase = React.useMemo(
    () =>
      (testCases ?? []).find((testCase) => testCase.id === activeTestCaseId) ??
      null,
    [testCases, activeTestCaseId],
  );

  const toggleCategory = React.useCallback((id: number) => {
    setSelectedCategories((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id],
    );

    setPage(1);
    setPdfError(null);
  }, []);

  const toggleTestType = React.useCallback((id: number) => {
    setSelectedTestTypes((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id],
    );

    setPage(1);
    setPdfError(null);
  }, []);

  const toggleSeverity = React.useCallback((id: number) => {
    setSelectedSeverities((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id],
    );

    setPage(1);
    setPdfError(null);
  }, []);

  const clearCategories = React.useCallback(() => {
    setSelectedCategories([]);
    setPage(1);
    setPdfError(null);
  }, []);

  const clearTestTypes = React.useCallback(() => {
    setSelectedTestTypes([]);
    setPage(1);
    setPdfError(null);
  }, []);

  const clearSeverities = React.useCallback(() => {
    setSelectedSeverities([]);
    setPage(1);
    setPdfError(null);
  }, []);

  const clearAllFilters = React.useCallback(() => {
    setSelectedCategories([]);
    setSelectedTestTypes([]);
    setSelectedSeverities([]);
    setSearch("");
    setPage(1);
    setPdfError(null);
  }, []);

  const severityOptions = React.useMemo(() => {
    const seen = new Map<
      number,
      {
        id: number;
        name: string;
        rank: number;
      }
    >();

    for (const testCase of testCases ?? []) {
      if (testCase.severity && !seen.has(testCase.severity.id)) {
        seen.set(testCase.severity.id, {
          id: testCase.severity.id,
          name: testCase.severity.name,
          rank: testCase.severity.severity_rank,
        });
      }
    }

    return Array.from(seen.values()).sort(
      (first, second) => first.rank - second.rank,
    );
  }, [testCases]);

  const filteredTestCases = React.useMemo(() => {
    let result = testCases ?? [];

    if (selectedSeverities.length > 0) {
      result = result.filter(
        (testCase) =>
          testCase.severity_id !== null &&
          selectedSeverities.includes(testCase.severity_id),
      );
    }

    const query = search.trim().toLowerCase();

    if (query) {
      result = result.filter((testCase) => {
        const haystack = [
          testCase.action_test_case,
          testCase.description,
          testCase.attack_path,
          testCase.test_steps,
          testCase.expected_output,
          testCase.category?.name,
          testCase.objective?.name,
          testCase.protocol?.name,
          testCase.attack_vector?.name,
          testCase.test_type?.name,
          testCase.severity?.name,
          testCase.threat?.threat_text,
          ...testCase.test_case_tools.map((item) => item.tool.tool_name),
          ...testCase.test_case_references.map(
            (item) => item.reference.ref_text,
          ),
        ]
          .filter(
            (value): value is string =>
              typeof value === "string" && value.length > 0,
          )
          .join(" ")
          .toLowerCase();

        return haystack.includes(query);
      });
    }

    return result;
  }, [testCases, selectedSeverities, search]);

  const handleDownloadPDF = React.useCallback(async () => {
    if (filteredTestCases.length === 0) {
      setPdfError("No test cases match the current filters.");

      return;
    }

    setPdfError(null);
    setIsPdfLoading(true);

    try {
      await downloadTestCasesPDF({
        projectId,
        testCaseIds: filteredTestCases.map((testCase) => testCase.id),
        categoryIds: selectedCategories,
        testTypeIds: selectedTestTypes,
      });
    } catch (error) {
      setPdfError(
        error instanceof Error ? error.message : "Failed to generate PDF",
      );
    } finally {
      setIsPdfLoading(false);
    }
  }, [projectId, filteredTestCases, selectedCategories, selectedTestTypes]);

  const handleRunTestCases = React.useCallback(async () => {
    if (filteredTestCases.length === 0) {
      setPdfError("No test cases match the current filters.");
      return;
    }
    setIsRunStarting(true);
    try {
      const { createExecutionRun } = await import("@/lib/execution");
      const created = await createExecutionRun({
        projectId,
        testCaseIds: filteredTestCases.map((testCase) => testCase.id),
        durationPerCaseS: 90,
      });
      toast.success("Run started", {
        description: `${created.run.total_cases} test cases queued for execution.`,
      });
      router.push(`/projects/${projectId}/runs/${created.run.id}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to start run");
    } finally {
      setIsRunStarting(false);
    }
  }, [projectId, filteredTestCases, router]);

  const totalItems = filteredTestCases.length;

  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  React.useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const safePage = Math.max(1, Math.min(page, totalPages));

  const pageStart = (safePage - 1) * pageSize;

  const visible = filteredTestCases.slice(pageStart, pageStart + pageSize);

  const isLoading = categoriesLoading || testTypesLoading || casesLoading;

  const hasFilters =
    selectedCategories.length > 0 ||
    selectedTestTypes.length > 0 ||
    selectedSeverities.length > 0 ||
    search.trim().length > 0;

  const categoryChips = (categories ?? [])
    .filter((category) => selectedCategories.includes(category.id))
    .map((category) => ({
      id: category.id,
      name: category.name,
      kind: "category" as const,
    }));

  const testTypeChips = (testTypes ?? [])
    .filter((testType) => selectedTestTypes.includes(testType.id))
    .map((testType) => ({
      id: testType.id,
      name: testType.name,
      kind: "testType" as const,
    }));

  const severityChips = severityOptions
    .filter((severity) => selectedSeverities.includes(severity.id))
    .map((severity) => ({
      id: severity.id,
      name: severity.name,
      kind: "severity" as const,
    }));

  const activeChips = [...categoryChips, ...testTypeChips, ...severityChips];

  const columns = React.useMemo<ColumnDef<TestCase>[]>(
    () => [
      {
        id: "testCase",
        header: "Test case",
        meta: {
          className: "w-[36%]",
        },
        cell: ({ row }) => {
          const testCase = row.original;

          return (
            <>
              <div className="line-clamp-3 break-words text-sm font-medium leading-snug text-foreground">
                {testCase.action_test_case}
              </div>

              <div className="mt-1 flex flex-wrap items-center gap-1.5">
                {testCase.objective?.name && (
                  <div className="line-clamp-1 break-words text-xs text-muted-foreground">
                    {testCase.objective.name}
                  </div>
                )}

                {testCase.is_overridden && (
                  <Badge variant="secondary" className="text-[10px]">
                    Edited
                  </Badge>
                )}
              </div>
            </>
          );
        },
      },
      {
        id: "category",
        header: "Category",
        meta: {
          className: "w-[14%]",
        },
        cell: ({ row }) => (
          <span className="block break-words text-sm text-muted-foreground">
            {row.original.category?.name ?? "—"}
          </span>
        ),
      },
      {
        id: "type",
        header: "Type",
        meta: {
          className: "w-[10%]",
        },
        cell: ({ row }) => (
          <span className="block break-words text-sm text-muted-foreground">
            {row.original.test_type?.name ?? "—"}
          </span>
        ),
      },
      {
        id: "severity",
        header: "Severity",
        meta: {
          className: "w-[12%]",
        },
        cell: ({ row }) => {
          const severity = severityFromRank(
            row.original.severity?.severity_rank,
          );

          const SeverityIcon = severity?.icon;

          return severity && SeverityIcon ? (
            <span
              className={cn(
                "inline-flex w-fit max-w-full items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
                severity.color,
                severity.ring,
              )}
            >
              <SeverityIcon className="size-3 shrink-0" />

              <span className="truncate">
                {row.original.severity?.name ?? severity.label}
              </span>
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          );
        },
      },
      {
        id: "actions",
        header: () => <span className="sr-only">View details</span>,
        meta: {
          className: "w-[8%] text-right",
        },
        cell: ({ row }) => {
          const testCase = row.original;

          return (
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={(event) => {
                event.stopPropagation();

                setActiveTestCaseId(testCase.id);
              }}
              aria-label={`View details for ${testCase.action_test_case}`}
            >
              <Eye className="size-3.5" />
            </Button>
          );
        },
      },
    ],
    [],
  );

  // TanStack Table returns functions that React Compiler
  // cannot safely memoize.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data: visible,
    columns,
    getCoreRowModel: getCoreRowModel(),
    autoResetPageIndex: false,
    getRowId: (row) => String(row.id),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold tracking-tight">
            Security test cases
          </h2>

          <p className="text-sm text-muted-foreground">
            Search and filter by category, test type, or severity to narrow the
            relevant coverage.
          </p>
        </div>

        <div className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex">
          <SlidersHorizontal className="size-3.5" />

          <span>
            {totalItems} matching{" "}
            {totalItems === 1 ? "test case" : "test cases"}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-border/60 bg-card/60 p-4">
        <div className="flex min-w-[16rem] flex-1 flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">
            Search
          </span>

          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />

            <Input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);

                setPage(1);
                setPdfError(null);
              }}
              placeholder="Search test cases..."
              className="pl-8"
            />
          </div>
        </div>

        <MultiFilterDropdown
          label="Category"
          items={categories as Category[] | undefined}
          selected={selectedCategories}
          onToggle={toggleCategory}
          onClear={clearCategories}
          icon={Target}
          allLabel="All categories"
        />

        <MultiFilterDropdown
          label="Test type"
          items={testTypes as TestType[] | undefined}
          selected={selectedTestTypes}
          onToggle={toggleTestType}
          onClear={clearTestTypes}
          icon={Wrench}
          allLabel="All test types"
        />

        <MultiFilterDropdown
          label="Severity"
          items={severityOptions}
          selected={selectedSeverities}
          onToggle={toggleSeverity}
          onClear={clearSeverities}
          icon={ShieldAlert}
          allLabel="All severities"
        />

        {hasFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="self-end"
          >
            Clear filters
          </Button>
        )}
      </div>

      {activeChips.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Active:</span>

          {activeChips.map((chip) => (
            <button
              key={`${chip.kind}-${chip.id}`}
              type="button"
              onClick={() => {
                if (chip.kind === "category") {
                  toggleCategory(chip.id);
                } else if (chip.kind === "testType") {
                  toggleTestType(chip.id);
                } else {
                  toggleSeverity(chip.id);
                }
              }}
              className="group inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/5 px-2.5 py-0.5 text-xs font-medium text-foreground transition-colors hover:bg-primary/10"
            >
              <span>{chip.name}</span>

              <X className="size-3 text-muted-foreground group-hover:text-foreground" />
            </button>
          ))}
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-border/60 bg-card">
        {isLoading ? (
          <div className="space-y-3 p-6">
            {Array.from({
              length: 5,
            }).map((_, index) => (
              <div key={index} className="space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-10 w-full" />
              </div>
            ))}
          </div>
        ) : filteredTestCases.length > 0 ? (
          <>
            <DataTable
              table={table}
              onRowClick={(testCase) => {
                setActiveTestCaseId(testCase.id);
              }}
            />

            <Pagination
              page={safePage}
              pageSize={pageSize}
              totalItems={totalItems}
              onPageChange={setPage}
              onPageSizeChange={(newPageSize) => {
                setPageSize(newPageSize);

                setPage(1);
              }}
            />

            <div className="flex flex-col gap-3 border-t border-border/60 px-6 py-4">
              {pdfError && (
                <div
                  role="alert"
                  className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
                >
                  <p className="font-medium">PDF Generation Error</p>

                  <p className="text-xs">{pdfError}</p>
                </div>
              )}

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-muted-foreground">
                  {filteredTestCases.length} matching{" "}
                  {filteredTestCases.length === 1 ? "test case" : "test cases"}
                </p>

                <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownloadPDF}
                  disabled={isPdfLoading || filteredTestCases.length === 0}
                  className="gap-2"
                >
                  <Download className="size-4" />

                  {isPdfLoading ? "Generating PDF..." : "Generate PDF Report"}
                </Button>

                <Button
                  size="sm"
                  onClick={handleRunTestCases}
                  disabled={isRunStarting || filteredTestCases.length === 0}
                  className="gap-2"
                >
                  <Play className="size-4" />

                  {isRunStarting ? "Starting run..." : "Run Test Cases"}
                </Button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
            <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <ShieldCheck className="size-5" />
            </div>

            <div className="space-y-1">
              <p className="text-sm font-semibold">No test cases match</p>

              <p className="mx-auto max-w-sm text-xs text-muted-foreground">
                {hasFilters
                  ? "Try removing some filters."
                  : "No security test cases are currently available."}
              </p>
            </div>

            {hasFilters && (
              <Button variant="outline" size="sm" onClick={clearAllFilters}>
                Clear filters
              </Button>
            )}
          </div>
        )}
      </div>

      <TestCaseDetailDialog
        testCase={activeTestCase}
        projectId={projectId}
        open={activeTestCase !== null}
        onOpenChange={(open) => {
          if (!open) {
            setActiveTestCaseId(null);
          }
        }}
      />
    </div>
  );
}
