"use client";

import * as React from "react";
import { CartesianGrid, XAxis } from "recharts";
import type { LegendProps } from "recharts";

import { cn } from "@/lib/utils";

export type ChartConfig = Record<
  string,
  {
    label?: React.ReactNode;
    color?: string;
  }
>;

interface ChartContextValue {
  config: ChartConfig;
}

const ChartContext = React.createContext<ChartContextValue | null>(null);

void ChartContext;

function ChartContainer({
  config,
  className,
  children,
  ...props
}: React.ComponentProps<"div"> & { config: ChartConfig }) {
  const style = React.useMemo(() => {
    const entries = Object.entries(config);
    if (entries.length === 0) return undefined;
    const css = entries
      .map(([key, value]) =>
        value.color ? `--color-${key}: ${value.color};` : "",
      )
      .join(" ");
    return { "--chart-style": css } as React.CSSProperties;
  }, [config]);

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-slot="chart"
        style={style}
        className={cn(
          "[&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line]:stroke-border/60 [&_.recharts-tooltip-cursor]:stroke-border",
          className,
        )}
        {...props}
      >
        {children}
      </div>
    </ChartContext.Provider>
  );
}

function ChartTooltipContent({
  active,
  payload,
  label,
  labelFormatter,
  formatter,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number | string; color?: string; dataKey?: string | number; payload?: Record<string, unknown> }>;
  label?: string | number;
  labelFormatter?: (label: string | number, payload: unknown[]) => React.ReactNode;
  formatter?: (value: number | string, name: string, item: unknown, index: number, payload: unknown) => React.ReactNode;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border/60 bg-popover px-3 py-2 text-xs shadow-md">
      {label !== undefined && (
        <div className="mb-1 font-medium text-popover-foreground">
          {labelFormatter ? labelFormatter(label, payload) : label}
        </div>
      )}
      <div className="space-y-0.5">
        {payload.map((item, index) => (
          <div key={index} className="flex items-center gap-2 text-muted-foreground">
            <span
              className="size-2 rounded-full"
              style={{ background: item.color ?? "var(--primary)" }}
            />
            <span>{item.name}</span>
            <span className="ml-auto pl-4 font-tabular font-medium text-foreground">
              {formatter
                ? formatter(item.value ?? "", String(item.name ?? item.dataKey ?? ""), item, index, item.payload)
                : item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChartLegendContent({
  payload,
}: LegendProps & { payload?: Array<{ value?: string; color?: string }> }) {
  if (!payload?.length) return null;
  return (
    <div className="flex flex-wrap items-center justify-center gap-3 pt-2 text-xs text-muted-foreground">
      {payload.map((item, index) => (
        <span key={index} className="inline-flex items-center gap-1.5">
          <span className="size-2 rounded-full" style={{ background: item.color }} />
          {item.value}
        </span>
      ))}
    </div>
  );
}

export { ChartContainer, ChartTooltipContent, ChartLegendContent, CartesianGrid, XAxis };
