"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, Loader2 } from "lucide-react";

import { totalPages } from "@/lib/navigation";
import { getPageAttributes, getSelections, saveSelections } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";

interface PageSelectionFormProps {
  projectId: number;
  pageNumber: number;
}

export function PageSelectionForm({
  projectId,
  pageNumber,
}: PageSelectionFormProps) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const groupsQuery = useQuery({
    queryKey: ["page-attributes", pageNumber],
    queryFn: () => getPageAttributes(pageNumber),
  });

  const selectionsQuery = useQuery({
    queryKey: ["selections", projectId, pageNumber],
    queryFn: () => getSelections(projectId, pageNumber),
  });

  const [selected, setSelected] = React.useState<Set<number>>(
    () => new Set(selectionsQuery.data?.attribute_ids ?? []),
  );
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Re-seed selection when the server returns a different selection payload.
  const lastSeededRef = React.useRef<number[] | null>(null);
  React.useEffect(() => {
    const ids = selectionsQuery.data?.attribute_ids;
    if (!ids) return;
    if (lastSeededRef.current === ids) return;
    lastSeededRef.current = ids;
    setSelected(new Set(ids));
  }, [selectionsQuery.data]);

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const saveAndContinue = async () => {
    setSaving(true);
    setError(null);
    try {
      await saveSelections(
        projectId,
        pageNumber,
        Array.from(selected).sort((a, b) => a - b),
      );
      queryClient.invalidateQueries({
        queryKey: ["selections", projectId, pageNumber],
      });
      const next = pageNumber >= totalPages ? null : pageNumber + 1;
      router.push(next ? `/projects/${projectId}/page/${next}` : "/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save selections.");
      setSaving(false);
    }
  };

  const goBack = () => {
    const prev = pageNumber > 1 ? pageNumber - 1 : null;
    router.push(prev ? `/projects/${projectId}/page/${prev}` : "/");
  };

  const loading = groupsQuery.isLoading;
  const progressPct = (pageNumber / totalPages) * 100;

  return (
    <div className="flex flex-col gap-8">
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Setup step
            </p>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Step {pageNumber}{" "}
              <span className="text-muted-foreground">of {totalPages}</span>
            </h1>
          </div>
          <div className="hidden items-center gap-2 rounded-full border border-border/60 bg-card px-3 py-1.5 text-xs sm:flex">
            <span className="size-1.5 rounded-full bg-[var(--signal)] shadow-[0_0_0_3px_oklch(0.62_0.13_215/0.18)]" />
            <span className="font-medium text-foreground">
              {selected.size}
            </span>
            <span className="text-muted-foreground">selected</span>
          </div>
        </div>
        <Progress value={progressPct} className="h-1.5" />
        <p className="text-sm text-muted-foreground">
          Select one or more sub-attributes for each group below. You can
          change your choices at any time before continuing.
        </p>
      </section>

      {loading ? (
        <div className="flex flex-col gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : groupsQuery.isError ? (
        <p className="text-sm text-destructive">
          Failed to load attributes:{" "}
          {groupsQuery.error instanceof Error
            ? groupsQuery.error.message
            : "unknown error"}
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          {(groupsQuery.data ?? []).map((group) => (
            <Card key={group.id}>
              <CardHeader>
                <CardTitle className="text-base font-semibold">
                  {group.name}
                </CardTitle>
                <CardDescription>
                  Multiple selections allowed
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {group.attributes.map((attr) => {
                    const isSelected = selected.has(attr.id);
                    return (
                      <button
                        key={attr.id}
                        type="button"
                        onClick={() => toggle(attr.id)}
                        aria-pressed={isSelected}
                        className={
                          "inline-flex h-9 items-center gap-1.5 rounded-md border px-3 text-sm font-medium transition-colors " +
                          (isSelected
                            ? "border-primary bg-primary text-primary-foreground shadow-sm"
                            : "border-border bg-card text-foreground hover:border-foreground/30 hover:bg-accent")
                        }
                      >
                        {isSelected ? (
                          <Check className="size-3.5" />
                        ) : (
                          <span className="size-1.5 rounded-full bg-muted-foreground/40" />
                        )}
                        {attr.name}
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {error && (
        <p className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="sticky bottom-0 -mx-6 flex items-center justify-between gap-3 border-t border-border/60 bg-background/80 px-6 py-4 backdrop-blur sm:-mx-8 sm:px-8">
        <Button variant="outline" onClick={goBack} disabled={saving}>
          <ArrowLeft />
          Back
        </Button>
        <Button onClick={saveAndContinue} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="animate-spin" />
              Saving…
            </>
          ) : pageNumber >= totalPages ? (
            <>
              <Check />
              Finish
            </>
          ) : (
            <>
              Save &amp; continue
              <ArrowRight />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
