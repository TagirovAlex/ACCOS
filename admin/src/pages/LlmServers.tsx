import { useState, useEffect } from "react";
import {
  Typography, Box, Button, Card, CardContent, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Switch, FormControlLabel, Tooltip, Chip, Grid as MuiGrid,
  ToggleButtonGroup, ToggleButton, CircularProgress, Alert,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import DnsIcon from "@mui/icons-material/Dns";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
import { useNotify, Confirm } from "react-admin";
import { getToken } from "../services/api";

const API_BASE = "/api/v1/admin/llm-servers";

interface LlmServer {
  id: string;
  name: string;
  base_url: string;
  api_key: string;
  model_name: string;
  system_prompt: string;
  weight: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const emptyForm = {
  name: "", base_url: "", api_key: "", model_name: "default",
  system_prompt: "", weight: 1, is_active: true,
};

export const LlmServerList = () => {
  const [servers, setServers] = useState<LlmServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"list" | "tiles">(() => (localStorage.getItem("llm_servers_view") as "list" | "tiles") ?? "list");
  const [formOpen, setFormOpen] = useState(false);
  const [formData, setFormData] = useState<any>({ ...emptyForm });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const notify = useNotify();

  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const fetchServers = async () => {
    setLoading(true);
    try {
      const res = await fetch(API_BASE, { headers });
      const json = await res.json();
      if (json.success) setServers(json.servers || []);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchServers(); }, []);

  const openCreate = () => {
    setEditingId(null);
    setFormData({ ...emptyForm });
    setFormOpen(true);
  };

  const openEdit = (s: LlmServer) => {
    setEditingId(s.id);
    setFormData({ ...s });
    setFormOpen(true);
  };

  const handleSave = async () => {
    if (!formData.name || !formData.base_url) {
      notify("Заполните название и URL", { type: "warning" });
      return;
    }
    setSaving(true);
    try {
      const url = editingId ? `${API_BASE}/${editingId}` : API_BASE;
      const method = editingId ? "PUT" : "POST";
      const body = editingId
        ? Object.fromEntries(Object.entries(formData).filter(([_, v]) => v !== null))
        : formData;
      delete body.id;
      delete body.created_at;
      delete body.updated_at;
      const res = await fetch(url, {
        method, headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (res.ok) {
        notify(editingId ? "Сервер обновлён" : "Сервер создан", { type: "success" });
        setFormOpen(false);
        fetchServers();
      } else {
        notify(json.error || json.detail || "Ошибка", { type: "error" });
      }
    } catch (e: any) {
      notify("Ошибка: " + e.message, { type: "error" });
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      const res = await fetch(`${API_BASE}/${deleteTarget}`, { method: "DELETE", headers });
      const json = await res.json();
      if (json.success) {
        notify("Сервер удалён", { type: "success" });
        setDeleteTarget(null);
        fetchServers();
      }
    } catch {}
  };

  const handleTest = async (id: string) => {
    setTesting(id);
    try {
      const res = await fetch(`${API_BASE}/${id}/test`, { method: "POST", headers });
      const json = await res.json();
      if (json.success) {
        notify("Соединение OK: " + (json.error || ""), { type: "success" });
      } else {
        notify("Ошибка: " + (json.error || "неизвестная"), { type: "error" });
      }
    } catch (e: any) {
      notify("Ошибка: " + e.message, { type: "error" });
    }
    setTesting(null);
  };

  const listView = (
    <Box>
      {servers.map((s) => (
        <Card key={s.id} sx={{ mb: 1, "&:hover": { bgcolor: "action.hover" } }}>
          <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, py: 1.5, "&:last-child": { pb: 1.5 } }}>
            <DnsIcon color={s.is_active ? "success" : "disabled"} />
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="body2" fontWeight={600}>{s.name}</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                {s.base_url} · {s.model_name}
              </Typography>
            </Box>
            <Chip label={`weight: ${s.weight}`} size="small" variant="outlined" />
            <Chip label={s.is_active ? "Активен" : "Неактивен"} size="small" color={s.is_active ? "success" : "default"} />
            <Tooltip title="Тест соединения">
              <IconButton size="small" onClick={() => handleTest(s.id)} disabled={testing === s.id}>
                {testing === s.id ? <CircularProgress size={16} /> : <PlayArrowIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Редактировать">
              <IconButton size="small" onClick={() => openEdit(s)}><EditIcon fontSize="small" /></IconButton>
            </Tooltip>
            <Tooltip title="Удалить">
              <IconButton size="small" color="error" onClick={() => setDeleteTarget(s.id)}><DeleteIcon fontSize="small" /></IconButton>
            </Tooltip>
          </CardContent>
        </Card>
      ))}
    </Box>
  );

  const tilesView = (
    <MuiGrid container spacing={2}>
      {servers.map((s) => (
        <MuiGrid key={s.id} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <Card sx={{ height: "100%", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <DnsIcon color={s.is_active ? "success" : "disabled"} />
                <Typography variant="body2" fontWeight={600} noWrap sx={{ flex: 1 }}>{s.name}</Typography>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5, wordBreak: "break-all" }}>{s.base_url}</Typography>
              <Chip label={s.model_name} size="small" variant="outlined" sx={{ mr: 0.5 }} />
              <Chip label={`w: ${s.weight}`} size="small" variant="outlined" sx={{ mr: 0.5 }} />
              <Chip label={s.is_active ? "Активен" : "Неактивен"} size="small" color={s.is_active ? "success" : "default"} />
              <Box sx={{ mt: 1, display: "flex", gap: 0.5 }}>
                <Tooltip title="Тест">
                  <IconButton size="small" onClick={() => handleTest(s.id)} disabled={testing === s.id}>
                    {testing === s.id ? <CircularProgress size={16} /> : <PlayArrowIcon fontSize="small" />}
                  </IconButton>
                </Tooltip>
                <Tooltip title="Редактировать">
                  <IconButton size="small" onClick={() => openEdit(s)}><EditIcon fontSize="small" /></IconButton>
                </Tooltip>
                <Tooltip title="Удалить">
                  <IconButton size="small" color="error" onClick={() => setDeleteTarget(s.id)}><DeleteIcon fontSize="small" /></IconButton>
                </Tooltip>
              </Box>
            </CardContent>
          </Card>
        </MuiGrid>
      ))}
    </MuiGrid>
  );

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
        <Typography variant="h5" sx={{ flex: 1 }}>LLM-серверы</Typography>
        <ToggleButtonGroup value={view} exclusive size="small"
          onChange={(_, v) => { if (v) { setView(v); localStorage.setItem("llm_servers_view", v); } }}>
          <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
          <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
        </ToggleButtonGroup>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          Добавить сервер
        </Button>
      </Box>

      {servers.length === 0 && !loading && (
        <Alert severity="info">LLM-серверы не настроены. Добавьте хотя бы один сервер для работы чата.</Alert>
      )}

      {view === "list" ? listView : tilesView}

      <Dialog open={formOpen} onClose={() => !saving && setFormOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingId ? "Редактировать сервер" : "Добавить LLM-сервер"}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
            <TextField label="Название" size="small" required fullWidth value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
            <TextField label="Base URL" size="small" required fullWidth value={formData.base_url}
              onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
              placeholder="http://localhost:1234/v1" />
            <TextField label="API Key" size="small" fullWidth value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              type="password" />
            <TextField label="Модель" size="small" fullWidth value={formData.model_name}
              onChange={(e) => setFormData({ ...formData, model_name: e.target.value })} />
            <TextField label="System Prompt" size="small" fullWidth multiline rows={3} value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })} />
            <TextField label="Weight" size="small" type="number" fullWidth value={formData.weight}
              onChange={(e) => setFormData({ ...formData, weight: parseInt(e.target.value) || 1 })} />
            <FormControlLabel control={
              <Switch checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} />
            } label="Активен" />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFormOpen(false)} disabled={saving}>Отмена</Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? "Сохранение..." : "Сохранить"}
          </Button>
        </DialogActions>
      </Dialog>

      <Confirm
        isOpen={!!deleteTarget}
        title="Удалить сервер?"
        content="Сервер будет удалён без возможности восстановления."
        onConfirm={handleDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </Box>
  );
};
