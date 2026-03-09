import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { searchPatients } from "@/api/patients";
import type { Patient } from "@/types/api";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Users, Search, ChevronRight } from "lucide-react";
import { formatDate } from "@/lib/utils";

export function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadPatients();
  }, []);

  async function loadPatients() {
    setLoading(true);
    try {
      const data = await searchPatients({ _count: 50 });
      setPatients(data);
    } catch {
      // handle silently
    } finally {
      setLoading(false);
    }
  }

  const filtered = patients.filter((p) => {
    const q = search.toLowerCase();
    return (
      p.given_name.toLowerCase().includes(q) ||
      p.family_name.toLowerCase().includes(q) ||
      p.mrn?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <Users size={20} className="text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Patients</h1>
            <p className="text-sm text-muted-foreground">
              {patients.length} registered patients
            </p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-6 max-w-md">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          placeholder="Search by name or MRN..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Spinner size={24} />
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-20 text-center text-muted-foreground">
          No patients found
        </div>
      ) : (
        <div className="grid gap-3">
          {filtered.map((patient) => (
            <Link key={patient.id} to={`/patients/${patient.id}`}>
              <Card className="flex items-center justify-between p-4 transition-colors hover:bg-accent/50">
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                    {patient.given_name[0]}
                    {patient.family_name[0]}
                  </div>
                  <div>
                    <p className="font-medium">
                      {patient.given_name} {patient.family_name}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      {patient.mrn && <span>MRN: {patient.mrn}</span>}
                      <span>DOB: {formatDate(patient.birth_date)}</span>
                      {patient.gender && (
                        <Badge variant="outline">{patient.gender}</Badge>
                      )}
                    </div>
                  </div>
                </div>
                <ChevronRight size={16} className="text-muted-foreground" />
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
