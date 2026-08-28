"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  useReactTable,
  getCoreRowModel,
  type ColumnDef,
} from "@tanstack/react-table";
import {
  SlidersHorizontal,
  Target,
  Wrench,
  ShieldCheck,
  Eye,
  ChevronDown,
  CheckCircle,
  Zap,
  CircleAlert,
  ShieldAlert,
  X,
  Download,
  Search,
  type LucideIcon,
} from "lucide-react";

import {
  getCategories,
  getTestTypes,
  listTestCases,
  downloadTestCasesPDF,
  type Category,
  type TestCase,
  type TestType,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DataTable } from "@/components/ui/data-table";
import { Skeleton } from "@/components/ui/skeleton";
import { Pagination } from "@/components/pagination";
import { TestCaseDetailDialog } from "@/components/test-case-detail-dialog";

interface TestCasesDashboardProps {
  projectId: number;
}

type SeverityRank = 1 | 2 | 3 | 4;

const severityMeta: Record<
  SeverityRank,
  { label: string; color: string; ring: string; icon: LucideIcon }
> = {
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

function severityFromRank(rank: number | undefined) {
  if (!rank) return null;
  const safe = (rank >= 4 ? 4 : rank <= 1 ? 1 : rank) as SeverityRank;
  return severityMeta[safe];
}

interface MultiFilterDropdownProps<T extends { id: number; name: string }> {
  label: string;
  items: T[] | undefined;
  selected: number[];
  onToggle: (id: number) => void;
  onClear: () => void;
  icon: LucideIcon;
  allLabel: string;
}

function MultiFilterDropdown<T extends { id: number; name: string }>({
  label,
  items,
  selected,
  onToggle,
  onClear,
  icon: Icon,
  allLabel,
}: MultiFilterDropdownProps<T>) {
  const selectedItems = items?.filter((i) => selected.includes(i.id)) ?? [];
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
              "justify-between font-normal",
              selectedItems.length > 0 &&
                "border-primary/40 bg-primary/5 text-foreground",
            )}
          >
            <span className="flex items-center gap-2 truncate">
              <Icon className="size-3.5 text-muted-foreground" />
              {triggerLabel}
            </span>
            <ChevronDown className="size-4 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-64">
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>{label}</span>
            {selectedItems.length > 0 && (
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  onClear();
                }}
                className="text-xs font-normal text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            )}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          {items?.map((item) => (
            <DropdownMenuCheckboxItem
              key={item.id}
              checked={selected.includes(item.id)}
              onCheckedChange={() => onToggle(item.id)}
            >
              {item.name}
            </DropdownMenuCheckboxItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

