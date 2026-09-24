"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, Check, ChevronDown, Loader2, X } from "lucide-react";

import {
  createAdminLookupItem,
  getAdminFieldSuggestions,
  getAdminLookups,
  type LookupCreateType,
  type LookupItem,
  type TestCase,
  type TestCaseWritePayload,
} from "@/lib/api";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const NOT_SPECIFIED = "__not_specified__";
const OTHER_OPTION = "__other__";

interface TestCaseFormProps {
  testCase?: TestCase;
  onSubmit: (payload: TestCaseWritePayload) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string | null;
}

interface FormData {
  test_case_name: string;
  pre_condition: string;
  impact: string;
  action_test_case: string;
  category_id: string;
  objective_id: string;
  protocol_id: string;
  attack_vector_id: string;
  test_type_id: string;
  severity_id: string;
  threat_id: string;
  description: string;
  attack_path: string;
  test_steps: string;
  expected_output: string;
  attack_feasibility: string;
  cia_impact: string;
  safety_impact: string;
  tool_ids: number[];
  reference_ids: number[];
}

function initialFormData(testCase?: TestCase): FormData {
  return {
    test_case_name: testCase?.test_case_name ?? "",
    pre_condition: testCase?.pre_condition ?? "",
    impact: testCase?.impact ?? "",
    action_test_case: testCase?.action_test_case ?? "",
    category_id: testCase !== undefined ? String(testCase.category_id) : "",
    objective_id: testCase !== undefined ? String(testCase.objective_id) : "",
    protocol_id:
      testCase?.protocol_id != null ? String(testCase.protocol_id) : "",
    attack_vector_id:
      testCase?.attack_vector_id != null
        ? String(testCase.attack_vector_id)
        : "",
    test_type_id:
      testCase?.test_type_id != null ? String(testCase.test_type_id) : "",
    severity_id:
      testCase?.severity_id != null ? String(testCase.severity_id) : "",
    threat_id: testCase?.threat_id != null ? String(testCase.threat_id) : "",
    description: testCase?.description ?? "",
    attack_path: testCase?.attack_path ?? "",
    test_steps: testCase?.test_steps ?? "",
    expected_output: testCase?.expected_output ?? "",
    attack_feasibility: testCase?.attack_feasibility ?? "",
    cia_impact: testCase?.cia_impact ?? "",
    safety_impact: testCase?.safety_impact ?? "",
    tool_ids: testCase?.test_case_tools.map((t) => Number(t.tool.id)) ?? [],
    reference_ids:
      testCase?.test_case_references.map((r) => Number(r.reference.id)) ?? [],
  };
}

