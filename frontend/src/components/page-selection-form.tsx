"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";

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

  const [selected, setSelected] = React.useState<Set<number>>(new Set());
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (selectionsQuery.data) {
      setSelected(new Set(selectionsQuery.data.attribute_ids));
    }
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
      await saveSelections(projectId, pageNumber, Array.from(selected).sort((a, b) => a - b));
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

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold tracking-tight">
            Page {pageNumber} of {totalPages}
          </h1>
          <span className="text-sm text-muted-foreground">
            {selected.size} selected
          </span>
        </div>
        <Progress value={(pageNumber / totalPages) * 100} />
        <p className="text-sm text-muted-foreground">
          Select one or more sub-attributes for each group below.
        </p>
      </section>

      {loading ? (
        <div className="flex flex-col gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : groupsQuery.isError ? (
        <p className="text-destructive">
          Failed to load attributes:{" "}
          {groupsQuery.error instanceof Error ? groupsQuery.error.message : "unknown error"}
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          {(groupsQuery.data ?? []).map((group) => (
            <Card key={group.id}>
              <CardHeader>
                <CardTitle className="text-base">{group.name}</CardTitle>
                <CardDescription>Multiple selections allowed</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {group.attributes.map((attr) => {
                    const isSelected = selected.has(attr.id);
                    return (
                      <Button
                        key={attr.id}
                        type="button"
                        variant={isSelected ? "default" : "outline"}
                        size="sm"
                        onClick={() => toggle(attr.id)}
                      >
                        {attr.name}
                      </Button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      <section className="flex items-center justify-between">
        <Button variant="outline" onClick={goBack}>
          <ArrowLeft />
          Back
        </Button>
        <Button onClick={saveAndContinue} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="animate-spin" />
              Saving...
            </>
          ) : pageNumber >= totalPages ? (
            "Finish"
          ) : (
            <>
              Save &amp; continue
              <ArrowRight />
            </>
          )}
        </Button>
      </section>
    </div>
  );
}