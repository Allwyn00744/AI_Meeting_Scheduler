import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Lock } from "lucide-react";
import { AuthLayout } from "@/components/layouts/AuthLayout";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { getApiErrorMessage } from "@/api/client";

const schema = z.object({
  email: z.string().min(1, "Enter your email.").email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});
type FormValues = z.infer<typeof schema>;

export default function Login() {
  const navigate = useNavigate();
  const { push } = useToast();
  const { login } = useAuth();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    try {
      await login(values);
      push("success", "Welcome back", "Signed in successfully.");
      navigate("/dashboard");
    } catch (err) {
      const message = getApiErrorMessage(err, "Invalid email or password.");
      setError("password", { message });
      push("error", "Sign in failed", message);
    }
  };

  return (
    <AuthLayout variant="login">
      <h1 className="text-[26px] font-bold text-slate-900">Welcome back</h1>
      <p className="mt-1 text-sm text-slate-500">Sign in to AI meeting scheduler</p>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Email</label>
          <Input
            icon={<Mail className="h-4 w-4" />}
            placeholder="name@company.com"
            error={errors.email?.message}
            {...register("email")}
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Password</label>
          <Input
            icon={<Lock className="h-4 w-4" />}
            type="password"
            placeholder="Enter your password"
            error={errors.password?.message}
            {...register("password")}
          />
        </div>

        <Button type="submit" variant="dark" className="w-full" loading={isSubmitting}>
          Sign in
        </Button>

        <p className="pt-2 text-center text-sm text-slate-500">
          No account?{" "}
          <Link to="/register" className="font-medium text-brand-600 hover:text-brand-700">
            Register
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
