import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, DoorOpen, MapPin, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { ResourceStatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Dialog } from "@/components/ui/Dialog";
import { Input } from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { resourcesApi } from "@/api/resources";
import { getApiErrorMessage } from "@/api/client";
import type { Resource } from "@/types";

function CreateResourceDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { push } = useToast();
  const queryClient = useQueryClient();
  const [name, setName] = React.useState("");
  const [type, setType] = React.useState("Meeting room");
  const [location, setLocation] = React.useState("");

  const create = useMutation({
    mutationFn: () => resourcesApi.create({ name, resource_type: type, location: location || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resources"] });
      push("success", "Resource added");
      setName("");
      setLocation("");
      onClose();
    },
    onError: (err) => push("error", "Couldn't add resource", getApiErrorMessage(err)),
  });

  return (
    <Dialog open={open} onClose={onClose} title="Register new resource" description="Rooms and equipment your team can book.">
      <div className="space-y-3">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Name</label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Room 2B" />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Type</label>
          <Input value={type} onChange={(e) => setType(e.target.value)} placeholder="Meeting room" />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Location</label>
          <Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Floor 2, East wing" />
        </div>
        <Button
          className="w-full"
          disabled={!name.trim() || !type.trim()}
          loading={create.isPending}
          onClick={() => create.mutate()}
        >
          Add resource
        </Button>
      </div>
    </Dialog>
  );
}

export default function Resources() {
  const { push } = useToast();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = React.useState(false);

  const { data: resources, isLoading } = useQuery({
    queryKey: ["resources"],
    queryFn: () => resourcesApi.list(),
  });

  const toggleActive = useMutation({
    mutationFn: (r: Resource) => resourcesApi.update(r.id, { is_active: !r.is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resources"] });
      push("success", "Resource updated");
    },
    onError: (err) => push("error", "Couldn't update resource", getApiErrorMessage(err)),
  });

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-[28px] font-bold text-slate-900">Resources</h1>
          <p className="mt-1 text-sm text-slate-500">Manage rooms and equipment available for booking.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="dark" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" /> Add resource
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-slate-100" />
          ))}
        </div>
      ) : !resources || resources.length === 0 ? (
        <EmptyState
          icon={<DoorOpen className="h-5 w-5" />}
          title="No resources yet"
          body="Add rooms or equipment so people can book them when scheduling meetings."
          actionLabel="Add resource"
          onAction={() => setCreateOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {resources.map((r) => (
            <div key={r.id} className="overflow-hidden rounded-xl border border-slate-200 bg-white">
              <div className={`h-1 ${r.is_active ? "bg-brand-600" : "bg-slate-200"}`} />
              <div className="p-5">
                <div className="mb-3 flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                    <DoorOpen className="h-5 w-5" />
                  </div>
                  <ResourceStatusBadge isActive={r.is_active} />
                </div>
                <p className="font-semibold text-slate-900">{r.name}</p>
                <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                  <MapPin className="h-3 w-3" /> {r.resource_type}
                  {r.location ? ` · ${r.location}` : ""}
                </p>
                <div className="mt-4 flex items-center justify-end border-t border-slate-100 pt-3">
                  <button
                    onClick={() => toggleActive.mutate(r)}
                    className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-800"
                  >
                    {r.is_active ? (
                      <>
                        <X className="h-3.5 w-3.5" /> Deactivate
                      </>
                    ) : (
                      "Reactivate"
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}

          <button
            onClick={() => setCreateOpen(true)}
            className="flex min-h-[176px] flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 text-slate-400 hover:border-brand-300 hover:text-brand-500"
          >
            <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-full border-2 border-current">
              <Plus className="h-4 w-4" />
            </div>
            <p className="text-sm font-medium">Register New Resource</p>
          </button>
        </div>
      )}

      <CreateResourceDialog open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  );
}
