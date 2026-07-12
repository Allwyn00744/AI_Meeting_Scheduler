import { Sparkles, Zap } from "lucide-react";
import { Logo } from "../shared/Logo";

interface AuthLayoutProps {
  children: React.ReactNode;
  variant: "login" | "register";
}

/** Split-panel layout shared by Login / Register / Forgot password. */
export function AuthLayout({ children, variant }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen w-full bg-white">
      <div className="flex w-full flex-col justify-center px-6 py-12 sm:px-12 lg:w-1/2 lg:px-20 xl:px-28">
        <div className="mx-auto w-full max-w-sm">
          <div className="mb-8">
            <Logo />
          </div>
          {children}
        </div>
      </div>

      <div className="relative hidden overflow-hidden bg-ink-950 lg:flex lg:w-1/2 lg:items-center lg:justify-center lg:p-10">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-brand-600/30 blur-3xl" />
        <div className="pointer-events-none absolute -left-10 bottom-0 h-72 w-72 rounded-full bg-emerald-500/10 blur-3xl" />

        <div className="relative z-10 w-full max-w-md">
          <div className="mb-8 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-emerald-500">
            <Sparkles className="h-8 w-8 text-white" />
          </div>

          {variant === "login" ? (
            <>
              <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-brand-300">Sched AI</p>
              <h1 className="text-4xl font-extrabold leading-tight text-white">
                The Invisible Architect of Your Schedule
              </h1>
              <div className="mt-10 rounded-2xl bg-white/5 p-5">
                <p className="text-sm leading-relaxed text-slate-300">
                  Arcana helps professionals schedule and manage meetings with AI-driven
                  intelligence. Experience the easiest way to align complex calendars.
                </p>
                <div className="mt-4 flex items-center gap-3">
                  <div className="flex -space-x-2">
                    {["A", "B", "C"].map((l) => (
                      <div key={l} className="h-7 w-7 rounded-full border-2 border-ink-950 bg-slate-500" />
                    ))}
                    <div className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-ink-950 bg-brand-600 text-[10px] font-medium text-white">
                      +17k
                    </div>
                  </div>
                  <p className="text-xs text-slate-400">More than 17k professionals joined us</p>
                </div>
              </div>
            </>
          ) : (
            <>
              <h1 className="text-4xl font-extrabold leading-tight text-white">
                Start Scheduling with Intelligence
              </h1>
              <p className="mt-4 text-sm leading-relaxed text-slate-300">
                Join 17k+ professionals who have reclaimed their focus time using the Invisible
                Architect.
              </p>

              <div className="mt-8 flex items-center gap-4 rounded-2xl bg-white/5 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600">
                  <Zap className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-white">Smart Priority</p>
                  <p className="text-xs text-slate-400">AI automatically detects your highest-impact meetings.</p>
                </div>
                <p className="text-sm font-semibold text-emerald-400">+12%</p>
              </div>

              <div className="mt-3 flex items-center gap-4 rounded-2xl bg-white/5 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-600">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-white">AI Suggestions</p>
                  <p className="text-xs text-slate-400">Optimized time slots based on your focus cycles.</p>
                </div>
                <div className="h-5 w-9 rounded-full bg-white/20 p-0.5">
                  <div className="ml-auto h-4 w-4 rounded-full bg-white" />
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
