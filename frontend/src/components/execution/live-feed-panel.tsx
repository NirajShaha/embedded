"use client";

import * as React from "react";
import {
  ArrowDown,
  ArrowDownToLine,
  ArrowUp,
  ArrowUpDown,
  ArrowDownUp,
  ChevronDown,
  Columns3,
  Maximize2,
  Pause,
  Plus,
  Radio,
  Search,
  SearchX,
  SlidersHorizontal,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/pagination";
import { TRACE_FRAME_RE } from "@/lib/script-run";
import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { FeedLine } from "@/hooks/use-script-stream";

type DirFilter = "both" | "Rx" | "Tx";
type TypeFilter = "all" | "d" | "fd";
type SortKey = "ts" | "id";
type SortOption = "ts-asc" | "ts-desc" | "id-asc" | "id-desc";

interface TraceRow {
  key: number;
  isData: boolean;
  raw: string;
  timestamp: number | null;
  channel: string;
  idText: string;
  idValue: number | null;
  dir: string;
  frameType: string;
  dlc: number | null;
  data: string;
}

function parseTraceLine(line: FeedLine): TraceRow {
  const match = TRACE_FRAME_RE.exec(line.line);
  if (!match) {
    return {
      key: line.id,
      isData: false,
      raw: line.line,
      timestamp: null,
      channel: "",
      idText: "",
      idValue: null,
      dir: "",
      frameType: "",
      dlc: null,
      data: "",
    };
  }
  const [, ts, channel, idText, dir, frameType, dlcText, data] = match;
  const id = Number.parseInt(idText, 16);
  return {
    key: line.id,
    isData: true,
    raw: line.line,
    timestamp: Number(ts),
    channel,
    idText: idText.toUpperCase(),
    idValue: Number.isNaN(id) ? null : id,
    dir,
    frameType,
    dlc: Number(dlcText),
    data: (data ?? "").trim(),
  };
}

function parseHexBound(raw: string): number | null {
  const text = raw.trim().toLowerCase().replace(/^0x/, "");
  if (!text) return null;
  const value = Number.parseInt(text, 16);
  return Number.isNaN(value) ? null : value;
}

function parseNumBound(raw: string): number | null {
  if (raw.trim() === "") return null;
  const value = Number(raw);
  return Number.isNaN(value) ? null : value;
}

function SortButton({
  label,
  active,
  dir,
  onClick,
}: {
  label: string;
  active: boolean;
  dir: "asc" | "desc";
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1 transition-colors hover:text-foreground"
      aria-label={`Sort by ${label}`}
    >
      {label}
      {active ? (
        dir === "asc" ? (
          <ArrowUp className="size-3" />
        ) : (
          <ArrowDown className="size-3" />
        )
      ) : (
        <ArrowUpDown className="size-3 text-muted-foreground/60" />
      )}
    </button>
  );
}

function FilterField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <span className="text-[11px] font-medium text-muted-foreground">
        {label}
      </span>
      {children}
    </div>
  );
}

