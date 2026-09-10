"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Edit2,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";

import {
  createAdminTestCase,
  deleteAdminTestCase,
  listAdminTestCases,
  updateAdminTestCase,
  type TestCase,
  type TestCaseWritePayload,
} from "@/lib/api";

import { TestCaseForm } from "@/components/admin/test-case-form";
import { ProtectedRoute } from "@/components/protected-route";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";


const PAGE_SIZE = 10;


export default function AdminTestCasesPage() {
  const queryClient = useQueryClient();

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingTestCase, setEditingTestCase] = useState<TestCase | null>(null);
  const [deletingTestCaseId, setDeletingTestCaseId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const {
    data: testCases = [],
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["admin", "test-cases"],
    queryFn: listAdminTestCases,
  });

  // Filter test cases by search query
  const filteredTestCases = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return testCases;
    return testCases.filter(
      (tc) =>
        tc.action_test_case.toLowerCase().includes(q) ||
        tc.category?.name.toLowerCase().includes(q) ||
        tc.objective?.name.toLowerCase().includes(q) ||
        tc.severity?.name.toLowerCase().includes(q),
    );
  }, [testCases, searchQuery]);

  // Pagination derived values
  const totalPages = Math.max(1, Math.ceil(filteredTestCases.length / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const pageStart = (safePage - 1) * PAGE_SIZE;
  const pageEnd = pageStart + PAGE_SIZE;
  const visibleTestCases = filteredTestCases.slice(pageStart, pageEnd);

  // Reset to page 1 when search changes
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
  };

  const createMutation = useMutation({
    mutationFn: createAdminTestCase,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin", "test-cases"] }),
        queryClient.invalidateQueries({ queryKey: ["test-cases"] }),
        queryClient.invalidateQueries({ queryKey: ["admin", "stats"] }),
      ]);
      setIsCreateDialogOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: TestCaseWritePayload }) =>
      updateAdminTestCase(id, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin", "test-cases"] }),
        queryClient.invalidateQueries({ queryKey: ["test-cases"] }),
        queryClient.invalidateQueries({ queryKey: ["admin", "stats"] }),
      ]);
      setEditingTestCase(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAdminTestCase,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin", "test-cases"] }),
        queryClient.invalidateQueries({ queryKey: ["test-cases"] }),
        queryClient.invalidateQueries({ queryKey: ["admin", "stats"] }),
      ]);
      setDeletingTestCaseId(null);
    },
  });

  const activeMutationError = createMutation.error ?? updateMutation.error;
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  const closeEditor = () => {
    if (isSubmitting) return;
    setIsCreateDialogOpen(false);
    setEditingTestCase(null);
    createMutation.reset();
    updateMutation.reset();
  };

  const handleSubmit = async (payload: TestCaseWritePayload) => {
    if (editingTestCase) {
      await updateMutation.mutateAsync({ id: editingTestCase.id, payload });
      return;
    }
    await createMutation.mutateAsync(payload);
  };

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <div className="space-y-6 p-8">
        {/* Page header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="icon-sm" asChild>
                <Link href="/admin">
                  <ChevronLeft />
                  <span className="sr-only">Back to admin dashboard</span>
                </Link>
              </Button>
              <h1 className="text-3xl font-bold tracking-tight">
                Test Case Management
              </h1>
              <Badge variant="secondary">Admin Only</Badge>
            </div>
            <p className="text-muted-foreground">
              Create, edit, and delete security assessment test cases.
            </p>
          </div>

          <Button
            onClick={() => {
              createMutation.reset();
              setIsCreateDialogOpen(true);
            }}
            size="lg"
          >
            <Plus />
            New Test Case
          </Button>
        </div>

        {/* Test cases table card */}
        <Card>
          <CardHeader className="pb-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>All Active Test Cases</CardTitle>
                <CardDescription className="mt-1">
                  {searchQuery.trim()
                    ? `${filteredTestCases.length} result${filteredTestCases.length !== 1 ? "s" : ""} for "${searchQuery.trim()}" — ${testCases.length} total`
                    : `${testCases.length} active test case${testCases.length !== 1 ? "s" : ""}`}
                </CardDescription>
              </div>

              {/* Search bar */}
              <div className="relative w-full sm:w-72">
                <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
                <Input
                  placeholder="Search test cases..."
                  value={searchQuery}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  className="pl-8 pr-8"
                />
                {searchQuery && (
                  <button
                    onClick={() => handleSearchChange("")}
                    className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                    aria-label="Clear search"
                  >
                    <X className="size-4" />
                  </button>
                )}
              </div>
            </div>
          </CardHeader>

          <CardContent className="p-0">
            {isLoading ? (
              <div className="py-16 text-center text-muted-foreground">
                Loading test cases...
              </div>
            ) : isError ? (
              <div className="m-6 rounded-md border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
                {error instanceof Error ? error.message : "Could not load test cases."}
              </div>
            ) : testCases.length === 0 ? (
              <div className="py-16 text-center">
                <p className="text-muted-foreground">No active test cases found.</p>
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(true)}
                  className="mt-4"
                >
                  Create First Test Case
                </Button>
              </div>
            ) : filteredTestCases.length === 0 ? (
              <div className="py-16 text-center">
                <p className="text-muted-foreground">
                  No test cases match &quot;{searchQuery}&quot;.
                </p>
                <Button
                  variant="ghost"
                  onClick={() => handleSearchChange("")}
                  className="mt-2 text-sm"
                >
                  Clear search
                </Button>
              </div>
            ) : (
              <>
                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 z-10 border-b bg-muted/60 backdrop-blur-sm">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          #
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          Action / Test Case
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          Category
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          Objective
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          Severity
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          Created
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          Actions
                        </th>
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-border">
                      {visibleTestCases.map((testCase, index) => (
                        <tr
                          key={testCase.id}
                          className="group transition-colors hover:bg-muted/40"
                        >
                          {/* Row number */}
                          <td className="px-4 py-3 text-xs tabular-nums text-muted-foreground">
                            {pageStart + index + 1}
                          </td>

                          {/* Action/Test Case */}
                          <td className="max-w-sm px-4 py-3">
                            <p className="line-clamp-2 font-medium leading-snug">
                              {testCase.action_test_case}
                            </p>
                          </td>

                          {/* Category */}
                          <td className="whitespace-nowrap px-4 py-3">
                            {testCase.category ? (
                              <Badge variant="outline" className="font-normal">
                                {testCase.category.name}
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </td>

                          {/* Objective */}
                          <td className="max-w-xs px-4 py-3">
                            <span className="line-clamp-2 text-muted-foreground">
                              {testCase.objective?.name ?? "—"}
                            </span>
                          </td>

                          {/* Severity */}
                          <td className="whitespace-nowrap px-4 py-3">
                            {testCase.severity ? (
                              <Badge
                                variant={
                                  testCase.severity.severity_rank >= 4
                                    ? "destructive"
                                    : "secondary"
                                }
                              >
                                {testCase.severity.name}
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </td>

                          {/* Created date */}
                          <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                            {new Date(testCase.created_at).toLocaleDateString()}
                          </td>

                          {/* Actions */}
                          <td className="px-4 py-3 text-right">
                            <div className="flex justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => {
                                  updateMutation.reset();
                                  setEditingTestCase(testCase);
                                }}
                                aria-label="Edit test case"
                                title="Edit"
                              >
                                <Edit2 className="size-3.5" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                className="text-destructive hover:text-destructive"
                                onClick={() => setDeletingTestCaseId(testCase.id)}
                                aria-label="Delete test case"
                                title="Delete"
                              >
                                <Trash2 className="size-3.5" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination controls */}
                <div className="flex items-center justify-between border-t px-4 py-3">
                  <p className="text-sm text-muted-foreground">
                    Showing{" "}
                    <span className="font-medium text-foreground">
                      {pageStart + 1}–{Math.min(pageEnd, filteredTestCases.length)}
                    </span>{" "}
                    of{" "}
                    <span className="font-medium text-foreground">
                      {filteredTestCases.length}
                    </span>
                  </p>

                  <div className="flex items-center gap-1">
                    <Button
                      variant="outline"
                      size="icon-sm"
                      onClick={() => setCurrentPage(1)}
                      disabled={safePage === 1}
                      aria-label="First page"
                    >
                      <ChevronsLeft className="size-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon-sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={safePage === 1}
                      aria-label="Previous page"
                    >
                      <ChevronLeft className="size-4" />
                    </Button>

                    <span className="mx-2 text-sm">
                      Page{" "}
                      <span className="font-medium">{safePage}</span>
                      {" "}of{" "}
                      <span className="font-medium">{totalPages}</span>
                    </span>

                    <Button
                      variant="outline"
                      size="icon-sm"
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={safePage === totalPages}
                      aria-label="Next page"
                    >
                      <ChevronRight className="size-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon-sm"
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={safePage === totalPages}
                      aria-label="Last page"
                    >
                      <ChevronsRight className="size-4" />
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Create / Edit dialog */}
        <Dialog
          open={isCreateDialogOpen || editingTestCase !== null}
          onOpenChange={(open) => { if (!open) closeEditor(); }}
        >
          <DialogContent
            className="
              flex h-[92vh] max-h-[92vh]
              w-[min(1200px,calc(100vw-2rem))]
              max-w-none flex-col gap-0 overflow-hidden p-0 sm:max-w-none
            "
          >
            <DialogHeader className="border-b p-6">
              <DialogTitle>
                {editingTestCase ? "Edit Test Case" : "Create New Test Case"}
              </DialogTitle>
              <DialogDescription>
                {editingTestCase
                  ? "Update the selected test case and its associated tools and references."
                  : "Create a security test case with all required information."}
              </DialogDescription>
            </DialogHeader>

            <TestCaseForm
              key={editingTestCase ? `edit-${editingTestCase.id}` : "create"}
              testCase={editingTestCase ?? undefined}
              onSubmit={handleSubmit}
              onCancel={closeEditor}
              isLoading={isSubmitting}
              error={
                activeMutationError instanceof Error
                  ? activeMutationError.message
                  : null
              }
            />
          </DialogContent>
        </Dialog>

        {/* Delete confirmation dialog */}
        <AlertDialog
          open={deletingTestCaseId !== null}
          onOpenChange={(open) => {
            if (!open && !deleteMutation.isPending) {
              setDeletingTestCaseId(null);
              deleteMutation.reset();
            }
          }}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Test Case</AlertDialogTitle>
              <AlertDialogDescription>
                This test case will be removed from the normal dashboard and PDF
                reports. The audit information will be retained.
              </AlertDialogDescription>
            </AlertDialogHeader>

            {deleteMutation.isError && (
              <div className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                {deleteMutation.error instanceof Error
                  ? deleteMutation.error.message
                  : "Could not delete the test case."}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <AlertDialogCancel disabled={deleteMutation.isPending}>
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                disabled={deleteMutation.isPending}
                onClick={(event) => {
                  event.preventDefault();
                  if (deletingTestCaseId !== null) {
                    deleteMutation.mutate(deletingTestCaseId);
                  }
                }}
              >
                {deleteMutation.isPending ? "Deleting..." : "Delete"}
              </AlertDialogAction>
            </div>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </ProtectedRoute>
  );
}