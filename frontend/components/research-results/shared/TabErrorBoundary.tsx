'use client';

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  tabName: string;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class TabErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error(`[TabErrorBoundary] Error in ${this.props.tabName}:`, error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-center">
          <p className="text-red-600 font-medium">
            Something went wrong loading {this.props.tabName}.
          </p>
          {this.state.error?.message && (
            <p className="text-sm text-gray-500 mt-2">{this.state.error.message}</p>
          )}
          <button
            onClick={() => this.setState({ hasError: false, error: undefined })}
            className="mt-3 px-3 py-1.5 text-sm bg-gray-100 rounded hover:bg-gray-200 transition-colors"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
