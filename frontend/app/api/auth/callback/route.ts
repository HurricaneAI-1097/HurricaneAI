import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@/lib/supabase-server";

/**
 * Handles the Supabase OAuth / magic-link / email-confirmation redirect.
 * Exchanges the `code` query param for a session and redirects the user
 * into the authenticated dashboard.
 */
export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const redirectTo = searchParams.get("redirectedFrom") ?? "/dashboard";

  if (code) {
    const supabase = createServerClient();
    await supabase.auth.exchangeCodeForSession(code);
  }

  return NextResponse.redirect(`${origin}${redirectTo}`);
}
