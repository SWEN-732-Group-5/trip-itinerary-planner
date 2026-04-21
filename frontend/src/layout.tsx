import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useSession } from "@/lib/auth/auth";
import { useSelf } from "@/api/user";
import { Link } from "react-router";
import { User } from "lucide-react";

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  const { isLoggedIn } = useSession()
  const { data: profile } = useSelf(isLoggedIn)

  return (
    <div className={cn("flex min-h-screen flex-col bg-background")}>
      <Toaster />
      <header className="border-b bg-background/95 sticky top-0 z-50 w-full">
        <div className="flex h-16 w-full items-center justify-between px-4 md:px-6">
          <h1 className="text-lg font-semibold tracking-tight">Trip Itinerary Planner</h1>
          {isLoggedIn && (
            <Button asChild variant="ghost" className="h-auto px-2 py-1.5">
              <Link to="/account" className="flex items-center gap-2">
                <Avatar size="sm">
                  <AvatarFallback>
                    <User className="h-3.5 w-3.5" />
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium">{profile?.display_name ?? "Account"}</span>
              </Link>
            </Button>
          )}
        </div>
      </header>
      <main className="flex-1 flex items-start justify-center mt-8">
        <Card className="w-full max-w-3xl mx-4 shadow-md">
          <CardContent className="p-6">{children}</CardContent>
        </Card>
      </main>
      <footer className="border-t bg-background/95 mt-auto py-4 text-center text-xs text-muted-foreground">
        &copy; 2026 Trip Itinerary Planner. All rights reserved.
      </footer>
    </div>
  );
}
