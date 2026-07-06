"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { createCampaign } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export default function NewCampaignPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [industry, setIndustry] = useState("");
  const [companySize, setCompanySize] = useState("");
  const [aiPrompt, setAiPrompt] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await createCampaign({
        name,
        description: description || undefined,
        target_criteria: {
          industry: industry || undefined,
          company_size: companySize || undefined,
        },
        ai_prompt: aiPrompt,
      });

      if (response.data) {
        router.push(`/dashboard/campaigns`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create campaign");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Header title="New campaign" />
      <main className="flex-1 p-6">
        <button
          onClick={() => router.push("/dashboard/campaigns")}
          className="mb-4 flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to campaigns
        </button>

        <Card className="max-w-2xl">
          <CardHeader>
            <CardTitle>Create a new campaign</CardTitle>
            <CardDescription>
              Describe your ideal customer profile and let AI generate targeted
              buyer personas and outreach content.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <Input
                label="Campaign name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Q3 Enterprise Outbound"
              />
              <Input
                label="Description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Short internal description of this campaign"
              />
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Target industry"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="SaaS"
                />
                <Input
                  label="Target company size"
                  value={companySize}
                  onChange={(e) => setCompanySize(e.target.value)}
                  placeholder="201-1000"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-zinc-700">
                  AI targeting brief
                </label>
                <textarea
                  required
                  rows={5}
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  placeholder="Describe the ideal customer profile, pain points, and value proposition to target."
                  className="rounded-md border border-zinc-300 bg-white p-3 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" isLoading={isSubmitting} className="mt-2 w-full">
                Create campaign
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </>
  );
}
