import { API_URL } from "@/config";
import type { AttributeGroup, PageSelections, Project } from "@/lib/types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Request failed (${res.status}): ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const listProjects = () => request<Project[]>("/projects");

export const createProject = (payload: {
  name: string;
  description?: string;
}) =>
  request<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const getProject = (id: number) => request<Project>(`/projects/${id}`);

export const getPageAttributes = (page: number) =>
  request<AttributeGroup[]>(`/pages/${page}/attributes`);

export const getSelections = (projectId: number, page: number) =>
  request<PageSelections>(`/projects/${projectId}/page/${page}/selections`);

export const saveSelections = (
  projectId: number,
  page: number,
  attributeIds: number[],
) =>
  request<PageSelections>(`/projects/${projectId}/page/${page}/selections`, {
    method: "PUT",
    body: JSON.stringify({ attribute_ids: attributeIds }),
  });

// ECU Detail APIs
export interface EcuDetail {
  id: number;
  project_id: number;
  ecu_name: string;
  part_number: string;
  ecu_risk_rating: string;
  architecture: string;
  vehicle_line: string;
  year: number;
  microcontroller_cpu_provider: string;
  date_hardware_b_sample_available: string | null;
  date_harness_available: string | null;
  date_production_intent_software_available: string | null;
  export_control_classification: string;
  pentest_provider_name: string;
  created_at: string;
  updated_at: string;
}

export const getEcuDetail = (projectId: number) =>
  request<EcuDetail>(`/projects/${projectId}/ecu-detail`);

export const createEcuDetail = (
  projectId: number,
  payload: Omit<EcuDetail, "id" | "project_id" | "created_at" | "updated_at">,
) =>
  request<EcuDetail>(`/projects/${projectId}/ecu-detail`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateEcuDetail = (
  projectId: number,
  payload: Partial<
    Omit<EcuDetail, "id" | "project_id" | "created_at" | "updated_at">
  >,
) =>
  request<EcuDetail>(`/projects/${projectId}/ecu-detail`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

// Test Case APIs
export interface Category {
  id: number;
  name: string;
}

export interface TestType {
  id: number;
  name: string;
}

export interface TestCase {
  id: number;
  category_id: number;
  objective_id: number;
  protocol_id: number | null;
  attack_vector_id: number | null;
  test_type_id: number | null;
  severity_id: number | null;
  threat_id: number | null;
  asset_id: number | null;
  action_test_case: string;
  source_scope_status: string | null;
  description: string | null;
  attack_path: string | null;
  test_steps: string | null;
  expected_output: string | null;
  attack_feasibility: string | null;
  cia_impact: string | null;
  safety_impact: string | null;
  automation_possible: string | null;
  created_at: string;
  category: { id: number; name: string } | null;
  objective: { id: number; name: string; category_id: number } | null;
  protocol: { id: number; name: string } | null;
  attack_vector: { id: number; name: string } | null;
  test_type: { id: number; name: string } | null;
  severity: { id: number; name: string; severity_rank: number } | null;
  threat: { id: number; threat_text: string } | null;
  asset: { id: number; asset_name: string } | null;
  test_case_tools: Array<{ tool: { id: number; tool_name: string } }>;
  test_case_references: Array<{ reference: { id: number; ref_text: string } }>;
}

export const getCategories = () =>
  request<Category[]>("/test-cases/categories");

export const getTestTypes = () => request<TestType[]>("/test-cases/types");

export const listTestCases = (
  categoryIds?: number[] | number,
  testTypeIds?: number[] | number,
) => {
  const params = new URLSearchParams();
  const cats = Array.isArray(categoryIds)
    ? categoryIds
    : categoryIds !== undefined
      ? [categoryIds]
      : [];
  const types = Array.isArray(testTypeIds)
    ? testTypeIds
    : testTypeIds !== undefined
      ? [testTypeIds]
      : [];
  for (const id of cats) params.append("category_ids", String(id));
  for (const id of types) params.append("test_type_ids", String(id));
  const query = params.toString();
  return request<TestCase[]>(`/test-cases${query ? `?${query}` : ""}`);
};

export const getTestCase = (id: number) =>
  request<TestCase>(`/test-cases/${id}`);

export const downloadTestCasesPDF = async (
  categoryIds?: number[],
  testTypeIds?: number[],
): Promise<void> => {
  const params = new URLSearchParams();

  if (categoryIds && categoryIds.length > 0) {
    for (const id of categoryIds) {
      params.append("category_ids", String(id));
    }
  }

  if (testTypeIds && testTypeIds.length > 0) {
    for (const id of testTypeIds) {
      params.append("test_type_ids", String(id));
    }
  }

  const query = params.toString();
  const url = `${API_URL}/test-cases/export/pdf${query ? `?${query}` : ""}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`PDF generation failed (${response.status}): ${error}`);
    }

    // Get the filename from content-disposition header
    const contentDisposition = response.headers.get("content-disposition");
    let filename = "test_cases_report.pdf";
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=([^;]+)/);
      if (match) {
        filename = match[1].replace(/"/g, "");
      }
    }

    // Create blob and download
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to download PDF: ${error.message}`);
    }
    throw error;
  }
};
