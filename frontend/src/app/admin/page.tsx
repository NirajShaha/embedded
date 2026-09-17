"use client";

import { useQuery } from "@tanstack/react-query";
import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ArrowRight,
  BarChart3,
  CheckSquare,
  Clock,
  LogOut,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";
import Link from "next/link";
import { getAdminStats } from "@/lib/api";


function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  iconBg,
  iconColor,
  loading,
}: {
  label: string;
  value: number | string;
  sub: string;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  loading: boolean;
}) {
  return (
    <div className="flex items-center gap-4 rounded-xl border bg-card p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className={`flex size-12 shrink-0 items-center justify-center rounded-xl ${iconBg}`}>
        <Icon className={`size-6 ${iconColor}`} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </p>
        <p className="mt-0.5 text-3xl font-bold tabular-nums text-foreground">
          {loading ? (
            <span className="inline-block h-8 w-16 animate-pulse rounded-md bg-muted" />
          ) : (
            value
          )}
        </p>
        <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>
      </div>
    </div>
  );
}


function ActionCard({
  href,
  icon: Icon,
  iconBg,
  iconColor,
  title,
  description,
  badge,
  disabled = false,
}: {
  href?: string;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  title: string;
  description: string;
  badge?: string;
  disabled?: boolean;
}) {
  const inner = (
    <div
      className={[
        "group flex items-center gap-4 rounded-xl border p-5 transition-all",
        disabled
          ? "cursor-not-allowed opacity-50"
          : "cursor-pointer bg-card shadow-sm hover:border-primary/40 hover:shadow-md",
      ].join(" ")}
    >
      <div className={`flex size-11 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
        <Icon className={`size-5 ${iconColor}`} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-foreground">{title}</span>
          {badge && (
            <Badge variant="secondary" className="text-xs">
              {badge}
            </Badge>
          )}
        </div>
        <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>
      </div>
      {!disabled && (
        <ArrowRight className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-primary" />
      )}
    </div>
  );

  if (href && !disabled) {
    return <Link href={href}>{inner}</Link>;
  }
  return inner;
}


export default function AdminDashboardPage() {
  const { user, logout } = useAuth();

  const {
    data: stats,
    isLoading: statsLoading,
    isError: statsError,
  } = useQuery({
    queryKey: ["admin", "stats"],
    queryFn: getAdminStats,
  });

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <div className="min-h-screen space-y-8 p-6 sm:p-8">

        {/* ── Hero banner ── */}
        <div className="relative overflow-hidden rounded-2xl border bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 text-white shadow-lg dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
          {/* decorative blobs */}
          <div className="pointer-events-none absolute -right-16 -top-16 size-64 rounded-full bg-blue-500/10 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-8 left-8 size-40 rounded-full bg-indigo-500/10 blur-2xl" />

          <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              {/* identity row */}
              <div className="flex items-center gap-2">
                <div className="flex size-9 items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/20">
                  <ShieldCheck className="size-5 text-white" />
                </div>
                <Badge className="border-white/20 bg-white/10 text-white hover:bg-white/20">
                  🔐 Admin
                </Badge>
              </div>

              <h1 className="text-3xl font-bold tracking-tight text-white">
                Welcome back,{" "}
                <span className="text-blue-300">{user?.username}</span>
              </h1>
              <p className="max-w-md text-sm text-slate-400">
                You have full administrative control over the test case library.
                Changes you make are reflected immediately for all users.
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="shrink-0 border-white/20 bg-white/10 text-white hover:bg-white/20 hover:text-white"
            >
              <LogOut className="size-4" />
              Logout
            </Button>
          </div>
        </div>

        {/* ── Stats strip ── */}
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Active Test Cases"
            value={stats?.total_test_cases ?? 0}
            sub="Total in the system"
            icon={CheckSquare}
            iconBg="bg-blue-50 dark:bg-blue-950/60"
            iconColor="text-blue-600 dark:text-blue-400"
            loading={statsLoading}
          />
          <StatCard
            label="Users"
            value={stats?.total_users ?? 0}
            sub="Registered accounts"
            icon={Users}
            iconBg="bg-violet-50 dark:bg-violet-950/60"
            iconColor="text-violet-600 dark:text-violet-400"
            loading={statsLoading}
          />
          <StatCard
            label="Recent Updates"
            value={stats?.recent_updates ?? 0}
            sub="Test cases edited in last 7 days"
            icon={BarChart3}
            iconBg="bg-emerald-50 dark:bg-emerald-950/60"
            iconColor="text-emerald-600 dark:text-emerald-400"
            loading={statsLoading}
          />
        </div>

        {statsError && (
          <div className="rounded-xl border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            ⚠️ Could not load admin statistics. Please refresh the page.
          </div>
        )}

        {/* ── Quick Actions ── */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold tracking-tight">Quick Actions</h2>
            <div className="h-px flex-1 bg-border" />
          </div>

          <div className="grid gap-3 sm:grid-cols-1 lg:grid-cols-3">
            <ActionCard
              href="/admin/test-cases"
              icon={CheckSquare}
              iconBg="bg-blue-50 dark:bg-blue-950/60"
              iconColor="text-blue-600 dark:text-blue-400"
              title="Test Case Management"
              description="Create, edit, and delete security test cases"
            />
            <ActionCard
              icon={Users}
              iconBg="bg-violet-50 dark:bg-violet-950/60"
              iconColor="text-violet-600 dark:text-violet-400"
              title="User Management"
              description="Manage users and roles"
              badge="Coming soon"
              disabled
            />
            <ActionCard
              icon={Settings}
              iconBg="bg-slate-100 dark:bg-slate-800"
              iconColor="text-slate-600 dark:text-slate-400"
              title="System Settings"
              description="Configure system-wide settings"
              badge="Coming soon"
              disabled
            />
          </div>
        </div>

        {/* ── Capabilities info ── */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold tracking-tight">Your Permissions</h2>
            <div className="h-px flex-1 bg-border" />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {[
              {
                icon: CheckSquare,
                color: "text-blue-500",
                title: "Create test cases",
                desc: "Add new entries to the security test library with all metadata fields.",
              },
              {
                icon: Settings,
                color: "text-amber-500",
                title: "Edit any test case",
                desc: "Modify existing test cases including all fields, tools, and references.",
              },
              {
                icon: Users,
                color: "text-violet-500",
                title: "Audit trail",
                desc: "Every change is tracked with who created or last edited the record.",
              },
              {
                icon: Clock,
                color: "text-emerald-500",
                title: "Soft delete",
                desc: "Deleted test cases are hidden from users but retained for audits.",
              },
            ].map(({ icon: Icon, color, title, desc }) => (
              <div
                key={title}
                className="flex items-start gap-3 rounded-xl border bg-card p-4"
              >
                <Icon className={`mt-0.5 size-4 shrink-0 ${color}`} />
                <div>
                  <p className="text-sm font-medium">{title}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </ProtectedRoute>
  );
}
