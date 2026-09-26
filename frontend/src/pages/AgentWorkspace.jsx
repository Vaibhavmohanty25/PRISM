import {
    useState,
  } from "react";
  
  import ReactMarkdown from "react-markdown";
  
  import {
    Bot,
    Send,
    User,
    Loader2,
    AlertCircle,
    Wrench,
    RotateCcw,
  } from "lucide-react";
  
  import {
    askAgent,
  } from "../api/prismApi";
  
  
  const suggestedQuestions = [
    "Give me the predictive status of Project Alpha.",
    "What requires attention in Project Alpha?",
    "What is the forecast status of Foundation Work?",
    "Explain the risks and evidence limitations in Project Alpha.",
  ];
  
  
  export default function AgentWorkspace() {
    const [query, setQuery] = useState("");
  
    const [messages, setMessages] = useState([]);
  
    const [loading, setLoading] = useState(false);
  
    const [error, setError] = useState("");
  
  
    const submitQuery = async (
      selectedQuery = query
    ) => {
      const cleanQuery =
        selectedQuery.trim();
  
      if (!cleanQuery || loading) {
        return;
      }
  
      const userMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: cleanQuery,
      };
  
      setMessages((current) => [
        ...current,
        userMessage,
      ]);
  
      setQuery("");
      setError("");
      setLoading(true);
  
      try {
        const response = await askAgent(
          cleanQuery
        );
  
        const assistantMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          toolsUsed:
            response.tools_used || [],
          iterations:
            response.iterations,
        };
  
        setMessages((current) => [
          ...current,
          assistantMessage,
        ]);
  
      } catch (err) {
        console.error(err);
  
        const apiMessage =
          err.response?.data?.error?.message;
  
        setError(
          apiMessage ||
            "PRISM Agent could not complete the request."
        );
  
      } finally {
        setLoading(false);
      }
    };
  
  
    const handleKeyDown = (
      event
    ) => {
      if (
        event.key === "Enter" &&
        !event.shiftKey
      ) {
        event.preventDefault();
  
        submitQuery();
      }
    };
  
  
    const clearConversation = () => {
      setMessages([]);
      setError("");
    };
  
  
    return (
      <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-6xl flex-col">
  
        <div className="mb-5 flex items-center justify-between">
  
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              PRISM Agent
            </h1>
  
            <p className="mt-1 text-sm text-slate-500">
              Ask questions about project progress,
              forecasts, risks, schedule impact,
              and supporting evidence.
            </p>
          </div>
  
  
          {messages.length > 0 && (
            <button
              onClick={clearConversation}
              className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
            >
              <RotateCcw size={16} />
              New Conversation
            </button>
          )}
  
        </div>
  
  
        <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
  
          <div className="flex-1 overflow-y-auto p-6">
  
            {messages.length === 0 && (
              <EmptyAgentState
                onQuestion={
                  submitQuery
                }
              />
            )}
  
  
            <div className="space-y-6">
  
              {messages.map(
                (message) => (
                  <AgentMessage
                    key={message.id}
                    message={message}
                  />
                )
              )}
  
  
              {loading && (
                <div className="flex items-start gap-3">
  
                  <div className="rounded-lg bg-slate-900 p-2 text-white">
                    <Bot size={18} />
                  </div>
  
                  <div className="rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-600">
                    <div className="flex items-center gap-2">
                      <Loader2
                        size={16}
                        className="animate-spin"
                      />
  
                      PRISM is investigating the project...
                    </div>
                  </div>
  
                </div>
              )}
  
            </div>
  
          </div>
  
  
          {error && (
            <div className="mx-6 mb-3 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertCircle size={17} />
              {error}
            </div>
          )}
  
  
          <div className="border-t border-slate-200 p-4">
  
            <div className="flex items-end gap-3">
  
              <textarea
                value={query}
                onChange={(event) =>
                  setQuery(
                    event.target.value
                  )
                }
                onKeyDown={
                  handleKeyDown
                }
                rows={2}
                placeholder="Ask PRISM about your project..."
                className="min-h-[52px] flex-1 resize-none rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
  
  
              <button
                onClick={() =>
                  submitQuery()
                }
                disabled={
                  loading ||
                  !query.trim()
                }
                className="flex h-[52px] w-[52px] items-center justify-center rounded-xl bg-slate-900 text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send size={19} />
              </button>
  
            </div>
  
  
            <p className="mt-2 text-xs text-slate-400">
              PRISM uses deterministic analytics as
              the source of truth. The agent investigates
              and explains the available evidence.
            </p>
  
          </div>
  
        </div>
  
      </div>
    );
  }
  
  
  function EmptyAgentState({
    onQuestion,
  }) {
    return (
      <div className="flex h-full min-h-[380px] flex-col items-center justify-center text-center">
  
        <div className="rounded-2xl bg-slate-900 p-4 text-white">
          <Bot size={30} />
        </div>
  
        <h2 className="mt-5 text-xl font-semibold text-slate-900">
          Ask PRISM about your project
        </h2>
  
        <p className="mt-2 max-w-lg text-sm leading-6 text-slate-500">
          PRISM can investigate uploaded project reports
          and explain forecasts, risks, progress trends,
          schedule impact, and evidence limitations.
        </p>
  
  
        <div className="mt-7 grid max-w-2xl gap-3 md:grid-cols-2">
  
          {suggestedQuestions.map(
            (question) => (
              <button
                key={question}
                onClick={() =>
                  onQuestion(
                    question
                  )
                }
                className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-left text-sm text-slate-700 transition hover:border-slate-400 hover:bg-white"
              >
                {question}
              </button>
            )
          )}
  
        </div>
  
      </div>
    );
  }
  
  
  function AgentMessage({
    message,
  }) {
    const isUser =
      message.role === "user";
  
    return (
      <div
        className={[
          "flex gap-3",
          isUser
            ? "justify-end"
            : "justify-start",
        ].join(" ")}
      >
  
        {!isUser && (
          <div className="h-fit rounded-lg bg-slate-900 p-2 text-white">
            <Bot size={18} />
          </div>
        )}
  
  
        <div
          className={[
            "max-w-[82%] rounded-2xl px-5 py-4",
            isUser
              ? "bg-slate-900 text-white"
              : "bg-slate-50 text-slate-700",
          ].join(" ")}
        >
  
          {isUser ? (
            <p className="whitespace-pre-wrap text-sm">
              {message.content}
            </p>
          ) : (
            <>
              <div className="prose prose-sm max-w-none prose-slate">
                <ReactMarkdown>
                  {message.content}
                </ReactMarkdown>
              </div>
  
  
              {(message.toolsUsed?.length >
                0 ||
                message.iterations) && (
                <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-slate-200 pt-3 text-xs text-slate-400">
  
                  {message.toolsUsed?.length >
                    0 && (
                    <span className="flex items-center gap-1">
                      <Wrench size={13} />
  
                      {message.toolsUsed.join(
                        ", "
                      )}
                    </span>
                  )}
  
  
                  {message.iterations && (
                    <span>
                      {message.iterations} agent
                      iteration
                      {message.iterations !== 1
                        ? "s"
                        : ""}
                    </span>
                  )}
  
                </div>
              )}
            </>
          )}
  
        </div>
  
  
        {isUser && (
          <div className="h-fit rounded-lg bg-slate-200 p-2 text-slate-700">
            <User size={18} />
          </div>
        )}
  
      </div>
    );
  }