import { Users, TrendingUp, Megaphone, Target } from "lucide-react";
import { createServerClient } from "@/lib/supabase-server";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

interface OverviewStat {
  label: string;
  value: string;
  icon: typeof Users;
}

async function getOverviewStats(): Promise<OverviewStat[]> {
  // In production this calls the FastAPI `/api/v1/analytics/overview` route
  // via `lib/api-client.ts`. Placeholder zeros are shown until real data
  // is wired up in a Client Component or server action.
  return [
    { label: "Total Leads", value: "0", icon: Users },
    { label: "Qualified Leads", value: "0", icon: Target },
    { label: "Active Campaigns", value: "0", icon: Megaphone },
    { label: "Conversion Rate", value: "0%", icon: TrendingUp },
  ];
}

export default async function DashboardOverviewPage() {
  const supabase = createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const stats = await getOverviewStats();

  return (
    <>
      <Header title="Overview" userEmail={session?.user?.email} />
      <main className="flex-1 p-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.label}>
              <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-zinc-500">
                  {stat.label}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-zinc-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-zinc-900">{stat.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>Getting started</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-zinc-600">
              Create your first campaign to let AI generate targeted buyer
              personas, then import or add leads to begin automated
              enrichment and scoring.
            </CardContent>
          </Card>
        </div>
      </main>
    </>
  );
}
