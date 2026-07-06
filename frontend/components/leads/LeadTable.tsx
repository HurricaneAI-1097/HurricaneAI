"use client";

import Link from "next/link";
import { clsx } from "clsx";
import type { Lead, LeadStatus } from "@/lib/types";

export interface LeadTableProps {
  leads: Lead[];
  isLoading?: boolean;
}

const STATUS_STYLES: Record<LeadStatus, string> = {
  NEW: "bg-blue-50 text-blue-700",
  CONTACTED: "bg-amber-50 text-amber-700",
  QUALIFIED: "bg-purple-50 text-purple-700",
  CONVERTED: "bg-green-50 text-green-700",
  LOST: "bg-zinc-100 text-zinc-500",
};

function StatusBadge({ status }: { status: LeadStatus }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        STATUS_STYLES[status]
      )}
    >
      {status}
    </span>
  );
}

export function LeadTable({ leads, isLoading = false }: LeadTableProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16 text-sm text-zinc-500">
        Loading leads…
      </div>
    );
  }

  if (leads.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
        <p className="text-sm font-medium text-zinc-900">No leads found</p>
        <p className="text-sm text-zinc-500">
          Try adjusting your filters or add a new lead to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-200">
      <table className="w-full min-w-[720px] divide-y divide-zinc-200 text-sm">
        <thead className="bg-zinc-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">Name</th>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">Company</th>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">Title</th>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">Status</th>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">Score</th>
            <th className="px-4 py-3 text-left font-medium text-zinc-500">Source</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 bg-white">
          {leads.map((lead) => (
            <tr key={lead.id} className="hover:bg-zinc-50">
              <td className="px-4 py-3">
                <Link
                  href={`/dashboard/leads/${lead.id}`}
                  className="font-medium text-primary hover:underline"
                >
                  {lead.firstName} {lead.lastName}
                </Link>
                <div className="text-xs text-zinc-500">{lead.email}</div>
              </td>
              <td className="px-4 py-3 text-zinc-700">{lead.company}</td>
              <td className="px-4 py-3 text-zinc-700">{lead.title}</td>
              <td className="px-4 py-3">
                <StatusBadge status={lead.status} />
              </td>
              <td className="px-4 py-3">
                <span className="font-medium text-zinc-900">{lead.score}</span>
                <span className="text-zinc-400">/100</span>
              </td>
              <td className="px-4 py-3 text-zinc-500">{lead.source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
