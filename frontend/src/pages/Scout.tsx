import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { Send, Sparkles, AlertCircle } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
  error?: boolean;
}

const SUGGESTIONS = [
  "Who are the favourites in Group H?",
  "Explain Argentina's tactical approach.",
  "Which key players are carrying injuries?",
  "Compare Brazil and France going into the tournament.",
];

function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 rounded-full bg-muted"
          style={{ animation: "typing 1.2s ease-in-out infinite", animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

export function Scout() {
  const [params, setParams] = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const threadRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Deep-link: prefill input from ?q= (from "Ask Scout about this" CTAs)
  useEffect(() => {
    const q = params.get("q");
    if (q) {
      setInput(q);
      setParams({}, { replace: true });
      inputRef.current?.focus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || loading) return;

    // Build [user, ai] history pairs from completed exchanges
    const history: [string, string][] = [];
    for (let i = 0; i < messages.length - 1; i++) {
      if (messages[i].role === "user" && messages[i + 1]?.role === "assistant" && !messages[i + 1].error) {
        history.push([messages[i].content, messages[i + 1].content]);
      }
    }

    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/scout/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, history }),
      });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: data.answer ?? "(No answer returned.)" }]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          error: true,
          content:
            "I couldn't reach the Scout service. Make sure the backend is running at localhost:5000, then try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  const empty = messages.length === 0;

  return (
    <div className="mx-auto flex h-[calc(100vh-4rem)] max-w-3xl flex-col px-4 sm:px-6">
      {/* header */}
      <div className="flex items-center gap-3 border-b border-border py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-accent-fg">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-display text-xl font-bold tracking-wide">AI Scout</h1>
          <p className="text-xs text-muted">Tactical analysis for World Cup 2026 · history resets on refresh</p>
        </div>
      </div>

      {/* thread */}
      <div ref={threadRef} className="scroll-thin flex-1 space-y-5 overflow-y-auto py-6">
        {empty && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-2">
              <Sparkles className="h-7 w-7 text-fg" />
            </div>
            <h2 className="font-display text-2xl font-bold tracking-wide">Ask me about the tournament</h2>
            <p className="mt-2 max-w-md text-sm text-muted">
              Squads, tactics, key players, group outlooks — I read from the tournament knowledge base.
            </p>
            <div className="mt-7 grid w-full max-w-lg gap-2.5 sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-xl border border-border bg-surface px-4 py-3 text-left text-sm text-fg transition-colors hover:border-accent/50 hover:bg-surface-2"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className={cn(
                "max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed",
                m.role === "user"
                  ? "rounded-br-md bg-accent text-accent-fg"
                  : m.error
                    ? "rounded-bl-md border border-amber-500/40 bg-amber-500/10 text-fg"
                    : "rounded-bl-md border border-border bg-surface text-fg"
              )}
            >
              {m.error && (
                <span className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-amber-600 dark:text-amber-400">
                  <AlertCircle className="h-3.5 w-3.5" /> Connection issue
                </span>
              )}
              {m.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-md border border-border bg-surface px-3 py-2">
              <TypingDots />
            </div>
          </div>
        )}
      </div>

      {/* input */}
      <form onSubmit={onSubmit} className="border-t border-border py-4">
        <div className="flex items-center gap-2 rounded-full border border-border bg-surface pl-5 pr-2 transition-shadow duration-200 focus-within:shadow-[inset_0_0_14px_-4px_var(--color-ring)]">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the Scout anything…"
            className="h-12 flex-1 bg-transparent text-sm text-fg placeholder:text-muted focus:outline-none"
            aria-label="Message the AI Scout"
          />
          <Button type="submit" size="icon" disabled={!input.trim() || loading} aria-label="Send message">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
