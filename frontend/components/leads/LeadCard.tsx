import { Building2, Mail, Phone, Linkedin } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { Lead } from "@/lib/types";

export interface LeadCardProps {
  lead: Lead;
}

export function LeadCard({ lead }: LeadCardProps) {
  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-4">
        <div>
          <CardTitle>
            {lead.firstName} {lead.lastName}
          </CardTitle>
          <p className="text-sm text-zinc-500">{lead.title}</p>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-2xl font-semibold text-primary">{lead.score}</span>
          <span className="text-xs text-zinc-400">Lead score</span>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-center gap-2 text-sm text-zinc-700">
          <Building2 className="h-4 w-4 text-zinc-400" />
          <span>{lead.company}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-zinc-700">
          <Mail className="h-4 w-4 text-zinc-400" />
          <a href={`mailto:${lead.email}`} className="hover:underline">
            {lead.email}
          </a>
        </div>
        {lead.phone && (
          <div className="flex items-center gap-2 text-sm text-zinc-700">
            <Phone className="h-4 w-4 text-zinc-400" />
            <span>{lead.phone}</span>
          </div>
        )}
        {lead.linkedinUrl && (
          <div className="flex items-center gap-2 text-sm text-zinc-700">
            <Linkedin className="h-4 w-4 text-zinc-400" />
            <a
              href={lead.linkedinUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline"
            >
              LinkedIn profile
            </a>
          </div>
        )}
        {lead.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {lead.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
