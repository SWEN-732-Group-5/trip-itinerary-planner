import { useTrips } from "@/api/trip"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, MapPin, CalendarDays } from "lucide-react"
import { Link } from "react-router"

export const UserTrips = () => {
  const { data: trips, isLoading, error, isError } = useTrips()

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-40" />
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Error loading trips:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!trips || trips.length === 0) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center gap-3">
            <MapPin className="h-10 w-10 text-muted-foreground" />
            <p className="text-muted-foreground text-sm">
              You have no trips yet. Start planning your first trip!
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Your Trips</h2>
        <Badge variant="secondary">{trips.length} trip{trips.length !== 1 ? "s" : ""}</Badge>
      </div>

      <ul className="space-y-3">
        {trips.map((trip) => (
          <li key={trip.trip_id}>
            <Link to={`/trips/${trip.trip_id}`} className="block group">
              <Card className="transition-colors hover:bg-accent hover:text-accent-foreground cursor-pointer">
                <CardContent className="flex items-center justify-between py-4 px-5">
                  <div className="space-y-1">
                    <p className="text-base font-semibold leading-none group-hover:underline underline-offset-2">
                      {trip.trip_name}
                    </p>
                    <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                      <CalendarDays className="h-3.5 w-3.5" />
                      <span>
                        {new Date(trip.start_time).toLocaleDateString()} –{" "}
                        {new Date(trip.end_time).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <MapPin className="h-4 w-4 text-muted-foreground group-hover:text-accent-foreground transition-colors shrink-0" />
                </CardContent>
              </Card>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
