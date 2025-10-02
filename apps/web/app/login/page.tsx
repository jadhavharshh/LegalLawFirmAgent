"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";
import { ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, register } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({ email: "", password: "", fullName: "" });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100,
      });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    
    try {
      await login(loginForm.email, loginForm.password);
      router.push("/");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    
    try {
      await register(registerForm.email, registerForm.password, registerForm.fullName);
      router.push("/");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Subtle animated gradient */}
      <div
        className="fixed inset-0 opacity-30 pointer-events-none transition-all duration-1000 ease-out"
        style={{
          background: `radial-gradient(600px circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(59, 130, 246, 0.15), transparent 40%)`,
        }}
      />

      {/* Top Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 backdrop-blur-sm bg-background/80">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <button
            onClick={() => router.push("/")}
            className="text-lg font-medium tracking-tight hover:opacity-70 transition-opacity"
          >
            LEGAL AI
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative flex items-center justify-center min-h-screen px-6">
        <div className="max-w-md w-full space-y-8">
          {/* Header */}
          <div className="text-center space-y-2">
            <h1 className="text-5xl md:text-6xl font-light tracking-tighter">
              {isRegister ? "Create Account" : "Welcome Back"}
            </h1>
            <p className="text-muted-foreground font-light">
              {isRegister 
                ? "Sign up to access your legal AI assistant" 
                : "Sign in to continue to your workspace"}
            </p>
          </div>

          {/* Form */}
          <div className="space-y-6">
            <form onSubmit={isRegister ? handleRegister : handleLogin} className="space-y-4">
              {isRegister && (
                <div className="space-y-2">
                  <label className="text-sm text-muted-foreground tracking-wide">
                    FULL NAME
                  </label>
                  <Input
                    type="text"
                    placeholder="John Doe"
                    value={registerForm.fullName}
                    onChange={(e) => setRegisterForm({ ...registerForm, fullName: e.target.value })}
                    required
                    className="h-12 bg-transparent border-border/60 focus:border-foreground/20 transition-colors"
                  />
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground tracking-wide">
                  EMAIL
                </label>
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={isRegister ? registerForm.email : loginForm.email}
                  onChange={(e) => isRegister 
                    ? setRegisterForm({ ...registerForm, email: e.target.value })
                    : setLoginForm({ ...loginForm, email: e.target.value })
                  }
                  required
                  className="h-12 bg-transparent border-border/60 focus:border-foreground/20 transition-colors"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground tracking-wide">
                  PASSWORD
                </label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={isRegister ? registerForm.password : loginForm.password}
                  onChange={(e) => isRegister
                    ? setRegisterForm({ ...registerForm, password: e.target.value })
                    : setLoginForm({ ...loginForm, password: e.target.value })
                  }
                  required
                  className="h-12 bg-transparent border-border/60 focus:border-foreground/20 transition-colors"
                />
              </div>

              {error && (
                <div className="text-sm text-red-500 border border-red-500/20 bg-red-500/5 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full h-12 text-base font-medium rounded-full group hover:scale-105 transition-transform duration-200"
              >
                <span className="flex items-center justify-center gap-2">
                  {isLoading ? "Loading..." : isRegister ? "Create Account" : "Sign In"}
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </span>
              </Button>
            </form>

            {/* Toggle */}
            <div className="text-center">
              <button
                onClick={() => {
                  setIsRegister(!isRegister);
                  setError("");
                }}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                {isRegister 
                  ? "Already have an account? Sign in" 
                  : "Don't have an account? Sign up"}
              </button>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center pt-8">
            <p className="text-xs text-muted-foreground">
              Secured with JWT Authentication
            </p>
          </div>
        </div>
      </main>

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
