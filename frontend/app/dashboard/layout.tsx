import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase-server";
import { Sidebar } from "@/components/layout/Sidebar";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/login");
  }

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-50">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-y-auto">{children}</div>
    </div>
  );
}
