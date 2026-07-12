import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Clock, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Switch } from "@/components/ui/Switch";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { availabilityApi } from "@/api/availability";
import { getApiErrorMessage } from "@/api/client";
import { useAuth } from "@/hooks/useAuth";
import type { Availability as AvailabilityRow } from "@/types";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function Availability() {
  const { push } = useToast();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const { data: rows, isLoading } = useQuery({
    queryKey: ["availability"],
    queryFn: availabilityApi.list,
  });

  const createRow = useMutation({
    mutationFn: (day: string) =>
      availabilityApi.create({ day_of_week: day, start_time: "09:00:00", end_time: "17:00:00", is_available: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["availability"] });
      push("success", "Day added");
    },
    onError: (err) => push("error", "Couldn't add day", getApiErrorMessage(err)),
  });

  const updateRow = useMutation({
    mutationFn: ({ id, ...payload }: Partial<AvailabilityRow> & { id: number }) =>
      availabilityApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["availability"] }),
    onError: (err) => push("error", "Couldn't update", getApiErrorMessage(err)),
  });

  const deleteRow = useMutation({
    mutationFn: (id: number) => availabilityApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["availability"] });
      push("success", "Day removed");
    },
    onError: (err) => push("error", "Couldn't remove day", getApiErrorMessage(err)),
  });

  const daysConfigured = new Set((rows ?? []).map((r) => r.day_of_week));
  const missingDays = DAYS.filter((d) => !daysConfigured.has(d));

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6">
        <h1 className="text-[28px] font-bold text-slate-900">Availability</h1>
        <p className="mt-1 text-sm text-slate-500">
          Set the hours you're open to being scheduled. Your timezone is {user?.timezone}.
        </p>
      </div>

      <Card className="mb-6 overflow-hidden">
        <div className="flex items-center justify-between bg-brand-50 px-6 py-3.5">
          <p className="font-semibold text-slate-900">Weekly Schedule</p>
          {missingDays.length > 0 && (
            <select
              className="h-8 rounded-lg border border-brand-200 bg-white px-2 text-xs text-brand-700"
              value=""
              onChange={(e) => {
                if (e.target.value) createRow.mutate(e.target.value);
              }}
            >
              <option value="">+ Add a day...</option>
              {missingDays.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          )}
        </div>

        {isLoading ? (
          <div className="p-6">
            <div className="h-32 animate-pulse rounded-lg bg-slate-100" />
          </div>
        ) : !rows || rows.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<Clock className="h-5 w-5" />}
              title="No availability set"
              body="Add days you're open to being scheduled."
              actionLabel="Add Monday"
              onAction={() => createRow.mutate("Monday")}
            />
          </div>
        ) : (
          rows.map((row, i) => (
            <div
              key={row.id}
              className={`flex flex-wrap items-center gap-3 px-6 py-3.5 ${
                i !== rows.length - 1 ? "border-b border-slate-100" : ""
              } ${!row.is_available ? "bg-slate-50/60" : ""}`}
            >
              <span className={`w-24 text-sm ${row.is_available ? "text-slate-800" : "text-slate-400"}`}>
                {row.day_of_week}
              </span>
              <Input
                type="time"
                defaultValue={row.start_time.slice(0, 5)}
                disabled={!row.is_available}
                className="h-9 w-32"
                onBlur={(e) =>
                  e.target.value &&
                  updateRow.mutate({ id: row.id, start_time: `${e.target.value}:00` })
                }
              />
              <span className="text-sm text-slate-400">to</span>
              <Input
                type="time"
                defaultValue={row.end_time.slice(0, 5)}
                disabled={!row.is_available}
                className="h-9 w-32"
                onBlur={(e) =>
                  e.target.value && updateRow.mutate({ id: row.id, end_time: `${e.target.value}:00` })
                }
              />
              <button onClick={() => deleteRow.mutate(row.id)} className="text-slate-400 hover:text-red-500">
                <Trash2 className="h-4 w-4" />
              </button>
              <div className="ml-auto flex items-center gap-2">
                <span className="text-sm text-slate-500">{row.is_available ? "Available" : "Unavailable"}</span>
                <Switch
                  checked={row.is_available}
                  onCheckedChange={(v) => updateRow.mutate({ id: row.id, is_available: v })}
                />
              </div>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
