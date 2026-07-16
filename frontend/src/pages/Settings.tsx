import * as React from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Calendar, CheckCircle2, MailWarning, Video } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Avatar } from "@/components/ui/Avatar";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { usersApi } from "@/api/users";
import { googleApi } from "@/api/google";
import { outlookApi } from "@/api/outlook";
import { zoomApi } from "@/api/zoom";
import { getApiErrorMessage } from "@/api/client";

const TABS = ["Profile", "Google Calendar", "Outlook Calendar", "Zoom Meetings", "Security"] as const;

function initialsOf(name: string) {
  const parts = name.trim().split(/\s+/);
  return parts.length === 1 ? parts[0].slice(0, 2).toUpperCase() : (parts[0][0] + parts[1][0]).toUpperCase();
}

export default function Settings() {
  const { push } = useToast();
  const { user, refetchUser } = useAuth();
  const [tab, setTab] = React.useState<(typeof TABS)[number]>("Profile");
  const [searchParams, setSearchParams] = useSearchParams();

  const [name, setName] = React.useState(user?.name ?? "");
  const [email, setEmail] = React.useState(user?.email ?? "");
  const [timezone, setTimezone] = React.useState(user?.timezone ?? "UTC");
  React.useEffect(() => {
    if (user) {
      setName(user.name);
      setEmail(user.email);
      setTimezone(user.timezone);
    }
  }, [user]);

  const saveProfile = useMutation({
    mutationFn: () => usersApi.update(user!.id, { name, email, timezone }),
    onSuccess: async () => {
      await refetchUser();
      push("success", "Profile updated");
    },
    onError: (err) => push("error", "Couldn't save profile", getApiErrorMessage(err)),
  });

  const [password, setPassword] = React.useState("");
  const savePassword = useMutation({
    mutationFn: () => usersApi.updatePassword(user!.id, password),
    onSuccess: () => {
      push("success", "Password updated");
      setPassword("");
    },
    onError: (err) => push("error", "Couldn't update password", getApiErrorMessage(err)),
  });

  const { data: googleStatus, isLoading: googleStatusLoading, refetch: refetchGoogle } = useQuery({
    queryKey: ["google-status"],
    queryFn: googleApi.status,
  });
  const disconnectGoogle = useMutation({
    mutationFn: googleApi.disconnect,
    onSuccess: () => {
      push("success", "Google Calendar disconnected");
      refetchGoogle();
    },
    onError: (err) => push("error", "Couldn't disconnect", getApiErrorMessage(err)),
  });

  React.useEffect(() => {
    const googleResult = searchParams.get("google");
    if (!googleResult) return;

    if (googleResult === "connected") {
      push("success", "Google Calendar connected");
      refetchGoogle();
    } else if (googleResult === "error") {
      push("error", "Couldn't connect Google Calendar", "Please try again.");
    }

    const next = new URLSearchParams(searchParams);
    next.delete("google");
    setSearchParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const { data: outlookStatus, isLoading: outlookStatusLoading, refetch: refetchOutlook } = useQuery({
    queryKey: ["outlook-status"],
    queryFn: outlookApi.status,
  });
  const connectOutlook = useMutation({
    mutationFn: outlookApi.connect,
    onSuccess: (data) => {
      window.location.href = data.authorization_url;
    },
    onError: (err) => push("error", "Couldn't connect Outlook", getApiErrorMessage(err)),
  });
  const disconnectOutlook = useMutation({
    mutationFn: outlookApi.disconnect,
    onSuccess: () => {
      push("success", "Outlook Calendar disconnected");
      refetchOutlook();
    },
    onError: (err) => push("error", "Couldn't disconnect", getApiErrorMessage(err)),
  });

  React.useEffect(() => {
    const outlookResult = searchParams.get("outlook");
    if (!outlookResult) return;

    if (outlookResult === "connected") {
      push("success", "Outlook Calendar connected");
      refetchOutlook();
    } else if (outlookResult === "error") {
      push("error", "Couldn't connect Outlook Calendar", "Please try again.");
    }

    const next = new URLSearchParams(searchParams);
    next.delete("outlook");
    setSearchParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const { data: zoomStatus, isLoading: zoomStatusLoading, refetch: refetchZoom } = useQuery({
    queryKey: ["zoom-status"],
    queryFn: zoomApi.status,
  });
  const connectZoom = useMutation({
    mutationFn: zoomApi.connect,
    onSuccess: (data) => {
      window.location.href = data.authorization_url;
    },
    onError: (err) => push("error", "Couldn't connect Zoom", getApiErrorMessage(err)),
  });
  const disconnectZoom = useMutation({
    mutationFn: zoomApi.disconnect,
    onSuccess: () => {
      push("success", "Zoom disconnected");
      refetchZoom();
    },
    onError: (err) => push("error", "Couldn't disconnect", getApiErrorMessage(err)),
  });

  React.useEffect(() => {
    const zoomResult = searchParams.get("zoom");
    if (!zoomResult) return;

    if (zoomResult === "connected") {
      push("success", "Zoom connected");
      refetchZoom();
    } else if (zoomResult === "error") {
      push("error", "Couldn't connect Zoom", "Please try again.");
    }

    const next = new URLSearchParams(searchParams);
    next.delete("zoom");
    setSearchParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  if (!user) return null;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6">
        <h1 className="text-[28px] font-bold text-slate-900">Account settings</h1>
        <p className="mt-1 text-sm text-slate-500">Manage your profile, integrations, and security.</p>
      </div>

      <div className="mb-6 flex items-center gap-3">
        <Avatar initials={initialsOf(user.name)} size={56} colorClass="bg-brand-100 text-brand-700" />
        <div>
          <p className="font-semibold text-slate-900">{user.name}</p>
          <p className="text-sm text-slate-500">{user.email}</p>
        </div>
      </div>

      <div className="mb-6 flex gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${
              tab === t ? "border-brand-600 font-medium text-brand-700" : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Profile" && (
        <Card className="space-y-4 p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Full name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Email</label>
              <Input value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Timezone</label>
            <Select value={timezone} onChange={(e) => setTimezone(e.target.value)}>
              <option value="UTC">UTC</option>
              <option value="Asia/Kolkata">Asia/Kolkata (UTC+5:30)</option>
              <option value="America/New_York">America/New_York (UTC-5:00)</option>
              <option value="Europe/London">Europe/London (UTC+0:00)</option>
            </Select>
          </div>
          <div className="flex justify-end">
            <Button onClick={() => saveProfile.mutate()} loading={saveProfile.isPending}>
              Save changes
            </Button>
          </div>
        </Card>
      )}

      {tab === "Google Calendar" && (
        <Card className="p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100">
              <Calendar className="h-4 w-4 text-slate-600" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-slate-900">Google Calendar</p>
              <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
                {googleStatusLoading ? (
                  "Checking connection..."
                ) : googleStatus?.connected ? (
                  <>
                    <CheckCircle2 className="h-3 w-3 text-emerald-600" /> Connected
                  </>
                ) : (
                  <>
                    <MailWarning className="h-3 w-3 text-amber-600" /> Not connected
                  </>
                )}
              </p>
            </div>
            {googleStatus?.connected ? (
              <Button
                variant="danger"
                onClick={() => disconnectGoogle.mutate()}
                loading={disconnectGoogle.isPending}
              >
                Disconnect
              </Button>
            ) : (
              <Button
                disabled={googleStatusLoading}
                onClick={() => (window.location.href = googleApi.connectRedirectUrl())}
              >
                Connect Google
              </Button>
            )}
          </div>
        </Card>
      )}

      {tab === "Outlook Calendar" && (
        <Card className="p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100">
              <Calendar className="h-4 w-4 text-slate-600" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-slate-900">Outlook Calendar</p>
              <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
                {outlookStatusLoading ? (
                  "Checking connection..."
                ) : outlookStatus?.connected ? (
                  <>
                    <CheckCircle2 className="h-3 w-3 text-emerald-600" /> Connected
                  </>
                ) : (
                  <>
                    <MailWarning className="h-3 w-3 text-amber-600" /> Not connected
                  </>
                )}
              </p>
            </div>
            {outlookStatus?.connected ? (
              <Button
                variant="danger"
                onClick={() => disconnectOutlook.mutate()}
                loading={disconnectOutlook.isPending}
              >
                Disconnect
              </Button>
            ) : (
              <Button
                disabled={outlookStatusLoading}
                onClick={() => connectOutlook.mutate()}
                loading={connectOutlook.isPending}
              >
                Connect Outlook
              </Button>
            )}
          </div>
        </Card>
      )}

      {tab === "Zoom Meetings" && (
        <Card className="p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100">
              <Video className="h-4 w-4 text-slate-600" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-slate-900">Zoom Meetings</p>
              <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
                {zoomStatusLoading ? (
                  "Checking connection..."
                ) : zoomStatus?.connected ? (
                  <>
                    <CheckCircle2 className="h-3 w-3 text-emerald-600" /> Connected
                  </>
                ) : (
                  <>
                    <MailWarning className="h-3 w-3 text-amber-600" /> Not connected
                  </>
                )}
              </p>
            </div>
            {zoomStatus?.connected ? (
              <Button
                variant="danger"
                onClick={() => disconnectZoom.mutate()}
                loading={disconnectZoom.isPending}
              >
                Disconnect
              </Button>
            ) : (
              <Button
                disabled={zoomStatusLoading}
                onClick={() => connectZoom.mutate()}
                loading={connectZoom.isPending}
              >
                Connect Zoom
              </Button>
            )}
          </div>
        </Card>
      )}

      {tab === "Security" && (
        <Card className="space-y-4 p-6">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">New password</label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          <div className="flex justify-end">
            <Button
              disabled={password.length < 1}
              onClick={() => savePassword.mutate()}
              loading={savePassword.isPending}
            >
              Update password
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
