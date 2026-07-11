import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const publicPaths = ['/login', '/signup', '/', '/setup'];

const protectedPaths = [
  '/dashboard',
  '/campaigns',
  '/content',
  '/ai-content',
  '/calendar',
  '/notifications',
  '/analytics',
  '/workflows',
  '/advertising',
  '/email',
  '/automation',
  '/monitoring',
  '/reports',
  '/team',
  '/settings',
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (publicPaths.some((p) => pathname === p || pathname.startsWith(p + '/'))) {
    return NextResponse.next();
  }

  const isProtected = protectedPaths.some((p) => pathname.startsWith(p));

  if (!isProtected) {
    return NextResponse.next();
  }

  const accessToken = request.cookies.get('astra_access_token')?.value
    ?? request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!accessToken) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api/).*)'],
};