const PAGE_SIZE_DEFAULT = 10;

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function TestCasesDashboard({
  projectId: _projectId,
}: TestCasesDashboardProps) {
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
  const [activeTestCase, setActiveTestCase] = React.useState<TestCase | null>(
    null,
  );
  const [isPdfLoading, setIsPdfLoading] = React.useState(false);
  const [pdfError, setPdfError] = React.useState<string | null>(null);

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
      [...selectedCategories].sort((a, b) => a - b),
      [...selectedTestTypes].sort((a, b) => a - b),
    ],
    queryFn: () =>
      listTestCases(
        selectedCategories.length > 0 ? selectedCategories : undefined,
        selectedTestTypes.length > 0 ? selectedTestTypes : undefined,
      ),
  });

  const toggleCategory = React.useCallback((id: number) => {
    setSelectedCategories((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
    setPage(1);
  }, []);

  const toggleTestType = React.useCallback((id: number) => {
    setSelectedTestTypes((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
    setPage(1);
  }, []);

  const toggleSeverity = React.useCallback((id: number) => {
    setSelectedSeverities((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
    setPage(1);
  }, []);

  const clearCategories = React.useCallback(() => {
    setSelectedCategories([]);
    setPage(1);
  }, []);

  const clearTestTypes = React.useCallback(() => {
    setSelectedTestTypes([]);
    setPage(1);
  }, []);

  const clearSeverities = React.useCallback(() => {
    setSelectedSeverities([]);
    setPage(1);
  }, []);

  const clearAllFilters = React.useCallback(() => {
    setSelectedCategories([]);
    setSelectedTestTypes([]);
    setSelectedSeverities([]);
    setSearch("");
    setPage(1);
  }, []);

  const handleDownloadPDF = React.useCallback(async () => {
    setPdfError(null);
    setIsPdfLoading(true);
    try {
      await downloadTestCasesPDF(
        selectedCategories.length > 0 ? selectedCategories : undefined,
        selectedTestTypes.length > 0 ? selectedTestTypes : undefined,
      );
    } catch (error) {
      setPdfError(
        error instanceof Error ? error.message : "Failed to generate PDF",
      );
    } finally {
      setIsPdfLoading(false);
    }
  }, [selectedCategories, selectedTestTypes]);

  const severityOptions = React.useMemo(() => {
    const seen = new Map<number, { id: number; name: string; rank: number }>();
    for (const tc of testCases ?? []) {
      if (tc.severity && !seen.has(tc.severity.id)) {
        seen.set(tc.severity.id, {
          id: tc.severity.id,
          name: tc.severity.name,
          rank: tc.severity.severity_rank,
        });
      }
    }
    return Array.from(seen.values()).sort((a, b) => a.rank - b.rank);
  }, [testCases]);

  const filteredTestCases = React.useMemo(() => {
    let result = testCases ?? [];

    if (selectedSeverities.length > 0) {
      result = result.filter(
        (tc) =>
          tc.severity_id !== null &&
          selectedSeverities.includes(tc.severity_id),
      );
    }

    const query = search.trim().toLowerCase();
    if (query) {
      result = result.filter((tc) => {
        const haystack = [
          tc.action_test_case,
          tc.description,
          tc.attack_path,
          tc.test_steps,
          tc.expected_output,
          tc.category?.name,
          tc.objective?.name,
          tc.protocol?.name,
          tc.attack_vector?.name,
          tc.test_type?.name,
          tc.severity?.name,
          tc.asset?.asset_name,
          tc.threat?.threat_text,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return haystack.includes(query);
      });
    }

    return result;
  }, [testCases, selectedSeverities, search]);

  const totalItems = filteredTestCases.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * pageSize;
  const visible = filteredTestCases.slice(pageStart, pageStart + pageSize);

  const isLoading = categoriesLoading || testTypesLoading || casesLoading;
  const hasFilters =
    selectedCategories.length > 0 ||
    selectedTestTypes.length > 0 ||
    selectedSeverities.length > 0 ||
    search.trim().length > 0;

  const categoryChips = (categories ?? [])
    .filter((c) => selectedCategories.includes(c.id))
    .map((c) => ({ id: c.id, name: c.name, kind: "category" as const }));
  const testTypeChips = (testTypes ?? [])
    .filter((t) => selectedTestTypes.includes(t.id))
    .map((t) => ({ id: t.id, name: t.name, kind: "testType" as const }));
  const severityChips = severityOptions
    .filter((s) => selectedSeverities.includes(s.id))
    .map((s) => ({ id: s.id, name: s.name, kind: "severity" as const }));
  const activeChips = [...categoryChips, ...testTypeChips, ...severityChips];

  const columns = React.useMemo<ColumnDef<TestCase>[]>(
    () => [
      {
        id: "testCase",
        header: "Test case",
        meta: { className: "w-[36%]" },
        cell: ({ row }) => {
          const testCase = row.original;
          return (
            <>
              <div className="line-clamp-3 text-sm font-medium leading-snug text-foreground break-words">
                {testCase.action_test_case}
              </div>
              {testCase.objective?.name && (
                <div className="mt-0.5 line-clamp-1 text-xs text-muted-foreground break-words">
                  {testCase.objective.name}
                </div>
              )}
            </>
          );
        },
      },
      {
        id: "category",
        header: "Category",
        meta: { className: "w-[14%]" },
        cell: ({ row }) => (
          <span className="block break-words text-sm text-muted-foreground">
            {row.original.category?.name ?? "—"}
          </span>
        ),
      },
      {
        id: "type",
        header: "Type",
        meta: { className: "w-[10%]" },
        cell: ({ row }) => (
          <span className="block break-words text-sm text-muted-foreground">
            {row.original.test_type?.name ?? "—"}
          </span>
        ),
      },
      {
        id: "severity",
        header: "Severity",
        meta: { className: "w-[12%]" },
        cell: ({ row }) => {
          const sev = severityFromRank(row.original.severity?.severity_rank);
          const SevIcon = sev?.icon;
          return sev && SevIcon ? (
            <span
              className={`inline-flex w-fit max-w-full items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${sev.color} ${sev.ring}`}
            >
              <SevIcon className="size-3 shrink-0" />
              <span className="truncate">{row.original.severity?.name}</span>
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          );
        },
      },
      {
        id: "asset",
        header: "Asset",
        meta: { className: "w-[16%]" },
        cell: ({ row }) => (
          <span className="block break-words text-sm text-foreground">
            {row.original.asset?.asset_name ?? "—"}
          </span>
        ),
      },
      {
        id: "actions",
        header: () => <span className="sr-only">View details</span>,
        meta: { className: "w-[8%] text-right" },
        cell: ({ row }) => {
          const testCase = row.original;
          return (
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={(e) => {
                e.stopPropagation();
                setActiveTestCase(testCase);
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

  const table = useReactTable({
    data: visible,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold tracking-tight">
            Security test cases
          </h2>
          <p className="text-sm text-muted-foreground">
            Search, and filter by category, test type, or severity to narrow the
            relevant coverage.
          </p>
        </div>
        <div className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex">
          <SlidersHorizontal className="size-3.5" />
          <span>{totalItems} matching</span>
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
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
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
                if (chip.kind === "category") toggleCategory(chip.id);
                else if (chip.kind === "testType") toggleTestType(chip.id);
                else toggleSeverity(chip.id);
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
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-10 w-full" />
              </div>
            ))}
          </div>
        ) : filteredTestCases.length > 0 ? (
          <>
            <DataTable table={table} onRowClick={setActiveTestCase} />

            <Pagination
              page={safePage}
              pageSize={pageSize}
              totalItems={totalItems}
              onPageChange={setPage}
              onPageSizeChange={(n) => {
                setPageSize(n);
                setPage(1);
              }}
            />

            {testCases && testCases.length > 0 && (
              <div className="flex flex-col gap-3 border-t border-border/60 px-6 py-4">
                {pdfError && (
                  <div className="rounded-md bg-red-50 p-3 text-sm text-red-900">
                    <p className="font-medium">PDF Generation Error</p>
                    <p className="text-xs">{pdfError}</p>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">
                    {testCases.length} test case
                    {testCases.length !== 1 ? "s" : ""} total
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownloadPDF}
                    disabled={isPdfLoading || testCases.length === 0}
                    className="gap-2"
                  >
                    <Download className="size-4" />
                    {isPdfLoading ? "Generating PDF..." : "Generate PDF Report"}
                  </Button>
                </div>
              </div>
            )}
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
                  : "Try adjusting your search."}
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
        open={activeTestCase !== null}
        onOpenChange={(open) => {
          if (!open) setActiveTestCase(null);
        }}
      />
    </div>
  );
}
