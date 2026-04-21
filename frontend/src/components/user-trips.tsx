import { useState } from "react"
import { useMutateTrip, useTrips } from "@/api/trip"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { AlertCircle, MapPin, CalendarDays } from "lucide-react"
import { toast } from "sonner"
import { Link } from "react-router"

export const UserTrips = () => {
  const { data: trips, isLoading, error, isError } = useTrips()
  const { mutateAsync: createTrip, isPending: isCreatingTrip } = useMutateTrip()
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [tripName, setTripName] = useState("")
  const [startTime, setStartTime] = useState("")
  const [endTime, setEndTime] = useState("")

  const toApiDatetime = (value: string) => {
    if (!value) return value
    return value.length === 16 ? `${value}:00Z` : value
  }

  const resetCreateTripForm = () => {
    setTripName("")
    setStartTime("")
    setEndTime("")
  }

  const handleCreateTrip = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const trimmedName = tripName.trim()
    if (!trimmedName || !startTime || !endTime) {
      toast.error("Please provide a trip name, start date, and end date.")
      return
    }

    const startDate = new Date(startTime)
    const endDate = new Date(endTime)
    if (endDate < startDate) {
      toast.error("End date must be after start date.")
      return
    }

    try {
      await createTrip({
        trip_name: trimmedName,
        start_time: toApiDatetime(startTime),
        end_time: toApiDatetime(endTime),
      })
      toast.success("Trip created.")
      setIsCreateDialogOpen(false)
      resetCreateTripForm()
    } catch (createError) {
      toast.error(
        createError instanceof Error ? createError.message : "Failed to create trip."
      )
    }
  }

  const createTripForm = (
    <form id="create-trip-form" onSubmit={handleCreateTrip} className="space-y-3">
      <Input
        placeholder="Trip name"
        value={tripName}
        onChange={(e) => setTripName(e.target.value)}
        autoComplete="off"
        required
      />
      <Input
        type="datetime-local"
        value={startTime}
        onChange={(e) => setStartTime(e.target.value)}
        required
      />
      <Input
        type="datetime-local"
        value={endTime}
        onChange={(e) => setEndTime(e.target.value)}
        required
      />
    </form>
  )

  const createTripDialogContent = (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Create Trip</DialogTitle>
        <DialogDescription>
          Add the trip basics now. You can add events from the trip details page.
        </DialogDescription>
      </DialogHeader>
      {createTripForm}
      <DialogFooter>
        <Button
          type="submit"
          form="create-trip-form"
          disabled={isCreatingTrip}
        >
          {isCreatingTrip ? "Creating..." : "Create Trip"}
        </Button>
      </DialogFooter>
    </DialogContent>
  )

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
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <div className="p-6">
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12 text-center gap-3">
              <MapPin className="h-10 w-10 text-muted-foreground" />
              <p className="text-muted-foreground text-sm">
                You have no trips yet. Start planning your first trip!
              </p>
              <Button onClick={() => setIsCreateDialogOpen(true)}>
                Create Trip
              </Button>
            </CardContent>
          </Card>
        </div>
        {createTripDialogContent}
      </Dialog>
    )
  }

  return (
    <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-2xl font-bold tracking-tight">Your Trips</h2>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{trips.length} trip{trips.length !== 1 ? "s" : ""}</Badge>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              Create Trip
            </Button>
          </div>
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
      {createTripDialogContent}
    </Dialog>
  )
}
