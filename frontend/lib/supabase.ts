/**
 * Browser-side Supabase client factory.
 * Safe to import in Client Components ("use client").
 * For server-side (RSC / Route Handlers), import from "./supabase-server".
 */

import { createBrowserClient } from "@supabase/ssr";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL as string;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string;

if (typeof window !== "undefined" && (!SUPABASE_URL || !SUPABASE_ANON_KEY)) {
  // eslint-disable-next-line no-console
  console.warn(
    "Supabase env vars not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY."
  );
}

/**
 * Browser-side Supabase client. Safe to use in Client Components.
 */
export function createClient() {
  return createBrowserClient(SUPABASE_URL ?? "", SUPABASE_ANON_KEY ?? "");
}
