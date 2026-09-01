"use client";

import * as React from "react";

interface State {
  error: Error | null;
}

interface Props {
  children: React.ReactNode;
  label: string;
}

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error(
      "[ErrorBoundary:" + this.props.label + "] caught:",
      error,
      info.componentStack,
    );
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
        </div>
      );
    }
    return this.props.children;
  }
}