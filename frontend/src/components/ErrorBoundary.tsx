import { Component } from "react";
import { ErrorPage } from "../pages/ErrorPage";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  info?: string;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(_error: Error, info: any) {
    this.setState({ info: info?.componentStack || "" });
  }

  render() {
    if (this.state.hasError) {
      const detail = {
        status: 0,
        error: this.state.error?.message || "Неизвестная ошибка",
        traceback: this.state.info || this.state.error?.stack || "",
        request: { method: "N/A", path: window.location.pathname },
      };
      return (
        <ErrorPage
          error={detail}
          onRetry={() => {
            this.setState({ hasError: false });
            window.location.reload();
          }}
        />
      );
    }
    return this.props.children;
  }
}
