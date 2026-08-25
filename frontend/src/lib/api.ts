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

export const createProject = (payload: { name: string; description?: string }) =>
  request<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const getProject = (id: number) => request<Project>(`/projects/${id}`);

export const getPageAttributes = (page: number) =>
  request<AttributeGroup[]>(`/pages/${page}/attributes`);

export const getSelections = (projectId: number, page: number) =>
  request<PageSelections>(`/projects/${projectId}/page/${page}/selections`);

export const saveSelections = (projectId: number, page: number, attributeIds: number[]) =>
  request<PageSelections>(`/projects/${projectId}/page/${page}/selections`, {
    method: "PUT",
    body: JSON.stringify({ attribute_ids: attributeIds }),
  });