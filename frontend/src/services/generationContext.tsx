import { createContext, useContext, useState, useCallback, useRef, useEffect, type ReactNode } from "react";
import { api } from "./api";

interface AssetInfo {
  id: string;
  filename: string;
  file_path: string;
}

interface GenerationStatus {
  generation_id: string;
  status: string;
  cost: number;
  images: AssetInfo[];
  error_message?: string;
}

interface GenerationContextType {
  runningGen: GenerationStatus | null;
  startTracking: (genId: string) => void;
  stopTracking: () => void;
}

const GenerationContext = createContext<GenerationContextType>({
  runningGen: null,
  startTracking: () => {},
  stopTracking: () => {},
});

export const GenerationProvider = ({ children }: { children: ReactNode }) => {
  const [runningGen, setRunningGen] = useState<GenerationStatus | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopTracking = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    setRunningGen(null);
  }, []);

  const startTracking = useCallback((genId: string) => {
    stopTracking();
    setRunningGen({ generation_id: genId, status: "queued", cost: 0, images: [] });
    pollingRef.current = setInterval(async () => {
      try {
        const res: any = await api("GET", `/generate/${genId}/status`);
        setRunningGen({
          generation_id: genId,
          status: res.status,
          cost: res.cost || 0,
          images: res.images || [],
          error_message: res.error_message,
        });
        if (res.status === "completed" || res.status === "failed") {
          if (pollingRef.current) clearInterval(pollingRef.current);
          pollingRef.current = null;
          setTimeout(() => setRunningGen(null), 10000);
        }
      } catch {
        stopTracking();
      }
    }, 3000);
  }, [stopTracking]);

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  return (
    <GenerationContext.Provider value={{ runningGen, startTracking, stopTracking }}>
      {children}
    </GenerationContext.Provider>
  );
};

export const useGenerationStatus = () => useContext(GenerationContext);
