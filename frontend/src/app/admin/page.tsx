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
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";
import Link from "next/link";
import { getAdminStats } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { SectionHeader } from "@/components/section-header";
import { ContentWrapper } from "@/components/content-wrapper";
import { StatCard } from "@/components/stat-card";

// Action Card component - inline since it's admin-specific
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
  const { user } = useAuth();

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
      <ContentWrapper>
        {/* Page Header */}
        <PageHeader
          title="Admin Dashboard"
          description="Manage security test cases, users, and system settings. Full administrative control over the test case library."
          badge="Admin"
          icon={<ShieldCheck className="h-6 w-6 text-blue-600" />}
        />

        {/* Statistics Section */}
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Active Test Cases"
            value={stats?.total_test_cases ?? 0}
            subLabel="Total in the system"
            icon={CheckSquare}
            iconBg="bg-blue-100 dark:bg-blue-950"
            iconColor="text-blue-600 dark:text-blue-200"
            isLoading={statsLoading}
          />
          <StatCard
            label="Users"
            value={stats?.total_users ?? 0}
            subLabel="Registered accounts"
            icon={Users}
            iconBg="bg-violet-100 dark:bg-violet-950"
            iconColor="text-violet-600 dark:text-violet-200"
            isLoading={statsLoading}
          />
          <StatCard
            label="Recent Updates"
            value={stats?.recent_updates ?? 0}
            subLabel="Test cases edited in last 7 days"
            icon={BarChart3}
            iconBg="bg-emerald-100 dark:bg-emerald-950"
            iconColor="text-emerald-600 dark:text-emerald-200"
            isLoading={statsLoading}
          />
        </div>

        {statsError && (
          <div className="rounded-xl border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            ⚠️ Could not load admin statistics. Please refresh the page.
          </div>
        )}

        {/* Quick Actions Section */}
        <div className="space-y-6">
          <SectionHeader
            title="Quick Actions"
            description="Common administrative tasks and shortcuts"
          />

          <div className="grid gap-3 sm:grid-cols-1 lg:grid-cols-3">
            <ActionCard
              href="/admin/test-cases"
              icon={CheckSquare}
              iconBg="bg-blue-100 dark:bg-blue-950"
              iconColor="text-blue-600 dark:text-blue-200"
              title="Test Case Management"
              description="Create, edit, and delete security test cases"
            />
            <ActionCard
              icon={Users}
              iconBg="bg-violet-100 dark:bg-violet-950"
              iconColor="text-violet-600 dark:text-violet-200"
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

        {/* Permissions Section */}
        <div className="space-y-6">
          <SectionHeader
            title="Your Permissions"
            description="Administrative capabilities available to your account"
          />

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
                className="flex items-start gap-3 rounded-xl border bg-card p-4 transition-shadow hover:shadow-sm"
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
      </ContentWrapper>
    </ProtectedRoute>
  );
}
