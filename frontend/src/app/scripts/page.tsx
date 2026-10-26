"use client";

import * as React from "react";
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  Radio,
  Send,
  Square,
} from "lucide-react";

import { ContentWrapper } from "@/components/content-wrapper";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { runScript } from "@/lib/api";

const MAX_OUTPUT_LINES = 500;

const SCRIPT_OPTIONS = [
  {
    id: "test-1",
    title: "Test 1",
    description: "Simulate sending 100 data packets.",
    icon: ArrowUpFromLine,
  },
  {
    id: "test-2",
    title: "Test 2",
    description: "Simulate receiving 100 data packets.",
    icon: ArrowDownToLine,
  },
  {
    id: "send_message",
    title: "send_message",
    description: "Launch the existing CAN message sender.",
    icon: Send,
  },
  {
    id: "trace_window",
    title: "trace_window",
    description: "Start the existing live CAN trace.",
    icon: Radio,
  },
  {
    id: "dummy",
    title: "dummy",
    description: "Run the dummy UDS discovery scan.",
    icon: Radio,
  },
] as const;

type ScriptId = (typeof SCRIPT_OPTIONS)[number]["id"];

export default function ScriptsPage() {
  const [activeScript, setActiveScript] = React.useState<ScriptId | null>(null);
  const [status, setStatus] = React.useState("Choose a script to run.");
  const [error, setError] = React.useState<string | null>(null);
  const [scriptOutput, setScriptOutput] = React.useState("");
  const [outputTruncated, setOutputTruncated] = React.useState(false);
  const scriptOutputRef = React.useRef("");
  const controllerRef = React.useRef<AbortController | null>(null);

  const appendOutput = (chunk: string) => {
    const lines = (scriptOutputRef.current + chunk).split("\n");
    const visibleLineCount =
      lines.length - (lines[lines.length - 1] === "" ? 1 : 0);
    if (visibleLineCount > MAX_OUTPUT_LINES) {
      lines.splice(0, visibleLineCount - MAX_OUTPUT_LINES);
      setOutputTruncated(true);
    }
    scriptOutputRef.current = lines.join("\n");
    setScriptOutput(scriptOutputRef.current);
  };

  React.useEffect(
    () => () => {
      controllerRef.current?.abort();
    },
    [],
  );

  const startScript = async (scriptId: ScriptId) => {
    const controller = new AbortController();
    controllerRef.current = controller;
    setActiveScript(scriptId);
    setError(null);
    scriptOutputRef.current = "";
    setScriptOutput("");
    setOutputTruncated(false);
    setStatus("Running. Output is streaming to the backend terminal and this page.");

    try {
      await runScript(scriptId, controller.signal, appendOutput);
      setStatus("Script finished. Output is available below and in the backend terminal.");
    } catch (caughtError) {
      if (controller.signal.aborted) {
        setStatus("Script stopped.");
      } else {
        const message =
          caughtError instanceof Error
            ? caughtError.message
            : "The script could not be run.";
        setError(message);
        setStatus("Script failed.");
      }
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null;
      }
      setActiveScript(null);
    }
  };

  const stopScript = () => controllerRef.current?.abort();

  return (
    <ContentWrapper>
      <PageHeader
        title="Script tools"
        description="Run packet demos or launch the existing CAN scripts. Live output appears here and in the backend terminal."
        actions={
          activeScript ? (
            <Button
              variant="destructive"
              onClick={stopScript}
              className="gap-2"
            >
              <Square className="h-4 w-4" />
              Stop script
            </Button>
          ) : undefined
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        {SCRIPT_OPTIONS.map(({ id, title, description, icon: Icon }) => (
          <Card key={id}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="size-5" />
                </div>
                <CardTitle>{title}</CardTitle>
              </div>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => void startScript(id)}
                disabled={activeScript !== null}
              >
                {activeScript === id ? "Running…" : "Run"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div aria-live="polite" className="space-y-1 text-sm">
        <p>{status}</p>
        {error && <p className="text-destructive">{error}</p>}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Live output</CardTitle>
          <CardDescription>
            {outputTruncated
              ? `Showing the latest ${MAX_OUTPUT_LINES} lines; earlier output was trimmed.`
              : `Script output appears here as it runs (up to ${MAX_OUTPUT_LINES} lines).`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96 rounded-md border bg-muted/30">
            <pre
              role="log"
              aria-label="Live script output"
              aria-live="polite"
              className="min-h-full whitespace-pre-wrap break-words p-4 font-mono text-xs leading-relaxed"
            >
              {scriptOutput ||
                (activeScript
                  ? "Waiting for script output..."
                  : "Run a script to see its output here.")}
            </pre>
          </ScrollArea>
        </CardContent>
      </Card>
    </ContentWrapper>
  );
}
