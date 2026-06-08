import { createContext, useContext, useState, type ReactNode } from "react";
import { ErrorPage } from "../pages/ErrorPage";

interface ErrorDetail {
  status?: number;
  error?: string;
  error_id?: string;
  request?: { method?: string; path?: string; query?: string };
  traceback?: string;
}

interface ErrorContextType {
  showError: (detail: ErrorDetail) => void;
  clearError: () => void;
}

const ErrorCtx = createContext<ErrorContextType>({ showError: () => {}, clearError: () => {} });

export const useError = () => useContext(ErrorCtx);

export const ErrorProvider = ({ children }: { children: ReactNode }) => {
  const [error, setError] = useState<ErrorDetail | null>(null);

  return (
    <ErrorCtx.Provider value={{ showError: setError, clearError: () => setError(null) }}>
      {error && (
        <div style={{ position: "fixed", inset: 0, zIndex: 9999, background: "#fff", overflow: "auto" }}>
          <ErrorPage error={error} onRetry={() => setError(null)} />
        </div>
      )}
      {children}
    </ErrorCtx.Provider>
  );
};
