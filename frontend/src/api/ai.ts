import { api } from "./client";
import type { ScheduleMeetingResponse, MeetingSummary, FollowUpDraft } from "@/types";

export const aiApi = {
  scheduleFromText: (text: string) =>
    api.post<ScheduleMeetingResponse>("/ai/schedule-text", { text }).then((r) => r.data),

  summarizeMeeting: (meetingId: number, notes: string) =>
    api
      .post<MeetingSummary>(`/ai/meetings/${meetingId}/summary`, { notes })
      .then((r) => r.data),

  followUp: (meetingId: number, notes: string) =>
    api
      .post<FollowUpDraft>(`/ai/meetings/${meetingId}/follow-up`, { notes })
      .then((r) => r.data),
};
