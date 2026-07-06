"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Sparkles, Trash2 } from "lucide-react";
import { getLead, enrichLead, deleteLead } from "@/lib/api-client";
import type { Lead } from "@/lib/types";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";
import { LeadCard } from "@/components/leads/LeadCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

export default function LeadDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [lead, setLead] = useState<Lead | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEnriching, setIsEnriching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function fetchLead() {
      setIsLoading(true);
      try {
        const response = await getLead(params.id);
        if (!isCancelled) {
          setLead(response.data);
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : "Failed to load lead");
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchLead();
    return () => {
      isCancelled = true;
    };
  }, [params.id]);

  async function handleEnrich() {
    setIsEnriching(true);
    try {
      await enrichLead(params.id);
    } finally {
      setIsEnriching(false);
    }
  }

  async function handleDelete() {
    await deleteLead(params.id);
    router.push("/dashboard/leads");
  }

  return (
    <>
      <Header title="Lead detail" />
      <main className="flex-1 p-6">
        <button
          onClick={() => router.push("/dashboard/leads")}
          className="mb-4 flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to leads
        </button>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {isLoading && <p className="text-sm text-zinc-500">Loading lead…</p>}

        {!isLoading && lead && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <LeadCard lead={lead} />
            </div>

            <div className="flex flex-col gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Actions</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-2">
                  <Button onClick={handleEnrich} isLoading={isEnriching}>
                    <Sparkles className="h-4 w-4" />
                    {lead.enriched ? "Re-run enrichment" : "Run AI enrichment"}
                  </Button>
                  <Button variant="destructive" onClick={handleDelete}>
                    <Trash2 className="h-4 w-4" />
                    Delete lead
                  </Button>
                </CardContent>
              </Card>

              {lead.enrichment && (
                <Card>
                  <CardHeader>
                    <CardTitle>AI Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-zinc-600">
                    {lead.enrichment.aiSummary ?? "No summary available yet."}
                  </CardContent>
                </Card>
              )}

              {lead.notes && (
                <Card>
                  <CardHeader>
                    <CardTitle>Notes</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-zinc-600">
                    {lead.notes}
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </main>
    </>
  );
}
