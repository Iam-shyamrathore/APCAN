import { useEffect, useState } from "react";
import { getAuditLogs } from "@/api/audit";
import type { AuditLog } from "@/types/api";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Shield, Search } from "lucide-react";
import { relativeTime } from "@/lib/utils";

export function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    getAuditLogs({ limit: 200 })
      .then((data) => {
        setLogs(data.logs);
        setTotal(data.total);
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = logs.filter((log) => {
    const q = search.toLowerCase();
    return (
      log.action.toLowerCase().includes(q) ||
      log.tool_name?.toLowerCase().includes(q) ||
      log.agent?.toLowerCase().includes(q) ||
      log.resource_type?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
          <Shield size={20} className="text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Audit Logs</h1>
          <p className="text-sm text-muted-foreground">{total} entries</p>
        </div>
      </div>

      <div className="relative mb-6 max-w-md">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          placeholder="Filter by action, tool, agent..."
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
          No audit logs found
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((log) => (
            <Card
              key={log.id}
              className="flex items-center justify-between p-4"
            >
              <div className="flex items-center gap-4">
                <div
                  className={`h-2 w-2 rounded-full ${log.success ? "bg-success" : "bg-destructive"}`}
                />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{log.action}</span>
                    {log.tool_name && (
                      <span className="font-mono text-xs text-muted-foreground">
                        {log.tool_name}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {log.agent && <Badge variant="outline">{log.agent}</Badge>}
                    {log.resource_type && <span>{log.resource_type}</span>}
                    {log.patient_id && <span>Patient #{log.patient_id}</span>}
                    <span>{relativeTime(log.timestamp)}</span>
                  </div>
                  {log.error_message && (
                    <p className="mt-1 text-xs text-destructive">
                      {log.error_message}
                    </p>
                  )}
                </div>
              </div>
              <span className="text-xs text-muted-foreground">#{log.id}</span>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
