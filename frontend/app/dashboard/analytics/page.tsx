"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

interface StatusBreakdown {
  NEW: number;
  CONTACTED: number;
  QUALIFIED: number;
  CONVERTED: number;
  LOST: number;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default function AnalyticsPage() {
  const [breakdown, setBreakdown] = useState<StatusBreakdown | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Direct fetch example — in a full implementation this would go through
    // `lib/api-client.ts` to attach the Supabase auth token automatically.
    async function fetchBreakdown() {
      try {
        const response = await fetch(`${API_BASE_URL}/analytics/leads-by-status`, {
          credentials: "include",
        });
        if (!response.ok) {
          throw new Error("Failed to load analytics");
        }
        const body = await response.json();
        setBreakdown(body.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      } finally {
        setIsLoading(false);
      }
    }

    fetchBreakdown();
  }, []);

  return (
    <>
      <Header title="Analytics" />
      <main className="flex-1 p-6">
        {isLoading && <p className="text-sm text-zinc-500">Loading analytics…</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}

        {breakdown && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {(Object.keys(breakdown) as Array<keyof StatusBreakdown>).map((status) => (
              <Card key={status}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-zinc-500">
                    {status}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-zinc-900">
                    {breakdown[status]}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </>
  );
}
