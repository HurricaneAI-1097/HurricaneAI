"use client";

import { useRouter } from "next/navigation";
import { LogOut, User as UserIcon } from "lucide-react";
import { createClient } from "@/lib/supabase";
import { Button } from "@/components/ui/Button";

export interface HeaderProps {
  title: string;
  userEmail?: string | null;
}

export function Header({ title, userEmail }: HeaderProps) {
  const router = useRouter();

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-zinc-200 bg-white px-6">
      <h1 className="text-xl font-semibold text-zinc-900">{title}</h1>

      <div className="flex items-center gap-4">
        {userEmail && (
          <div className="flex items-center gap-2 text-sm text-zinc-600">
            <UserIcon className="h-4 w-4" />
            <span>{userEmail}</span>
          </div>
        )}
        <Button variant="ghost" size="sm" onClick={handleSignOut}>
          <LogOut className="h-4 w-4" />
          Sign out
        </Button>
      </div>
    </header>
  );
}
