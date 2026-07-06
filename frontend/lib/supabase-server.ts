/**
 * Server-side Supabase client factory bound to the current request's cookies.
 * Use inside Server Components, Route Handlers, and Server Actions.
 */

import { createServerClient as createSSRClient } from "@supabase/ssr";
import { cookies } from "next/headers";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL as string;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string;

export function createServerClient() {
  const cookieStore = cookies();

  return createSSRClient(SUPABASE_URL ?? "", SUPABASE_ANON_KEY ?? "", {
    cookies: {
      get(name: string) {
        return cookieStore.get(name)?.value;
      },
      set(name: string, value: string, options: Record<string, unknown>) {
        try {
          cookieStore.set({ name, value, ...options });
        } catch {
          // Some Next.js contexts disallow cookie mutation; middleware refreshes.
        }
      },
      remove(name: string, options: Record<string, unknown>) {
        try {
          cookieStore.set({ name, value: "", ...options });
        } catch {
          // See note above.
        }
      },
    },
  });
}
