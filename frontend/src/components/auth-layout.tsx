"use client";

import {
  useEffect,
  type ReactNode,
} from "react";
import {
  usePathname,
  useRouter,
} from "next/navigation";

import { useAuth } from "@/contexts/auth-context";


interface AuthLayoutProps {
  children: ReactNode;
}


export function AuthLayout({
  children,
}: AuthLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();

  const {
    user,
    isLoading,
  } = useAuth();

  const isLoginPage =
    pathname === "/login";

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (!user && !isLoginPage) {
      router.replace("/login");
      return;
    }

    if (user && isLoginPage) {
      router.replace(
        user.role === "ADMIN"
          ? "/admin"
          : "/",
      );
    }
  }, [
    user,
    isLoading,
    isLoginPage,
    router,
  ]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-sm text-muted-foreground">
          Loading...
        </div>
      </div>
    );
  }

  if (!user && !isLoginPage) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-sm text-muted-foreground">
          Redirecting to login...
        </div>
      </div>
    );
  }

  if (user && isLoginPage) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-sm text-muted-foreground">
          Redirecting...
        </div>
      </div>
    );
  }

  return <>{children}</>;
}