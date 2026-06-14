import { useState, useEffect, useCallback } from "react";
import {
  Card, CardContent, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Switch, Button,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  IconButton, Tooltip, Chip, Box, Snackbar, Alert,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import LanguageIcon from "@mui/icons-material/Language";
import { apiRequest } from "../services/api";

interface WebFetchPerms {
  id: string;
  user_id: string;
  username: string;
  enabled: boolean;
  requests_per_hour: number;
  requests_per_day: number;
  max_chars: number;
  allowed_domains: string;
  blocked_domains: string;
}

interface UserWithoutPerms {
  user_id: string;
  username: string;
}

export const WebFetchAccess = () => {
  const [permissions, setPermissions] = useState<WebFetchPerms[]>([]);
  const [usersWithoutPerms, setUsersWithoutPerms] = useState<UserWithoutPerms[]>([]);
  const [editDialog, setEditDialog] = useState<{ open: boolean; perms: WebFetchPerms | null; userId?: string }>({ open: false, perms: null });
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: "success" | "error" }>({ open: false, message: "", severity: "success" });

  const loadData = useCallback(async () => {
    try {
      const res: any = await apiRequest("GET", "/admin/web-fetch/permissions");
      setPermissions(res.permissions || []);
      setUsersWithoutPerms(res.users_without_perms || []);
    } catch (e: any) {
      setSnackbar({ open: true, message: e.message, severity: "error" });
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleToggle = async (userId: string, current: boolean) => {
    try {
      await apiRequest("PUT", `/admin/web-fetch/permissions/${userId}`, { enabled: !current });
      setSnackbar({ open: true, message: "Сохранено", severity: "success" });
      loadData();
    } catch (e: any) {
      setSnackbar({ open: true, message: e.message, severity: "error" });
    }
  };

  const handleSave = async () => {
    if (!editDialog.perms) return;
    const { user_id, ...rest } = editDialog.perms;
    try {
      await apiRequest("PUT", `/admin/web-fetch/permissions/${user_id}`, rest);
      setEditDialog({ open: false, perms: null });
      setSnackbar({ open: true, message: "Сохранено", severity: "success" });
      loadData();
    } catch (e: any) {
      setSnackbar({ open: true, message: e.message, severity: "error" });
    }
  };

  return (
    <Card sx={{ m: 2, mt: 10 }}>
      <CardContent>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
          <LanguageIcon color="primary" fontSize="large" />
          <Typography variant="h5" fontWeight={700}>Web Fetch — Доступ к веб-страницам</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Управление доступом пользователей к веб-страницам через чат.
          Право <Chip label="web" size="small" color="primary" variant="outlined" /> должно быть в правах пользователя.
        </Typography>

        {usersWithoutPerms.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
              Пользователи без настроек web fetch ({usersWithoutPerms.length}):
            </Typography>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
              {usersWithoutPerms.map((u) => (
                <Chip
                  key={u.user_id}
                  label={u.username}
                  size="small"
                  variant="outlined"
                  onClick={() => setEditDialog({ open: true, perms: { ...emptyPerms(u.user_id, u.username), user_id: u.user_id, username: u.username }, userId: u.user_id })}
                />
              ))}
            </Box>
          </Box>
        )}

        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Пользователь</TableCell>
                <TableCell align="center">Включён</TableCell>
                <TableCell align="right">Запросов/час</TableCell>
                <TableCell align="right">Запросов/день</TableCell>
                <TableCell align="right">Макс. символов</TableCell>
                <TableCell>Разрешённые домены</TableCell>
                <TableCell>Заблокиров. домены</TableCell>
                <TableCell align="center">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {permissions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                      Нет настроек web fetch. Нажмите на пользователя выше, чтобы добавить.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
              {permissions.map((p) => (
                <TableRow key={p.id} hover>
                  <TableCell>{p.username || p.user_id}</TableCell>
                  <TableCell align="center">
                    <Switch checked={p.enabled} onChange={() => handleToggle(p.user_id, p.enabled)} size="small" />
                  </TableCell>
                  <TableCell align="right">{p.requests_per_hour}</TableCell>
                  <TableCell align="right">{p.requests_per_day}</TableCell>
                  <TableCell align="right">{p.max_chars.toLocaleString()}</TableCell>
                  <TableCell sx={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {p.allowed_domains || "—"}
                  </TableCell>
                  <TableCell sx={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {p.blocked_domains || "—"}
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="Редактировать"><IconButton size="small" onClick={() => setEditDialog({ open: true, perms: p })}><EditIcon fontSize="small" /></IconButton></Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>

      <Dialog open={editDialog.open} onClose={() => setEditDialog({ open: false, perms: null })} maxWidth="sm" fullWidth>
        <DialogTitle>Настройки web fetch — {editDialog.perms?.username || editDialog.userId}</DialogTitle>
        <DialogContent>
          {editDialog.perms && (
            <Box sx={{ pt: 1, display: "flex", flexDirection: "column", gap: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Switch checked={editDialog.perms.enabled} onChange={(e) => setEditDialog({ ...editDialog, perms: { ...editDialog.perms!, enabled: e.target.checked } })} />
                <Typography variant="body2">Включён</Typography>
              </Box>
              <TextField label="Запросов в час" type="number" value={editDialog.perms.requests_per_hour} onChange={(e) => setEditDialog({ ...editDialog, perms: { ...editDialog.perms!, requests_per_hour: parseInt(e.target.value) || 0 } })} fullWidth />
              <TextField label="Запросов в день" type="number" value={editDialog.perms.requests_per_day} onChange={(e) => setEditDialog({ ...editDialog, perms: { ...editDialog.perms!, requests_per_day: parseInt(e.target.value) || 0 } })} fullWidth />
              <TextField label="Макс. символов" type="number" value={editDialog.perms.max_chars} onChange={(e) => setEditDialog({ ...editDialog, perms: { ...editDialog.perms!, max_chars: parseInt(e.target.value) || 0 } })} fullWidth />
              <TextField label="Разрешённые домены (через запятую)" value={editDialog.perms.allowed_domains} onChange={(e) => setEditDialog({ ...editDialog, perms: { ...editDialog.perms!, allowed_domains: e.target.value } })} fullWidth multiline rows={2} placeholder="example.com, docs.example.org" />
              <TextField label="Заблокированные домены (через запятую)" value={editDialog.perms.blocked_domains} onChange={(e) => setEditDialog({ ...editDialog, perms: { ...editDialog.perms!, blocked_domains: e.target.value } })} fullWidth multiline rows={2} placeholder="blocked-site.com" />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog({ open: false, perms: null })}>Отмена</Button>
          <Button onClick={handleSave} variant="contained">Сохранить</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={snackbar.open} autoHideDuration={3000} onClose={() => setSnackbar({ ...snackbar, open: false })} anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
        <Alert severity={snackbar.severity} variant="filled">{snackbar.message}</Alert>
      </Snackbar>
    </Card>
  );
};

function emptyPerms(userId: string, username: string): WebFetchPerms {
  return { id: "", user_id: userId, username, enabled: false, requests_per_hour: 10, requests_per_day: 50, max_chars: 10000, allowed_domains: "", blocked_domains: "" };
}
