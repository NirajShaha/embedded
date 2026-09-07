"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2 } from "lucide-react";

interface TestCaseFormProps {
  testCase?: unknown;
  onSubmit: (data: unknown) => Promise<void>;
  isLoading?: boolean;
}

interface SelectOption {
  id: number;
  name: string;
}

export function TestCaseForm({ testCase, onSubmit, isLoading = false }: TestCaseFormProps) {
  const [formData, setFormData] = useState({
    action_test_case: "",
    category_id: "",
    objective_id: "",
    protocol_id: "",
    attack_vector_id: "",
    test_type_id: "",
    severity_id: "",
    threat_id: "",
    asset_id: "",
    source_scope_status: "",
    description: "",
    attack_path: "",
    test_steps: "",
    expected_output: "",
    attack_feasibility: "",
    cia_impact: "",
    safety_impact: "",
    automation_possible: "",
  });

  // Fetch dropdown options
  const { data: categories = [] } = useQuery({
    queryKey: ["test-cases", "categories"],
    queryFn: async () => {
      // Placeholder - will be real API call later
      return [] as SelectOption[];
    },
  });

  const { data: objectives = [] } = useQuery({
    queryKey: ["test-cases", "objectives"],
    queryFn: async () => {
      return [] as SelectOption[];
    },
  });

  const { data: protocols = [] } = useQuery({
    queryKey: ["test-cases", "protocols"],
    queryFn: async () => {
      return [] as SelectOption[];
    },
  });

  const { data: attackVectors = [] } = useQuery({
    queryKey: ["test-cases", "attack-vectors"],
    queryFn: async () => {
      return [] as SelectOption[];
    },
  });

  const { data: testTypes = [] } = useQuery({
    queryKey: ["test-cases", "test-types"],
    queryFn: async () => {
      return [] as SelectOption[];
    },
  });

  const { data: severities = [] } = useQuery({
    queryKey: ["test-cases", "severities"],
    queryFn: async () => {
      return [] as SelectOption[];
    },
  });

  const { data: threats = [] } = useQuery({
    queryKey: ["test-cases", "threats"],
    queryFn: async () => {
      return [] as SelectOption[];
    },
  });

  const { data: assets = [] } = useQuery({
    queryKey: ["test-cases", "assets"],
    queryFn: async () => {
      return [] as SelectOption[];
    },
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <ScrollArea className="h-full">
      <form onSubmit={handleSubmit} className="space-y-6 pr-4">
        {/* Primary Fields - Required */}
        <div className="space-y-4 rounded-lg border border-border/60 bg-card/50 p-4">
          <h3 className="font-semibold text-sm">Required Fields</h3>

          <div className="space-y-2">
            <Label htmlFor="action_test_case">
              Action/Test Case <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="action_test_case"
              name="action_test_case"
              placeholder="Describe the action or test case..."
              value={formData.action_test_case}
              onChange={handleChange}
              required
              className="min-h-24"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="category_id">
                Category <span className="text-destructive">*</span>
              </Label>
              <Select value={formData.category_id} onValueChange={(val) => handleSelectChange("category_id", val)}>
                <SelectTrigger id="category_id">
                  <SelectValue placeholder="Select category..." />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={String(cat.id)}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="objective_id">
                Objective <span className="text-destructive">*</span>
              </Label>
              <Select value={formData.objective_id} onValueChange={(val) => handleSelectChange("objective_id", val)}>
                <SelectTrigger id="objective_id">
                  <SelectValue placeholder="Select objective..." />
                </SelectTrigger>
                <SelectContent>
                  {objectives.map((obj) => (
                    <SelectItem key={obj.id} value={String(obj.id)}>
                      {obj.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Optional Fields - Related Resources */}
        <div className="space-y-4 rounded-lg border border-border/60 bg-card/50 p-4">
          <h3 className="font-semibold text-sm">Related Resources (Optional)</h3>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="protocol_id">Protocol</Label>
              <Select value={formData.protocol_id} onValueChange={(val) => handleSelectChange("protocol_id", val)}>
                <SelectTrigger id="protocol_id">
                  <SelectValue placeholder="Select protocol..." />
                </SelectTrigger>
                <SelectContent>
                  {protocols.map((proto) => (
                    <SelectItem key={proto.id} value={String(proto.id)}>
                      {proto.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="attack_vector_id">Attack Vector</Label>
              <Select value={formData.attack_vector_id} onValueChange={(val) => handleSelectChange("attack_vector_id", val)}>
                <SelectTrigger id="attack_vector_id">
                  <SelectValue placeholder="Select attack vector..." />
                </SelectTrigger>
                <SelectContent>
                  {attackVectors.map((av) => (
                    <SelectItem key={av.id} value={String(av.id)}>
                      {av.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="test_type_id">Test Type</Label>
              <Select value={formData.test_type_id} onValueChange={(val) => handleSelectChange("test_type_id", val)}>
                <SelectTrigger id="test_type_id">
                  <SelectValue placeholder="Select test type..." />
                </SelectTrigger>
                <SelectContent>
                  {testTypes.map((tt) => (
                    <SelectItem key={tt.id} value={String(tt.id)}>
                      {tt.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="severity_id">Severity</Label>
              <Select value={formData.severity_id} onValueChange={(val) => handleSelectChange("severity_id", val)}>
                <SelectTrigger id="severity_id">
                  <SelectValue placeholder="Select severity..." />
                </SelectTrigger>
                <SelectContent>
                  {severities.map((sev) => (
                    <SelectItem key={sev.id} value={String(sev.id)}>
                      {sev.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="threat_id">Threat</Label>
              <Select value={formData.threat_id} onValueChange={(val) => handleSelectChange("threat_id", val)}>
                <SelectTrigger id="threat_id">
                  <SelectValue placeholder="Select threat..." />
                </SelectTrigger>
                <SelectContent>
                  {threats.map((threat) => (
                    <SelectItem key={threat.id} value={String(threat.id)}>
                      {threat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="asset_id">Asset</Label>
              <Select value={formData.asset_id} onValueChange={(val) => handleSelectChange("asset_id", val)}>
                <SelectTrigger id="asset_id">
                  <SelectValue placeholder="Select asset..." />
                </SelectTrigger>
                <SelectContent>
                  {assets.map((asset) => (
                    <SelectItem key={asset.id} value={String(asset.id)}>
                      {asset.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Details & Analysis */}
        <div className="space-y-4 rounded-lg border border-border/60 bg-card/50 p-4">
          <h3 className="font-semibold text-sm">Test Details & Analysis</h3>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              name="description"
              placeholder="Detailed description of the test case..."
              value={formData.description}
              onChange={handleChange}
              className="min-h-20"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="attack_path">Attack Path</Label>
            <Textarea
              id="attack_path"
              name="attack_path"
              placeholder="Describe the attack path..."
              value={formData.attack_path}
              onChange={handleChange}
              className="min-h-20"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="test_steps">Test Steps</Label>
            <Textarea
              id="test_steps"
              name="test_steps"
              placeholder="Step-by-step instructions for executing the test..."
              value={formData.test_steps}
              onChange={handleChange}
              className="min-h-20"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="expected_output">Expected Output</Label>
            <Textarea
              id="expected_output"
              name="expected_output"
              placeholder="Expected results when test case succeeds..."
              value={formData.expected_output}
              onChange={handleChange}
              className="min-h-20"
            />
          </div>
        </div>

        {/* Risk & Feasibility */}
        <div className="space-y-4 rounded-lg border border-border/60 bg-card/50 p-4">
          <h3 className="font-semibold text-sm">Risk & Feasibility Analysis</h3>

          <div className="space-y-2">
            <Label htmlFor="attack_feasibility">Attack Feasibility</Label>
            <Textarea
              id="attack_feasibility"
              name="attack_feasibility"
              placeholder="Assess the feasibility of this attack..."
              value={formData.attack_feasibility}
              onChange={handleChange}
              className="min-h-16"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="cia_impact">CIA Impact</Label>
            <Textarea
              id="cia_impact"
              name="cia_impact"
              placeholder="Impact on Confidentiality, Integrity, Availability..."
              value={formData.cia_impact}
              onChange={handleChange}
              className="min-h-16"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="safety_impact">Safety Impact</Label>
            <Textarea
              id="safety_impact"
              name="safety_impact"
              placeholder="Describe safety implications..."
              value={formData.safety_impact}
              onChange={handleChange}
              className="min-h-16"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="automation_possible">Automation Possible</Label>
            <Select value={formData.automation_possible} onValueChange={(val) => handleSelectChange("automation_possible", val)}>
              <SelectTrigger id="automation_possible">
                <SelectValue placeholder="Can this be automated?" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="yes">Yes</SelectItem>
                <SelectItem value="no">No</SelectItem>
                <SelectItem value="partial">Partial</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="source_scope_status">Source Scope Status</Label>
            <Input
              id="source_scope_status"
              name="source_scope_status"
              placeholder="E.g., In Scope, Out of Scope..."
              value={formData.source_scope_status}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex gap-2 border-t pt-6">
          <Button type="submit" disabled={isLoading} className="flex-1">
            {isLoading && <Loader2 className="size-4 animate-spin mr-2" />}
            {testCase ? "Update Test Case" : "Create Test Case"}
          </Button>
        </div>
      </form>
    </ScrollArea>
  );
}
