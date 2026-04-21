import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className={cn("flex min-h-screen flex-col bg-background")}>
      <Toaster />
      <header className="border-b bg-background/95 sticky top-0 z-50 w-full">
        <div className="container flex h-16 items-center px-4">
          <h1 className="text-lg font-semibold tracking-tight">Trip Itinerary Planner</h1>
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
