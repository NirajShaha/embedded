import { API_URL } from "@/config";
import type {
  AttributeGroup,
  PageSelections,
  Project,
} from "@/lib/types";


async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("token")
      : null;

  const headers = new Headers(
    init?.headers,
  );

  if (
    init?.body !== undefined &&
    !(init.body instanceof FormData)
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...init,
      headers,
    },
  );

  if (response.status === 401) {
    handleUnauthorizedResponse();

    throw new Error(
      "Your session has expired. Please sign in again.",
    );
  }

  if (!response.ok) {
    throw new Error(
      await getResponseErrorMessage(
        response,
      ),
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}


function handleUnauthorizedResponse(): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem("token");
  localStorage.removeItem("user");

  window.dispatchEvent(
    new CustomEvent(
      "auth:unauthorized",
    ),
  );
}


async function getResponseErrorMessage(
  response: Response,
): Promise<string> {
  const fallbackMessage =
    `Request failed (${response.status})`;

  const contentType =
    response.headers.get(
      "content-type",
    );

  if (
    contentType
      ?.toLowerCase()
      .includes("application/json")
  ) {
    try {
      const payload =
        (await response.json()) as {
          detail?: unknown;
        };

      if (
        typeof payload.detail ===
        "string" &&
        payload.detail.trim()
      ) {
        return payload.detail.trim();
      }

      if (
        Array.isArray(
          payload.detail,
        )
      ) {
        const validationMessages =
          payload.detail
            .map((item) => {
              if (
                typeof item !==
                "object" ||
                item === null
              ) {
                return null;
              }

              const message =
                "msg" in item
                  ? item.msg
                  : null;

              return typeof message ===
                "string"
                ? message
                : null;
            })
            .filter(
              (
                message,
              ): message is string =>
                message !== null,
            );

        if (
          validationMessages.length >
          0
        ) {
          return validationMessages.join(
            ", ",
          );
        }
      }
    } catch {
      return fallbackMessage;
    }

    return fallbackMessage;
  }

  try {
    const responseText =
      await response.text();

    return (
      responseText.trim() ||
      fallbackMessage
    );
  } catch {
    return fallbackMessage;
  }
}


function normalizePositiveIds(
  values: number[],
): number[] {
  return [
    ...new Set(
      values.filter(
        (value) =>
          Number.isInteger(value) &&
          value > 0,
      ),
    ),
  ].sort(
    (first, second) =>
      first - second,
  );
}


function getDownloadFilename(
  contentDisposition: string | null,
): string | null {
  if (!contentDisposition) {
    return null;
  }

  const utf8Match =
    contentDisposition.match(
      /filename\*=UTF-8''([^;]+)/i,
    );

  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(
        utf8Match[1].trim(),
      );
    } catch {
      return utf8Match[1].trim();
    }
  }

  const quotedMatch =
    contentDisposition.match(
      /filename="([^"]+)"/i,
    );

  if (quotedMatch?.[1]) {
    return quotedMatch[1].trim();
  }

  const plainMatch =
    contentDisposition.match(
      /filename=([^;]+)/i,
    );

  return (
    plainMatch?.[1]
      ?.trim()
      .replace(
        /^["']|["']$/g,
        "",
      ) ?? null
  );
}


// Project APIs

export const listProjects = () =>
  request<Project[]>(
    "/projects",
  );


export const createProject = (
  payload: {
    name: string;
    description?: string;
  },
) =>
  request<Project>(
    "/projects",
    {
      method: "POST",
      body: JSON.stringify(
        payload,
      ),
    },
  );


export const getProject = (
  id: number,
) =>
  request<Project>(
    `/projects/${id}`,
  );


// Page and selection APIs

export const getPageAttributes = (
  page: number,
) =>
  request<AttributeGroup[]>(
    `/pages/${page}/attributes`,
  );


export const getSelections = (
  projectId: number,
  page: number,
) =>
  request<PageSelections>(
    `/projects/${projectId}/page/${page}/selections`,
  );


export const saveSelections = (
  projectId: number,
  page: number,
  attributeIds: number[],
) =>
  request<PageSelections>(
    `/projects/${projectId}/page/${page}/selections`,
    {
      method: "PUT",
      body: JSON.stringify({
        attribute_ids:
          attributeIds,
      }),
    },
  );


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
  date_hardware_b_sample_available:
  | string
  | null;
  date_harness_available:
  | string
  | null;
  date_production_intent_software_available:
  | string
  | null;
  export_control_classification: string;
  pentest_provider_name: string;
  created_at: string;
  updated_at: string;
}


export type EcuDetailWritePayload =
  Omit<
    EcuDetail,
    | "id"
    | "project_id"
    | "created_at"
    | "updated_at"
  >;


export const getEcuDetail = (
  projectId: number,
) =>
  request<EcuDetail>(
    `/projects/${projectId}/ecu-detail`,
  );


export const createEcuDetail = (
  projectId: number,
  payload: EcuDetailWritePayload,
) =>
  request<EcuDetail>(
    `/projects/${projectId}/ecu-detail`,
    {
      method: "POST",
      body: JSON.stringify(
        payload,
      ),
    },
  );


