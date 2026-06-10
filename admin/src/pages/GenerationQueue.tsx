import { useEffect, useState } from "react";
import { useRedirect } from "react-admin";
import { Box, Typography, Chip, IconButton, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, LinearProgress } from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import RefreshIcon from "@mui/icons-material/Refresh";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

interface QueueItem {
  id: string;
  user_id: string;
  username: string;
  workflow_type: string;
  prompt: string;
  status: string;
  created_at: string;
}

const statusLabels: Record<string, string> = {
  queued: "В очереди",
  processing: "Обработка",
};

function adminToken(): string | null {
  return localStorage.getItem("admin_token") || localStorage.getItem("token") || null;
}

const statusColors: Record<string, "default" | "info" | "success" | "error"> = {
  queued: "default",
  processing: "info",
};

export const GenerationQueue = () => {
  const redirect = useRedirect();
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const token = adminToken();
      const res = await fetch("/api/v1/admin/generation-queue", { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      if (data.success) setItems(data.items || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleCancel = async (id: string) => {
    setProcessingId(id);
    try {
      const token = adminToken();
      await fetch(`/api/v1/admin/generation-queue/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      load();
    } catch { /* ignore */ }
    setProcessingId(null);
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Button startIcon={<ArrowBackIcon />} size="small" onClick={() => redirect("list", "generations")}>
          Генерации
        </Button>
        <Typography variant="h5" fontWeight={700} sx={{ flex: 1 }}>Очередь генераций</Typography>
        <IconButton onClick={load} title="Обновить"><RefreshIcon /></IconButton>
      </Box>

      {loading ? <LinearProgress /> : (
        <>
          <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
            <Chip label={`В обработке: ${items.filter(i => i.status === "processing").length}`} color="info" />
            <Chip label={`В очереди: ${items.filter(i => i.status === "queued").length}`} color="default" />
          </Box>

          {items.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 4 }}>
              Очередь пуста
            </Typography>
          ) : (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>#</TableCell>
                    <TableCell>Пользователь</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell>Промпт</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell>Создана</TableCell>
                    <TableCell>Действия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {items.map((item, idx) => (
                    <TableRow key={item.id}>
                      <TableCell>{idx + 1}</TableCell>
                      <TableCell>{item.username}</TableCell>
                      <TableCell><Chip label={item.workflow_type} size="small" /></TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {item.prompt}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={statusLabels[item.status] || item.status} size="small" color={statusColors[item.status] || "default"} />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">{new Date(item.created_at).toLocaleString()}</Typography>
                      </TableCell>
                      <TableCell>
                        <IconButton size="small" color="error" onClick={() => handleCancel(item.id)} disabled={processingId === item.id}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </>
      )}
    </Box>
  );
};