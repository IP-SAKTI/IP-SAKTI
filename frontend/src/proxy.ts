/**
 * Next.js Edge Middleware — Route Protection for IP-SAKTI Sahayak
 *
 * Runs on the server/edge BEFORE any page HTML is delivered to the browser.
 * This is the only reliable pattern in Next.js App Router for preventing
 * unauthenticated users from seeing protected page HTML.
 *
 * Strategy
 * ─────────
 * 1. When the user logs in (or magic-link callback succeeds), AuthContext sets
 *    a lightweight JS cookie called `ipsakti_session`.
 * 2. This middleware reads that cookie. If it is absent on a protected route,
 *    the request is redirected to /login BEFORE the page renders.
 * 3. If the cookie IS present but the real Supabase token has expired, the
 *    client-side AuthContext.verifySession() catches the 401 from /auth/verify,
 *    clears the cookie + localStorage, and redirects to /login client-side.
 *
 * Note: The cookie is NOT used as an authentication source-of-truth.
 * It is only a routing hint. The actual session is always validated against
 * Supabase by the backend /auth/verify endpoint in AuthContext.
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/** Routes that require an active session to access. */
const PROTECTED_PATHS = ['/', '/brief', '/compare', '/knowledge', '/settings'];

/** Auth-only routes — if already authenticated, redirect to dashboard. */
const AUTH_ONLY_PATHS = ['/login', '/register'];

/** Public routes that are always accessible. */
// /about, /contact, /auth/callback are always public

const SESSION_COOKIE = 'ipsakti_session';

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip Next.js internals and static files (images, fonts, icons, etc.)
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon') ||
    pathname.match(/\.(png|jpg|jpeg|gif|svg|ico|webp|woff|woff2|ttf|css|js|json|map)$/)
  ) {
    return NextResponse.next();
  }

  const sessionCookie = request.cookies.get(SESSION_COOKIE);
  const isAuthenticated = Boolean(sessionCookie?.value);

  // Exact match for '/' or prefix match for other protected paths
  const isProtected =
    pathname === '/' ||
    PROTECTED_PATHS.filter((p) => p !== '/').some(
      (p) => pathname === p || pathname.startsWith(p + '/')
    );

  // Unauthenticated user trying to access a protected page → /login
  if (isProtected && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  /*
   * Match all routes except:
   * - /_next/static   (Next.js static assets)
   * - /_next/image    (Next.js image optimization)
   * - /favicon.ico
   */
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};

