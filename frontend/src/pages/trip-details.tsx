import { useEffect, useState } from "react";
import { useParams } from "react-router";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ArrowRight, MapPin } from "lucide-react";

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

function TripDetails() {
  const { id } = useParams();
  const [tripData, setTripData] = useState(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    event_name: "",
    event_description: "",
    event_type: "other",
    location_name: "",
    location_type: "other",
    location_coords: ["", ""],
    start_time: "",
    end_time: "",
  });

  useEffect(() => {
    fetch(`/api/trips/${id}`)
      .then((response) => response.json())
      .then((data) => setTripData(data))
      .catch((error) =>
        console.error("Error fetching trip details:", error)
      );
  }, [id]);

  if (!tripData) return <div className="p-6">Loading...</div>;

  const {
    trip_name,
    start_time,
    end_time,
    organizers,
    guests,
    events,
  } = tripData;

  const handleCreateEvent = async () => {
    if (!form.start_time || !form.end_time) {
      alert("Start and end time required");
      return;
    }
    try {
      const res = await fetch(`/api/trips/${id}/event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          location_coords: form.location_coords.map(Number),
          start_time: new Date(form.start_time).toISOString(),
          end_time: new Date(form.end_time).toISOString(),
        }),
      });

      if (!res.ok) throw new Error("Failed to create event");

      const updated = await res.json();
      setTripData(updated); // 🔥 refresh UI
      setOpen(false);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">{trip_name}</h1>
        <p className="text-muted-foreground">
          {new Date(start_time).toLocaleString()} <ArrowRight className="inline mx-1" />
          {new Date(end_time).toLocaleString()}
        </p>
      </div>

      <Separator />

      {/* People */}
      <Card>
        <CardHeader>
          <CardTitle>People</CardTitle>

        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <h3 className="font-semibold mb-1">Organizers</h3>
            {organizers.length === 0 ? (
              <p className="text-sm text-muted-foreground">None</p>
            ) : (
              organizers.map((user) => (
                <Badge key={user.user_id} className="mr-2">
                  {user.display_name}
                </Badge>
              ))
            )}
          </div>

          <div>
            <h3 className="font-semibold mb-1">Guests</h3>
            {guests.length === 0 ? (
              <p className="text-sm text-muted-foreground">None</p>
            ) : (
              guests.map((user) => (
                <Badge key={user.user_id} variant="secondary" className="mr-2">
                  {user.display_name}
                </Badge>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Events */}
      <Card>
        <CardHeader>
          <CardTitle>Events</CardTitle>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button>Add Event</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Event</DialogTitle>
              </DialogHeader>

              <div className="space-y-3">
                <div>
                  <Label>Name</Label>
                  <Input
                    value={form.event_name}
                    onChange={(e) =>
                      setForm({ ...form, event_name: e.target.value })
                    }
                  />
                </div>

                <div>
                  <Label>Description</Label>
                  <Input
                    value={form.event_description}
                    onChange={(e) =>
                      setForm({ ...form, event_description: e.target.value })
                    }
                  />
                </div>

                <div>
                  <Label>Location</Label>
                  <Input
                    value={form.location_name}
                    onChange={(e) =>
                      setForm({ ...form, location_name: e.target.value })
                    }
                  />
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Lat"
                    onChange={(e) =>
                      setForm({
                        ...form,
                        location_coords: [e.target.value, form.location_coords[1]],
                      })
                    }
                  />
                  <Input
                    placeholder="Lng"
                    onChange={(e) =>
                      setForm({
                        ...form,
                        location_coords: [form.location_coords[0], e.target.value],
                      })
                    }
                  />
                </div>

                <div>
                  <Label>Start</Label>
                  <Input
                    type="datetime-local"
                    onChange={(e) =>
                      setForm({ ...form, start_time: e.target.value })
                    }
                  />
                </div>

                <div>
                  <Label>End</Label>
                  <Input
                    type="datetime-local"
                    onChange={(e) =>
                      setForm({ ...form, end_time: e.target.value })
                    }
                  />
                </div>

                <Button onClick={handleCreateEvent} className="w-full">
                  Create
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent className="space-y-4">
          {events.length === 0 ? (
            <p className="text-muted-foreground">No events yet</p>
          ) : (
            events.map((event) => (
              <div key={event.event_id} className="border p-3 rounded-xl">
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold">{event.event_name}</h3>
                  <Badge>{event.event_type}</Badge>
                </div>

                <p className="text-sm text-muted-foreground">
                  {new Date(event.start_time).toLocaleString()} <ArrowRight className="inline mx-1" />
                  {new Date(event.end_time).toLocaleString()}
                </p>

                <p className="text-sm mt-1">
                  {event.event_description || "No description"}
                </p>

                {event.location && (
                  <p className="text-sm mt-1 text-muted-foreground">
                    <MapPin className="inline" /> {event.location.name}
                  </p>
                )}
              </div>
            ))
          )}
        </CardContent>
      </Card>

    </div>
  );
}

export default TripDetails;
