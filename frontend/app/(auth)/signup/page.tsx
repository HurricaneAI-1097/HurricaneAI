"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    const supabase = createClient();
    const { error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: name },
        emailRedirectTo: `${window.location.origin}/api/auth/callback`,
      },
    });

    setIsLoading(false);

    if (signUpError) {
      setError(signUpError.message);
      return;
    }

    setIsSubmitted(true);
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create your account</CardTitle>
          <CardDescription>Start generating and scoring leads with AI</CardDescription>
        </CardHeader>
        <CardContent>
          {isSubmitted ? (
            <p className="text-sm text-zinc-700">
              Check your inbox at <span className="font-medium">{email}</span> to
              confirm your account before logging in.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <Input
                label="Full name"
                name="name"
                autoComplete="name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Jane Doe"
              />
              <Input
                label="Email"
                type="email"
                name="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
              />
              <Input
                label="Password"
                type="password"
                name="password"
                autoComplete="new-password"
                minLength={8}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
              />
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" isLoading={isLoading} className="mt-2 w-full">
                Create account
              </Button>
            </form>
          )}
          <p className="mt-4 text-center text-sm text-zinc-500">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-primary hover:underline">
              Log in
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
