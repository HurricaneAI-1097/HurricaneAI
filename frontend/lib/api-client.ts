/**
 * Typed fetch wrapper for the FastAPI backend.
 *
 * Every request automatically attaches the current Supabase session's
 * access token as a Bearer credential.
 */

import { createClient } from "./supabase";
import type {
  ApiResponse,
  Campaign,
  CampaignAnalytics,
  CampaignCreateInput,
  CampaignWithLeads,
  Lead,
  LeadCreateInput,
  LeadListParams,
  LeadUpdateInput,
  PaginatedResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function getAuthHeader(): Promise<Record<string, string>> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    return {};
  }
  return { Authorization: `Bearer ${session.access_token}` };
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const authHeader = await getAuthHeader();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeader,
      ...(options.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errorBody = await response.json();
      detail = errorBody.detail ?? detail;
    } catch {
      // Response body was not JSON; fall back to statusText.
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function buildQueryString(params: Record<string, unknown>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const qs = searchParams.toString();
  return qs ? `?${qs}` : "";
}

// --- Leads ---------------------------------------------------------------

export async function getLeads(
  params: LeadListParams = {}
): Promise<PaginatedResponse<Lead>> {
  const qs = buildQueryString(params as Record<string, unknown>);
  return request<PaginatedResponse<Lead>>(`/leads${qs}`);
}

export async function getLead(id: string): Promise<ApiResponse<Lead>> {
  return request<ApiResponse<Lead>>(`/leads/${id}`);
}

export async function createLead(
  data: LeadCreateInput
): Promise<ApiResponse<Lead>> {
  return request<ApiResponse<Lead>>("/leads", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateLead(
  id: string,
  data: LeadUpdateInput
): Promise<ApiResponse<Lead>> {
  return request<ApiResponse<Lead>>(`/leads/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteLead(id: string): Promise<void> {
  await request<void>(`/leads/${id}`, { method: "DELETE" });
}

export async function enrichLead(id: string): Promise<ApiResponse<{ job_id: string | null }>> {
  return request<ApiResponse<{ job_id: string | null }>>(`/leads/${id}/enrich`, {
    method: "POST",
  });
}

export async function bulkImportLeads(
  file: File,
  campaignId?: string
): Promise<ApiResponse<{ total_rows: number; created: number; skipped: number; errors: string[] }>> {
  const authHeader = await getAuthHeader();
  const formData = new FormData();
  formData.append("file", file);

  const qs = campaignId ? `?campaign_id=${encodeURIComponent(campaignId)}` : "";
  const response = await fetch(`${API_BASE_URL}/leads/bulk-import${qs}`, {
    method: "POST",
    headers: { ...authHeader },
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, errorBody.detail ?? response.statusText);
  }

  return response.json();
}

// --- Campaigns -------------------------------------------------------------

export async function getCampaigns(
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<Campaign>> {
  const qs = buildQueryString({ page, page_size: pageSize });
  return request<PaginatedResponse<Campaign>>(`/campaigns${qs}`);
}

export async function getCampaign(
  id: string
): Promise<ApiResponse<CampaignWithLeads>> {
  return request<ApiResponse<CampaignWithLeads>>(`/campaigns/${id}`);
}

export async function createCampaign(
  data: CampaignCreateInput
): Promise<ApiResponse<Campaign>> {
  return request<ApiResponse<Campaign>>("/campaigns", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function startCampaign(
  id: string
): Promise<ApiResponse<Campaign>> {
  return request<ApiResponse<Campaign>>(`/campaigns/${id}/start`, {
    method: "POST",
  });
}

export async function getCampaignAnalytics(
  id: string
): Promise<ApiResponse<CampaignAnalytics>> {
  return request<ApiResponse<CampaignAnalytics>>(`/campaigns/${id}/analytics`);
}