export function LiveFeedPanel({
  lines,
  connected,
  className,
  onMaximize,
}: {
  lines: FeedLine[];
  connected?: boolean;
  className?: string;
  onMaximize?: () => void;
}) {
  const [tsFrom, setTsFrom] = React.useState("");
  const [tsTo, setTsTo] = React.useState("");
  const [idFrom, setIdFrom] = React.useState("");
  const [idTo, setIdTo] = React.useState("");
  const [dir, setDir] = React.useState<DirFilter>("both");
  const [typeFilter, setTypeFilter] = React.useState<TypeFilter>("all");
  const [dlcFrom, setDlcFrom] = React.useState("");
  const [dlcTo, setDlcTo] = React.useState("");
  const [dataQuery, setDataQuery] = React.useState("");
  const [filtersOpen, setFiltersOpen] = React.useState(false);
  const [sort, setSort] = React.useState<{ key: SortKey; dir: "asc" | "desc" }>({
    key: "ts",
    dir: "asc",
  });
  const [showChannel, setShowChannel] = React.useState(true);
  const [showFrameType, setShowFrameType] = React.useState(true);
  const [showDlc, setShowDlc] = React.useState(true);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [live, setLive] = React.useState(true);
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const skipScrollCheck = React.useRef(0);

  const rows = React.useMemo(() => lines.map(parseTraceLine), [lines]);

  const dataCount = React.useMemo(
    () => rows.filter((row) => row.isData).length,
    [rows],
  );

  const filterSig = [
    tsFrom,
    tsTo,
    idFrom,
    idTo,
    dir,
    typeFilter,
    dlcFrom,
    dlcTo,
    dataQuery,
    sort.key,
    sort.dir,
  ].join("|");

  const hasActiveFilter =
    tsFrom.trim() !== "" ||
    tsTo.trim() !== "" ||
    idFrom.trim() !== "" ||
    idTo.trim() !== "" ||
    dir !== "both" ||
    typeFilter !== "all" ||
    dlcFrom.trim() !== "" ||
    dlcTo.trim() !== "" ||
    dataQuery.trim() !== "";

  const chips = React.useMemo(() => {
    const list: { key: string; label: string; clear: () => void }[] = [];
    const tsLabel =
      tsFrom.trim() && tsTo.trim()
        ? `${tsFrom.trim()}–${tsTo.trim()}s`
        : tsFrom.trim()
          ? `≥ ${tsFrom.trim()}s`
          : `≤ ${tsTo.trim()}s`;
    if (tsFrom.trim() !== "" || tsTo.trim() !== "")
      list.push({
        key: "ts",
        label: tsLabel,
        clear: () => {
          setTsFrom("");
          setTsTo("");
        },
      });
    const idLabel =
      idFrom.trim() && idTo.trim()
        ? `${idFrom.trim().toUpperCase()}–${idTo.trim().toUpperCase()}`
        : idFrom.trim()
          ? `≥ ${idFrom.trim().toUpperCase()}`
          : `≤ ${idTo.trim().toUpperCase()}`;
    if (idFrom.trim() !== "" || idTo.trim() !== "")
      list.push({
        key: "id",
        label: `ID ${idLabel}`,
        clear: () => {
          setIdFrom("");
          setIdTo("");
        },
      });
    if (dir !== "both")
      list.push({ key: "dir", label: dir, clear: () => setDir("both") });
    if (typeFilter !== "all")
      list.push({
        key: "type",
        label: `Type ${typeFilter}`,
        clear: () => setTypeFilter("all"),
      });
    const dlcLabel =
      dlcFrom.trim() && dlcTo.trim()
        ? `DLC ${dlcFrom.trim()}–${dlcTo.trim()}`
        : dlcFrom.trim()
          ? `DLC ≥ ${dlcFrom.trim()}`
          : `DLC ≤ ${dlcTo.trim()}`;
    if (dlcFrom.trim() !== "" || dlcTo.trim() !== "")
      list.push({
        key: "dlc",
        label: dlcLabel,
        clear: () => {
          setDlcFrom("");
          setDlcTo("");
        },
      });
    if (dataQuery.trim() !== "")
      list.push({
        key: "data",
        label: `Search “${dataQuery.trim().slice(0, 24)}”`,
        clear: () => setDataQuery(""),
      });
    return list;
  }, [tsFrom, tsTo, idFrom, idTo, dir, typeFilter, dlcFrom, dlcTo, dataQuery]);

  const showBanners =
    !hasActiveFilter && sort.key === "ts" && sort.dir === "asc";

  const visible = React.useMemo(() => {
    const tsLo = parseNumBound(tsFrom);
    const tsHi = parseNumBound(tsTo);
    const idLo = parseHexBound(idFrom);
    const idHi = parseHexBound(idTo);
    const dlcLo = parseNumBound(dlcFrom);
    const dlcHi = parseNumBound(dlcTo);
    const query = dataQuery.replace(/\s+/g, "").toLowerCase();
    const idQuery = query.replace(/^0x/, "");
    const matched = rows.filter((row) => {
      if (!row.isData) return showBanners && row.raw.trim() !== "";
      if (tsLo !== null && (row.timestamp === null || row.timestamp < tsLo))
        return false;
      if (tsHi !== null && (row.timestamp === null || row.timestamp > tsHi))
        return false;
      if (idLo !== null && (row.idValue === null || row.idValue < idLo))
        return false;
      if (idHi !== null && (row.idValue === null || row.idValue > idHi))
        return false;
      if (dir !== "both" && row.dir !== dir) return false;
      if (typeFilter !== "all" && row.frameType !== typeFilter) return false;
      if (dlcLo !== null && (row.dlc === null || row.dlc < dlcLo)) return false;
      if (dlcHi !== null && (row.dlc === null || row.dlc > dlcHi)) return false;
      if (
        query &&
        !row.idText.toLowerCase().includes(idQuery) &&
        !row.data.replace(/\s+/g, "").toLowerCase().includes(query)
      )
        return false;
      return true;
    });
    if (sort.key === "ts" && sort.dir === "asc") return matched;
    const data = matched.filter((row) => row.isData);
    data.sort((a, b) => {
      const aVal = sort.key === "ts" ? (a.timestamp ?? 0) : (a.idValue ?? 0);
      const bVal = sort.key === "ts" ? (b.timestamp ?? 0) : (b.idValue ?? 0);
      return sort.dir === "asc" ? aVal - bVal : bVal - aVal;
    });
    return data;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, filterSig]);

  const totalPages = Math.max(1, Math.ceil(visible.length / pageSize));
  const sortValue: SortOption = `${sort.key}-${sort.dir}`;
  const columnCount =
    4 + Number(showChannel) + Number(showFrameType) + Number(showDlc);
  const followPage = sort.dir === "asc" ? totalPages : 1;
  const currentPage = live
    ? followPage
    : Math.min(Math.max(1, page), totalPages);
  const pageItems = visible.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );

  React.useEffect(() => {
    if (!live) setPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterSig]);

  React.useEffect(() => {
    if (!live) return;
    const el = scrollRef.current;
    if (!el) return;
    skipScrollCheck.current = Date.now();
    el.scrollTop = sort.dir === "asc" ? el.scrollHeight : 0;
  }, [pageItems, live, sort.dir]);

  const onScroll = () => {
    const el = scrollRef.current;
    if (!el || !live) return;
    if (Date.now() - skipScrollCheck.current < 200) return;
    const atEdge =
      sort.dir === "asc"
        ? el.scrollHeight - el.scrollTop - el.clientHeight < 48
        : el.scrollTop < 48;
    if (!atEdge) setLive(false);
  };

  const handlePageChange = (next: number) => {
    setPage(next);
    setLive(next === followPage);
  };

  const toggleSort = (key: SortKey) => {
    setSort((prev) =>
      prev.key !== key
        ? { key, dir: "asc" }
        : { key, dir: prev.dir === "asc" ? "desc" : "asc" },
    );
  };

  const clearFilters = () => {
    setTsFrom("");
    setTsTo("");
    setIdFrom("");
    setIdTo("");
    setDir("both");
    setTypeFilter("all");
    setDlcFrom("");
    setDlcTo("");
    setDataQuery("");
  };

  const rangeInputClass = "h-8 min-w-0 flex-1 px-2 font-mono text-xs";

  return (
    <Card
      className={cn(
        "flex min-h-0 min-w-0 flex-col gap-0 overflow-hidden rounded-xl py-0",
        className,
      )}
    >
      <CardHeader className="flex shrink-0 flex-row items-center justify-between gap-2 border-b border-border/60 px-4 py-2.5">
        <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Radio className="size-3.5" />
          Live feed — trace window
          <Badge
            variant="secondary"
            className="font-mono font-normal tabular-nums"
          >
            {hasActiveFilter
              ? `${visible.length}/${dataCount}`
              : `${dataCount}`}
          </Badge>
        </CardTitle>
        <div className="flex items-center gap-1.5">
          {connected !== undefined && (
            <span
              className={cn(
                "flex items-center gap-1 text-[11px]",
                connected ? "text-emerald-600" : "text-muted-foreground",
              )}
            >
              <span
                className={cn(
                  "size-1.5 rounded-full",
                  connected ? "bg-emerald-500" : "bg-muted-foreground/40",
                )}
              />
              {connected ? "live" : "offline"}
            </span>
          )}
          <Button
            type="button"
            size="icon-xs"
            variant={live ? "secondary" : "ghost"}
            className="text-muted-foreground hover:text-foreground"
            onClick={() => setLive((v) => !v)}
            aria-label={live ? "Pause following" : "Follow latest"}
            title={live ? "Pause following" : "Follow latest"}
          >
            {live ? (
              <Pause className="size-3.5" />
            ) : (
              <ArrowDownToLine className="size-3.5" />
            )}
          </Button>
          {onMaximize ? (
            <Button
              type="button"
              size="icon-xs"
              variant="ghost"
              className="text-muted-foreground hover:text-foreground"
              onClick={onMaximize}
              aria-label="Maximize Live feed"
              title="Maximize"
            >
              <Maximize2 className="size-3.5" />
            </Button>
          ) : null}
        </div>
      </CardHeader>

      <div className="flex shrink-0 flex-wrap items-center gap-1.5 border-b border-border/60 bg-card px-3 py-2">
        <div className="relative min-w-[180px] flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={dataQuery}
            onChange={(event) => setDataQuery(event.target.value)}
            placeholder="Search ID or bytes…"
            aria-label="Search CAN ID or data bytes"
            className="h-8 pr-7 pl-8 text-xs"
          />
          {dataQuery !== "" && (
            <button
              type="button"
              onClick={() => setDataQuery("")}
              aria-label="Clear data search"
              className="absolute top-1/2 right-1.5 inline-flex size-5 -translate-y-1/2 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <X className="size-3" />
            </button>
          )}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              size="sm"
              variant="outline"
              aria-label="Filter by direction"
              className="gap-1.5"
            >
              <Plus className="size-3.5" />
              Direction
              {dir !== "both" && (
                <span className="border-l border-border pl-1.5 text-muted-foreground">
                  {dir}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-40">
            <DropdownMenuLabel>Direction</DropdownMenuLabel>
            <DropdownMenuRadioGroup
              value={dir}
              onValueChange={(value) => {
                if (value === "both" || value === "Rx" || value === "Tx") {
                  setDir(value);
                }
              }}
            >
              <DropdownMenuRadioItem value="both">Both</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="Rx">Receive (Rx)</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="Tx">Transmit (Tx)</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              size="sm"
              variant="outline"
              aria-label="Filter by frame type"
              className="gap-1.5"
            >
              <Plus className="size-3.5" />
              Frame
              {typeFilter !== "all" && (
                <span className="border-l border-border pl-1.5 font-mono text-muted-foreground">
                  {typeFilter}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-36">
            <DropdownMenuLabel>Frame type</DropdownMenuLabel>
            <DropdownMenuRadioGroup
              value={typeFilter}
              onValueChange={(value) => {
                if (value === "all" || value === "d" || value === "fd") {
                  setTypeFilter(value);
                }
              }}
            >
              <DropdownMenuRadioItem value="all">All frames</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="d">CAN (d)</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="fd">CAN FD</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
        <Button
          type="button"
          size="sm"
          variant={filtersOpen || hasActiveFilter ? "secondary" : "outline"}
          onClick={() => setFiltersOpen((v) => !v)}
          aria-expanded={filtersOpen}
          aria-label="Toggle advanced filters"
          className="gap-1.5"
        >
          <SlidersHorizontal className="size-3.5" />
          Filters
          {chips.length > 0 && (
            <Badge variant="secondary" className="h-4 min-w-4 px-1 font-mono">
              {chips.length}
            </Badge>
          )}
          <ChevronDown
            className={cn(
              "size-3.5 transition-transform",
              filtersOpen && "rotate-180",
            )}
          />
        </Button>
        <div className="ml-auto flex shrink-0 items-center gap-1.5">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                size="sm"
                variant="outline"
                aria-label={`Sort by ${sort.key === "ts" ? "timestamp" : "CAN ID"}`}
                className="gap-1.5"
              >
                <ArrowDownUp className="size-3.5" />
                Sort
                <Badge variant="secondary" className="h-4 min-w-4 px-1 font-mono">
                  1
                </Badge>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel>Sort frames</DropdownMenuLabel>
              <DropdownMenuRadioGroup
                value={sortValue}
                onValueChange={(value) => {
                  if (
                    value === "ts-asc" ||
                    value === "ts-desc" ||
                    value === "id-asc" ||
                    value === "id-desc"
                  ) {
                    const [key, direction] = value.split("-");
                    setSort({
                      key: key === "ts" ? "ts" : "id",
                      dir: direction === "asc" ? "asc" : "desc",
                    });
                  }
                }}
              >
                <DropdownMenuRadioItem value="ts-asc">
                  Timestamp, oldest first
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="ts-desc">
                  Timestamp, newest first
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="id-asc">
                  CAN ID, low to high
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="id-desc">
                  CAN ID, high to low
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                size="sm"
                variant="outline"
                aria-label="Choose visible columns"
                className="gap-1.5"
              >
                <Columns3 className="size-3.5" />
                View
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              <DropdownMenuLabel>Toggle columns</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuCheckboxItem
                checked={showChannel}
                onCheckedChange={setShowChannel}
              >
                Channel
              </DropdownMenuCheckboxItem>
              <DropdownMenuCheckboxItem
                checked={showFrameType}
                onCheckedChange={setShowFrameType}
              >
                Frame type
              </DropdownMenuCheckboxItem>
              <DropdownMenuCheckboxItem
                checked={showDlc}
                onCheckedChange={setShowDlc}
              >
                DLC
              </DropdownMenuCheckboxItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div
        className={cn(
          "grid shrink-0 transition-all duration-200 ease-out",
          filtersOpen
            ? "grid-rows-[1fr] opacity-100"
            : "grid-rows-[0fr] opacity-0",
        )}
      >
        <div className="overflow-hidden">
          <div className="grid gap-4 border-b border-border/60 bg-muted/40 px-4 py-3 sm:grid-cols-2 lg:grid-cols-3">
            <FilterField label="Timestamp (s)">
              <div className="flex gap-1.5">
                <Input
                  value={tsFrom}
                  onChange={(event) => setTsFrom(event.target.value)}
                  placeholder="From"
                  aria-label="Timestamp from"
                  className={rangeInputClass}
                />
                <Input
                  value={tsTo}
                  onChange={(event) => setTsTo(event.target.value)}
                  placeholder="To"
                  aria-label="Timestamp to"
                  className={rangeInputClass}
                />
              </div>
            </FilterField>
            <FilterField label="CAN ID (hex)">
              <div className="flex gap-1.5">
                <Input
                  value={idFrom}
                  onChange={(event) => setIdFrom(event.target.value)}
                  placeholder="0x000"
                  aria-label="ID from"
                  className={rangeInputClass}
                />
                <Input
                  value={idTo}
                  onChange={(event) => setIdTo(event.target.value)}
                  placeholder="0xFFF"
                  aria-label="ID to"
                  className={rangeInputClass}
                />
              </div>
            </FilterField>
            <FilterField label="DLC (bytes)">
              <div className="flex gap-1.5">
                <Input
                  value={dlcFrom}
                  onChange={(event) => setDlcFrom(event.target.value)}
                  placeholder="Min"
                  aria-label="DLC min"
                  className={cn(rangeInputClass, "text-right")}
                />
                <Input
                  value={dlcTo}
                  onChange={(event) => setDlcTo(event.target.value)}
                  placeholder="Max"
                  aria-label="DLC max"
                  className={cn(rangeInputClass, "text-right")}
                />
              </div>
            </FilterField>
            <div className="flex flex-col justify-end gap-1.5">
              <span className="text-[11px] text-muted-foreground tabular-nums">
                {visible.length} of {dataCount} frames match
              </span>
              <Button
                type="button"
                size="xs"
                variant="outline"
                onClick={clearFilters}
                disabled={!hasActiveFilter}
                className="self-start"
              >
                Clear all
              </Button>
            </div>
          </div>
        </div>
      </div>

      {chips.length > 0 && (
        <div className="flex shrink-0 flex-wrap items-center gap-1.5 border-b border-border/60 bg-muted/20 px-3 py-2">
          <span className="mr-1 text-[11px] text-muted-foreground">Active filters</span>
          {chips.map((chip) => (
            <button
              key={chip.key}
              type="button"
              onClick={chip.clear}
              className="group inline-flex h-6 items-center gap-1 rounded-md border border-border bg-background px-2 text-[11px] font-medium text-foreground transition-colors hover:bg-muted"
            >
              <span>{chip.label}</span>
              <X className="size-3 text-muted-foreground group-hover:text-foreground" aria-hidden="true" />
            </button>
          ))}
        </div>
      )}

      <CardContent className="relative min-h-0 min-w-0 flex-1 overflow-hidden p-3">
        <div
          ref={scrollRef}
          onScroll={onScroll}
          className="h-full overflow-auto rounded-lg border border-border"
        >
          <table
            aria-label="Live CAN frames"
            className="w-full min-w-[600px] caption-bottom table-fixed text-xs [&_td]:px-3 [&_td]:py-2"
          >
            <TableHeader className="sticky top-0 z-10 bg-muted/40 backdrop-blur [&_th]:h-10 [&_th]:px-3 [&_th]:text-[11px] [&_th]:font-medium [&_th]:text-muted-foreground">
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[132px]">
                  <SortButton
                    label="Timestamp"
                    active={sort.key === "ts"}
                    dir={sort.dir}
                    onClick={() => toggleSort("ts")}
                  />
                </TableHead>
                {showChannel && <TableHead className="w-[52px]">Channel</TableHead>}
                <TableHead className="w-[88px]">
                  <SortButton
                    label="ID"
                    active={sort.key === "id"}
                    dir={sort.dir}
                    onClick={() => toggleSort("id")}
                  />
                </TableHead>
                <TableHead className="w-[72px]">Dir</TableHead>
                {showFrameType && <TableHead className="w-[72px]">Frame</TableHead>}
                {showDlc && (
                  <TableHead className="w-[56px] text-right">
                    <span className="inline-flex w-full items-center justify-end">
                      DLC
                    </span>
                  </TableHead>
                )}
                <TableHead>Data</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pageItems.map((row) =>
                row.isData ? (
                  <TableRow key={row.key} className="h-10 border-border/70 hover:bg-muted/40">
                    <TableCell className="font-mono text-[11px] text-muted-foreground tabular-nums">
                      {row.timestamp !== null ? row.timestamp.toFixed(6) : "—"}
                    </TableCell>
                    {showChannel && (
                      <TableCell className="font-mono text-[11px] text-muted-foreground">
                        {row.channel}
                      </TableCell>
                    )}
                    <TableCell className="font-mono font-semibold">
                      <span className="inline-flex rounded-md border border-border/70 bg-muted/50 px-1.5 py-0.5 text-[11px]">
                        0x{row.idText}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={row.dir === "Rx" ? "secondary" : "outline"}
                        className={cn(
                          "gap-1 font-mono",
                          row.dir === "Rx" && "text-emerald-600",
                          row.dir === "Tx" && "text-sky-600",
                        )}
                      >
                        {row.dir === "Rx" ? (
                          <ArrowDown className="size-3" />
                        ) : (
                          <ArrowUp className="size-3" />
                        )}
                        {row.dir}
                      </Badge>
                    </TableCell>
                    {showFrameType && (
                      <TableCell>
                        <Badge variant="outline" className="h-5 px-1.5 font-mono text-[10px] font-normal text-muted-foreground">
                          {row.frameType === "fd" ? "CAN FD" : "CAN"}
                        </Badge>
                      </TableCell>
                    )}
                    {showDlc && (
                      <TableCell className="text-right font-mono text-[11px] tabular-nums text-muted-foreground">
                        {row.dlc}
                      </TableCell>
                    )}
                    <TableCell className="max-w-0">
                      <span
                        className="block truncate font-mono text-[11px] tracking-wide"
                        title={row.data}
                      >
                        {row.data}
                      </span>
                    </TableCell>
                  </TableRow>
                ) : (
                  <TableRow key={row.key} className="hover:bg-transparent">
                    <TableCell
                      colSpan={columnCount}
                      className="whitespace-pre-wrap break-words py-3 text-muted-foreground"
                    >
                      {row.raw}
                    </TableCell>
                  </TableRow>
                ),
              )}
              {pageItems.length === 0 && (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={columnCount} className="h-40 text-center">
                    <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
                      <SearchX className="size-5" />
                      <p className="text-xs font-medium text-foreground">
                        {dataCount === 0
                          ? "No frames yet"
                          : "No frames match the current filters"}
                      </p>
                      <p className="text-xs">
                        {dataCount === 0
                          ? "Start the trace window to see CAN frames here."
                          : "Try widening the range or clearing the filters."}
                      </p>
                      {hasActiveFilter && (
                        <Button
                          type="button"
                          variant="outline"
                          size="xs"
                          onClick={clearFilters}
                          className="mt-1"
                        >
                          Clear filters
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </table>
        </div>
        {!live && visible.length > 0 && (
          <Button
            type="button"
            size="xs"
            className="absolute right-2 bottom-2 gap-1 shadow"
            onClick={() => setLive(true)}
          >
            <ArrowDownToLine className="size-3" />
            {sort.dir === "asc" ? "Latest" : "Live"}
          </Button>
        )}
      </CardContent>

      {visible.length > 0 && (
        <Pagination
          page={currentPage}
          pageSize={pageSize}
          totalItems={visible.length}
          onPageChange={handlePageChange}
          onPageSizeChange={setPageSize}
          className="shrink-0"
        />
      )}
    </Card>
  );
}
