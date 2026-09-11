"use client";

import {
  useMemo,
  useState,
  type FormEvent,
} from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  Loader2,
} from "lucide-react";

import {
  getAdminLookups,
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


const NOT_SPECIFIED_VALUE =
  "__not_specified__";


interface TestCaseFormProps {
  testCase?: TestCase;

  onSubmit: (
    payload: TestCaseWritePayload,
  ) => Promise<void>;

  onCancel: () => void;
  isLoading?: boolean;
  error?: string | null;
}


interface FormData {
  action_test_case: string;
  category_id: string;
  objective_id: string;
  protocol_id: string;
  attack_vector_id: string;
  test_type_id: string;
  severity_id: string;
  threat_id: string;
  asset_id: string;
  source_scope_status: string;
  description: string;
  attack_path: string;
  test_steps: string;
  expected_output: string;
  attack_feasibility: string;
  cia_impact: string;
  safety_impact: string;
  automation_possible: string;
  tool_ids: number[];
  reference_ids: number[];
}


function initialFormData(
  testCase?: TestCase,
): FormData {
  return {
    action_test_case:
      testCase?.action_test_case ?? "",

    category_id:
      testCase !== undefined
        ? String(testCase.category_id)
        : "",

    objective_id:
      testCase !== undefined
        ? String(testCase.objective_id)
        : "",

    protocol_id:
      testCase?.protocol_id !== null &&
        testCase?.protocol_id !== undefined
        ? String(testCase.protocol_id)
        : "",

    attack_vector_id:
      testCase?.attack_vector_id !== null &&
        testCase?.attack_vector_id !== undefined
        ? String(
          testCase.attack_vector_id,
        )
        : "",

    test_type_id:
      testCase?.test_type_id !== null &&
        testCase?.test_type_id !== undefined
        ? String(testCase.test_type_id)
        : "",

    severity_id:
      testCase?.severity_id !== null &&
        testCase?.severity_id !== undefined
        ? String(testCase.severity_id)
        : "",

    threat_id:
      testCase?.threat_id !== null &&
        testCase?.threat_id !== undefined
        ? String(testCase.threat_id)
        : "",

    asset_id:
      testCase?.asset_id !== null &&
        testCase?.asset_id !== undefined
        ? String(testCase.asset_id)
        : "",

    source_scope_status:
      testCase?.source_scope_status ?? "",

    description:
      testCase?.description ?? "",

    attack_path:
      testCase?.attack_path ?? "",

    test_steps:
      testCase?.test_steps ?? "",

    expected_output:
      testCase?.expected_output ?? "",

    attack_feasibility:
      testCase?.attack_feasibility ?? "",

    cia_impact:
      testCase?.cia_impact ?? "",

    safety_impact:
      testCase?.safety_impact ?? "",

    automation_possible:
      testCase?.automation_possible ?? "",

    tool_ids:
      testCase?.test_case_tools.map(
        (item) => item.tool.id,
      ) ?? [],

    reference_ids:
      testCase?.test_case_references.map(
        (item) => item.reference.id,
      ) ?? [],
  };
}


function optionalId(
  value: string,
): number | null {
  if (!value) {
    return null;
  }

  const parsedValue = Number(value);

  return Number.isFinite(parsedValue)
    ? parsedValue
    : null;
}


function optionalText(
  value: string,
): string | null {
  const trimmedValue = value.trim();

  return trimmedValue || null;
}


function MultiSelectList({
  label,
  items,
  selected,
  onToggle,
  disabled = false,
}: {
  label: string;
  items: LookupItem[];
  selected: number[];
  onToggle: (id: number) => void;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>

      <div className="max-h-44 space-y-1 overflow-y-auto rounded-md border p-2">
        {items.length === 0 ? (
          <p className="p-2 text-xs text-muted-foreground">
            No options available.
          </p>
        ) : (
          items.map((item) => {
            const checked =
              selected.includes(item.id);

            return (
              <label
                key={item.id}
                className={[
                  "flex items-start gap-2 rounded-md p-2 text-sm",
                  disabled
                    ? "cursor-not-allowed opacity-60"
                    : "cursor-pointer hover:bg-muted",
                ].join(" ")}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={disabled}
                  onChange={() => {
                    if (!disabled) {
                      onToggle(item.id);
                    }
                  }}
                  className="mt-0.5 size-4"
                />

                <span className="break-words">
                  {item.name}
                </span>
              </label>
            );
          })
        )}
      </div>
    </div>
  );
}


export function TestCaseForm({
  testCase,
  onSubmit,
  onCancel,
  isLoading = false,
  error,
}: TestCaseFormProps) {
  const [
    formData,
    setFormData,
  ] = useState<FormData>(() =>
    initialFormData(testCase),
  );

  const [
    validationError,
    setValidationError,
  ] = useState<string | null>(null);

  const {
    data: lookups,
    isLoading: lookupsLoading,
    isError: lookupsError,
    error: lookupError,
  } = useQuery({
    queryKey: [
      "admin",
      "test-case-lookups",
    ],
    queryFn: getAdminLookups,
  });

  const selectedCategoryIdStr = formData.category_id;

  const objectives = useMemo(
    () =>
      (lookups?.objectives ?? []).filter(
        (objective) =>
          selectedCategoryIdStr !== "" &&
          String(objective.category_id) === selectedCategoryIdStr,
      ),
    [
      lookups?.objectives,
      selectedCategoryIdStr,
    ],
  );

  const isFormValid =
    formData.action_test_case
      .trim()
      .length > 0 &&
    formData.category_id.length > 0 &&
    formData.objective_id.length > 0;

  const setField = (
    field: keyof FormData,
    value: string | number[],
  ) => {
    setValidationError(null);

    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const toggleListItem = (
    field:
      | "tool_ids"
      | "reference_ids",
    id: number,
  ) => {
    setValidationError(null);

    setFormData((previous) => {
      const current = previous[field];

      return {
        ...previous,
        [field]: current.includes(id)
          ? current.filter(
            (item) => item !== id,
          )
          : [
            ...current,
            id,
          ],
      };
    });
  };

  const handleCategoryChange = (
    value: string,
  ) => {
    setValidationError(null);

    setFormData((previous) => ({
      ...previous,
      category_id: value,
      objective_id: "",
    }));
  };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setValidationError(null);

    const actionTestCase =
      formData.action_test_case.trim();

    if (!actionTestCase) {
      setValidationError(
        "Action/Test Case is required.",
      );
      return;
    }

    if (!formData.category_id) {
      setValidationError(
        "Category is required.",
      );
      return;
    }

    if (!formData.objective_id) {
      setValidationError(
        "Objective is required.",
      );
      return;
    }

    const categoryId = Number(
      formData.category_id,
    );

    const objectiveId = Number(
      formData.objective_id,
    );

    if (
      !Number.isFinite(categoryId) ||
      categoryId <= 0
    ) {
      setValidationError(
        "Please select a valid category.",
      );
      return;
    }

    if (
      !Number.isFinite(objectiveId) ||
      objectiveId <= 0
    ) {
      setValidationError(
        "Please select a valid objective.",
      );
      return;
    }

    // Verify the chosen objective exists in the filtered list (string comparison
    // avoids BigInt-to-float precision loss for very large IDs).
    const selectedObjective = objectives.find(
      (objective) => String(objective.id) === String(objectiveId),
    );

    if (!selectedObjective) {
      setValidationError(
        "Please re-select the objective — it may not match the chosen category.",
      );
      return;
    }

    const automation =
      formData.automation_possible;

    const payload: TestCaseWritePayload = {
      action_test_case:
        actionTestCase,

      category_id:
        categoryId,

      objective_id:
        objectiveId,

      protocol_id: optionalId(
        formData.protocol_id,
      ),

      attack_vector_id: optionalId(
        formData.attack_vector_id,
      ),

      test_type_id: optionalId(
        formData.test_type_id,
      ),

      severity_id: optionalId(
        formData.severity_id,
      ),

      threat_id: optionalId(
        formData.threat_id,
      ),

      asset_id: optionalId(
        formData.asset_id,
      ),

      source_scope_status:
        optionalText(
          formData.source_scope_status,
        ),

      description: optionalText(
        formData.description,
      ),

      attack_path: optionalText(
        formData.attack_path,
      ),

      test_steps: optionalText(
        formData.test_steps,
      ),

      expected_output: optionalText(
        formData.expected_output,
      ),

      attack_feasibility:
        optionalText(
          formData.attack_feasibility,
        ),

      cia_impact: optionalText(
        formData.cia_impact,
      ),

      safety_impact: optionalText(
        formData.safety_impact,
      ),

      automation_possible:
        automation === "Yes" ||
          automation === "No" ||
          automation === "Partial"
          ? automation
          : null,

      tool_ids: [
        ...new Set(
          formData.tool_ids,
        ),
      ].sort(
        (first, second) =>
          first - second,
      ),

      reference_ids: [
        ...new Set(
          formData.reference_ids,
        ),
      ].sort(
        (first, second) =>
          first - second,
      ),
    };

    try {
      await onSubmit(payload);
    } catch {
      /*
       * The parent React Query mutation exposes
       * the backend error through the error prop.
       */
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
          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">
              Required Fields
            </h3>

            <div className="space-y-2">
              <Label htmlFor="action_test_case">
                Action/Test Case
                <span className="text-destructive">
                  {" "}
                  *
                </span>
              </Label>

              <Textarea
                id="action_test_case"
                value={
                  formData.action_test_case
                }
                onChange={(event) =>
                  setField(
                    "action_test_case",
                    event.target.value,
                  )
                }
                disabled={isLoading}
                required
                aria-required="true"
                className="min-h-28"
                placeholder="Enter the security action or test case."
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="category_id">
                  Category
                  <span className="text-destructive">
                    {" "}
                    *
                  </span>
                </Label>

                <Select
                  value={
                    formData.category_id
                  }
                  onValueChange={
                    handleCategoryChange
                  }
                  disabled={isLoading}
                  required
                >
                  <SelectTrigger
                    id="category_id"
                    className="w-full"
                    aria-required="true"
                  >
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>

                  <SelectContent>
                    {(lookups?.categories ?? []).map(
                      (item) => (
                        <SelectItem
                          key={item.id}
                          value={String(
                            item.id,
                          )}
                        >
                          {item.name}
                        </SelectItem>
                      ),
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="objective_id">
                  Objective
                  <span className="text-destructive">
                    {" "}
                    *
                  </span>
                </Label>

                <Select
                  value={
                    formData.objective_id
                  }
                  onValueChange={(value) =>
                    setField(
                      "objective_id",
                      value,
                    )
                  }
                  disabled={
                    isLoading ||
                    !formData.category_id
                  }
                  required
                >
                  <SelectTrigger
                    id="objective_id"
                    className="w-full"
                    aria-required="true"
                  >
                    <SelectValue
                      placeholder={
                        formData.category_id
                          ? "Select objective"
                          : "Select category first"
                      }
                    />
                  </SelectTrigger>

                  <SelectContent>
                    {objectives.length === 0 ? (
                      <div className="px-2 py-3 text-sm text-muted-foreground">
                        No objectives are available
                        for this category.
                      </div>
                    ) : (
                      objectives.map(
                        (item) => (
                          <SelectItem
                            key={item.id}
                            value={String(
                              item.id,
                            )}
                          >
                            {item.name}
                          </SelectItem>
                        ),
                      )
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </section>

          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">
              Test Classification
            </h3>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <LookupSelect
                label="Protocol"
                value={
                  formData.protocol_id
                }
                items={
                  lookups?.protocols ?? []
                }
                disabled={isLoading}
                onChange={(value) =>
                  setField(
                    "protocol_id",
                    value,
                  )
                }
              />

              <LookupSelect
                label="Attack Vector"
                value={
                  formData.attack_vector_id
                }
                items={
                  lookups?.attack_vectors ??
                  []
                }
                disabled={isLoading}
                onChange={(value) =>
                  setField(
                    "attack_vector_id",
                    value,
                  )
                }
              />

              <LookupSelect
                label="Test Type"
                value={
                  formData.test_type_id
                }
                items={
                  lookups?.test_types ?? []
                }
                disabled={isLoading}
                onChange={(value) =>
                  setField(
                    "test_type_id",
                    value,
                  )
                }
              />

              <LookupSelect
                label="Severity"
                value={
                  formData.severity_id
                }
                items={
                  lookups?.severities ?? []
                }
                disabled={isLoading}
                onChange={(value) =>
                  setField(
                    "severity_id",
                    value,
                  )
                }
              />

              <LookupSelect
                label="Threat"
                value={
                  formData.threat_id
                }
                items={
                  lookups?.threats ?? []
                }
                disabled={isLoading}
                onChange={(value) =>
                  setField(
                    "threat_id",
                    value,
                  )
                }
              />

              <LookupSelect
                label="Asset"
                value={
                  formData.asset_id
                }
                items={
                  lookups?.assets ?? []
                }
                disabled={isLoading}
                onChange={(value) =>
                  setField(
                    "asset_id",
                    value,
                  )
                }
              />
            </div>
          </section>

          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">
              Test Details and Analysis
            </h3>

            <TextField
              label="Description"
              value={
                formData.description
              }
              disabled={isLoading}
              onChange={(value) =>
                setField(
                  "description",
                  value,
                )
              }
            />

            <TextField
              label="Attack Path"
              value={
                formData.attack_path
              }
              disabled={isLoading}
              onChange={(value) =>
                setField(
                  "attack_path",
                  value,
                )
              }
            />

            <TextField
              label="Test Steps"
              value={
                formData.test_steps
              }
              disabled={isLoading}
              onChange={(value) =>
                setField(
                  "test_steps",
                  value,
                )
              }
            />

            <TextField
              label="Expected Output"
              value={
                formData.expected_output
              }
              disabled={isLoading}
              onChange={(value) =>
                setField(
                  "expected_output",
                  value,
                )
              }
            />
          </section>

          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">
              Risk and Feasibility
            </h3>

            <TextField
              label="Attack Feasibility"
              value={
                formData.attack_feasibility
              }
              disabled={isLoading}
              onChange={(value) =>
                setField(
                  "attack_feasibility",
                  value,
                )
              }
            />

            <TextField
              label="CIA Impact"
              value={
                formData.cia_impact
              }
              disabled={isLoading}
              onChange={(value) =>
                setField(
                  "cia_impact",
                  value,
                )
              }
            />

            <TextField
              label="Safety Impact"
              value={
                formData.safety_impact
              }
              disabled={isLoading}
              onChange={(value) =>
                setField(
                  "safety_impact",
                  value,
                )
              }
            />

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="automation_possible">
                  Automation Possible
                </Label>

                <Select
                  value={
                    formData
                      .automation_possible ||
                    NOT_SPECIFIED_VALUE
                  }
                  disabled={isLoading}
                  onValueChange={(value) =>
                    setField(
                      "automation_possible",
                      value ===
                        NOT_SPECIFIED_VALUE
                        ? ""
                        : value,
                    )
                  }
                >
                  <SelectTrigger
                    id="automation_possible"
                    className="w-full"
                  >
                    <SelectValue placeholder="Select option" />
                  </SelectTrigger>

                  <SelectContent>
                    <SelectItem
                      value={
                        NOT_SPECIFIED_VALUE
                      }
                    >
                      Not specified
                    </SelectItem>

                    <SelectItem value="Yes">
                      Yes
                    </SelectItem>

                    <SelectItem value="No">
                      No
                    </SelectItem>

                    <SelectItem value="Partial">
                      Partial
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="source_scope_status">
                  Source Scope Status
                </Label>

                <Input
                  id="source_scope_status"
                  value={
                    formData
                      .source_scope_status
                  }
                  disabled={isLoading}
                  onChange={(event) =>
                    setField(
                      "source_scope_status",
                      event.target.value,
                    )
                  }
                  maxLength={100}
                  placeholder="Enter source or scope status."
                />
              </div>
            </div>
          </section>

          <section className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">
              Tools and References
            </h3>

            <div className="grid gap-6 md:grid-cols-2">
              <MultiSelectList
                label="Tools"
                items={
                  lookups?.tools ?? []
                }
                selected={
                  formData.tool_ids
                }
                disabled={isLoading}
                onToggle={(id) =>
                  toggleListItem(
                    "tool_ids",
                    id,
                  )
                }
              />

              <MultiSelectList
                label="References"
                items={
                  lookups?.references ?? []
                }
                selected={
                  formData.reference_ids
                }
                disabled={isLoading}
                onToggle={(id) =>
                  toggleListItem(
                    "reference_ids",
                    id,
                  )
                }
              />
            </div>
          </section>
        </div>
      </div>

      <div className="shrink-0 space-y-3 border-t bg-card p-4 sm:p-6">
        {(validationError || error) && (
          <div
            role="alert"
            className="flex gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive"
          >
            <AlertCircle className="mt-0.5 size-4 shrink-0" />

            <span>
              {validationError || error}
            </span>
          </div>
        )}

        {!isFormValid && (
          <p className="text-xs text-muted-foreground">
            Complete Action/Test Case,
            Category, and Objective to enable
            the submit button.
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

          <Button
            type="submit"
            disabled={
              isLoading ||
              !isFormValid
            }
          >
            {isLoading && (
              <Loader2 className="animate-spin" />
            )}

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


function LookupSelect({
  label,
  value,
  items,
  onChange,
  disabled = false,
}: {
  label: string;
  value: string;
  items: LookupItem[];
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const fieldId = label
    .toLowerCase()
    .replaceAll(" ", "_");

  return (
    <div className="space-y-2">
      <Label htmlFor={fieldId}>
        {label}
      </Label>

      <Select
        value={
          value ||
          NOT_SPECIFIED_VALUE
        }
        disabled={disabled}
        onValueChange={(selectedValue) => {
          onChange(
            selectedValue ===
              NOT_SPECIFIED_VALUE
              ? ""
              : selectedValue,
          );
        }}
      >
        <SelectTrigger
          id={fieldId}
          className="w-full"
        >
          <SelectValue
            placeholder={`Select ${label.toLowerCase()}`}
          />
        </SelectTrigger>

        <SelectContent>
          <SelectItem
            value={
              NOT_SPECIFIED_VALUE
            }
          >
            Not specified
          </SelectItem>

          {items.map((item) => (
            <SelectItem
              key={item.id}
              value={String(item.id)}
            >
              {item.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}


function TextField({
  label,
  value,
  onChange,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const id = label
    .toLowerCase()
    .replaceAll(" ", "_");

  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {label}
      </Label>

      <Textarea
        id={id}
        value={value}
        disabled={disabled}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className="min-h-20"
      />
    </div>
  );
}