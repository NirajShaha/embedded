"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ProtectedRoute } from "@/components/protected-route";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Badge } from "@/components/ui/badge";
import { Plus, Edit2, Trash2, ChevronLeft } from "lucide-react";
import Link from "next/link";
import { TestCaseForm } from "@/components/admin/test-case-form";

interface TestCase {
  id: number;
  action_test_case: string;
  category: { id: number; name: string } | null;
  objective: { id: number; name: string } | null;
  severity: { id: number; name: string; severity_rank: number } | null;
  created_at: string;
}

export default function AdminTestCasesPage() {
  const queryClient = useQueryClient();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingTestCase, setEditingTestCase] = useState<TestCase | null>(null);
  const [deletingTestCaseId, setDeletingTestCaseId] = useState<number | null>(null);

  // Fetch test cases (placeholder - will be real API call later)
  const { data: testCases = [], isLoading } = useQuery({
    queryKey: ["admin", "test-cases"],
    queryFn: async () => {
      // Placeholder - will be implemented when backend is ready
      return [] as TestCase[];
    },
  });

  // Create/Update mutation
  const createMutation = useMutation({
    mutationFn: async (data: unknown) => {
      // Placeholder
      console.log("Create test case:", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "test-cases"] });
      setIsCreateDialogOpen(false);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      // Placeholder
      console.log("Delete test case:", id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "test-cases"] });
      setDeletingTestCaseId(null);
    },
  });

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <div className="space-y-6 p-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <Link href="/admin">
                <Button variant="ghost" size="sm">
                  <ChevronLeft className="size-4" />
                </Button>
              </Link>
              <h1 className="text-3xl font-bold tracking-tight">Test Case Management</h1>
              <Badge variant="secondary">Admin Only</Badge>
            </div>
            <p className="text-muted-foreground">
              Create, edit, and delete test cases for security assessments
            </p>
          </div>
          <Button onClick={() => setIsCreateDialogOpen(true)} size="lg">
            <Plus className="size-4" />
            New Test Case
          </Button>
        </div>

        {/* Test Cases Table */}
        <Card>
          <CardHeader>
            <CardTitle>All Test Cases</CardTitle>
            <CardDescription>
              {testCases.length} test case{testCases.length !== 1 ? "s" : ""}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="py-8 text-center text-muted-foreground">Loading...</div>
            ) : testCases.length === 0 ? (
              <div className="py-12 text-center">
                <div className="text-muted-foreground">No test cases found</div>
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(true)}
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
                      <th className="px-4 py-2 text-left font-semibold">Action/Test Case</th>
                      <th className="px-4 py-2 text-left font-semibold">Category</th>
                      <th className="px-4 py-2 text-left font-semibold">Objective</th>
                      <th className="px-4 py-2 text-left font-semibold">Severity</th>
                      <th className="px-4 py-2 text-left font-semibold">Created</th>
                      <th className="px-4 py-2 text-right font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {testCases.map((testCase) => (
                      <tr
                        key={testCase.id}
                        className="border-b hover:bg-muted/50 transition-colors"
                      >
                        <td className="px-4 py-3">
                          <div className="font-medium line-clamp-1">
                            {testCase.action_test_case.substring(0, 50)}...
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {testCase.category ? (
                            <Badge variant="outline">{testCase.category.name}</Badge>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {testCase.objective ? (
                            <span className="text-sm">{testCase.objective.name}</span>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {testCase.severity ? (
                            <Badge
                              variant={
                                testCase.severity.severity_rank >= 3 ? "destructive" : "secondary"
                              }
                            >
                              {testCase.severity.name}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-muted-foreground">
                          {new Date(testCase.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingTestCase(testCase)}
                            >
                              <Edit2 className="size-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-destructive hover:text-destructive"
                              onClick={() => setDeletingTestCaseId(testCase.id)}
                            >
                              <Trash2 className="size-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Create/Edit Dialog */}
        <Dialog open={isCreateDialogOpen || !!editingTestCase} onOpenChange={(open) => {
          if (!open) {
            setIsCreateDialogOpen(false);
            setEditingTestCase(null);
          }
        }}>
          <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingTestCase ? "Edit Test Case" : "Create New Test Case"}
              </DialogTitle>
              <DialogDescription>
                {editingTestCase
                  ? "Update test case details"
                  : "Create a new security test case with all required fields"}
              </DialogDescription>
            </DialogHeader>
            <TestCaseForm
              testCase={editingTestCase || undefined}
              onSubmit={async (data) => {
                await createMutation.mutateAsync(data);
              }}
              isLoading={createMutation.isPending}
            />
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deletingTestCaseId !== null} onOpenChange={(open) => {
          if (!open) setDeletingTestCaseId(null);
        }}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Test Case</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete this test case? This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <div className="flex gap-3">
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                onClick={() => {
                  if (deletingTestCaseId) {
                    deleteMutation.mutate(deletingTestCaseId);
                  }
                }}
              >
                Delete
              </AlertDialogAction>
            </div>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </ProtectedRoute>
  );
}
