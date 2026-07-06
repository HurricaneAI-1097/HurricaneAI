"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Play, Users } from "lucide-react";
import { getCampaigns, startCampaign } from "@/lib/api-client";
import type { Campaign } from "@/lib/types";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [startingId, setStartingId] = useState<string | null>(null);

  async function loadCampaigns() {
    setIsLoading(true);
    try {
      const response = await getCampaigns();
      setCampaigns(response.items);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadCampaigns();
  }, []);

  async function handleStart(id: string) {
    setStartingId(id);
    try {
      await startCampaign(id);
      await loadCampaigns();
    } finally {
      setStartingId(null);
    }
  }

  return (
    <>
      <Header title="Campaigns" />
      <main className="flex-1 p-6">
        <div className="mb-6 flex items-center justify-between">
          <p className="text-sm text-zinc-500">
            Manage AI-driven lead generation campaigns
          </p>
          <Link href="/dashboard/campaigns/new">
            <Button>
              <Plus className="h-4 w-4" />
              New campaign
            </Button>
          </Link>
        </div>

        {isLoading && <p className="text-sm text-zinc-500">Loading campaigns…</p>}

        {!isLoading && campaigns.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-zinc-300 py-16 text-center">
            <p className="text-sm font-medium text-zinc-900">No campaigns yet</p>
            <p className="text-sm text-zinc-500">
              Create your first AI-generated campaign to start sourcing leads.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {campaigns.map((campaign) => (
            <Card key={campaign.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{campaign.name}</CardTitle>
                  <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600">
                    {campaign.status}
                  </span>
                </div>
                <CardDescription>{campaign.description ?? "No description"}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <div className="flex items-center gap-2 text-sm text-zinc-600">
                  <Users className="h-4 w-4 text-zinc-400" />
                  {campaign.totalLeads} leads · {campaign.convertedLeads} converted
                </div>
                {(campaign.status === "DRAFT" || campaign.status === "PAUSED") && (
                  <Button
                    size="sm"
                    onClick={() => handleStart(campaign.id)}
                    isLoading={startingId === campaign.id}
                  >
                    <Play className="h-4 w-4" />
                    Start campaign
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </>
  );
}
