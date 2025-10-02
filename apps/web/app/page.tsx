"use client";

import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { ArrowUpRight } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";

const HomePage = () => {
  const { user } = useAuth();
  const router = useRouter();
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

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

          <div className="flex items-center gap-3">
            {user ? (
              <Button
                size="sm"
                onClick={() => router.push("/chat")}
                className="rounded-full"
              >
                Open Platform
              </Button>
            ) : (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => router.push("/login")}
                className="rounded-full"
              >
                Sign In
              </Button>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <main className="relative flex items-center justify-center min-h-screen px-6">
        <div className="max-w-4xl mx-auto text-center space-y-12">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border/60 text-xs tracking-wide group hover:border-foreground/20 transition-colors cursor-default">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
            </span>
            <span className="text-muted-foreground">POWERED BY AI</span>
          </div>

          {/* Title */}
          <div className="space-y-6">
            <h1 className="text-7xl md:text-8xl lg:text-9xl font-light tracking-tighter">
              Legal
              <br />
              <span className="font-normal">Intelligence</span>
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground font-light max-w-xl mx-auto leading-relaxed">
              AI-powered legal assistant for document analysis.
              Upload cases. Get insights. Make decisions.
            </p>
          </div>

          {/* CTA */}
          <div className="flex items-center justify-center gap-4">
            <Button
              size="lg"
              onClick={() => router.push(user ? "/chat" : "/login")}
              className="group relative px-8 h-12 text-base font-medium rounded-full overflow-hidden hover:scale-105 transition-transform duration-200"
            >
              <span className="relative z-10 flex items-center gap-2">
                {user ? "Open Platform" : "Get Started"}
                <ArrowUpRight className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </span>
            </Button>

            {user && (
              <Button
                size="lg"
                variant="ghost"
                onClick={() => router.push("/chat")}
                className="px-8 h-12 text-base font-medium rounded-full hover:bg-muted transition-colors"
              >
                View Docs
              </Button>
            )}
          </div>

          {/* Stats */}
          <div className="pt-16 grid grid-cols-3 gap-8 max-w-2xl mx-auto">
            {[
              { value: "AI", label: "Powered" },
              { value: "24/7", label: "Available" },
              { value: "Instant", label: "Analysis" },
            ].map((stat, i) => (
              <div
                key={i}
                className="group cursor-default"
                style={{
                  animation: `fadeIn 0.6s ease-out ${i * 0.1}s both`,
                }}
              >
                <div className="text-3xl font-light mb-1 group-hover:scale-105 transition-transform">
                  {stat.value}
                </div>
                <div className="text-xs text-muted-foreground tracking-wider uppercase">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Features Section */}
      <section className="relative border-t border-border/40 py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-3 gap-16 md:gap-8">
            {[
              {
                label: "01",
                title: "Document Analysis",
                description: "Upload legal documents and get instant AI-powered analysis of key terms, risks, and obligations.",
              },
              {
                label: "02",
                title: "Voice Interface",
                description: "Ask questions naturally using voice commands. Get spoken responses from your AI legal assistant.",
              },
              {
                label: "03",
                title: "Case Intelligence",
                description: "Deep insights into case documents with contextual understanding and strategic recommendations.",
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="group space-y-4 hover:translate-y-[-4px] transition-transform duration-300"
                style={{
                  animation: `fadeIn 0.8s ease-out ${i * 0.15}s both`,
                }}
              >
                <div className="text-xs text-muted-foreground tracking-widest font-medium">
                  {feature.label}
                </div>
                <h3 className="text-2xl font-light">{feature.title}</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="relative border-t border-border/40 py-24 px-6">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h2 className="text-4xl md:text-5xl font-light tracking-tight">
            {user ? "Ready to analyze?" : "Get started today"}
          </h2>
          <p className="text-muted-foreground text-lg">
            {user
              ? "Your account is active. Start analyzing legal documents now."
              : "Sign up to access AI-powered legal document analysis."}
          </p>
          <Button
            size="lg"
            onClick={() => router.push(user ? "/chat" : "/login")}
            className="group px-8 h-12 text-base font-medium rounded-full hover:scale-105 transition-transform duration-200"
          >
            <span className="flex items-center gap-2">
              {user ? "Open Platform" : "Create Account"}
              <ArrowUpRight className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </span>
          </Button>
        </div>
      </section>

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
};

export default HomePage;
