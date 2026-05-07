import { redirect } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  getLocalAuthConfigurationError,
  isLocalAuthEnabled,
  isLocalAuthMisconfigured,
  LOCAL_AUTH_DEFAULT_REDIRECT,
  normalizeNextPath,
} from "@/server/local-auth";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  if (isLocalAuthMisconfigured()) {
    return (
      <main className="from-background via-muted/30 to-background flex min-h-screen items-center justify-center bg-linear-to-br px-6 py-12">
        <Card className="w-full max-w-md border shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle>MedrixFlow</CardTitle>
            <CardDescription>Protected mode is enabled, but no UI password is configured.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-6 text-muted-foreground">
              {getLocalAuthConfigurationError()}
            </p>
          </CardContent>
        </Card>
      </main>
    );
  }

  if (!isLocalAuthEnabled()) {
    redirect(LOCAL_AUTH_DEFAULT_REDIRECT);
  }

  const params = await searchParams;
  const error = params.error === "invalid_password";
  const nextValue = params.next;
  const nextPath = normalizeNextPath(
    Array.isArray(nextValue) ? nextValue[0] : nextValue,
  );

  return (
    <main className="from-background via-muted/30 to-background flex min-h-screen items-center justify-center bg-linear-to-br px-6 py-12">
      <Card className="w-full max-w-md border shadow-lg">
        <CardHeader className="space-y-1">
          <CardTitle>MedrixFlow</CardTitle>
          <CardDescription>
            Enter the workspace password to access the UI and API.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form action="/api/session/login" method="post" className="space-y-4">
            <input type="hidden" name="next" value={nextPath} />
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="password">
                Password
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                autoFocus
              />
            </div>
            {error && (
              <p className="text-destructive text-sm">
                Invalid password.
              </p>
            )}
            <Button type="submit" className="w-full">
              Unlock Workspace
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
