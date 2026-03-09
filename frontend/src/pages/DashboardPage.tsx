import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { searchPatients } from "@/api/patients";
import { searchAppointments } from "@/api/appointments";
import type { Patient, Appointment } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Users,
  CalendarDays,
  MessageSquare,
  Activity,
  ArrowRight,
} from "lucide-react";
import { formatDate, formatTime } from "@/lib/utils";

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  useEffect(() => {
    searchPatients({ _count: 5 })
      .then(setPatients)
      .catch(() => {});
    searchAppointments({ _count: 5 })
      .then(setAppointments)
      .catch(() => {});
  }, []);

  const stats = [
    {
      label: "Patients",
      value: patients.length,
      icon: Users,
      color: "text-blue-400 bg-blue-500/10",
    },
    {
      label: "Appointments",
      value: appointments.length,
      icon: CalendarDays,
      color: "text-purple-400 bg-purple-500/10",
    },
    {
      label: "Active Agents",
      value: 4,
      icon: Activity,
      color: "text-emerald-400 bg-emerald-500/10",
    },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          Welcome back
          {user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
        </h1>
        <p className="mt-1 text-muted-foreground">
          Here's what's happening in your healthcare system
        </p>
      </div>

      {/* Stats */}
      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <Card key={label} className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="mt-1 text-3xl font-bold">{value}</p>
              </div>
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-xl ${color}`}
              >
                <Icon size={24} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Quick action */}
      <Card className="mb-8 overflow-hidden bg-gradient-to-r from-primary/20 via-primary/10 to-transparent p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Start a conversation</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Use the AI assistant for patient intake, scheduling, or care
              management
            </p>
          </div>
          <Link to="/chat">
            <Button className="gap-2">
              <MessageSquare size={16} />
              Open Chat
              <ArrowRight size={14} />
            </Button>
          </Link>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent patients */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Patients</CardTitle>
            <Link
              to="/patients"
              className="text-xs text-primary hover:underline"
            >
              View all
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {patients.length === 0 ? (
              <p className="text-sm text-muted-foreground">No patients yet</p>
            ) : (
              patients.map((p) => (
                <Link
                  key={p.id}
                  to={`/patients/${p.id}`}
                  className="flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-accent/50"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    {p.given_name[0]}
                    {p.family_name[0]}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {p.given_name} {p.family_name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(p.birth_date)}
                    </p>
                  </div>
                </Link>
              ))
            )}
          </CardContent>
        </Card>

        {/* Upcoming appointments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Upcoming Appointments</CardTitle>
            <Link
              to="/appointments"
              className="text-xs text-primary hover:underline"
            >
              View all
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {appointments.length === 0 ? (
              <p className="text-sm text-muted-foreground">No appointments</p>
            ) : (
              appointments.map((apt) => (
                <div
                  key={apt.id}
                  className="flex items-center justify-between rounded-lg border border-border p-3"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {apt.description ?? `Appointment #${apt.id}`}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(apt.start_time)} at{" "}
                      {formatTime(apt.start_time)}
                    </p>
                  </div>
                  <Badge
                    variant={apt.status === "booked" ? "default" : "outline"}
                  >
                    {apt.status}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
