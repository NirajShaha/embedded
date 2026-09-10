"use client";

import { useQuery } from "@tanstack/react-query";
import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart3, CheckSquare, Users, Settings, LogOut } from "lucide-react";
import Link from "next/link";
import { getAdminStats } from "@/lib/api";

export default function AdminDashboardPage() {
  const { user, logout } = useAuth();

  // Fetch admin stats
  const {
    data: stats,
    isLoading: statsLoading,
    isError: statsError,
  } = useQuery({
    queryKey: [
      "admin",
      "stats",
    ],
    queryFn: getAdminStats,
  });

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <div className="space-y-6 p-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back, <span className="font-semibold text-foreground">{user?.username}</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              🔐 ADMIN
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="text-destructive hover:text-destructive"
            >
              <LogOut className="size-4" />
              Logout
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Test Cases</CardTitle>
              <CheckSquare className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statsLoading
                ? "..."
                : stats?.total_test_cases ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Total in system</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Users</CardTitle>
              <Users className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statsLoading
                ? "..."
                : stats?.total_users ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Active users</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Recent Updates</CardTitle>
              <BarChart3 className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statsLoading
                ? "..."
                : stats?.recent_updates ?? 0}
                {statsError && (
                  <div className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                    Could not load admin statistics.
                  </div>
                )}</div>
              <p className="text-xs text-muted-foreground mt-1">Last 7 days</p>
            </CardContent>
          </Card>
        </div>

        {/* Admin Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Admin Actions</CardTitle>
            <CardDescription>Manage test cases and system settings</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <Link href="/admin/test-cases">
              <Button variant="outline" className="w-full justify-start text-left h-auto py-3">
                <div className="flex items-center gap-3 flex-1">
                  <CheckSquare className="size-5" />
                  <div>
                    <div className="font-semibold">Test Case Management</div>
                    <div className="text-xs text-muted-foreground">
                      Create, edit, and delete test cases
                    </div>
                  </div>
                </div>
              </Button>
            </Link>

            <Button variant="outline" className="w-full justify-start text-left h-auto py-3" disabled>
              <div className="flex items-center gap-3 flex-1">
                <Users className="size-5" />
                <div>
                  <div className="font-semibold">User Management</div>
                  <div className="text-xs text-muted-foreground">
                    Coming soon - Manage users and roles
                  </div>
                </div>
              </div>
            </Button>

            <Button variant="outline" className="w-full justify-start text-left h-auto py-3" disabled>
              <div className="flex items-center gap-3 flex-1">
                <Settings className="size-5" />
                <div>
                  <div className="font-semibold">System Settings</div>
                  <div className="text-xs text-muted-foreground">
                    Coming soon - Configure system settings
                  </div>
                </div>
              </div>
            </Button>
          </CardContent>
        </Card>

        {/* Quick Info */}
        <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
          <CardHeader>
            <CardTitle className="text-blue-900 dark:text-blue-100">Admin Panel Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
            <p>
              As an admin, you have full control over test case management. You can:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Create new test cases with all fields required</li>
              <li>Edit existing test cases</li>
              <li>Delete test cases permanently</li>
              <li>View audit history (who created/edited each test case)</li>
            </ul>
            <p className="mt-3 pt-2 border-t border-blue-200 dark:border-blue-800">
              Regular users can only view test cases and cannot make any modifications.
            </p>
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
