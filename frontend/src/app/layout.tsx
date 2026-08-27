import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Providers } from "@/app/providers";
import { APP_USER_NAME } from "@/config";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Embedded Config — Security Setup",
  description: "Configure automotive ECU projects and run security test coverage.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-background text-foreground">
        <Providers>
          <SidebarProvider>
            <AppSidebar />
            <SidebarInset className="surface-grain">
              <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-3 border-b border-border/60 bg-background/80 px-5 backdrop-blur-md">
                <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-foreground" />
                <div className="h-5 w-px bg-border" />
                <div className="flex flex-1 items-center gap-2 text-sm">
                  <span className="text-muted-foreground">Signed in as</span>
                  <span className="font-medium text-foreground">{APP_USER_NAME}</span>
                  <span className="ml-2 inline-flex h-1.5 w-1.5 rounded-full bg-[var(--signal)] shadow-[0_0_0_3px_oklch(0.62_0.13_215/0.18)]" />
                </div>
                <div className="hidden items-center gap-1.5 rounded-full border border-border/60 bg-card/60 px-2.5 py-1 text-xs text-muted-foreground sm:flex">
                  <kbd className="rounded border border-border/80 bg-background px-1 font-mono text-[10px]">⌘</kbd>
                  <kbd className="rounded border border-border/80 bg-background px-1 font-mono text-[10px]">B</kbd>
                  <span className="ml-1">Toggle sidebar</span>
                </div>
              </header>
              <main className="flex-1 overflow-auto">
                <div className="mx-auto w-full max-w-6xl px-6 py-8 sm:px-8 sm:py-10">
                  {children}
                </div>
              </main>
            </SidebarInset>
          </SidebarProvider>
        </Providers>
      </body>
    </html>
  );
}
