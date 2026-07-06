import Link from "next/link";
import { Sparkles, ArrowRight, Users, Megaphone, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

const FEATURES = [
  {
    icon: Users,
    title: "AI-Enriched Leads",
    description:
      "Automatically enrich every lead with firmographic data, seniority signals, and an AI-generated fit score.",
  },
  {
    icon: Megaphone,
    title: "Campaign Generation",
    description:
      "Describe your ideal customer in plain English and let AI generate targeted personas and outreach copy.",
  },
  {
    icon: BarChart3,
    title: "Conversion Analytics",
    description:
      "Track pipeline health across every campaign with real-time conversion and scoring analytics.",
  },
];

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between px-6 py-5 sm:px-10">
        <div className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">AI LeadGen</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost">Log in</Button>
          </Link>
          <Link href="/signup">
            <Button>Get started</Button>
          </Link>
        </div>
      </header>

      <section className="flex flex-1 flex-col items-center justify-center gap-6 px-6 py-20 text-center sm:px-10">
        <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-zinc-900 sm:text-5xl">
          Find, score, and convert leads with AI
        </h1>
        <p className="max-w-xl text-lg text-zinc-500">
          AI Lead Generation combines LangChain-powered enrichment, automated
          scoring, and personalized outreach to help your sales team focus on
          the leads that matter.
        </p>
        <Link href="/signup">
          <Button size="lg">
            Start generating leads
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </section>

      <section className="grid grid-cols-1 gap-6 px-6 pb-20 sm:grid-cols-3 sm:px-10">
        {FEATURES.map((feature) => (
          <Card key={feature.title}>
            <CardHeader>
              <feature.icon className="mb-2 h-8 w-8 text-primary" />
              <CardTitle>{feature.title}</CardTitle>
              <CardDescription>{feature.description}</CardDescription>
            </CardHeader>
            <CardContent />
          </Card>
        ))}
      </section>
    </main>
  );
}
