import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getPatient } from "@/api/patients";
import { searchAppointments } from "@/api/appointments";
import type { Patient, Appointment } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { ArrowLeft, Phone, MapPin, Calendar, Heart } from "lucide-react";
import { formatDate, formatTime } from "@/lib/utils";

export function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    const pid = Number(id);
    Promise.all([
      getPatient(pid),
      searchAppointments({ patient: pid, _count: 10 }),
    ])
      .then(([p, a]) => {
        setPatient(p);
        setAppointments(a);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size={24} />
      </div>
    );
  }

  if (!patient) {
    return <div className="p-6 text-muted-foreground">Patient not found</div>;
  }

  const STATUS_VARIANT: Record<
    string,
    "default" | "success" | "warning" | "destructive"
  > = {
    booked: "default",
    fulfilled: "success",
    arrived: "warning",
    cancelled: "destructive",
    noshow: "destructive",
  };

  return (
    <div className="p-6">
      <Link
        to="/patients"
        className="mb-6 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={16} />
        Back to patients
      </Link>

      {/* Patient header */}
      <div className="mb-8 flex items-start gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-xl font-bold text-primary">
          {patient.given_name[0]}
          {patient.family_name[0]}
        </div>
        <div>
          <h1 className="text-2xl font-bold">
            {patient.given_name} {patient.family_name}
          </h1>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            {patient.mrn && <span>MRN: {patient.mrn}</span>}
            <span>DOB: {formatDate(patient.birth_date)}</span>
            {patient.gender && (
              <Badge variant="outline">{patient.gender}</Badge>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Contact Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Phone size={16} className="text-primary" />
              Contact Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {patient.phone && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Phone</span>
                <span>{patient.phone}</span>
              </div>
            )}
            {(patient.address_line || patient.city) && (
              <div className="flex items-start justify-between gap-4">
                <span className="text-muted-foreground">
                  <MapPin size={14} className="inline" /> Address
                </span>
                <span className="text-right">
                  {[
                    patient.address_line,
                    patient.city,
                    patient.state,
                    patient.postal_code,
                  ]
                    .filter(Boolean)
                    .join(", ")}
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Emergency Contact */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Heart size={16} className="text-destructive" />
              Emergency Contact
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {patient.emergency_contact_name ? (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Name</span>
                  <span>{patient.emergency_contact_name}</span>
                </div>
                {patient.emergency_contact_phone && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Phone</span>
                    <span>{patient.emergency_contact_phone}</span>
                  </div>
                )}
              </>
            ) : (
              <p className="text-muted-foreground">Not provided</p>
            )}
          </CardContent>
        </Card>

        {/* Appointments */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar size={16} className="text-primary" />
              Recent Appointments
            </CardTitle>
          </CardHeader>
          <CardContent>
            {appointments.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No appointments found
              </p>
            ) : (
              <div className="space-y-3">
                {appointments.map((apt) => (
                  <div
                    key={apt.id}
                    className="flex items-center justify-between rounded-lg border border-border p-3"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {apt.description ??
                          apt.appointment_type ??
                          "Appointment"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatDate(apt.start_time)} at{" "}
                        {formatTime(apt.start_time)}
                        {apt.provider_name && ` • ${apt.provider_name}`}
                      </p>
                    </div>
                    <Badge variant={STATUS_VARIANT[apt.status] ?? "outline"}>
                      {apt.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
