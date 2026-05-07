import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  ADMIN_TOKEN_HEADER_NAME,
  getLocalAuthConfigurationError,
  getProxyAuthorizationToken,
  isLocalAuthEnabled,
  isLocalAuthMisconfigured,
  isValidAdminAccessToken,
  isValidLocalAuthToken,
  LOCAL_AUTH_COOKIE_NAME,
  PROXY_AUTH_HEADER_NAME,
} from "@/server/local-auth";

function unauthorized() {
  return new NextResponse("Unauthorized", {
    status: 401,
    headers: {
      "Cache-Control": "no-store",
    },
  });
}

function notFound() {
  return new NextResponse("Not found", {
    status: 404,
    headers: {
      "Cache-Control": "no-store",
    },
  });
}

// Nginx auth_request always injects X-Original-URI; direct callers cannot forge it
// because nginx rewrites it. Blocks a misrouted request from bypassing auth.
function isNginxSubrequest(request: Request): boolean {
  return Boolean(request.headers.get("x-original-uri"));
}

function authorizedResponse() {
  const response = new NextResponse(null, {
    status: 204,
    headers: {
      "Cache-Control": "no-store",
    },
  });
  const proxyToken = getProxyAuthorizationToken();
  if (proxyToken) {
    response.headers.set(PROXY_AUTH_HEADER_NAME, proxyToken);
  }
  return response;
}

export async function GET(request: Request) {
  if (!isNginxSubrequest(request)) {
    return notFound();
  }

  const adminToken = request.headers.get(ADMIN_TOKEN_HEADER_NAME);
  if (isValidAdminAccessToken(adminToken)) {
    return authorizedResponse();
  }

  if (isLocalAuthMisconfigured()) {
    return new NextResponse(getLocalAuthConfigurationError(), {
      status: 403,
      headers: {
        "Cache-Control": "no-store",
      },
    });
  }

  if (!isLocalAuthEnabled()) {
    return authorizedResponse();
  }

  const cookieStore = await cookies();
  const token = cookieStore.get(LOCAL_AUTH_COOKIE_NAME)?.value;
  if (!isValidLocalAuthToken(token)) {
    return unauthorized();
  }

  return authorizedResponse();
}

export async function HEAD(request: Request) {
  return GET(request);
}
