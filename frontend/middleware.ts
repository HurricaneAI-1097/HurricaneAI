import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

const PUBLIC_PATH_PREFIXES = ["/api/auth", "/login", "/signup"];

function isPublicPath(pathname: string): boolean {
  if (pathname === "/") return true;
  return PUBLIC_PATH_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

function envConfigured(): boolean {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return false;
  if (url.includes("your-project-ref") || key.startsWith("your-")) return false;
  try {
    // must be a valid absolute URL
    // eslint-disable-next-line no-new
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const response = NextResponse.next({
    request: { headers: request.headers },
  });

  // If Supabase envs are missing or placeholder, skip auth checks so the
  // site still renders (useful for the first Vercel deploy before wiring
  // real credentials).
  if (!envConfigured()) {
    return response;
  }

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL as string,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: Record<string, unknown>) {
          response.cookies.set({ name, value, ...options });
        },
        remove(name: string, options: Record<string, unknown>) {
          response.cookies.set({ name, value: "", ...options });
        },
      },
    }
  );

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const { pathname } = request.nextUrl;

  if (isPublicPath(pathname)) {
    return response;
  }

  if (pathname.startsWith("/dashboard") && !session) {
    const redirectUrl = new URL("/login", request.url);
    redirectUrl.searchParams.set("redirectedFrom", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public assets (svg, png, jpg, jpeg, gif, webp)
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
