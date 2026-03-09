import { useEffect, useState } from "react";
import { searchAppointments } from "@/api/appointments";
import type { Appointment } from "@/types/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { CalendarDays, Clock } from "lucide-react";
import { formatDate, formatTime } from "@/lib/utils";

export function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    searchAppointments({ _count: 50 })
      .then(setAppointments)
      .finally(() => setLoading(false));
  }, []);

  const STATUS_VARIANT: Record<
    string,
    "default" | "success" | "warning" | "destructive"
  > = {
    booked: "default",
    fulfilled: "success",
    arrived: "warning",
    cancelled: "destructive",
    noshow: "destructive",
    proposed: "outline" as "default",
    pending: "warning",
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
          <CalendarDays size={20} className="text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Appointments</h1>
          <p className="text-sm text-muted-foreground">
            {appointments.length} appointments
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Spinner size={24} />
        </div>
      ) : appointments.length === 0 ? (
        <div className="py-20 text-center text-muted-foreground">
          No appointments found
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {appointments.map((apt) => (
            <Card key={apt.id} className="p-4">
              <div className="mb-3 flex items-start justify-between">
                <p className="font-medium text-sm">
                  {apt.description ??
                    apt.appointment_type ??
                    `Appointment #${apt.id}`}
                </p>
                <Badge variant={STATUS_VARIANT[apt.status] ?? "outline"}>
                  {apt.status}
                </Badge>
              </div>
              <div className="space-y-2 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <CalendarDays size={12} />
                  <span>{formatDate(apt.start_time)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock size={12} />
                  <span>
                    {formatTime(apt.start_time)} – {formatTime(apt.end_time)}
                  </span>
                </div>
                {apt.provider_name && <p>Provider: {apt.provider_name}</p>}
                {apt.location && <p>Location: {apt.location}</p>}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
