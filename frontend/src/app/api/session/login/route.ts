import { NextResponse } from "next/server";

import {
  createLocalAuthToken,
  getLocalAuthConfigurationError,
  getLocalAuthCookieSettings,
  isLocalAuthEnabled,
  isLocalAuthMisconfigured,
  isValidLocalAuthPassword,
  LOCAL_AUTH_COOKIE_NAME,
  LOCAL_AUTH_LOGIN_PATH,
  normalizeNextPath,
} from "@/server/local-auth";

function getFormValue(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === "string" ? value : "";
}

export async function POST(request: Request) {
  const formData = await request.formData();
  const password = getFormValue(formData, "password");
  const nextPath = normalizeNextPath(getFormValue(formData, "next"));
  const url = new URL(request.url);

  if (isLocalAuthMisconfigured()) {
    return new NextResponse(getLocalAuthConfigurationError(), { status: 503 });
  }

  if (!isLocalAuthEnabled()) {
    return NextResponse.redirect(new URL(nextPath, url), { status: 303 });
  }

  if (!isValidLocalAuthPassword(password)) {
    const loginUrl = new URL(LOCAL_AUTH_LOGIN_PATH, url);
    loginUrl.searchParams.set("error", "invalid_password");
    if (nextPath) {
      loginUrl.searchParams.set("next", nextPath);
    }
    return NextResponse.redirect(loginUrl, { status: 303 });
  }

  const response = NextResponse.redirect(new URL(nextPath, url), { status: 303 });
  response.cookies.set(
    LOCAL_AUTH_COOKIE_NAME,
    createLocalAuthToken(password.trim()),
    getLocalAuthCookieSettings(),
  );
  return response;
}
