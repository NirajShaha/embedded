"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
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
  type LucideIcon,
} from "lucide-react";

import {
  getCategories,
  getTestTypes,
  listTestCases,
  type Category,
  type TestCase,
  type TestType,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
export function TestCasesDashboard({ projectId: _projectId }: TestCasesDashboardProps) {
  const [selectedCategories, setSelectedCategories] = React.useState<number[]>(
    [],
  );
  const [selectedTestTypes, setSelectedTestTypes] = React.useState<number[]>(
    [],
  );
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(PAGE_SIZE_DEFAULT);
  const [activeTestCase, setActiveTestCase] = React.useState<TestCase | null>(null);

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

  const clearCategories = React.useCallback(() => {
    setSelectedCategories([]);
    setPage(1);
  }, []);

  const clearTestTypes = React.useCallback(() => {
    setSelectedTestTypes([]);
    setPage(1);
  }, []);

  const clearAllFilters = React.useCallback(() => {
    setSelectedCategories([]);
    setSelectedTestTypes([]);
    setPage(1);
  }, []);

  const totalItems = testCases?.length ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * pageSize;
  const visible = (testCases ?? []).slice(pageStart, pageStart + pageSize);

  const isLoading = categoriesLoading || testTypesLoading || casesLoading;
  const hasFilters =
    selectedCategories.length > 0 || selectedTestTypes.length > 0;

  const categoryChips = (categories ?? [])
    .filter((c) => selectedCategories.includes(c.id))
    .map((c) => ({ id: c.id, name: c.name, kind: "category" as const }));
  const testTypeChips = (testTypes ?? [])
    .filter((t) => selectedTestTypes.includes(t.id))
    .map((t) => ({ id: t.id, name: t.name, kind: "testType" as const }));
  const activeChips = [...categoryChips, ...testTypeChips];

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold tracking-tight">Security test cases</h2>
          <p className="text-sm text-muted-foreground">
            Filter by category and test type to narrow the relevant coverage.
          </p>
        </div>
        <div className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex">
          <SlidersHorizontal className="size-3.5" />
          <span>{totalItems} matching</span>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-border/60 bg-card/60 p-4">
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
              onClick={() =>
                chip.kind === "category"
                  ? toggleCategory(chip.id)
                  : toggleTestType(chip.id)
              }
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
        ) : testCases && testCases.length > 0 ? (
          <>
            <Table className="table-fixed">
              <colgroup>
                <col className="w-[40%]" />
                <col className="w-[14%]" />
                <col className="w-[10%]" />
                <col className="w-[12%]" />
                <col className="w-[16%]" />
                <col className="w-[8%]" />
              </colgroup>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="font-semibold">Test case</TableHead>
                  <TableHead className="font-semibold">Category</TableHead>
                  <TableHead className="font-semibold">Type</TableHead>
                  <TableHead className="font-semibold">Severity</TableHead>
                  <TableHead className="font-semibold">Asset</TableHead>
                  <TableHead className="text-right">
                    <span className="sr-only">View details</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visible.map((testCase) => {
                  const sev = severityFromRank(testCase.severity?.severity_rank);
                  const SevIcon = sev?.icon;
                  return (
                    <TableRow
                      key={testCase.id}
                      className="cursor-pointer"
                      onClick={() => setActiveTestCase(testCase)}
                    >
                      <TableCell className="whitespace-normal">
                        <div className="line-clamp-3 text-sm font-medium leading-snug text-foreground break-words">
                          {testCase.action_test_case}
                        </div>
                        {testCase.objective?.name && (
                          <div className="mt-0.5 line-clamp-1 text-xs text-muted-foreground break-words">
                            {testCase.objective.name}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="whitespace-normal">
                        <span className="block break-words text-sm text-muted-foreground">
                          {testCase.category?.name ?? "—"}
                        </span>
                      </TableCell>
                      <TableCell className="whitespace-normal">
                        <span className="block break-words text-sm text-muted-foreground">
                          {testCase.test_type?.name ?? "—"}
                        </span>
                      </TableCell>
                      <TableCell className="whitespace-normal">
                        {sev && SevIcon ? (
                          <span
                            className={`inline-flex w-fit max-w-full items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${sev.color} ${sev.ring}`}
                          >
                            <SevIcon className="size-3 shrink-0" />
                            <span className="truncate">
                              {testCase.severity?.name}
                            </span>
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell className="whitespace-normal">
                        <span className="block break-words text-sm text-foreground">
                          {testCase.asset?.asset_name ?? "—"}
                        </span>
                      </TableCell>
                      <TableCell className="text-right whitespace-normal">
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
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>

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
