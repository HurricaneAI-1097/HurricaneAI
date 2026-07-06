/**
 * TypeScript interfaces mirroring the Prisma schema and API response shapes.
 */

export type UserRole = "USER" | "ADMIN";

export type LeadStatus =
  | "NEW"
  | "CONTACTED"
  | "QUALIFIED"
  | "CONVERTED"
  | "LOST";

export type CampaignStatus = "DRAFT" | "ACTIVE" | "PAUSED" | "COMPLETED";

export interface User {
  id: string;
  email: string;
  name: string | null;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
}

export interface Enrichment {
  id: string;
  leadId: string;
  linkedinData: Record<string, unknown> | null;
  companyData: Record<string, unknown> | null;
  emailVerified: boolean;
  phoneVerified: boolean;
  aiSummary: string | null;
  aiScore: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface Lead {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  company: string;
  title: string;
  phone: string | null;
  linkedinUrl: string | null;
  website: string | null;
  score: number;
  status: LeadStatus;
  source: string;
  enriched: boolean;
  enrichedAt: string | null;
  notes: string | null;
  tags: string[];
  userId: string;
  campaignId: string | null;
  createdAt: string;
  updatedAt: string;
  enrichment?: Enrichment | null;
}

export interface Campaign {
  id: string;
  name: string;
  description: string | null;
  status: CampaignStatus;
  targetCriteria: Record<string, unknown>;
  aiPrompt: string;
  totalLeads: number;
  convertedLeads: number;
  userId: string;
  createdAt: string;
  updatedAt: string;
}

export interface CampaignWithLeads extends Campaign {
  leads: Partial<Lead>[];
}

export interface CampaignAnalytics {
  campaign_id: string;
  total_leads: number;
  new_count: number;
  contacted_count: number;
  qualified_count: number;
  converted_count: number;
  lost_count: number;
  conversion_rate: number;
  average_score: number;
}

export interface LeadCreateInput {
  email: string;
  first_name: string;
  last_name: string;
  company: string;
  title: string;
  phone?: string;
  linkedin_url?: string;
  website?: string;
  source?: string;
  tags?: string[];
  notes?: string;
  campaign_id?: string;
}

export interface LeadUpdateInput {
  email?: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  title?: string;
  phone?: string;
  linkedin_url?: string;
  website?: string;
  status?: LeadStatus;
  score?: number;
  notes?: string;
  tags?: string[];
  campaign_id?: string;
}

export interface CampaignCreateInput {
  name: string;
  description?: string;
  target_criteria: Record<string, unknown>;
  ai_prompt: string;
}

export interface LeadListParams {
  page?: number;
  page_size?: number;
  status?: LeadStatus;
  campaign_id?: string;
  search?: string;
}

// --- API response envelopes ------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message?: string | null;
}
