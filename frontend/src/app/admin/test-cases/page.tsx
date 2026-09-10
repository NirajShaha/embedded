"use client";

import { useState } from "react";
import Link from "next/link";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  ChevronLeft,
  Edit2,
  Plus,
  Trash2,
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


export default function AdminTestCasesPage() {
  const queryClient = useQueryClient();

  const [
    isCreateDialogOpen,
    setIsCreateDialogOpen,
  ] = useState(false);

  const [
    editingTestCase,
    setEditingTestCase,
  ] = useState<TestCase | null>(null);

  const [
    deletingTestCaseId,
    setDeletingTestCaseId,
  ] = useState<number | null>(null);

  const {
    data: testCases = [],
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: [
      "admin",
      "test-cases",
    ],
    queryFn: listAdminTestCases,
  });

  const createMutation = useMutation({
    mutationFn: createAdminTestCase,

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            "admin",
            "test-cases",
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            "test-cases",
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            "admin",
            "stats",
          ],
        }),
      ]);

      setIsCreateDialogOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: TestCaseWritePayload;
    }) =>
      updateAdminTestCase(
        id,
        payload,
      ),

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            "admin",
            "test-cases",
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            "test-cases",
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            "admin",
            "stats",
          ],
        }),
      ]);

      setEditingTestCase(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAdminTestCase,

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            "admin",
            "test-cases",
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            "test-cases",
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            "admin",
            "stats",
          ],
        }),
      ]);

      setDeletingTestCaseId(null);
    },
  });

  const activeMutationError =
    createMutation.error ??
    updateMutation.error;

  const isSubmitting =
    createMutation.isPending ||
    updateMutation.isPending;

  const closeEditor = () => {
    if (isSubmitting) {
      return;
    }

    setIsCreateDialogOpen(false);
    setEditingTestCase(null);

    createMutation.reset();
    updateMutation.reset();
  };

  const handleSubmit = async (
    payload: TestCaseWritePayload,
  ) => {
    if (editingTestCase) {
      await updateMutation.mutateAsync({
        id: editingTestCase.id,
        payload,
      });

      return;
    }

    await createMutation.mutateAsync(
      payload,
    );
  };

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <div className="space-y-6 p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon-sm"
                asChild
              >
                <Link href="/admin">
                  <ChevronLeft />
                  <span className="sr-only">
                    Back to admin dashboard
                  </span>
                </Link>
              </Button>

              <h1 className="text-3xl font-bold tracking-tight">
                Test Case Management
              </h1>

              <Badge variant="secondary">
                Admin Only
              </Badge>
            </div>

            <p className="text-muted-foreground">
              Create, edit, and delete
              security assessment test cases.
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

        <Card>
          <CardHeader>
            <CardTitle>
              All Active Test Cases
            </CardTitle>

            <CardDescription>
              {testCases.length} active test
              case
              {testCases.length !== 1
                ? "s"
                : ""}
            </CardDescription>
          </CardHeader>

          <CardContent>
            {isLoading ? (
              <div className="py-8 text-center text-muted-foreground">
                Loading test cases...
              </div>
            ) : isError ? (
              <div className="rounded-md border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
                {error instanceof Error
                  ? error.message
                  : "Could not load test cases."}
              </div>
            ) : testCases.length === 0 ? (
              <div className="py-12 text-center">
                <div className="text-muted-foreground">
                  No active test cases found.
                </div>

                <Button
                  variant="outline"
                  onClick={() =>
                    setIsCreateDialogOpen(
                      true,
                    )
                  }
                  className="mt-4"
                >
                  Create First Test Case
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="px-4 py-2 text-left font-semibold">
                        Action/Test Case
                      </th>

                      <th className="px-4 py-2 text-left font-semibold">
                        Category
                      </th>

                      <th className="px-4 py-2 text-left font-semibold">
                        Objective
                      </th>

                      <th className="px-4 py-2 text-left font-semibold">
                        Severity
                      </th>

                      <th className="px-4 py-2 text-left font-semibold">
                        Created
                      </th>

                      <th className="px-4 py-2 text-right font-semibold">
                        Actions
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {testCases.map(
                      (testCase) => (
                        <tr
                          key={testCase.id}
                          className="border-b transition-colors hover:bg-muted/50"
                        >
                          <td className="max-w-md px-4 py-3">
                            <div className="line-clamp-2 font-medium">
                              {
                                testCase.action_test_case
                              }
                            </div>
                          </td>

                          <td className="px-4 py-3">
                            {testCase.category ? (
                              <Badge variant="outline">
                                {
                                  testCase
                                    .category
                                    .name
                                }
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">
                                Not specified
                              </span>
                            )}
                          </td>

                          <td className="max-w-xs px-4 py-3">
                            <span className="line-clamp-2">
                              {testCase
                                .objective
                                ?.name ??
                                "Not specified"}
                            </span>
                          </td>

                          <td className="px-4 py-3">
                            {testCase.severity ? (
                              <Badge
                                variant={
                                  testCase
                                    .severity
                                    .severity_rank >=
                                    4
                                    ? "destructive"
                                    : "secondary"
                                }
                              >
                                {
                                  testCase
                                    .severity
                                    .name
                                }
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">
                                Not specified
                              </span>
                            )}
                          </td>

                          <td className="px-4 py-3 text-xs text-muted-foreground">
                            {new Date(
                              testCase.created_at,
                            ).toLocaleDateString()}
                          </td>

                          <td className="px-4 py-3 text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => {
                                  updateMutation.reset();
                                  setEditingTestCase(
                                    testCase,
                                  );
                                }}
                                aria-label="Edit test case"
                              >
                                <Edit2 />
                              </Button>

                              <Button
                                variant="ghost"
                                size="icon-sm"
                                className="text-destructive hover:text-destructive"
                                onClick={() =>
                                  setDeletingTestCaseId(
                                    testCase.id,
                                  )
                                }
                                aria-label="Delete test case"
                              >
                                <Trash2 />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Dialog
          open={
            isCreateDialogOpen ||
            editingTestCase !== null
          }
          onOpenChange={(open) => {
            if (!open) {
              closeEditor();
            }
          }}
        >
          <DialogContent
            className="
    flex
    h-[92vh]
    max-h-[92vh]
    w-[min(1200px,calc(100vw-2rem))]
    max-w-none
    flex-col
    gap-0
    overflow-hidden
    p-0
    sm:max-w-none
  "
          >
            <DialogHeader className="border-b p-6">
              <DialogTitle>
                {editingTestCase
                  ? "Edit Test Case"
                  : "Create New Test Case"}
              </DialogTitle>

              <DialogDescription>
                {editingTestCase
                  ? "Update the selected test case and its associated tools and references."
                  : "Create a security test case with all required information."}
              </DialogDescription>
            </DialogHeader>

            <TestCaseForm
              key={
                editingTestCase
                  ? `edit-${editingTestCase.id}`
                  : "create"
              }
              testCase={
                editingTestCase ??
                undefined
              }
              onSubmit={handleSubmit}
              onCancel={closeEditor}
              isLoading={isSubmitting}
              error={
                activeMutationError instanceof
                  Error
                  ? activeMutationError.message
                  : null
              }
            />
          </DialogContent>
        </Dialog>

        <AlertDialog
          open={
            deletingTestCaseId !== null
          }
          onOpenChange={(open) => {
            if (
              !open &&
              !deleteMutation.isPending
            ) {
              setDeletingTestCaseId(
                null,
              );
              deleteMutation.reset();
            }
          }}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                Delete Test Case
              </AlertDialogTitle>

              <AlertDialogDescription>
                This test case will be
                removed from the normal
                dashboard and PDF reports.
                The audit information will
                be retained.
              </AlertDialogDescription>
            </AlertDialogHeader>

            {deleteMutation.isError && (
              <div className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                {deleteMutation.error instanceof
                  Error
                  ? deleteMutation.error
                    .message
                  : "Could not delete the test case."}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <AlertDialogCancel
                disabled={
                  deleteMutation.isPending
                }
              >
                Cancel
              </AlertDialogCancel>

              <AlertDialogAction
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                disabled={
                  deleteMutation.isPending
                }
                onClick={(event) => {
                  event.preventDefault();

                  if (
                    deletingTestCaseId !==
                    null
                  ) {
                    deleteMutation.mutate(
                      deletingTestCaseId,
                    );
                  }
                }}
              >
                {deleteMutation.isPending
                  ? "Deleting..."
                  : "Delete"}
              </AlertDialogAction>
            </div>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </ProtectedRoute>
  );
}