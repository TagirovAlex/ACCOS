import { Chip } from "@mui/material";

const STATUS_COLORS: Record<string, "success" | "error" | "info" | "warning" | "default"> = {
  completed: "success",
  ready: "success",
  active: "success",
  failed: "error",
  error: "error",
  processing: "info",
  indexing: "info",
  queued: "default",
  pending: "warning",
};

const STATUS_LABELS: Record<string, string> = {
  completed: "Готово",
  processing: "Обработка",
  queued: "В очереди",
  failed: "Ошибка",
  active: "Активен",
  ready: "Готов",
  indexing: "Индексация",
  pending: "Ожидает",
  error: "Ошибка",
};

export const StatusChip = ({ status }: { status: string }) => (
  <Chip
    label={STATUS_LABELS[status] || status}
    size="small"
    color={STATUS_COLORS[status] || "default"}
  />
);
