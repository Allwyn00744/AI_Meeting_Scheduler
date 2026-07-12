/**
 * TypeScript mirrors of the backend's Pydantic response schemas.
 * Field names and shapes are kept identical to app/schemas/*.py so
 * there is exactly one source of truth to keep in sync.
 */

// ---- auth / users (app/schemas/user.py) ----------------------------------

export interface User {
  id: number;
  name: string;
  email: string;
  timezone: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// ---- meetings (app/schemas/meeting.py) ------------------------------------

export interface ExternalGuest {
  id: number;
  email: string;
}

export type MeetingStatus = "scheduled" | "cancelled" | "completed" | string;

export interface Meeting {
  id: number;
  title: string;
  description: string | null;
  start_time: string; // ISO 8601
  end_time: string;
  location: string | null;
  status: MeetingStatus;
  owner_id: number;
  resource_id: number | null;
  external_guests: ExternalGuest[];
}

export interface MeetingCreatePayload {
  title: string;
  description?: string | null;
  start_time: string;
  end_time: string;
  location?: string | null;
  resource_id?: number | null;
  external_guest_emails?: string[];
}

export interface MeetingUpdatePayload {
  title?: string;
  description?: string | null;
  start_time?: string;
  end_time?: string;
  location?: string | null;
  status?: string;
}

// ---- participants (app/schemas/meeting_participant.py) --------------------

export type ParticipantStatus = "Pending" | "Accepted" | "Declined" | string;

export interface Participant {
  id: number;
  meeting_id: number;
  user_id: number;
  status: ParticipantStatus;
  created_at: string;
}

// ---- resources (app/schemas/resource.py) -----------------------------------

export interface Resource {
  id: number;
  name: string;
  resource_type: string;
  description: string | null;
  location: string | null;
  is_active: boolean;
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

export interface ResourceCreatePayload {
  name: string;
  resource_type: string;
  description?: string | null;
  location?: string | null;
}

export interface ResourceUpdatePayload {
  name?: string;
  resource_type?: string;
  description?: string | null;
  location?: string | null;
  is_active?: boolean;
}

// ---- availability (app/schemas/availability.py) ----------------------------

export interface Availability {
  id: number;
  user_id: number;
  day_of_week: string;
  start_time: string; // "HH:MM:SS"
  end_time: string;
  is_available: boolean;
  created_at: string;
}

export interface AvailabilityCreatePayload {
  day_of_week: string;
  start_time: string;
  end_time: string;
  is_available?: boolean;
}

export interface AvailabilityUpdatePayload {
  day_of_week?: string;
  start_time?: string;
  end_time?: string;
  is_available?: boolean;
}

// ---- scheduler (app/schemas/scheduler.py) ----------------------------------

export interface ScheduleMeetingRequest {
  title: string;
  description?: string | null;
  start_time: string;
  end_time: string;
  location?: string | null;
  resource_id?: number | null;
  participant_ids: number[];
  external_guest_emails?: string[];
  repeat?: boolean;
  repeat_type?: "weekly" | null;
  occurrences?: number | null;
}

export interface ScheduleMeetingResponse {
  message: string;
  meeting_ids: number[];
}

export interface SuggestedSlot {
  start_time: string;
  end_time: string;
}

export interface SuggestSlotsResponse {
  slots: SuggestedSlot[];
}

// ---- meeting intelligence (app/schemas/meeting_intelligence.py, ai.py) ----

export type ActionItemStatus = "pending" | "completed";

export interface ActionItem {
  id: number;
  meeting_id: number;
  task: string;
  assignee: string | null;
  due_date: string | null;
  status: ActionItemStatus;
  created_at: string;
  updated_at: string;
}

export interface MeetingNotes {
  id: number;
  meeting_id: number;
  content: string;
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

export interface MeetingSummary {
  id: number;
  meeting_id: number;
  summary: string;
  action_items: ActionItem[];
  created_at: string;
  updated_at: string;
}

export interface FollowUpDraft {
  email_subject: string;
  email_body: string;
}

// ---- google (app/api/google_routes.py) -------------------------------------

export interface GoogleStatus {
  connected: boolean;
}

// ---- generic API error shape (FastAPI's default {"detail": ...}) ----------

export interface ApiErrorBody {
  detail?: string | { msg: string; loc: (string | number)[] }[];
}