function optionalId(value: string): number | null {
  if (!value) return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function optionalText(value: string): string | null {
  const t = value.trim();
  return t || null;
}

// ---------------------------------------------------------------------------
// SelectWithOther
//
// Normal state  : renders a <Select> dropdown with an "Other..." option.
// "Other" chosen: the dropdown box **morphs into** an <Input> at the exact same
//                 position (same height, same width). No extra row is added.
// Save (Enter / ✓): calls the API, refreshes lookups, auto-selects the new item,
//                   then switches back to dropdown mode.
// Cancel (Esc / ✕): reverts to dropdown mode without changing the selected value.
// ---------------------------------------------------------------------------
function SelectWithOther({
  label,
  fieldKey,
  lookupType,
  value,
  items,
  onChange,
  disabled = false,
  createMetadata,
}: {
  label: string;
  fieldKey: string;
  lookupType: LookupCreateType;
  value: string;
  items: LookupItem[];
  onChange: (value: string) => void;
  disabled?: boolean;
  createMetadata?: { category_id?: number; severity_rank?: number };
}) {
  const [mode, setMode] = useState<"select" | "input">("select");
  const [otherName, setOtherName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const handleSelectChange = (v: string) => {
    setSaveError(null);
    if (v === OTHER_OPTION) {
      // Morph to input mode
      setOtherName("");
      setMode("input");
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      onChange(v === NOT_SPECIFIED ? "" : v);
    }
  };

  const handleSave = async () => {
    const name = otherName.trim();
    if (!name) return;
    setSaving(true);
    setSaveError(null);
    try {
      const newItem = await createAdminLookupItem(
        lookupType,
        name,
        createMetadata,
      );
      await queryClient.invalidateQueries({
        queryKey: ["admin", "test-case-lookups"],
      });
      onChange(String(newItem.id));
      setMode("select");
      setOtherName("");
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save.");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setMode("select");
    setOtherName("");
    setSaveError(null);
  };

  return (
    <div className="space-y-2">
      <Label htmlFor={fieldKey}>{label}</Label>

      {mode === "select" ? (
        // ── Dropdown mode ──────────────────────────────────────────────────
        <Select
          value={value || NOT_SPECIFIED}
          disabled={disabled}
          onValueChange={handleSelectChange}
        >
          <SelectTrigger id={fieldKey} className="w-full">
            <SelectValue placeholder={`Select ${label.toLowerCase()}`} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NOT_SPECIFIED}>Not specified</SelectItem>
            {items.map((item) => (
              <SelectItem key={item.id} value={String(item.id)}>
                {item.name}
              </SelectItem>
            ))}
            <SelectItem
              value={OTHER_OPTION}
              className="mt-1 border-t pt-1 italic text-muted-foreground"
            >
              Other&hellip;
            </SelectItem>
          </SelectContent>
        </Select>
      ) : (
        // ── Input mode — same position as the dropdown ─────────────────────
        <div className="flex gap-1.5">
          <Input
            ref={inputRef}
            id={fieldKey}
            placeholder={`Type new ${label.toLowerCase()}\u2026`}
            value={otherName}
            onChange={(e) => {
              setOtherName(e.target.value);
              setSaveError(null);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void handleSave();
              }
              if (e.key === "Escape") handleCancel();
            }}
            disabled={saving}
            // h-9 matches the default SelectTrigger height
            className="h-9 flex-1"
          />
          <Button
            type="button"
            size="icon"
            variant="outline"
            className="size-9 shrink-0"
            disabled={!otherName.trim() || saving}
            onClick={() => void handleSave()}
            title="Save"
          >
            {saving ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <Check className="size-3.5" />
            )}
          </Button>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="size-9 shrink-0"
            disabled={saving}
            onClick={handleCancel}
            title="Cancel"
          >
            <X className="size-3.5" />
          </Button>
        </div>
      )}

      {saveError && <p className="text-xs text-destructive">{saveError}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// MultiSelectWithOther
//
// Scrollable checkbox list for Tools / References.
// At the bottom there is an "Other..." pseudo-checkbox row.
// When that row is checked, the label text itself is replaced by an <Input>
// inline — no extra row is added. Saving creates the entry, auto-checks it,
// and collapses back to the "Other..." label.
// ---------------------------------------------------------------------------
function MultiSelectWithOther({
  label,
  lookupType,
  items,
  selected,
  onToggle,
  onNewItemCreated,
  disabled = false,
}: {
  label: string;
  lookupType: "tools" | "references";
  items: LookupItem[];
  selected: number[];
  onToggle: (id: number) => void;
  onNewItemCreated: (id: number) => void;
  disabled?: boolean;
}) {
  const [filterText, setFilterText] = useState("");
  const [otherOpen, setOtherOpen] = useState(false);
  const [otherName, setOtherName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const singular = label === "Tools" ? "tool" : "reference";

  const filteredItems = useMemo(() => {
    const q = filterText.trim().toLowerCase();
    return q ? items.filter((i) => i.name.toLowerCase().includes(q)) : [];
  }, [items, filterText]);

  const handleOtherCheck = () => {
    if (otherOpen) {
      // Collapse without saving
      setOtherOpen(false);
      setOtherName("");
      setSaveError(null);
    } else {
      setOtherOpen(true);
      setOtherName("");
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  };

  const handleSave = async () => {
    const name = otherName.trim();
    if (!name) return;
    setSaving(true);
    setSaveError(null);
    try {
      const newItem = await createAdminLookupItem(lookupType, name);
      await queryClient.invalidateQueries({
        queryKey: ["admin", "test-case-lookups"],
      });
      onNewItemCreated(newItem.id);
      setOtherOpen(false);
      setOtherName("");
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>{label}</Label>
        {selected.length > 0 && (
          <span className="text-xs text-muted-foreground">
            {selected.length} selected
          </span>
        )}
      </div>

      {/* Search / filter */}
      <Input
        placeholder={`Search ${label.toLowerCase()}\u2026`}
        value={filterText}
        onChange={(e) => setFilterText(e.target.value)}
        disabled={disabled}
        className="h-8 text-sm"
      />

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5 rounded-md border border-border/60 bg-muted/20 p-2">
          {selected.map((id) => {
            const item = items.find((candidate) => candidate.id === id);
            return item ? (
              <button
                key={id}
                type="button"
                onClick={() => onToggle(id)}
                disabled={disabled}
                className="inline-flex max-w-full items-center gap-1 rounded-md border border-primary/30 bg-primary/10 px-2 py-1 text-xs leading-5 text-foreground hover:bg-primary/15"
                title={`Remove ${item.name}`}
              >
                <span className="truncate">{item.name}</span>
                <X className="size-3 shrink-0" />
              </button>
            ) : null;
          })}
        </div>
      )}

      {/* Suggestions appear only after the user starts typing. */}
      {filterText.trim() && (
        <div className="max-h-52 space-y-0.5 overflow-y-auto rounded-md border p-2">
          {/* Existing items */}
          {filteredItems.length === 0 && !otherOpen && (
            <p className="px-2 py-2 text-xs text-muted-foreground">
              {items.length === 0
                ? `No ${label.toLowerCase()} yet \u2014 check \u201cOther\u2026\u201d below to add one.`
                : "No matches found."}
            </p>
          )}
          {filteredItems.map((item) => {
            const checked = selected.includes(item.id);
            return (
              <label
                key={item.id}
                className={[
                  "flex items-start gap-2 rounded-md px-2 py-1.5 text-sm",
                  disabled
                    ? "cursor-not-allowed opacity-60"
                    : "cursor-pointer hover:bg-muted",
                  checked ? "bg-muted/60" : "",
                ].join(" ")}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={disabled}
                  onChange={() => {
                    if (!disabled) onToggle(item.id);
                  }}
                  className="mt-0.5 size-4 accent-primary"
                />
                <span className="break-words">{item.name}</span>
              </label>
            );
          })}

          <div className="mt-1 border-t pt-2">
            {!otherOpen ? (
              // Collapsed: looks like a regular checkbox row
              <label
                className={[
                  "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm italic text-muted-foreground",
                  disabled
                    ? "cursor-not-allowed opacity-60"
                    : "cursor-pointer hover:bg-muted",
                ].join(" ")}
              >
                <input
                  type="checkbox"
                  checked={false}
                  disabled={disabled}
                  onChange={handleOtherCheck}
                  className="size-4 accent-primary"
                />
                <span>Other&hellip;</span>
              </label>
            ) : (
              // Expanded: checkbox stays checked; label replaced by inline input + buttons
              <div className="flex items-center gap-1.5 px-2 py-1">
                <input
                  type="checkbox"
                  checked
                  readOnly
                  disabled={saving}
                  onChange={handleOtherCheck}
                  className="size-4 shrink-0 accent-primary cursor-pointer"
                />
                <Input
                  ref={inputRef}
                  placeholder={`New ${singular} name\u2026`}
                  value={otherName}
                  onChange={(e) => {
                    setOtherName(e.target.value);
                    setSaveError(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      void handleSave();
                    }
                    if (e.key === "Escape") {
                      setOtherOpen(false);
                      setOtherName("");
                    }
                  }}
                  disabled={saving}
                  className="h-7 flex-1 text-sm"
                />
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  className="size-7 shrink-0"
                  disabled={!otherName.trim() || saving}
                  onClick={() => void handleSave()}
                  title="Add"
                >
                  {saving ? (
                    <Loader2 className="size-3 animate-spin" />
                  ) : (
                    <Check className="size-3" />
                  )}
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="size-7 shrink-0"
                  disabled={saving}
                  onClick={() => {
                    setOtherOpen(false);
                    setOtherName("");
                    setSaveError(null);
                  }}
                  title="Cancel"
                >
                  <X className="size-3" />
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {saveError && <p className="text-xs text-destructive">{saveError}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// TextFieldWithSuggestions
//
// Free-text textarea with a "previous values" dropdown above it.
// The dropdown lists DB-sourced suggestions; choosing one fills the textarea.
// "Other... (type below)" is the last option — it simply keeps focus on the
// textarea so the user can type a fresh value (no extra box appears).
// ---------------------------------------------------------------------------
function TextFieldWithSuggestions({
  label,
  fieldKey,
  value,
  suggestions,
  suggestionsLoading,
  onChange,
  disabled = false,
}: {
  label: string;
  fieldKey: string;
  value: string;
  suggestions: string[];
  suggestionsLoading: boolean;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const hasSuggestions = !suggestionsLoading && suggestions.length > 0;
  const dropdownValue =
    hasSuggestions && suggestions.includes(value) ? value : OTHER_OPTION;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label htmlFor={fieldKey}>{label}</Label>
        {hasSuggestions && (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <ChevronDown className="size-3" />
            {suggestions.length} previous value
            {suggestions.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Suggestions dropdown — only rendered when data exists */}
      {hasSuggestions && (
        <Select
          value={dropdownValue}
          disabled={disabled}
          onValueChange={(v) => {
            if (v === OTHER_OPTION) {
              // Focus the textarea so user can type immediately
              setTimeout(() => textareaRef.current?.focus(), 0);
            } else {
              onChange(v);
            }
          }}
        >
          <SelectTrigger className="w-full text-muted-foreground">
            <SelectValue placeholder="Pick a previous value to fill below\u2026" />
          </SelectTrigger>
          <SelectContent className="max-h-60">
            {suggestions.map((s) => (
              <SelectItem key={s} value={s}>
                <span className="line-clamp-2 break-words">{s}</span>
              </SelectItem>
            ))}
            <SelectItem
              value={OTHER_OPTION}
              className="mt-1 border-t pt-1 italic text-muted-foreground"
            >
              Other&hellip; (type below)
            </SelectItem>
          </SelectContent>
        </Select>
      )}

      <Textarea
        ref={textareaRef}
        id={fieldKey}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="min-h-20"
        placeholder={
          hasSuggestions
            ? "Type a custom value, or pick one from the dropdown above."
            : `Enter ${label.toLowerCase()}.`
        }
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// TestCaseForm  (the exported component)
// ---------------------------------------------------------------------------
export function TestCaseForm({
  testCase,
  onSubmit,
  onCancel,
  isLoading = false,
  error,
}: TestCaseFormProps) {
  const [formData, setFormData] = useState<FormData>(() =>
    initialFormData(testCase),
  );
  const [validationError, setValidationError] = useState<string | null>(null);

  const {
    data: lookups,
    isLoading: lookupsLoading,
    isError: lookupsError,
    error: lookupError,
  } = useQuery({
    queryKey: ["admin", "test-case-lookups"],
    queryFn: getAdminLookups,
  });

  const { data: suggestions, isLoading: suggestionsLoading } = useQuery({
    queryKey: ["admin", "field-suggestions"],
    queryFn: getAdminFieldSuggestions,
    retry: 1,
  });

  const objectives = useMemo(
    () =>
      (lookups?.objectives ?? []).filter(
        (o) =>
          formData.category_id !== "" &&
          String(o.category_id) === formData.category_id,
      ),
    [lookups?.objectives, formData.category_id],
  );

  const isFormValid =
    formData.action_test_case.trim().length > 0 &&
    formData.category_id.length > 0 &&
    formData.objective_id.length > 0;

  const setField = (field: keyof FormData, value: string | number[]) => {
    setValidationError(null);
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleListItem = (field: "tool_ids" | "reference_ids", id: number) => {
    setFormData((prev) => {
      const cur = prev[field];
      return {
        ...prev,
        [field]: cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id],
      };
    });
  };

  const addToList = (field: "tool_ids" | "reference_ids", id: number) => {
    setFormData((prev) => {
      if (prev[field].includes(id)) return prev;
      return { ...prev, [field]: [...prev[field], id] };
    });
  };

  const handleCategoryChange = (value: string) => {
    setValidationError(null);
    setFormData((prev) => ({ ...prev, category_id: value, objective_id: "" }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setValidationError(null);

    const actionTestCase = formData.action_test_case.trim();
    if (!actionTestCase) {
      setValidationError("Action/Test Case is required.");
      return;
    }
    if (!formData.category_id) {
      setValidationError("Category is required.");
      return;
    }
    if (!formData.objective_id) {
      setValidationError("Objective is required.");
      return;
    }

    const categoryId = Number(formData.category_id);
    const objectiveId = Number(formData.objective_id);

    if (!Number.isFinite(categoryId) || categoryId <= 0) {
      setValidationError("Please select a valid category.");
      return;
    }
    if (!Number.isFinite(objectiveId) || objectiveId <= 0) {
      setValidationError("Please select a valid objective.");
      return;
    }
    if (!objectives.find((o) => String(o.id) === String(objectiveId))) {
      setValidationError(
        "Please re-select the objective \u2014 it may not match the chosen category.",
      );
      return;
    }

    const payload: TestCaseWritePayload = {
      test_case_name: optionalText(formData.test_case_name),
      pre_condition: optionalText(formData.pre_condition),
      impact: optionalText(formData.impact),
      action_test_case: actionTestCase,
      category_id: categoryId,
      objective_id: objectiveId,
      protocol_id: optionalId(formData.protocol_id),
      attack_vector_id: optionalId(formData.attack_vector_id),
      test_type_id: optionalId(formData.test_type_id),
      severity_id: optionalId(formData.severity_id),
      threat_id: optionalId(formData.threat_id),
      description: optionalText(formData.description),
      attack_path: optionalText(formData.attack_path),
      test_steps: optionalText(formData.test_steps),
      expected_output: optionalText(formData.expected_output),
      attack_feasibility: optionalText(formData.attack_feasibility),
      cia_impact: optionalText(formData.cia_impact),
      safety_impact: optionalText(formData.safety_impact),
      tool_ids: [...new Set(formData.tool_ids)].sort((a, b) => a - b),
      reference_ids: [...new Set(formData.reference_ids)].sort((a, b) => a - b),
    };

    try {
      await onSubmit(payload);
    } catch {
      /* error exposed via error prop */
    }
  };

  if (lookupsLoading) {
    return (
      <div className="flex min-h-60 flex-1 items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (lookupsError) {
    return (
      <div className="m-6 rounded-md border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
        {lookupError instanceof Error
          ? lookupError.message
          : "Could not load form options."}
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex min-h-0 flex-1 flex-col overflow-hidden"
      noValidate
    >
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
        <div className="space-y-6 p-6 pb-10">
          {/* ── Required Fields ──────────────────────────────────── */}
          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">Required Fields</h3>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="test_case_name">Test Case Name</Label>
                <Input
                  id="test_case_name"
                  value={formData.test_case_name}
                  onChange={(e) => setField("test_case_name", e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="pre_condition">Pre-condition</Label>
                <Textarea
                  id="pre_condition"
                  value={formData.pre_condition}
                  onChange={(e) => setField("pre_condition", e.target.value)}
                  disabled={isLoading}
                  className="min-h-24"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="action_test_case">
                Action/Test Case
                <span className="text-destructive"> *</span>
              </Label>
              <Textarea
                id="action_test_case"
                value={formData.action_test_case}
                onChange={(e) => setField("action_test_case", e.target.value)}
                disabled={isLoading}
                required
                aria-required="true"
                className="min-h-28"
                placeholder="Enter the security action or test case."
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <SelectWithOther
                label="Category"
                fieldKey="category_id"
                lookupType="categories"
                value={formData.category_id}
                items={lookups?.categories ?? []}
                disabled={isLoading}
                onChange={handleCategoryChange}
              />

              <div className="space-y-2">
                <Label htmlFor="objective_id">
                  Objective<span className="text-destructive"> *</span>
                </Label>
                <SelectWithOther
                  label="Objective"
                  fieldKey="objective_id"
                  lookupType="objectives"
                  value={formData.objective_id}
                  items={objectives}
                  disabled={isLoading || !formData.category_id}
                  createMetadata={{ category_id: Number(formData.category_id) }}
                  onChange={(v) => setField("objective_id", v)}
                />
              </div>
            </div>
          </section>

          {/* ── Test Classification ───────────────────────────────── */}
          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">Test Classification</h3>
            <p className="text-xs text-muted-foreground">
              Select an existing value, or choose <strong>Other&hellip;</strong>{" "}
              to type a new one directly in the same field.
            </p>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <SelectWithOther
                label="Protocol"
                fieldKey="protocol_id"
                lookupType="protocols"
                value={formData.protocol_id}
                items={lookups?.protocols ?? []}
                disabled={isLoading}
                onChange={(v) => setField("protocol_id", v)}
              />
              <SelectWithOther
                label="Attack Vector"
                fieldKey="attack_vector_id"
                lookupType="attack_vectors"
                value={formData.attack_vector_id}
                items={lookups?.attack_vectors ?? []}
                disabled={isLoading}
                onChange={(v) => setField("attack_vector_id", v)}
              />
              <SelectWithOther
                label="Test Type"
                fieldKey="test_type_id"
                lookupType="test_types"
                value={formData.test_type_id}
                items={lookups?.test_types ?? []}
                disabled={isLoading}
                onChange={(v) => setField("test_type_id", v)}
              />

              <SelectWithOther
                label="Severity"
                fieldKey="severity_id"
                lookupType="severities"
                value={formData.severity_id}
                items={lookups?.severities ?? []}
                disabled={isLoading}
                createMetadata={{ severity_rank: 1 }}
                onChange={(v) => setField("severity_id", v)}
              />

              <SelectWithOther
                label="Threat"
                fieldKey="threat_id"
                lookupType="threats"
                value={formData.threat_id}
                items={lookups?.threats ?? []}
                disabled={isLoading}
                onChange={(v) => setField("threat_id", v)}
              />
            </div>
          </section>

          {/* ── Test Details and Analysis ─────────────────────────── */}
          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">Test Details and Analysis</h3>

            <TextFieldWithSuggestions
              label="Impact"
              fieldKey="impact"
              value={formData.impact}
              suggestions={[]}
              suggestionsLoading={false}
              disabled={isLoading}
              onChange={(v) => setField("impact", v)}
            />

            {(
              [
                ["description", "Description"],
                ["attack_path", "Attack Path"],
                ["test_steps", "Test Steps"],
                ["expected_output", "Expected Output"],
              ] as const
            ).map(([f, lbl]) => (
              <TextFieldWithSuggestions
                key={f}
                label={lbl}
                fieldKey={f}
                value={formData[f]}
                suggestions={suggestions?.[f] ?? []}
                suggestionsLoading={suggestionsLoading}
                disabled={isLoading}
                onChange={(v) => setField(f, v)}
              />
            ))}
          </section>

          {/* ── Risk and Feasibility ──────────────────────────────── */}
          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">Risk and Feasibility</h3>

            {(
              [
                ["attack_feasibility", "Attack Feasibility"],
                ["cia_impact", "CIA Impact"],
                ["safety_impact", "Safety Impact"],
              ] as const
            ).map(([f, lbl]) => (
              <TextFieldWithSuggestions
                key={f}
                label={lbl}
                fieldKey={f}
                value={formData[f]}
                suggestions={suggestions?.[f] ?? []}
                suggestionsLoading={suggestionsLoading}
                disabled={isLoading}
                onChange={(v) => setField(f, v)}
              />
            ))}
          </section>

          {/* ── Tools and References ─────────────────────────────── */}
          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">Tools and References</h3>
            <p className="text-xs text-muted-foreground">
              Check items to associate them. Check{" "}
              <strong>Other&hellip;</strong> to add a brand-new entry inline.
            </p>

            <div className="grid gap-6 md:grid-cols-2">
              <MultiSelectWithOther
                label="Tools"
                lookupType="tools"
                items={lookups?.tools ?? []}
                selected={formData.tool_ids}
                disabled={isLoading}
                onToggle={(id) => toggleListItem("tool_ids", id)}
                onNewItemCreated={(id) => addToList("tool_ids", id)}
              />
              <MultiSelectWithOther
                label="References"
                lookupType="references"
                items={lookups?.references ?? []}
                selected={formData.reference_ids}
                disabled={isLoading}
                onToggle={(id) => toggleListItem("reference_ids", id)}
                onNewItemCreated={(id) => addToList("reference_ids", id)}
              />
            </div>
          </section>
        </div>
      </div>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <div className="shrink-0 space-y-3 border-t bg-card p-4 sm:p-6">
        {(validationError || error) && (
          <div
            role="alert"
            className="flex gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive"
          >
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <span>{validationError || error}</span>
          </div>
        )}

        {!isFormValid && (
          <p className="text-xs text-muted-foreground">
            Complete Action/Test Case, Category, and Objective to enable the
            submit button.
          </p>
        )}

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading || !isFormValid}>
            {isLoading && <Loader2 className="animate-spin" />}
            {isLoading
              ? "Saving..."
              : testCase
                ? "Save Changes"
                : "Create Test Case"}
          </Button>
        </div>
      </div>
    </form>
  );
}