export const updateEcuDetail = (
  projectId: number,
  payload: Partial<EcuDetailWritePayload>,
) =>
  request<EcuDetail>(
    `/projects/${projectId}/ecu-detail`,
    {
      method: "PUT",
      body: JSON.stringify(
        payload,
      ),
    },
  );


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
  attack_vector_id:
  | number
  | null;
  test_type_id: number | null;
  severity_id: number | null;
  threat_id: number | null;
  asset_id: number | null;

  action_test_case: string;
  source_scope_status:
  | string
  | null;
  description: string | null;
  attack_path: string | null;
  test_steps: string | null;
  expected_output: string | null;
  attack_feasibility:
  | string
  | null;
  cia_impact: string | null;
  safety_impact: string | null;
  automation_possible:
  | string
  | null;
  created_at: string;

  category: {
    id: number;
    name: string;
  } | null;

  objective: {
    id: number;
    name: string;
    category_id: number;
  } | null;

  protocol: {
    id: number;
    name: string;
  } | null;

  attack_vector: {
    id: number;
    name: string;
  } | null;

  test_type: {
    id: number;
    name: string;
  } | null;

  severity: {
    id: number;
    name: string;
    severity_rank: number;
  } | null;

  threat: {
    id: number;
    threat_text: string;
  } | null;

  asset: {
    id: number;
    asset_name: string;
  } | null;

  test_case_tools: Array<{
    tool: {
      id: number;
      tool_name: string;
    };
  }>;

  test_case_references: Array<{
    reference: {
      id: number;
      ref_text: string;
    };
  }>;
}


export const getCategories = () =>
  request<Category[]>(
    "/test-cases/categories",
  );


export const getTestTypes = () =>
  request<TestType[]>(
    "/test-cases/types",
  );


export const listTestCases = (
  categoryIds?:
    | number[]
    | number,
  testTypeIds?:
    | number[]
    | number,
) => {
  const searchParams =
    new URLSearchParams();

  const normalizedCategoryIds =
    normalizePositiveIds(
      Array.isArray(categoryIds)
        ? categoryIds
        : categoryIds !==
          undefined
          ? [categoryIds]
          : [],
    );

  const normalizedTestTypeIds =
    normalizePositiveIds(
      Array.isArray(testTypeIds)
        ? testTypeIds
        : testTypeIds !==
          undefined
          ? [testTypeIds]
          : [],
    );

  normalizedCategoryIds.forEach(
    (categoryId) => {
      searchParams.append(
        "category_ids",
        String(categoryId),
      );
    },
  );

  normalizedTestTypeIds.forEach(
    (testTypeId) => {
      searchParams.append(
        "test_type_ids",
        String(testTypeId),
      );
    },
  );

  const query =
    searchParams.toString();

  return request<TestCase[]>(
    `/test-cases${query
      ? `?${query}`
      : ""
    }`,
  );
};


export const getTestCase = (
  id: number,
) =>
  request<TestCase>(
    `/test-cases/${id}`,
  );


export interface DownloadTestCasesPDFParams {
  projectId: number;
  testCaseIds: number[];
  categoryIds?: number[];
  testTypeIds?: number[];
}


export const downloadTestCasesPDF =
  async ({
    projectId,
    testCaseIds,
    categoryIds = [],
    testTypeIds = [],
  }: DownloadTestCasesPDFParams): Promise<void> => {
    if (
      !Number.isInteger(
        projectId,
      ) ||
      projectId <= 0
    ) {
      throw new Error(
        "A valid project is required to generate the PDF.",
      );
    }

    const normalizedTestCaseIds =
      normalizePositiveIds(
        testCaseIds,
      );

    if (
      normalizedTestCaseIds.length ===
      0
    ) {
      throw new Error(
        "No test cases match the current filters.",
      );
    }

    const normalizedCategoryIds =
      normalizePositiveIds(
        categoryIds,
      );

    const normalizedTestTypeIds =
      normalizePositiveIds(
        testTypeIds,
      );

    const searchParams =
      new URLSearchParams();

    searchParams.set(
      "project_id",
      String(projectId),
    );

    normalizedTestCaseIds.forEach(
      (testCaseId) => {
        searchParams.append(
          "test_case_ids",
          String(testCaseId),
        );
      },
    );

    normalizedCategoryIds.forEach(
      (categoryId) => {
        searchParams.append(
          "category_ids",
          String(categoryId),
        );
      },
    );

    normalizedTestTypeIds.forEach(
      (testTypeId) => {
        searchParams.append(
          "test_type_ids",
          String(testTypeId),
        );
      },
    );

    const url =
      `${API_URL}/test-cases/export/pdf?` +
      searchParams.toString();

    const controller =
      new AbortController();

    const timeoutId =
      window.setTimeout(
        () => {
          controller.abort();
        },
        120_000,
      );

    try {
      const token =
        localStorage.getItem(
          "token",
        );

      const headers = new Headers({
        Accept: "application/pdf",
      });

      if (token) {
        headers.set(
          "Authorization",
          `Bearer ${token}`,
        );
      }

      const response = await fetch(
        url,
        {
          method: "GET",
          headers,
          signal:
            controller.signal,
        },
      );

      if (
        response.status === 401
      ) {
        handleUnauthorizedResponse();

        throw new Error(
          "Your session has expired. Please sign in again.",
        );
      }

      if (!response.ok) {
        throw new Error(
          await getResponseErrorMessage(
            response,
          ),
        );
      }

      const contentType =
        response.headers.get(
          "content-type",
        );

      if (
        !contentType
          ?.toLowerCase()
          .includes(
            "application/pdf",
          )
      ) {
        throw new Error(
          "The server returned an invalid PDF response.",
        );
      }

      const pdfBlob =
        await response.blob();

      if (pdfBlob.size === 0) {
        throw new Error(
          "The generated PDF is empty.",
        );
      }

      const contentDisposition =
        response.headers.get(
          "content-disposition",
        );

      const filename =
        getDownloadFilename(
          contentDisposition,
        ) ?? "test_plan.pdf";

      const blobUrl =
        window.URL.createObjectURL(
          pdfBlob,
        );

      const link =
        document.createElement("a");

      link.href = blobUrl;
      link.download = filename;
      link.rel = "noopener";
      link.style.display = "none";

      document.body.appendChild(
        link,
      );

      link.click();
      link.remove();

      window.setTimeout(
        () => {
          window.URL.revokeObjectURL(
            blobUrl,
          );
        },
        1_000,
      );
    } catch (error) {
      if (
        error instanceof
        DOMException &&
        error.name === "AbortError"
      ) {
        throw new Error(
          "PDF generation took too long. Please try again.",
        );
      }

      throw error;
    } finally {
      window.clearTimeout(
        timeoutId,
      );
    }
  };


