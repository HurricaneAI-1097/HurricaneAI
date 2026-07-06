"use client";

import { useState } from "react";

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

export function TriageLeadCard({ lead: initialLead }: { lead: Lead }) {
  const [lead, setLead] = useState(initialLead);
  const [busy, setBusy] = useState<"approve" | "reject" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apiBase =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

  async function handleDecision(decision: "approve" | "reject") {
    setBusy(decision);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/leads/${lead.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: decision === "approve" ? "QUALIFIED" : "LOST",
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail ?? "Update failed");
        return;
      }

      setLead((prev) => ({
        ...prev,
        status: decision === "approve" ? "QUALIFIED" : "LOST",
      }));
    } catch (e) {
      setError("Network error");
    } finally {
      setBusy(null);
    }
  }

  const isTriaged = lead.status === "QUALIFIED" || lead.status === "LOST";
  const label =
    lead.status === "QUALIFIED"
      ? "APPROVED"
      : lead.status === "LOST"
        ? "REJECTED"
        : "PENDING";

  return (
    <div className="rounded-md border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium text-zinc-900">
            {lead.firstName} {lead.lastName}
          </p>
          <p className="text-xs text-zinc-500">
            {lead.title} at {lead.company}
          </p>
          <p className="text-xs text-zinc-400">{lead.email}</p>
          {lead.score > 0 && (
            <p className="mt-1 text-xs font-medium text-zinc-600">
              AI Score: {lead.score}/100
            </p>
          )}
        </div>

        <div className="flex flex-col items-end gap-2">
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              label === "APPROVED"
                ? "bg-emerald-100 text-emerald-700"
                : label === "REJECTED"
                  ? "bg-red-100 text-red-700"
                  : "bg-amber-100 text-amber-700"
            }`}
          >
            {label}
          </span>

          {!isTriaged && (
            <div className="flex gap-2">
              <button
                type="button"
                disabled={busy !== null}
                onClick={() => handleDecision("approve")}
                className="rounded-md border border-emerald-600 px-3 py-1 text-xs text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
              >
                {busy === "approve" ? "Approving…" : "Approve"}
              </button>
              <button
                type="button"
                disabled={busy !== null}
                onClick={() => handleDecision("reject")}
                className="rounded-md border border-red-500 px-3 py-1 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50"
              >
                {busy === "reject" ? "Rejecting…" : "Reject"}
              </button>
            </div>
          )}
        </div>
      </div>

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </div>
  );
}
