import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "react-router-dom";
import { AuthLayout } from "@/components/layouts/AuthLayout";
import { Input, Select } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { getApiErrorMessage } from "@/api/client";

const schema = z.object({
  name: z.string().min(1, "Enter your full name."),
  email: z.string().min(1, "Enter your email.").email("Enter a valid email address."),
  password: z.string().min(8, "Password must be at least 8 characters."),
  timezone: z.string(),
});
type FormValues = z.infer<typeof schema>;

export default function Register() {
  const navigate = useNavigate();
  const { push } = useToast();
  const { register: doRegister } = useAuth();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { timezone: "UTC" },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      await doRegister(values);
      push("success", "Account created", "Welcome to SCHEDAI.");
      navigate("/dashboard");
    } catch (err) {
      const message = getApiErrorMessage(err, "Could not create your account.");
      setError("email", { message });
      push("error", "Registration failed", message);
    }
  };

  return (
    <AuthLayout variant="register">
      <h1 className="text-[26px] font-bold text-slate-900">Create your account</h1>
      <p className="mt-1 text-sm text-slate-500">Get started with AI-powered scheduling</p>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Full name</label>
          <Input placeholder="Maya Rodriguez" error={errors.name?.message} {...register("name")} />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Email</label>
          <Input placeholder="name@company.com" error={errors.email?.message} {...register("email")} />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Password</label>
          <Input
            type="password"
            placeholder="Min. 8 characters"
            error={errors.password?.message}
            {...register("password")}
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Timezone</label>
          <Select {...register("timezone")}>
            <option value="UTC">UTC</option>
            <option value="Asia/Kolkata">Asia/Kolkata (UTC+5:30)</option>
            <option value="America/New_York">America/New_York (UTC-5:00)</option>
            <option value="Europe/London">Europe/London (UTC+0:00)</option>
          </Select>
        </div>

        <Button type="submit" variant="dark" className="w-full" loading={isSubmitting}>
          Create account
        </Button>

        <p className="text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
