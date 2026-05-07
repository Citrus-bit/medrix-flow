import { NextResponse } from "next/server";

import { LOCAL_AUTH_COOKIE_NAME, LOCAL_AUTH_LOGIN_PATH } from "@/server/local-auth";

export async function POST(request: Request) {
  const response = NextResponse.redirect(new URL(LOCAL_AUTH_LOGIN_PATH, request.url), {
    status: 303,
  });
  response.cookies.set(LOCAL_AUTH_COOKIE_NAME, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  return response;
}
