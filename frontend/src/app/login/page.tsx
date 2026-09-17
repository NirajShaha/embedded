"use client";

import {
  useState,
  type FormEvent,
} from "react";
import {
  Loader2,
  ShieldCheck,
} from "lucide-react";

import {
  useAuth,
} from "@/contexts/auth-context";

import {
  Button,
} from "@/components/ui/button";
import {
  Input,
} from "@/components/ui/input";
import {
  Label,
} from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";


export default function LoginPage() {
  const {
    login,
    isLoading,
  } = useAuth();

  const [
    username,
    setUsername,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState("");

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setError("");

    const normalizedUsername =
      username.trim();

    if (!normalizedUsername) {
      setError(
        "Username is required.",
      );
      return;
    }

    if (!password) {
      setError(
        "Password is required.",
      );
      return;
    }

    try {
      /*
       * AuthProvider handles:
       * 1. Calling the login API
       * 2. Saving authentication
       * 3. Updating the authenticated user
       * 4. Redirecting ADMIN to /admin
       * 5. Redirecting USER to /
       *
       * Do not add another router.push()
       * or router.replace() here.
       */
      await login(
        normalizedUsername,
        password,
      );
    } catch (loginError) {
      setError(
        loginError instanceof Error
          ? loginError.message
          : "Login failed",
      );
    }
  };

  const handleUsernameChange = (
    value: string,
  ) => {
    setUsername(value);

    if (error) {
      setError("");
    }
  };

  const handlePasswordChange = (
    value: string,
  ) => {
    setPassword(value);

    if (error) {
      setError("");
    }
  };

  const canSubmit =
    !isLoading &&
    username.trim().length > 0 &&
    password.length > 0;

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 px-4 py-8">
      <Card className="w-full max-w-md border-border/60 shadow-2xl">
        <CardHeader className="space-y-1 text-center">
          <div className="mb-4 flex justify-center">
            <div className="flex aspect-square size-12 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-md">
              <ShieldCheck
                className="size-6"
                aria-hidden="true"
              />
            </div>
          </div>

          <CardTitle className="text-2xl">
            Embedded Config
          </CardTitle>

          <CardDescription>
            Security Testing Platform
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form
            onSubmit={handleSubmit}
            className="space-y-4"
            noValidate
          >
            <div className="space-y-2">
              <Label htmlFor="username">
                Username
              </Label>

              <Input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                placeholder="Enter your username"
                value={username}
                onChange={(event) =>
                  handleUsernameChange(
                    event.target.value,
                  )
                }
                disabled={isLoading}
                required
                aria-required="true"
                aria-invalid={
                  Boolean(error)
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">
                Password
              </Label>

              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                placeholder="Enter your password"
                value={password}
                onChange={(event) =>
                  handlePasswordChange(
                    event.target.value,
                  )
                }
                disabled={isLoading}
                required
                aria-required="true"
                aria-invalid={
                  Boolean(error)
                }
              />
            </div>

            {error && (
              <div
                role="alert"
                aria-live="polite"
                className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
              >
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={!canSubmit}
            >
              {isLoading && (
                <Loader2
                  className="size-4 animate-spin"
                  aria-hidden="true"
                />
              )}

              {isLoading
                ? "Signing in..."
                : "Sign In"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
