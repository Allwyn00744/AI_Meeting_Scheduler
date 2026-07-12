import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Search,
  CalendarCheck,
  CalendarClock,
  Ban,
  ChevronRight,
  Sparkles,
  ShieldCheck,
  Timer,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { DashboardSkeleton } from "@/components/ui/Skeleton";
import { meetingsApi } from "@/api/meetings";
import { analyticsApi } from "@/api/analytics";
import { getApiErrorMessage } from "@/api/client";

function formatDateParts(iso: string) {
  const d = new Date(iso);
  return {
    month: d.toLocaleDateString(undefined, { month: "short" }).toUpperCase(),
    day: d.getDate(),
    time: d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }),
  };
}

export default function Dashboard() {
  const navigate = useNavigate();

  const {
    data: meetings,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["meetings"],
    queryFn: () => meetingsApi.list({ limit: 50 }),
  });

  const { data: kpis } = useQuery({
    queryKey: ["kpis"],
    queryFn: analyticsApi.getKpis,
  });

  const now = Date.now();
  const upcoming = (meetings ?? []).filter((m) => new Date(m.start_time).getTime() >= now);
  const startOfWeek = new Date();
  startOfWeek.setHours(0, 0, 0, 0);
  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(endOfWeek.getDate() + 7);
  const thisWeek = upcoming.filter((m) => new Date(m.start_time) < endOfWeek);
  const cancelled = (meetings ?? []).filter((m) => m.status === "cancelled");

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-[28px] font-bold text-slate-900">Dashboard</h1>
          <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-500">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-600" />
            {upcoming.length} meetings upcoming
          </p>
        </div>
        <Button onClick={() => navigate("/ai-assistant")}>
          <Plus className="h-4 w-4" /> New meeting
        </Button>
      </div>

      {isLoading ? (
        <DashboardSkeleton />
      ) : isError ? (
        <EmptyState
          icon={<Ban className="h-5 w-5" />}
          title="Couldn't load your meetings"
          body={getApiErrorMessage(error, "Check that the backend is running and reachable.")}
        />
      ) : (
        <>
          <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <StatCard label="UPCOMING" value={upcoming.length} icon={<CalendarCheck className="h-4 w-4 text-slate-400" />} />
            <StatCard label="THIS WEEK" value={thisWeek.length} icon={<CalendarClock className="h-4 w-4 text-slate-400" />} />
            <StatCard label="CANCELLED" value={cancelled.length} icon={<Ban className="h-4 w-4 text-slate-400" />} />
          </div>

          {kpis && (
            <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <StatCard
                label="MEETINGS SCHEDULED"
                value={kpis.meetings_scheduled}
                icon={<CalendarCheck className="h-4 w-4 text-slate-400" />}
              />
              <StatCard
                label="CONFLICTS AVOIDED"
                value={kpis.conflicts_avoided}
                icon={<ShieldCheck className="h-4 w-4 text-slate-400" />}
              />
              <StatCard
                label="TIME SAVED (MIN)"
                value={kpis.time_saved_minutes}
                icon={<Timer className="h-4 w-4 text-slate-400" />}
              />
            </div>
          )}

          <Card className="mb-6">
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
              <h3 className="text-base font-semibold text-slate-900">Your meetings</h3>
              <div className="relative w-56">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                <input
                  className="h-9 w-full rounded-lg border border-slate-200 pl-8 text-xs placeholder:text-slate-400 focus-ring"
                  placeholder="Search meetings..."
                  onKeyDown={async (e) => {
                    if (e.key === "Enter") {
                      const keyword = (e.target as HTMLInputElement).value.trim();
                      if (keyword) navigate(`/meetings?q=${encodeURIComponent(keyword)}`);
                    }
                  }}
                />
              </div>
            </div>

            {!meetings || meetings.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  icon={<CalendarCheck className="h-5 w-5" />}
                  title="No meetings scheduled"
                  body="You don't have any meetings yet. Schedule one manually or describe it to the AI assistant."
                  actionLabel="New meeting"
                  onAction={() => navigate("/ai-assistant")}
                />
              </div>
            ) : (
              meetings
                .slice()
                .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
                .map((m, i, arr) => {
                  const { month, day, time } = formatDateParts(m.start_time);
                  return (
                    <button
                      key={m.id}
                      onClick={() => navigate(`/meetings/${m.id}`)}
                      className={`flex w-full items-center gap-4 px-6 py-4 text-left transition-colors hover:bg-slate-50 ${
                        i !== arr.length - 1 ? "border-b border-slate-100" : ""
                      }`}
                    >
                      <div className="w-14 shrink-0 text-center">
                        <p className="text-[11px] font-semibold text-brand-600">{month}</p>
                        <p className="text-lg font-bold text-slate-900">{day}</p>
                        <p className="text-[11px] text-slate-400">{time}</p>
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-slate-900">{m.title}</p>
                        <div className="mt-1.5 flex flex-wrap gap-1.5">
                          {m.location && (
                            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">{m.location}</span>
                          )}
                          {m.external_guests.length > 0 && (
                            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">
                              {m.external_guests.length} external guest{m.external_guests.length === 1 ? "" : "s"}
                            </span>
                          )}
                        </div>
                      </div>
                      <StatusBadge status={m.status} />
                      <ChevronRight className="h-4 w-4 shrink-0 text-slate-300" />
                    </button>
                  );
                })
            )}
          </Card>

          <div className="rounded-xl bg-gradient-to-br from-brand-600 to-brand-700 p-6 text-white">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-white/15">
              <Sparkles className="h-4.5 w-4.5" />
            </div>
            <p className="font-semibold">Try the AI assistant</p>
            <p className="mt-2 max-w-md text-sm text-brand-50/90">
              Describe a meeting in plain language — "30 min sync with the design team Tuesday
              afternoon" — and let AI find a time and book it.
            </p>
            <Button variant="secondary" className="mt-4 border-0 bg-white text-brand-700 hover:bg-brand-50" onClick={() => navigate("/ai-assistant")}>
              Open AI assistant
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
