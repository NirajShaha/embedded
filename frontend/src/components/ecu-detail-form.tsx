"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Plus,
  Cpu,
  Hash,
  AlertTriangle,
  Layers,
  Truck,
  Calendar,
  Shield,
  Lock,
  CheckSquare,
  Zap,
  Edit2,
} from "lucide-react";

import { createEcuDetail, getEcuDetail, updateEcuDetail } from "@/lib/api";
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
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface EcuDetailFormProps {
  projectId: number;
  onSuccess?: () => void;
}

export function EcuDetailForm({ projectId, onSuccess }: EcuDetailFormProps) {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = React.useState(false);

  const { data: existingDetail, isLoading: isLoadingDetail } = useQuery({
    queryKey: ["ecu-detail", projectId],
    queryFn: () => getEcuDetail(projectId),
    retry: false,
  });

  const [formData, setFormData] = React.useState({
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
  });

  // Load existing data if available
  React.useEffect(() => {
    if (existingDetail) {
      setFormData({
        ecu_name: existingDetail.ecu_name,
        part_number: existingDetail.part_number,
        ecu_risk_rating: existingDetail.ecu_risk_rating,
        architecture: existingDetail.architecture,
        vehicle_line: existingDetail.vehicle_line,
        year: existingDetail.year,
        microcontroller_cpu_provider:
          existingDetail.microcontroller_cpu_provider,
        date_hardware_b_sample_available:
          existingDetail.date_hardware_b_sample_available || "",
        date_harness_available: existingDetail.date_harness_available || "",
        date_production_intent_software_available:
          existingDetail.date_production_intent_software_available || "",
        export_control_classification:
          existingDetail.export_control_classification,
        pentest_provider_name: existingDetail.pentest_provider_name,
      });
    }
  }, [existingDetail]);

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
    if (existingDetail) {
      await updateMutation.mutateAsync();
    } else {
      await createMutation.mutateAsync();
    }
  };

  const handleChange = (field: string, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  if (!isOpen && !existingDetail && !isLoadingDetail) {
    return (
      <Card className="border-2 border-dashed border-blue-300 dark:border-blue-700 bg-gradient-to-br from-blue-50 to-blue-50/50 dark:from-blue-950/20 dark:to-blue-950/10">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <div>
              <CardTitle>ECU Details</CardTitle>
              <CardDescription>
                Add ECU specifications for this project
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Button
            onClick={() => setIsOpen(true)}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white"
          >
            <Plus className="mr-2 h-4 w-4" />
            Add ECU Details
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      {existingDetail && !isOpen && (
        <Card className="border-l-4 border-l-green-500 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 bg-gradient-to-r from-green-50 to-green-50/50 dark:from-green-950/20 dark:to-green-950/10">
            <div className="flex items-start gap-3">
              <Cpu className="h-5 w-5 text-green-600 dark:text-green-400 mt-1" />
              <div>
                <CardTitle className="text-lg">
                  {existingDetail.ecu_name}
                </CardTitle>
                <CardDescription className="mt-1">
                  ECU Configuration
                </CardDescription>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsOpen(true)}
              className="border-green-300 dark:border-green-700 hover:bg-green-50 dark:hover:bg-green-950/30"
            >
              <Edit2 className="mr-2 h-4 w-4" />
              Edit
            </Button>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            {/* Row 1: Part Number & Risk Rating */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-purple-50 dark:bg-purple-950/20 border-l-4 border-purple-500 p-3 rounded-r-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Hash className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  <p className="text-xs font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wide">
                    Part Number
                  </p>
                </div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {existingDetail.part_number}
                </p>
              </div>
              <div className="bg-red-50 dark:bg-red-950/20 border-l-4 border-red-500 p-3 rounded-r-lg">
                <div className="flex items-center gap-2 mb-1">
                  <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
                  <p className="text-xs font-semibold text-red-600 dark:text-red-400 uppercase tracking-wide">
                    Risk Rating
                  </p>
                </div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {existingDetail.ecu_risk_rating}
                </p>
              </div>
            </div>

            {/* Row 2: Architecture & Vehicle Line */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 dark:bg-blue-950/20 border-l-4 border-blue-500 p-3 rounded-r-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Layers className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wide">
                    Architecture
                  </p>
                </div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {existingDetail.architecture}
                </p>
              </div>
              <div className="bg-indigo-50 dark:bg-indigo-950/20 border-l-4 border-indigo-500 p-3 rounded-r-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Truck className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wide">
                    Vehicle Line
                  </p>
                </div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {existingDetail.vehicle_line}
                </p>
              </div>
            </div>

            {/* Row 3: Year & CPU Provider */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-orange-50 dark:bg-orange-950/20 border-l-4 border-orange-500 p-3 rounded-r-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Calendar className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                  <p className="text-xs font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-wide">
                    Year
                  </p>
                </div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {existingDetail.year}
                </p>
              </div>
              <div className="bg-cyan-50 dark:bg-cyan-950/20 border-l-4 border-cyan-500 p-3 rounded-r-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Cpu className="h-4 w-4 text-cyan-600 dark:text-cyan-400" />
                  <p className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 uppercase tracking-wide">
                    CPU Provider
                  </p>
                </div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {existingDetail.microcontroller_cpu_provider}
                </p>
              </div>
            </div>

            {/* Row 4: Export Control & Pentest Provider */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-green-50 dark:bg-green-950/20 border-l-4 border-green-500 p-3 rounded-r-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Lock className="h-4 w-4 text-green-600 dark:text-green-400" />
                  <p className="text-xs font-semibold text-green-600 dark:text-green-400 uppercase tracking-wide">
                    Export Control
                  </p>
                </div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {existingDetail.export_control_classification}
                </p>
              </div>
              <div className="bg-pink-50 dark:bg-pink-950/20 border-l-4 border-pink-500 p-3 rounded-r-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Shield className="h-4 w-4 text-pink-600 dark:text-pink-400" />
                  <p className="text-xs font-semibold text-pink-600 dark:text-pink-400 uppercase tracking-wide">
                    Pentest Provider
                  </p>
                </div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {existingDetail.pentest_provider_name}
                </p>
              </div>
            </div>

            {/* Dates Section */}
            <div className="bg-slate-100 dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 space-y-3 mt-4">
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Availability Dates
              </p>
              <div className="grid grid-cols-3 gap-3 text-sm">
                {existingDetail.date_hardware_b_sample_available && (
                  <div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 font-medium mb-1">
                      Hardware B-Sample
                    </p>
                    <p className="text-slate-900 dark:text-slate-100 font-medium">
                      {existingDetail.date_hardware_b_sample_available}
                    </p>
                  </div>
                )}
                {existingDetail.date_harness_available && (
                  <div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 font-medium mb-1">
                      Harness Available
                    </p>
                    <p className="text-slate-900 dark:text-slate-100 font-medium">
                      {existingDetail.date_harness_available}
                    </p>
                  </div>
                )}
                {existingDetail.date_production_intent_software_available && (
                  <div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 font-medium mb-1">
                      Production Software
                    </p>
                    <p className="text-slate-900 dark:text-slate-100 font-medium">
                      {existingDetail.date_production_intent_software_available}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
        <AlertDialogContent className="max-h-screen max-w-2xl overflow-y-auto">
          <AlertDialogTitle>
            {existingDetail ? "Edit ECU Details" : "Add ECU Details"}
          </AlertDialogTitle>
          <AlertDialogDescription>
            Enter detailed information about the ECU for this project.
          </AlertDialogDescription>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {/* ECU Name */}
              <div className="space-y-2">
                <Label htmlFor="ecu_name">ECU Name *</Label>
                <Input
                  id="ecu_name"
                  value={formData.ecu_name}
                  onChange={(e) => handleChange("ecu_name", e.target.value)}
                  required
                  placeholder="e.g., Gateway ECU"
                />
              </div>

              {/* Part Number */}
              <div className="space-y-2">
                <Label htmlFor="part_number">Part Number *</Label>
                <Input
                  id="part_number"
                  value={formData.part_number}
                  onChange={(e) => handleChange("part_number", e.target.value)}
                  required
                  placeholder="e.g., PN-123456"
                />
              </div>

              {/* ECU Risk Rating */}
              <div className="space-y-2">
                <Label htmlFor="ecu_risk_rating">ECU Risk Rating *</Label>
                <Input
                  id="ecu_risk_rating"
                  value={formData.ecu_risk_rating}
                  onChange={(e) =>
                    handleChange("ecu_risk_rating", e.target.value)
                  }
                  required
                  placeholder="e.g., High"
                />
              </div>

              {/* Architecture */}
              <div className="space-y-2">
                <Label htmlFor="architecture">Architecture *</Label>
                <Input
                  id="architecture"
                  value={formData.architecture}
                  onChange={(e) => handleChange("architecture", e.target.value)}
                  required
                  placeholder="e.g., ARM Cortex-M4"
                />
              </div>

              {/* Vehicle Line */}
              <div className="space-y-2">
                <Label htmlFor="vehicle_line">Vehicle Line *</Label>
                <Input
                  id="vehicle_line"
                  value={formData.vehicle_line}
                  onChange={(e) => handleChange("vehicle_line", e.target.value)}
                  required
                  placeholder="e.g., Sedan Series X"
                />
              </div>

              {/* Year */}
              <div className="space-y-2">
                <Label htmlFor="year">Year *</Label>
                <Input
                  id="year"
                  type="number"
                  value={formData.year}
                  onChange={(e) =>
                    handleChange("year", parseInt(e.target.value))
                  }
                  required
                  min={1900}
                  max={2100}
                />
              </div>

              {/* Microcontroller/CPU Provider */}
              <div className="space-y-2">
                <Label htmlFor="microcontroller_cpu_provider">
                  Microcontroller/CPU Provider *
                </Label>
                <Input
                  id="microcontroller_cpu_provider"
                  value={formData.microcontroller_cpu_provider}
                  onChange={(e) =>
                    handleChange("microcontroller_cpu_provider", e.target.value)
                  }
                  required
                  placeholder="e.g., STMicroelectronics"
                />
              </div>

              {/* Export Control Classification */}
              <div className="space-y-2">
                <Label htmlFor="export_control_classification">
                  Export Control Classification *
                </Label>
                <Input
                  id="export_control_classification"
                  value={formData.export_control_classification}
                  onChange={(e) =>
                    handleChange(
                      "export_control_classification",
                      e.target.value,
                    )
                  }
                  required
                  placeholder="e.g., EAR99"
                />
              </div>

              {/* Pentest Provider Name */}
              <div className="space-y-2">
                <Label htmlFor="pentest_provider_name">
                  Pentest Provider Name *
                </Label>
                <Input
                  id="pentest_provider_name"
                  value={formData.pentest_provider_name}
                  onChange={(e) =>
                    handleChange("pentest_provider_name", e.target.value)
                  }
                  required
                  placeholder="e.g., Security Firm XYZ"
                />
              </div>

              {/* Date Hardware B-Sample Available */}
              <div className="space-y-2">
                <Label htmlFor="date_hardware_b_sample_available">
                  Date Hardware B-Sample Available
                </Label>
                <Input
                  id="date_hardware_b_sample_available"
                  type="date"
                  value={formData.date_hardware_b_sample_available}
                  onChange={(e) =>
                    handleChange(
                      "date_hardware_b_sample_available",
                      e.target.value,
                    )
                  }
                />
              </div>

              {/* Date Harness Available */}
              <div className="space-y-2">
                <Label htmlFor="date_harness_available">
                  Date Harness Available
                </Label>
                <Input
                  id="date_harness_available"
                  type="date"
                  value={formData.date_harness_available}
                  onChange={(e) =>
                    handleChange("date_harness_available", e.target.value)
                  }
                />
              </div>

              {/* Date Production-Intent Software Available */}
              <div className="space-y-2">
                <Label htmlFor="date_production_intent_software_available">
                  Date Production-Intent Software Available
                </Label>
                <Input
                  id="date_production_intent_software_available"
                  type="date"
                  value={formData.date_production_intent_software_available}
                  onChange={(e) =>
                    handleChange(
                      "date_production_intent_software_available",
                      e.target.value,
                    )
                  }
                />
              </div>
            </div>

            {isError && (
              <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-destructive">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <p className="text-sm">
                  {createMutation.error?.message ||
                    updateMutation.error?.message}
                </p>
              </div>
            )}

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsOpen(false)}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading
                  ? "Saving..."
                  : existingDetail
                    ? "Update Details"
                    : "Add Details"}
              </Button>
            </div>
          </form>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
