import { useState, useEffect } from "react";
import {
  Typography, Box, Button, IconButton,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, CircularProgress, Alert, Tooltip,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import BackupIcon from "@mui/icons-material/Backup";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useNotify, Confirm } from "react-admin";
import { getToken } from "../services/api";

const API_BASE = "/api/v1/admin/backups";

interface Backup {
  filename: string;
  size_bytes: number;
  created_at: string;
}

function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  if (bytes >= 1024) return (bytes / 1024).toFixed(2) + " KB";
  return bytes + " B";
}

export const BackupList = () => {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const notify = useNotify();

  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const fetchBackups = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(API_BASE, { headers });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
      setBackups(json.backups || []);
    } catch (err: any) {
      setError(err.message);
      notify(`Ошибка загрузки: ${err.message}`, { type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackups();
  }, []);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const res = await fetch(API_BASE, { method: "POST", headers });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
      notify("Бэкап создан", { type: "success" });
      fetchBackups();
    } catch (err: any) {
      notify(`Ошибка создания: ${err.message}`, { type: "error" });
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      const res = await fetch(`${API_BASE}/${encodeURIComponent(deleteTarget)}`, {
        method: "DELETE", headers,
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
      notify("Бэкап удалён", { type: "success" });
      setDeleteTarget(null);
      fetchBackups();
    } catch (err: any) {
      notify(`Ошибка удаления: ${err.message}`, { type: "error" });
      setDeleteTarget(null);
    }
  };

  return (
    <Box>
      <Typography variant="h5" mb={3}>Управление бэкапами</Typography>

      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        <Button
          variant="contained"
          startIcon={<BackupIcon />}
          onClick={handleCreate}
          disabled={creating}
        >
          {creating ? "Создание..." : "Создать бэкап"}
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchBackups}
          disabled={loading}
        >
          Обновить
        </Button>
      </Box>

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}

      {!loading && !error && backups.length === 0 && (
        <Alert severity="info">Бэкапов пока нет</Alert>
      )}

      {!loading && backups.length > 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Имя файла</TableCell>
                <TableCell align="right">Размер</TableCell>
                <TableCell>Дата создания</TableCell>
                <TableCell align="center">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {backups.map((b) => (
                <TableRow key={b.filename}>
                  <TableCell>{b.filename}</TableCell>
                  <TableCell align="right">{formatBytes(b.size_bytes)}</TableCell>
                  <TableCell>{b.created_at}</TableCell>
                  <TableCell align="center">
                    <Tooltip title="Удалить">
                      <IconButton color="error" onClick={() => setDeleteTarget(b.filename)}>
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Confirm
        isOpen={!!deleteTarget}
        title="Удаление бэкапа"
        content={`Вы уверены, что хотите удалить бэкап "${deleteTarget}"?`}
        onConfirm={handleDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </Box>
  );
};
