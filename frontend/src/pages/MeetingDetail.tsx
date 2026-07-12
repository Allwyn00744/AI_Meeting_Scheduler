import * as React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft, Pencil, Trash2, Clock, DoorOpen, Sparkles, Mail,
  TriangleAlert, ArrowRight, X, UserPlus, Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";
import { Avatar } from "@/components/ui/Avatar";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Dialog } from "@/components/ui/Dialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input, Textarea } from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { meetingsApi } from "@/api/meetings";
import { participantsApi } from "@/api/participants";
import { usersApi } from "@/api/users";
import { meetingIntelligenceApi } from "@/api/meetingIntelligence";
import { aiApi } from "@/api/ai";
import { getApiErrorMessage } from "@/api/client";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const TABS = ["Details", "Participants", "Notes & Summary", "Action items"] as const;

function initialsOf(name: string) {
  const parts = name.trim().split(/\s+/);
  return parts.length === 1 ? parts[0].slice(0, 2).toUpperCase() : (parts[0][0] + parts[1][0]).toUpperCase();
}

export default function MeetingDetail() {
  const { id } = useParams();
  const meetingId = Number(id);
  const navigate = useNavigate();
  const { push } = useToast();
  const { user: me } = useAuth();
  const queryClient = useQueryClient();
  const [tab, setTab] = React.useState<(typeof TABS)[number]>("Details");
  const [deleteOpen, setDeleteOpen] = React.useState(false);
  const [editOpen, setEditOpen] = React.useState(false);

  const { data: meeting, isLoading, isError, error } = useQuery({
    queryKey: ["meeting", meetingId],
    queryFn: () => meetingsApi.getById(meetingId),
    enabled: Number.isFinite(meetingId),
  });

  const { data: users } = useQuery({ queryKey: ["users"], queryFn: usersApi.list });
  const userMap = React.useMemo(() => new Map((users ?? []).map((u) => [u.id, u])), [users]);

  const deleteMeeting = useMutation({
    mutationFn: () => meetingsApi.remove(meetingId),
    onSuccess: () => {
      push("success", "Meeting cancelled");
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      navigate("/dashboard");
    },
    onError: (err) => push("error", "Couldn't cancel meeting", getApiErrorMessage(err)),
  });

  if (isLoading) {
    return <div className="mx-auto h-64 max-w-3xl animate-pulse rounded-xl bg-slate-100" />;
  }

  if (isError || !meeting) {
    return (
      <div className="mx-auto max-w-3xl">
        <EmptyState
          icon={<TriangleAlert className="h-5 w-5" />}
          title="Couldn't load this meeting"
          body={getApiErrorMessage(error, "It may not exist, or you may not have access to it.")}
          actionLabel="Back to dashboard"
          onAction={() => navigate("/dashboard")}
        />
      </div>
    );
  }

  const isOwner = meeting.owner_id === me?.id;
  const owner = userMap.get(meeting.owner_id);

  return (
    <div className="mx-auto max-w-3xl">
      <button
        onClick={() => navigate("/dashboard")}
        className="mb-3 flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to meetings
      </button>

      <div className="mb-2 flex flex-wrap items-start justify-between gap-3">
        <h1 className="text-xl font-bold text-slate-900">{meeting.title}</h1>
        {isOwner && (
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => setEditOpen(true)}>
              <Pencil className="h-3.5 w-3.5" /> Edit
            </Button>
            <Button variant="danger" size="sm" onClick={() => setDeleteOpen(true)}>
              <Trash2 className="h-3.5 w-3.5" /> Cancel
            </Button>
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <StatusBadge status={meeting.status} />
        {owner && <span className="text-xs text-slate-400">Organized by {owner.name}</span>}
      </div>

      {meeting.status !== "cancelled" && (
        <button
          onClick={() => navigate(`/meetings/${meeting.id}/reschedule`)}
          className="mt-3 flex w-full items-center justify-between gap-2 rounded-lg bg-slate-50 px-4 py-3 text-left hover:bg-slate-100"
        >
          <span className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <TriangleAlert className="h-4 w-4 text-amber-500" /> Check for a better time / resolve a conflict
          </span>
          <ArrowRight className="h-4 w-4 text-slate-400" />
        </button>
      )}

      <div className="my-4 flex flex-wrap gap-x-6 gap-y-1.5 text-sm text-slate-500">
        <span className="flex items-center gap-1.5">
          <Clock className="h-4 w-4" />
          {new Date(meeting.start_time).toLocaleString(undefined, {
            weekday: "short",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
          {" – "}
          {new Date(meeting.end_time).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
        </span>
        {meeting.location && (
          <span className="flex items-center gap-1.5">
            <DoorOpen className="h-4 w-4" /> {meeting.location}
          </span>
        )}
      </div>

      <div className="mb-5 flex gap-1 overflow-x-auto border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "-mb-px whitespace-nowrap border-b-2 px-3 py-2 text-sm transition-colors",
              tab === t ? "border-brand-600 font-medium text-brand-700" : "border-transparent text-slate-500 hover:text-slate-800"
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Details" && (
        <div>
          <p className="mb-1 text-xs font-medium text-slate-500">Description</p>
          <p className="mb-5 text-sm text-slate-800">{meeting.description || "No description provided."}</p>
          {meeting.external_guests.length > 0 && (
            <>
              <p className="mb-2 text-xs font-medium text-slate-500">External guests</p>
              <div className="flex flex-wrap gap-2">
                {meeting.external_guests.map((g) => (
                  <span key={g.id} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                    {g.email}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {tab === "Participants" && (
        <ParticipantsTab meetingId={meeting.id} isOwner={isOwner} userMap={userMap} />
      )}

      {tab === "Notes & Summary" && <NotesSummaryTab meetingId={meeting.id} />}

      {tab === "Action items" && <ActionItemsTab meetingId={meeting.id} />}

      <ConfirmDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={() => {
          setDeleteOpen(false);
          deleteMeeting.mutate();
        }}
        title="Cancel this meeting?"
        description="This permanently deletes the meeting. All participants and any Google Calendar event will be removed."
        confirmLabel="Cancel meeting"
        loading={deleteMeeting.isPending}
      />

      <EditMeetingDialog open={editOpen} onClose={() => setEditOpen(false)} meeting={meeting} />
    </div>
  );
}

// ---------------------------------------------------------------------------

function EditMeetingDialog({
  open,
  onClose,
  meeting,
}: {
  open: boolean;
  onClose: () => void;
  meeting: { id: number; title: string; description: string | null; location: string | null };
}) {
  const { push } = useToast();
  const queryClient = useQueryClient();
  const [title, setTitle] = React.useState(meeting.title);
  const [description, setDescription] = React.useState(meeting.description ?? "");
  const [location, setLocation] = React.useState(meeting.location ?? "");

  React.useEffect(() => {
    setTitle(meeting.title);
    setDescription(meeting.description ?? "");
    setLocation(meeting.location ?? "");
  }, [meeting]);

  const save = useMutation({
    mutationFn: () => meetingsApi.update(meeting.id, { title, description, location }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meeting", meeting.id] });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      push("success", "Meeting updated");
      onClose();
    },
    onError: (err) => push("error", "Couldn't update meeting", getApiErrorMessage(err)),
  });

  return (
    <Dialog open={open} onClose={onClose} title="Edit meeting">
      <div className="space-y-3">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Title</label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Location</label>
          <Input value={location} onChange={(e) => setLocation(e.target.value)} />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Description</label>
          <Textarea className="h-24" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <Button className="w-full" onClick={() => save.mutate()} loading={save.isPending} disabled={!title.trim()}>
          Save changes
        </Button>
      </div>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------

function ParticipantsTab({
  meetingId,
  isOwner,
  userMap,
}: {
  meetingId: number;
  isOwner: boolean;
  userMap: Map<number, { id: number; name: string; email: string }>;
}) {
  const { push } = useToast();
  const queryClient = useQueryClient();

  const { data: participants, isLoading } = useQuery({
    queryKey: ["participants", meetingId],
    queryFn: () => participantsApi.list(meetingId),
  });

  const removeParticipant = useMutation({
    mutationFn: (participantId: number) => participantsApi.remove(participantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["participants", meetingId] });
      push("success", "Participant removed");
    },
    onError: (err) => push("error", "Couldn't remove participant", getApiErrorMessage(err)),
  });

  if (isLoading) return <div className="h-32 animate-pulse rounded-xl bg-slate-100" />;

  return (
    <div>
      {isOwner && (
        <div className="relative mb-4">
          <Input
            icon={<UserPlus className="h-4 w-4" />}
            placeholder="Inviting by search isn't available yet"
            disabled
          />
          <p className="mt-1.5 text-xs text-slate-400">
            A team directory isn't available yet, so participants can't be found and invited from here.
          </p>
        </div>
      )}

      {!participants || participants.length === 0 ? (
        <EmptyState icon={<UserPlus className="h-5 w-5" />} title="No participants yet" body="Invite teammates to this meeting." />
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200">
          {participants.map((p, i) => {
            const u = userMap.get(p.user_id);
            return (
              <div key={p.id} className={`flex items-center gap-3 px-4 py-3 ${i !== participants.length - 1 ? "border-b border-slate-100" : ""}`}>
                <Avatar initials={u ? initialsOf(u.name) : "?"} size={32} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-900">{u?.name ?? `User #${p.user_id}`}</p>
                  <p className="truncate text-xs text-slate-500">{u?.email}</p>
                </div>
                <StatusBadge status={p.status} />
                {isOwner && (
                  <button onClick={() => removeParticipant.mutate(p.id)} className="text-slate-400 hover:text-red-500">
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function NotesSummaryTab({ meetingId }: { meetingId: number }) {
  const { push } = useToast();
  const queryClient = useQueryClient();
  const [notesDraft, setNotesDraft] = React.useState("");

  const { data: notes } = useQuery({
    queryKey: ["notes", meetingId],
    queryFn: () => meetingIntelligenceApi.getNotes(meetingId),
    retry: false,
  });

  const { data: summary } = useQuery({
    queryKey: ["summary", meetingId],
    queryFn: () => meetingIntelligenceApi.getSummary(meetingId),
    retry: false,
  });

  React.useEffect(() => {
    if (notes) setNotesDraft(notes.content);
  }, [notes]);

  const generateSummary = useMutation({
    mutationFn: () => aiApi.summarizeMeeting(meetingId, notesDraft),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes", meetingId] });
      queryClient.invalidateQueries({ queryKey: ["summary", meetingId] });
      queryClient.invalidateQueries({ queryKey: ["action-items", meetingId] });
      push("success", "Summary generated");
    },
    onError: (err) =>
      push(
        "error",
        "Couldn't generate summary",
        getApiErrorMessage(err, "The backend's Gemini integration may not be configured (GEMINI_API_KEY).")
      ),
  });

  const [followUp, setFollowUp] = React.useState<{ email_subject: string; email_body: string } | null>(null);
  const generateFollowUp = useMutation({
    mutationFn: () => aiApi.followUp(meetingId, notesDraft || notes?.content || ""),
    onSuccess: (data) => {
      setFollowUp(data);
      push("success", "Follow-up draft ready");
    },
    onError: (err) => push("error", "Couldn't draft follow-up", getApiErrorMessage(err)),
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="mb-1.5 text-xs font-medium text-slate-500">Meeting notes / transcript</p>
        <Textarea
          className="h-32"
          placeholder="Paste your raw meeting notes or transcript here, then generate a summary."
          value={notesDraft}
          onChange={(e) => setNotesDraft(e.target.value)}
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <Button
            onClick={() => generateSummary.mutate()}
            loading={generateSummary.isPending}
            disabled={!notesDraft.trim()}
          >
            <Sparkles className="h-4 w-4" /> Generate summary & action items
          </Button>
          <Button
            variant="secondary"
            onClick={() => generateFollowUp.mutate()}
            loading={generateFollowUp.isPending}
            disabled={!notesDraft.trim() && !notes}
          >
            <Mail className="h-4 w-4" /> Draft follow-up email
          </Button>
        </div>
      </div>

      {summary && (
        <div className="rounded-xl bg-brand-50 p-5">
          <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-brand-700">
            <Sparkles className="h-4 w-4" /> AI-generated summary
          </p>
          <p className="text-sm text-slate-800">{summary.summary}</p>
          <p className="mt-3 text-xs text-slate-400">
            Last updated {new Date(summary.updated_at).toLocaleString()}
          </p>
        </div>
      )}

      {followUp && (
        <div className="rounded-xl border border-slate-200 p-5">
          <p className="mb-1 text-xs font-medium text-slate-500">Subject</p>
          <p className="mb-3 text-sm font-medium text-slate-900">{followUp.email_subject}</p>
          <p className="mb-1 text-xs font-medium text-slate-500">Body</p>
          <p className="whitespace-pre-wrap text-sm text-slate-800">{followUp.email_body}</p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function ActionItemsTab({ meetingId }: { meetingId: number }) {
  const { push } = useToast();
  const queryClient = useQueryClient();

  const { data: items, isLoading } = useQuery({
    queryKey: ["action-items", meetingId],
    queryFn: () => meetingIntelligenceApi.getActionItems(meetingId),
  });

  const toggleStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: "pending" | "completed" }) =>
      meetingIntelligenceApi.updateActionItemStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["action-items", meetingId] }),
    onError: (err) => push("error", "Couldn't update", getApiErrorMessage(err)),
  });

  if (isLoading) return <div className="h-32 animate-pulse rounded-xl bg-slate-100" />;

  if (!items || items.length === 0) {
    return (
      <EmptyState
        icon={<Loader2 className="h-5 w-5" />}
        title="No action items yet"
        body='Generate a summary in the "Notes & Summary" tab — action items are extracted automatically.'
      />
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <label key={item.id} className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2.5">
          <input
            type="checkbox"
            checked={item.status === "completed"}
            onChange={(e) =>
              toggleStatus.mutate({ id: item.id, status: e.target.checked ? "completed" : "pending" })
            }
            className="h-4 w-4 accent-brand-600"
          />
          <div className="flex-1">
            <p className={cn("text-sm", item.status === "completed" ? "text-slate-400 line-through" : "text-slate-800")}>
              {item.task}
            </p>
            <p className="mt-0.5 text-xs text-slate-400">
              {item.assignee ?? "Unassigned"}
              {item.due_date ? ` · Due ${item.due_date}` : ""}
            </p>
          </div>
        </label>
      ))}
    </div>
  );
}
