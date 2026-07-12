import * as React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sparkles, PenSquare, Video, X, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { SuccessDialog } from "@/components/ui/SuccessDialog";
import { usersApi } from "@/api/users";
import { resourcesApi } from "@/api/resources";
import { schedulerApi } from "@/api/scheduler";
import { aiApi } from "@/api/ai";
import { getApiErrorMessage } from "@/api/client";
import { useAuth } from "@/hooks/useAuth";
import type { SuggestedSlot } from "@/types";
import { cn } from "@/lib/utils";

function toDatetimeLocal(iso: string) {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function AIAssistant() {
  const navigate = useNavigate();
  const { push } = useToast();
  const { user } = useAuth();

  const { data: allUsers } = useQuery({ queryKey: ["users"], queryFn: usersApi.list });
  const { data: resources } = useQuery({ queryKey: ["resources"], queryFn: () => resourcesApi.list(false) });

  // --- AI text-to-schedule path (POST /ai/schedule-text) ---
  const [aiText, setAiText] = React.useState("");
  const [aiSubmitting, setAiSubmitting] = React.useState(false);
  const [aiSuccessOpen, setAiSuccessOpen] = React.useState(false);

  const scheduleWithAi = async () => {
    if (!aiText.trim()) {
      push("error", "Describe the meeting first");
      return;
    }
    setAiSubmitting(true);
    try {
      const result = await aiApi.scheduleFromText(aiText);
      push("success", result.message);
      setAiSuccessOpen(true);
    } catch (err) {
      push("error", "Couldn't schedule that meeting", getApiErrorMessage(err));
    } finally {
      setAiSubmitting(false);
    }
  };

  // --- Manual scheduling path (POST /scheduler/schedule + /suggest-slots) ---
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [startTime, setStartTime] = React.useState("");
  const [endTime, setEndTime] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [resourceId, setResourceId] = React.useState<string>("");
  const [participantIds, setParticipantIds] = React.useState<number[]>([]);
  const [guestQuery, setGuestQuery] = React.useState("");
  const [slots, setSlots] = React.useState<SuggestedSlot[] | null>(null);
  const [slotsLoading, setSlotsLoading] = React.useState(false);
  const [manualSubmitting, setManualSubmitting] = React.useState(false);
  const [manualErrors, setManualErrors] = React.useState<Record<string, string>>({});

  const otherUsers = (allUsers ?? []).filter((u) => u.id !== user?.id);
  const filteredUsers = otherUsers.filter(
    (u) =>
      !participantIds.includes(u.id) &&
      (guestQuery.trim() === "" || u.name.toLowerCase().includes(guestQuery.toLowerCase()))
  );

  const buildPayload = () => ({
    title,
    description: description || undefined,
    start_time: startTime ? new Date(startTime).toISOString() : "",
    end_time: endTime ? new Date(endTime).toISOString() : "",
    location: location || undefined,
    resource_id: resourceId ? Number(resourceId) : undefined,
    participant_ids: participantIds,
    external_guest_emails: [],
  });

  const validateManual = () => {
    const errs: Record<string, string> = {};
    if (!title.trim()) errs.title = "Title is required.";
    if (!startTime) errs.start_time = "Start time is required.";
    if (!endTime) errs.end_time = "End time is required.";
    if (startTime && endTime && new Date(endTime) <= new Date(startTime)) {
      errs.end_time = "End time must be after start time.";
    }
    setManualErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const fetchSuggestions = async () => {
    if (!validateManual()) return;
    setSlotsLoading(true);
    try {
      const result = await schedulerApi.suggestSlots(buildPayload());
      setSlots(result.slots);
      if (result.slots.length === 0) {
        push("info", "No open slots found", "Try widening the time range or removing a participant.");
      }
    } catch (err) {
      push("error", "Couldn't fetch suggestions", getApiErrorMessage(err));
    } finally {
      setSlotsLoading(false);
    }
  };

  const bookMeeting = async () => {
    if (!validateManual()) return;
    setManualSubmitting(true);
    try {
      const result = await schedulerApi.schedule(buildPayload());
      push("success", result.message);
      navigate(`/meetings/${result.meeting_ids[0]}`);
    } catch (err) {
      push("error", "Couldn't book this meeting", getApiErrorMessage(err));
    } finally {
      setManualSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="text-[28px] font-bold text-slate-900">Schedule a meeting</h1>
        <p className="mt-1 text-sm text-slate-500">Describe it in plain language, or fill the form manually.</p>
      </div>

      <Card className="mb-6">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
              <Sparkles className="h-4 w-4" />
            </div>
            <p className="font-semibold text-slate-900">Schedule with AI</p>
          </div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Natural language entry</p>
        </div>
        <div className="px-6 pb-6">
          <Textarea
            className="h-28 border-0 bg-slate-50 focus:bg-white"
            placeholder="e.g., 'Schedule a 30-minute sync with the Design Team on Tuesday afternoon between 2 PM and 5 PM.'"
            value={aiText}
            onChange={(e) => setAiText(e.target.value)}
          />
          <div className="mt-4 flex justify-end">
            <Button onClick={scheduleWithAi} loading={aiSubmitting}>
              <Sparkles className="h-4 w-4" /> Parse & schedule with AI
            </Button>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Requires the backend's Gemini integration to be configured (GEMINI_API_KEY); returns 503 otherwise.
          </p>
        </div>
      </Card>

      <div className="mb-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-slate-200" />
        <span className="text-xs font-medium text-slate-400">OR</span>
        <div className="h-px flex-1 bg-slate-200" />
      </div>

      <Card>
        <div className="flex items-center gap-2.5 px-6 py-4">
          <PenSquare className="h-4 w-4 text-slate-500" />
          <p className="font-semibold text-slate-900">Fill Manually</p>
        </div>
        <div className="grid grid-cols-1 gap-x-8 gap-y-4 px-6 pb-6 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Meeting Title</label>
            <Input
              placeholder="Design Review"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              error={manualErrors.title}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Location</label>
            <Input
              icon={<Video className="h-4 w-4" />}
              placeholder="Google Meet, Zoom, or Office Room"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Start</label>
            <Input
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              error={manualErrors.start_time}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">End</label>
            <Input
              type="datetime-local"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              error={manualErrors.end_time}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Resource (optional)</label>
            <select
              className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm focus-ring"
              value={resourceId}
              onChange={(e) => setResourceId(e.target.value)}
            >
              <option value="">None</option>
              {(resources ?? []).map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Description</label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Agenda / notes" />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Participants</label>
            <div className="relative rounded-lg border border-slate-200 bg-white p-2">
              <div className="flex flex-wrap items-center gap-1.5">
                {participantIds.map((id) => {
                  const u = otherUsers.find((x) => x.id === id);
                  if (!u) return null;
                  return (
                    <span
                      key={id}
                      className="flex items-center gap-1 rounded-full bg-slate-100 py-1 pl-2.5 pr-1.5 text-xs font-medium text-slate-700"
                    >
                      {u.name}
                      <button
                        onClick={() => setParticipantIds((prev) => prev.filter((x) => x !== id))}
                        className="rounded-full p-0.5 hover:bg-slate-200"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  );
                })}
                <input
                  className="min-w-[140px] flex-1 border-0 text-sm outline-none placeholder:text-slate-400"
                  placeholder="Search teammates..."
                  value={guestQuery}
                  onChange={(e) => setGuestQuery(e.target.value)}
                />
              </div>
              {guestQuery && filteredUsers.length > 0 && (
                <div className="absolute left-0 right-0 top-full z-10 mt-1 max-h-48 overflow-auto rounded-lg border border-slate-200 bg-white shadow-lg">
                  {filteredUsers.map((u) => (
                    <button
                      key={u.id}
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50"
                      onClick={() => {
                        setParticipantIds((prev) => [...prev, u.id]);
                        setGuestQuery("");
                      }}
                    >
                      <span className="font-medium text-slate-800">{u.name}</span>
                      <span className="text-xs text-slate-400">{u.email}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {slots && (
          <div className="border-t border-slate-100 px-6 py-5">
            <p className="mb-2 text-xs font-medium text-slate-500">AI-suggested slots (from your + participants' availability)</p>
            {slots.length === 0 ? (
              <p className="text-sm text-slate-400">No open slots found in this window.</p>
            ) : (
              <div className="flex flex-col gap-2">
                {slots.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setStartTime(toDatetimeLocal(s.start_time));
                      setEndTime(toDatetimeLocal(s.end_time));
                    }}
                    className={cn(
                      "flex items-center justify-between rounded-lg border px-3 py-2 text-left transition-colors",
                      "border-slate-200 hover:border-brand-400 hover:bg-brand-50"
                    )}
                  >
                    <span className="text-sm text-slate-800">
                      {new Date(s.start_time).toLocaleString(undefined, {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                      {" – "}
                      {new Date(s.end_time).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <span className="text-xs font-medium text-brand-600">Use this time</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-center justify-end gap-3 border-t border-slate-100 px-6 py-4">
          <Button variant="secondary" onClick={fetchSuggestions} loading={slotsLoading}>
            {slotsLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Suggest slots
          </Button>
          <Button onClick={bookMeeting} loading={manualSubmitting}>
            Book Meeting
          </Button>
        </div>
      </Card>

      <SuccessDialog
        open={aiSuccessOpen}
        onClose={() => {
          setAiSuccessOpen(false);
          navigate("/dashboard");
        }}
        title="Meeting scheduled"
        description="The AI assistant parsed your request and booked the meeting."
        actionLabel="Back to dashboard"
      />
    </div>
  );
}
