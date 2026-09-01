"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Cpu,
  Hash,
  AlertTriangle,
  Layers,
  Truck,
  Calendar,
  Shield,
  Lock,
  Plus,
  Pencil,
  Check,
  Save,
} from "lucide-react";

import {
  createEcuDetail,
  getEcuDetail,
  updateEcuDetail,
  type EcuDetail,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface EcuDetailFormProps {
  projectId: number;
  onSuccess?: () => void;
}

type FormState = {
  ecu_name: string;
  part_number: string;
  ecu_risk_rating: string;
  architecture: string;
  vehicle_line: string;
  year: number;
  microcontroller_cpu_provider: string;
  date_hardware_b_sample_available: string;
  date_harness_available: string;
  date_production_intent_software_available: string;
  export_control_classification: string;
  pentest_provider_name: string;
};

const emptyForm: FormState = {
  ecu_name: "",
  part_number: "",
  ecu_risk_rating: "",
  architecture: "",
  vehicle_line: "",
  year: new Date().getFullYear(),
  microcontroller_cpu_provider: "",
  date_hardware_b_sample_available: "",
  date_harness_available: "",
  date_production_intent_software_available: "",
  export_control_classification: "",
  pentest_provider_name: "",
};

export function EcuDetailForm({ projectId, onSuccess }: EcuDetailFormProps) {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = React.useState(false);
  const [formData, setFormData] = React.useState<FormState>(emptyForm);

  const { data: existingDetail, isLoading: isLoadingDetail } = useQuery({
    queryKey: ["ecu-detail", projectId],
    queryFn: () => getEcuDetail(projectId),
    retry: false,
  });

  const toFormState = (detail: EcuDetail): FormState => ({
    ecu_name: detail.ecu_name,
    part_number: detail.part_number,
    ecu_risk_rating: detail.ecu_risk_rating,
    architecture: detail.architecture,
    vehicle_line: detail.vehicle_line,
    year: detail.year,
    microcontroller_cpu_provider: detail.microcontroller_cpu_provider,
    date_hardware_b_sample_available:
      detail.date_hardware_b_sample_available || "",
    date_harness_available: detail.date_harness_available || "",
    date_production_intent_software_available:
      detail.date_production_intent_software_available || "",
    export_control_classification: detail.export_control_classification,
    pentest_provider_name: detail.pentest_provider_name,
  });

  // Seed the form when opening, instead of syncing via an effect, so the
  // dialog always reflects the latest saved values without re-render loops.
  const openDialog = React.useCallback(() => {
    setFormData(existingDetail ? toFormState(existingDetail) : emptyForm);
    setIsOpen(true);
  }, [existingDetail]);

  const handleOpenChange = React.useCallback((next: boolean) => {
    if (!next) setFormData(emptyForm);
    setIsOpen(next);
  }, []);

  const createMutation = useMutation({
    mutationFn: () => createEcuDetail(projectId, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ecu-detail", projectId] });
      setIsOpen(false);
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => updateEcuDetail(projectId, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ecu-detail", projectId] });
      setIsOpen(false);
      onSuccess?.();
    },
  });

  const isLoading =
    createMutation.isPending || updateMutation.isPending || isLoadingDetail;
  const isError = createMutation.isError || updateMutation.isError;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (existingDetail) await updateMutation.mutateAsync();
    else await createMutation.mutateAsync();
  };

  const handleChange = (field: keyof FormState, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  if (isLoadingDetail) {
    return (
      <>
        <Card>
          <CardContent className="p-6">
            <div className="space-y-3">
              <div className="h-4 w-32 animate-pulse rounded bg-muted" />
              <div className="h-8 w-full animate-pulse rounded bg-muted" />
              <div className="h-8 w-2/3 animate-pulse rounded bg-muted" />
            </div>
          </CardContent>
        </Card>
        <EcuFormDialog
          open={isOpen}
          onOpenChange={handleOpenChange}
          formData={formData}
          onChange={handleChange}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          isError={isError}
          error={createMutation.error?.message || updateMutation.error?.message}
          isEditing={!!existingDetail}
        />
      </>
    );
  }

  if (!existingDetail) {
    return (
      <>
        <Card className="border-dashed bg-card/60">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex size-9 items-center justify-center rounded-md bg-accent text-accent-foreground">
                <Shield className="size-4" />
              </div>
              <div>
                <CardTitle className="text-base">ECU details</CardTitle>
                <CardDescription>
                  Add ECU specifications to start running security tests.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Button onClick={openDialog} className="w-full">
              <Plus />
              Add ECU details
            </Button>
          </CardContent>
        </Card>
        <EcuFormDialog
          open={isOpen}
          onOpenChange={handleOpenChange}
          formData={formData}
          onChange={handleChange}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          isError={isError}
          error={createMutation.error?.message || updateMutation.error?.message}
          isEditing={!!existingDetail}
        />
      </>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex size-9 items-center justify-center rounded-md bg-[var(--signal)]/15 text-[var(--signal)]">
                <Cpu className="size-4" />
              </div>
              <div>
                <CardTitle className="text-base font-semibold">
                  {existingDetail.ecu_name}
                </CardTitle>
                <CardDescription>ECU configuration</CardDescription>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={openDialog}>
              <Pencil className="size-3.5" />
              Edit
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <Field
              label="Part number"
              value={existingDetail.part_number}
              icon={Hash}
            />
            <Field
              label="Risk rating"
              value={existingDetail.ecu_risk_rating}
              icon={AlertTriangle}
            />
            <Field
              label="Architecture"
              value={existingDetail.architecture}
              icon={Layers}
            />
            <Field
              label="Vehicle line"
              value={existingDetail.vehicle_line}
              icon={Truck}
            />
            <Field
              label="Year"
              value={String(existingDetail.year)}
              icon={Calendar}
            />
            <Field
              label="CPU provider"
              value={existingDetail.microcontroller_cpu_provider}
              icon={Cpu}
            />
            <Field
              label="Export control"
              value={existingDetail.export_control_classification}
              icon={Lock}
            />
            <Field
              label="Pentest provider"
              value={existingDetail.pentest_provider_name}
              icon={Shield}
            />
          </div>

          <Separator />

          <div>
            <h4 className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <Calendar className="size-3.5" />
              Availability dates
            </h4>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <DateField
                label="Hardware B-sample"
                value={existingDetail.date_hardware_b_sample_available}
              />
              <DateField
                label="Harness"
                value={existingDetail.date_harness_available}
              />
              <DateField
                label="Production software"
                value={existingDetail.date_production_intent_software_available}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <EcuFormDialog
        open={isOpen}
        onOpenChange={handleOpenChange}
        formData={formData}
        onChange={handleChange}
        onSubmit={handleSubmit}
        isLoading={isLoading}
        isError={isError}
        error={createMutation.error?.message || updateMutation.error?.message}
        isEditing={!!existingDetail}
      />
    </>
  );
}

function Field({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-md border border-border/60 bg-card p-3">
      <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Icon className="size-3.5" />
        {label}
      </div>
      <div className="mt-1 text-sm font-medium text-foreground">{value}</div>
    </div>
  );
}

function DateField({ label, value }: { label: string; value?: string | null }) {
  if (!value) {
    return (
      <div className="rounded-md border border-dashed border-border/60 bg-card/50 p-3">
        <div className="text-xs font-medium text-muted-foreground">{label}</div>
        <div className="mt-1 text-sm text-muted-foreground">Not set</div>
      </div>
    );
  }
  return (
    <div className="rounded-md border border-border/60 bg-card p-3">
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm font-medium text-foreground font-tabular">
        {new Date(value).toLocaleDateString("en", {
          year: "numeric",
          month: "short",
          day: "numeric",
        })}
      </div>
    </div>
  );
}

function EcuFormDialog({
  open,
  onOpenChange,
  formData,
  onChange,
  onSubmit,
  isLoading,
  isError,
  error,
  isEditing,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  formData: FormState;
  onChange: (field: keyof FormState, value: string | number) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  isError: boolean;
  error?: string;
  isEditing: boolean;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[min(85vh,820px)] w-[min(1400px,calc(100vw-2rem))] max-w-none flex-col gap-0 overflow-hidden p-0 sm:max-w-none">
        <DialogHeader className="shrink-0 gap-2 border-b border-border/60 bg-card/50 p-6">
          <DialogTitle className="text-xl">
            {isEditing ? "Edit ECU details" : "Add ECU details"}
          </DialogTitle>
          <DialogDescription>
            Enter the hardware and program details for this project&apos;s ECU.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={onSubmit}
          className="flex min-h-0 flex-1 flex-col"
          id="ecu-form"
        >
          <ScrollArea className="min-h-0 flex-1">
            <div className="space-y-6 p-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3">
                <FormField id="ecu_name" label="ECU name" required>
                  <Input
                    id="ecu_name"
                    value={formData.ecu_name}
                    onChange={(e) => onChange("ecu_name", e.target.value)}
                    required
                    placeholder="e.g., Gateway ECU"
                  />
                </FormField>
                <FormField id="part_number" label="Part number" required>
                  <Input
                    id="part_number"
                    value={formData.part_number}
                    onChange={(e) => onChange("part_number", e.target.value)}
                    required
                    placeholder="e.g., PN-123456"
                  />
                </FormField>
                <FormField
                  id="ecu_risk_rating"
                  label="ECU risk rating"
                  required
                >
                  <Input
                    id="ecu_risk_rating"
                    value={formData.ecu_risk_rating}
                    onChange={(e) =>
                      onChange("ecu_risk_rating", e.target.value)
                    }
                    required
                    placeholder="e.g., High"
                  />
                </FormField>
                <FormField id="architecture" label="Architecture" required>
                  <Input
                    id="architecture"
                    value={formData.architecture}
                    onChange={(e) => onChange("architecture", e.target.value)}
                    required
                    placeholder="e.g., ARM Cortex-M4"
                  />
                </FormField>
                <FormField id="vehicle_line" label="Vehicle line" required>
                  <Input
                    id="vehicle_line"
                    value={formData.vehicle_line}
                    onChange={(e) => onChange("vehicle_line", e.target.value)}
                    required
                    placeholder="e.g., Sedan Series X"
                  />
                </FormField>
                <FormField id="year" label="Year" required>
                  <Input
                    id="year"
                    type="number"
                    value={formData.year}
                    onChange={(e) => onChange("year", parseInt(e.target.value))}
                    required
                    min={1900}
                    max={2100}
                  />
                </FormField>
                <FormField
                  id="microcontroller_cpu_provider"
                  label="Microcontroller / CPU provider"
                  required
                >
                  <Input
                    id="microcontroller_cpu_provider"
                    value={formData.microcontroller_cpu_provider}
                    onChange={(e) =>
                      onChange("microcontroller_cpu_provider", e.target.value)
                    }
                    required
                    placeholder="e.g., STMicroelectronics"
                  />
                </FormField>
                <FormField
                  id="export_control_classification"
                  label="Export control classification"
                  required
                >
                  <Input
                    id="export_control_classification"
                    value={formData.export_control_classification}
                    onChange={(e) =>
                      onChange("export_control_classification", e.target.value)
                    }
                    required
                    placeholder="e.g., EAR99"
                  />
                </FormField>
                <FormField
                  id="pentest_provider_name"
                  label="Pentest provider name"
                  required
                >
                  <Input
                    id="pentest_provider_name"
                    value={formData.pentest_provider_name}
                    onChange={(e) =>
                      onChange("pentest_provider_name", e.target.value)
                    }
                    required
                    placeholder="e.g., Security Firm XYZ"
                  />
                </FormField>
              </div>

              <div>
                <h4 className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <Calendar className="size-3.5" />
                  Availability dates
                </h4>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <FormField
                    id="date_hardware_b_sample_available"
                    label="Hardware B-sample"
                  >
                    <Input
                      id="date_hardware_b_sample_available"
                      type="date"
                      value={formData.date_hardware_b_sample_available}
                      onChange={(e) =>
                        onChange(
                          "date_hardware_b_sample_available",
                          e.target.value,
                        )
                      }
                    />
                  </FormField>
                  <FormField
                    id="date_harness_available"
                    label="Harness available"
                  >
                    <Input
                      id="date_harness_available"
                      type="date"
                      value={formData.date_harness_available}
                      onChange={(e) =>
                        onChange("date_harness_available", e.target.value)
                      }
                    />
                  </FormField>
                  <FormField
                    id="date_production_intent_software_available"
                    label="Production software"
                  >
                    <Input
                      id="date_production_intent_software_available"
                      type="date"
                      value={formData.date_production_intent_software_available}
                      onChange={(e) =>
                        onChange(
                          "date_production_intent_software_available",
                          e.target.value,
                        )
                      }
                    />
                  </FormField>
                </div>
              </div>
            </div>
          </ScrollArea>

          <div className="shrink-0 space-y-3 border-t border-border/60 bg-card/50 p-6">
            {isError && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <p>{error || "Something went wrong. Please try again."}</p>
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <>Saving…</>
                ) : isEditing ? (
                  <>
                    <Save />
                    Save changes
                  </>
                ) : (
                  <>
                    <Check />
                    Add details
                  </>
                )}
              </Button>
            </DialogFooter>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function FormField({
  id,
  label,
  required,
  children,
}: {
  id: string;
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-sm">
        {label}
        {required && <span className="ml-0.5 text-destructive">*</span>}
      </Label>
      {children}
    </div>
  );
}
