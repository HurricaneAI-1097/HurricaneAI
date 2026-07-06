"use client";

import { useEffect, useState } from "react";
import { Plus, Search } from "lucide-react";
import { getLeads } from "@/lib/api-client";
import type { Lead, LeadStatus } from "@/lib/types";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { LeadTable } from "@/components/leads/LeadTable";

const STATUS_FILTERS: Array<LeadStatus | "ALL"> = [
  "ALL",
  "NEW",
  "CONTACTED",
  "QUALIFIED",
  "CONVERTED",
  "LOST",
];

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<LeadStatus | "ALL">("ALL");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function fetchLeads() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await getLeads({
          search: search || undefined,
          status: statusFilter === "ALL" ? undefined : statusFilter,
          page: 1,
          page_size: 50,
        });
        if (!isCancelled) {
          setLeads(response.items);
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : "Failed to load leads");
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    const debounceTimer = setTimeout(fetchLeads, 300);
    return () => {
      isCancelled = true;
      clearTimeout(debounceTimer);
    };
  }, [search, statusFilter]);

  return (
    <>
      <Header title="Leads" />
      <main className="flex-1 p-6">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative w-full max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
            <Input
              placeholder="Search by name, email, or company"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button>
            <Plus className="h-4 w-4" />
            Add lead
          </Button>
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          {STATUS_FILTERS.map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                statusFilter === status
                  ? "bg-primary text-white"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <LeadTable leads={leads} isLoading={isLoading} />
      </main>
    </>
  );
}
