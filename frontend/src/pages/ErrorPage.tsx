import { Box, Typography, Paper, Button, Chip } from "@mui/material";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";

interface ErrorDetail {
  status?: number;
  error?: string;
  error_id?: string;
  request?: { method?: string; path?: string; query?: string };
  traceback?: string;
}

interface Props {
  error?: ErrorDetail | null;
  onRetry?: () => void;
}

const STATUS_LABELS: Record<number, [string, string]> = {
  400: ["Bad Request", "Неверный запрос"],
  401: ["Unauthorized", "Требуется авторизация"],
  403: ["Forbidden", "Доступ запрещён"],
  404: ["Not Found", "Ресурс не найден"],
  422: ["Validation Error", "Ошибка валидации"],
  429: ["Too Many Requests", "Слишком много запросов"],
  500: ["Internal Server Error", "Внутренняя ошибка сервера"],
  502: ["Bad Gateway", "Ошибка шлюза"],
  503: ["Service Unavailable", "Сервис недоступен"],
};

export const ErrorPage = ({ error, onRetry }: Props) => {
  const status = error?.status || 500;
  const labels = STATUS_LABELS[status] || ["Error", "Ошибка"];
  const isDev = import.meta.env.DEV;

  return (
    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh", p: 3 }}>
      <Paper sx={{ maxWidth: 640, width: "100%", p: 4, textAlign: "center" }}>
        <ErrorOutlineIcon color="error" sx={{ fontSize: 64, mb: 2 }} />
        <Typography variant="h3" fontWeight={700}>{status}</Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>{labels[1]}</Typography>
        {error?.error && (
          <Typography variant="body1" sx={{ mt: 1, mb: 2, fontFamily: "monospace", bgcolor: "action.hover", p: 2, borderRadius: 1, textAlign: "left", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            {error.error}
          </Typography>
        )}

        <Box sx={{ display: "flex", gap: 1, justifyContent: "center", flexWrap: "wrap", mb: 2 }}>
          {error?.status && <Chip label={`HTTP ${error.status}`} color="error" size="small" variant="outlined" />}
          {error?.error_id && <Chip label={`ID: ${error.error_id}`} size="small" variant="outlined" />}
          {error?.request?.method && <Chip label={error.request.method} size="small" variant="outlined" />}
          {error?.request?.path && <Chip label={error.request.path} size="small" variant="outlined" />}
        </Box>

        {isDev && error?.traceback && (
          <Box sx={{ textAlign: "left", mt: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: "block" }}>Stacktrace:</Typography>
            <Box component="pre" sx={{ fontSize: 11, bgcolor: "grey.900", color: "grey.100", p: 2, borderRadius: 1, overflow: "auto", maxHeight: 300, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {error.traceback}
            </Box>
          </Box>
        )}

        <Box sx={{ mt: 3, display: "flex", gap: 2, justifyContent: "center" }}>
          <Button variant="outlined" onClick={() => window.history.back()}>Назад</Button>
          {onRetry && <Button variant="contained" onClick={onRetry}>Повторить</Button>}
          <Button variant="text" onClick={() => window.location.reload()}>Обновить страницу</Button>
        </Box>
      </Paper>
    </Box>
  );
};
