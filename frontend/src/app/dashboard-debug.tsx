"use client";

import * as React from "react";

interface State {
  error: Error | null;
  eventLog: string[];
}

interface Props {
  children: React.ReactNode;
  label: string;
}

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null, eventLog: [] };

  static getDerivedStateFromError(error: Error): State {
    return { error, eventLog: [] };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    const entry =
      new Date().toISOString() +
      " caught error: " +
      error.message +
      "\n" +
      (info.componentStack ?? "");
    this.setState((prev) => ({ eventLog: [...prev.eventLog, entry] }));
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 16, border: "2px solid red", margin: 8 }}>
          <strong>Error in {this.props.label}</strong>
          <pre style={{ whiteSpace: "pre-wrap" }}>
            {this.state.error.message}
            {"\n"}
            {this.state.error.stack}
          </pre>
          {this.state.eventLog.length > 0 ? (
            <pre style={{ whiteSpace: "pre-wrap" }}>
              {this.state.eventLog.join("\n---\n")}
            </pre>
          ) : null}
        </div>
      );
    }
    return this.props.children;
  }
}