// Admin lookup and CRUD APIs

export interface LookupItem {
  id: number;
  name: string;
}


export interface ObjectiveLookupItem
  extends LookupItem {
  category_id: number;
}


export interface SeverityLookupItem
  extends LookupItem {
  severity_rank: number;
}


export interface TestCaseLookups {
  categories: LookupItem[];
  objectives:
  ObjectiveLookupItem[];
  protocols: LookupItem[];
  attack_vectors: LookupItem[];
  test_types: LookupItem[];
  severities:
  SeverityLookupItem[];
  threats: LookupItem[];
  assets: LookupItem[];
  tools: LookupItem[];
  references: LookupItem[];
}


export interface FieldSuggestions {
  source_scope_status: string[];
  description: string[];
  attack_path: string[];
  test_steps: string[];
  expected_output: string[];
  attack_feasibility: string[];
  cia_impact: string[];
  safety_impact: string[];
}


export interface TestCaseWritePayload {
  action_test_case: string;

  category_id: number;
  objective_id: number;

  protocol_id:
  | number
  | null;
  attack_vector_id:
  | number
  | null;
  test_type_id:
  | number
  | null;
  severity_id:
  | number
  | null;
  threat_id:
  | number
  | null;
  asset_id:
  | number
  | null;

  source_scope_status:
  | string
  | null;
  description:
  | string
  | null;
  attack_path:
  | string
  | null;
  test_steps:
  | string
  | null;
  expected_output:
  | string
  | null;
  attack_feasibility:
  | string
  | null;
  cia_impact:
  | string
  | null;
  safety_impact:
  | string
  | null;

  automation_possible:
  | "Yes"
  | "No"
  | "Partial"
  | null;

  tool_ids: number[];
  reference_ids: number[];
}


export interface AdminStats {
  total_test_cases: number;
  total_users: number;
  recent_updates: number;
}


export const getAdminLookups = () =>
  request<TestCaseLookups>(
    "/admin/lookups",
  );


export const getAdminFieldSuggestions = () =>
  request<FieldSuggestions>(
    "/admin/field-suggestions",
  );


export type LookupCreateType =
  | "protocols"
  | "attack_vectors"
  | "test_types"
  | "threats"
  | "assets"
  | "tools"
  | "references";


export const createAdminLookupItem = (
  type: LookupCreateType,
  name: string,
) =>
  request<LookupItem>(
    `/admin/lookups/${type}`,
    {
      method: "POST",
      body: JSON.stringify({ name }),
    },
  );


export const listAdminTestCases = () =>
  request<TestCase[]>(
    "/admin/test-cases",
  );


export const createAdminTestCase = (
  payload: TestCaseWritePayload,
) =>
  request<TestCase>(
    "/admin/test-cases",
    {
      method: "POST",
      body: JSON.stringify(
        payload,
      ),
    },
  );


export const updateAdminTestCase = (
  testCaseId: number,
  payload: TestCaseWritePayload,
) =>
  request<TestCase>(
    `/admin/test-cases/${testCaseId}`,
    {
      method: "PUT",
      body: JSON.stringify(
        payload,
      ),
    },
  );


export const deleteAdminTestCase = (
  testCaseId: number,
) =>
  request<void>(
    `/admin/test-cases/${testCaseId}`,
    {
      method: "DELETE",
    },
  );


export const getAdminStats = () =>
  request<AdminStats>(
    "/admin/stats",
  );