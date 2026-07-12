import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { Calendar, MailWarning } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Avatar } from "@/components/ui/Avatar";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { usersApi } from "@/api/users";
import { getApiErrorMessage } from "@/api/client";

const TABS = ["Profile", "Google Calendar", "Security"] as const;

function initialsOf(name: string) {
  const parts = name.trim().split(/\s+/);
  return parts.length === 1 ? parts[0].slice(0, 2).toUpperCase() : (parts[0][0] + parts[1][0]).toUpperCase();
}

export default function Settings() {
  const { push } = useToast();
  const { user, refetchUser } = useAuth();
  const [tab, setTab] = React.useState<(typeof TABS)[number]>("Profile");

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
                <MailWarning className="h-3 w-3 text-amber-600" /> Not available yet
              </p>
            </div>
            <Button disabled>Connect</Button>
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
