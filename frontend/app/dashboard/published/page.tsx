/**
 * Published Application — Review & Triage
 *
 * Operator-facing surface showing KPIs, leads awaiting triage,
 * campaign status, and sync logs — all scoped to the current user session.
 */

import { createServerClient } from "@/lib/supabase-server";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { TriageLeadCard } from "@/components/leads/TriageLeadCard";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function kpiColorClass(value: number, green: number, yellow: number): string {
  if (value >= green) return "text-emerald-700";
  if (value >= yellow) return "text-amber-600";
  return "text-red-600";
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default async function PublishedPage() {
  const supabase = createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const apiBase =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

  // Fetch data from FastAPI backend (falls back to empty arrays on error)
  let leads: Lead[] = [];
  let campaigns: Campaign[] = [];
  let analytics: AnalyticsOverview = {
    total_leads: 0,
    qualified_leads: 0,
    active_campaigns: 0,
    conversion_rate: 0,
    approved_rate: 0,
    sync_success_rate: 0,
  };

  try {
    const authHeader = session?.access_token
      ? { Authorization: `Bearer ${session.access_token}` }
      : {};

    const [leadsRes, campaignsRes, analyticsRes] = await Promise.all([
      fetch(`${apiBase}/leads?limit=20&status=review`, {
        headers: authHeader,
        cache: "no-store",
      }),
      fetch(`${apiBase}/campaigns?limit=10`, {
        headers: authHeader,
        cache: "no-store",
      }),
      fetch(`${apiBase}/analytics/overview`, {
        headers: authHeader,
        cache: "no-store",
      }),
    ]);

    if (leadsRes.ok) {
      const data = await leadsRes.json();
      leads = data.items ?? data ?? [];
    }
    if (campaignsRes.ok) {
      const data = await campaignsRes.json();
      campaigns = data.items ?? data ?? [];
    }
    if (analyticsRes.ok) {
      analytics = await analyticsRes.json();
    }
  } catch {
    // Backend not yet configured — show empty state
  }

  const approvedRate = analytics.approved_rate ?? 0;
  const leadToQualRate =
    analytics.total_leads > 0
      ? Math.round((analytics.qualified_leads / analytics.total_leads) * 100)
      : 0;
  const syncRate = analytics.sync_success_rate ?? 100;

  return (
    <>
      <Header title="Published Application" userEmail={session?.user?.email} />
      <main className="flex-1 space-y-8 p-6">
        {/* KPIs */}
        <section>
          <h2 className="mb-4 text-base font-semibold text-zinc-900">
            Key Metrics
          </h2>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-zinc-500">AI-Approved Rate</p>
                <p
                  className={`text-2xl font-bold ${kpiColorClass(approvedRate, 40, 20)}`}
                >
                  {approvedRate}%
                </p>
                <p className="mt-1 text-xs text-zinc-400">
                  Green ≥ 40% · Yellow 20–39% · Red &lt; 20%
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-zinc-500">Lead → Qualified</p>
                <p
                  className={`text-2xl font-bold ${kpiColorClass(leadToQualRate, 25, 10)}`}
                >
                  {leadToQualRate}%
                </p>
                <p className="mt-1 text-xs text-zinc-400">
                  Green ≥ 25% · Yellow 10–24%
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-zinc-500">Sync Success Rate</p>
                <p
                  className={`text-2xl font-bold ${kpiColorClass(syncRate, 95, 85)}`}
                >
                  {syncRate}%
                </p>
                <p className="mt-1 text-xs text-zinc-400">
                  Green ≥ 95% · Yellow 85–94%
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-zinc-500">Total Leads</p>
                <p className="text-2xl font-bold text-zinc-900">
                  {analytics.total_leads ?? 0}
                </p>
                <p className="mt-1 text-xs text-zinc-400">
                  {analytics.active_campaigns ?? 0} active campaign
                  {(analytics.active_campaigns ?? 0) !== 1 ? "s" : ""}
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Leads awaiting triage */}
        <section>
          <h2 className="mb-4 text-base font-semibold text-zinc-900">
            Leads Awaiting Triage
          </h2>
          {leads.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-sm text-zinc-400">
                No leads pending review. Import leads or run AI scoring to
                populate this list.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {leads.map((lead) => (
                <TriageLeadCard key={lead.id} lead={lead} />
              ))}
            </div>
          )}
        </section>

        {/* Campaigns */}
        <section>
          <h2 className="mb-4 text-base font-semibold text-zinc-900">
            Campaigns
          </h2>
          {campaigns.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-sm text-zinc-400">
                No campaigns yet. Create one to start generating leads.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {campaigns.map((c) => (
                <Card key={c.id}>
                  <CardContent className="flex items-center justify-between py-4">
                    <div>
                      <p className="font-medium text-zinc-900">{c.name}</p>
                      {c.description && (
                        <p className="text-xs text-zinc-500">{c.description}</p>
                      )}
                    </div>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        c.status === "ACTIVE"
                          ? "bg-emerald-100 text-emerald-700"
                          : c.status === "DRAFT"
                            ? "bg-zinc-100 text-zinc-600"
                            : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {c.status}
                    </span>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>
      </main>
    </>
  );
}

// ---------------------------------------------------------------------------
// Types (inline for simplicity)
// ---------------------------------------------------------------------------
interface Lead {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  company: string;
  title: string;
  score: number;
  status: string;
}

interface Campaign {
  id: string;
  name: string;
  description?: string;
  status: string;
}

interface AnalyticsOverview {
  total_leads: number;
  qualified_leads: number;
  active_campaigns: number;
  conversion_rate: number;
  approved_rate?: number;
  sync_success_rate?: number;
}
