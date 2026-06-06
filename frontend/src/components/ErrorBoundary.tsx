import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  title?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div
            className="p-4 rounded-2xl flex flex-col gap-2 border text-xs"
            style={{
              background: 'rgba(244,63,94,0.08)',
              borderColor: 'rgba(244,63,94,0.2)',
              color: '#fda4af',
            }}
          >
            <span className="font-bold text-sm">
              ⚠️ {this.props.title || 'Panel'} Rendering Error
            </span>
            <p className="opacity-80">
              {this.state.error?.message || 'A runtime crash occurred while loading this view.'}
            </p>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
