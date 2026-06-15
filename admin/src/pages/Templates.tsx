import { useState, useEffect, useCallback } from "react";
import {
  Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Button,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  IconButton, Tooltip, Box, Snackbar, Alert, Chip,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import AddIcon from "@mui/icons-material/Add";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { apiRequest } from "../services/api";

interface Template {
  id: string;
  name: string;
  description: string | null;
  file_path: string;
  variables: string | null;
  category: string | null;
}

const emptyForm = () => ({ name: "", description: "", variables: "", category: "" });

export const TemplateList = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [dialog, setDialog] = useState<{ open: boolean; edit?: Template }>({ open: false });
  const [form, setForm] = useState(emptyForm());
  const [file, setFile] = useState<File | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Template | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: "success" | "error" }>({ open: false, message: "", severity: "success" });

  const load = useCallback(async () => {
    try {
      const res: any = await apiRequest("GET", "/admin/doc-templates");
      setTemplates(res.templates || []);
    } catch (e: any) {
      setSnackbar({ open: true, message: e.message, severity: "error" });
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => { setForm(emptyForm()); setFile(null); setDialog({ open: false }); setTimeout(() => setDialog({ open: true }), 10); };
  const openEdit = (t: Template) => {
    setForm({ name: t.name, description: t.description || "", variables: t.variables || "", category: t.category || "" });
    setFile(null);
    setDialog({ open: true, edit: t });
  };

  const handleSave = async () => {
    try {
      const fd = new FormData();
      fd.append("name", form.name);
      fd.append("description", form.description);
      fd.append("variables", form.variables);
      fd.append("category", form.category);
      if (file) fd.append("file", file);

      if (dialog.edit) {
        await fetch(`/api/v1/admin/doc-templates/${dialog.edit.id}`, {
          method: "PUT", headers: { Authorization: `Bearer ${localStorage.getItem("auth_token")}` },
          body: fd,
        });
      } else {
        await fetch(`/api/v1/admin/doc-templates`, {
          method: "POST", headers: { Authorization: `Bearer ${localStorage.getItem("auth_token")}` },
          body: fd,
        });
      }
      setDialog({ open: false });
      setSnackbar({ open: true, message: dialog.edit ? "Шаблон обновлён" : "Шаблон создан", severity: "success" });
      load();
    } catch (e: any) {
      setSnackbar({ open: true, message: e.message || "Ошибка", severity: "error" });
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await apiRequest("DELETE", `/admin/doc-templates/${deleteTarget.id}`);
      setDeleteTarget(null);
      setSnackbar({ open: true, message: "Шаблон удалён", severity: "success" });
      load();
    } catch (e: any) {
      setSnackbar({ open: true, message: e.message, severity: "error" });
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={700}>Бланки документов</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>Создать шаблон</Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Название</TableCell>
              <TableCell>Описание</TableCell>
              <TableCell>Категория</TableCell>
              <TableCell>Переменные</TableCell>
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {templates.length === 0 && (
              <TableRow><TableCell colSpan={5} align="center">Нет шаблонов</TableCell></TableRow>
            )}
            {templates.map((t) => (
              <TableRow key={t.id} hover>
                <TableCell><strong>{t.name}</strong></TableCell>
                <TableCell>{t.description || "—"}</TableCell>
                <TableCell>{t.category ? <Chip label={t.category} size="small" /> : "—"}</TableCell>
                <TableCell><code style={{ fontSize: 12 }}>{t.variables || "—"}</code></TableCell>
                <TableCell align="right">
                  <Tooltip title="Редактировать"><IconButton size="small" onClick={() => openEdit(t)}><EditIcon /></IconButton></Tooltip>
                  <Tooltip title="Удалить"><IconButton size="small" color="error" onClick={() => setDeleteTarget(t)}><DeleteIcon /></IconButton></Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialog.open} onClose={() => setDialog({ open: false })} maxWidth="sm" fullWidth>
        <DialogTitle>{dialog.edit ? "Редактировать шаблон" : "Создать шаблон"}</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <TextField label="Название" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} fullWidth required />
            <TextField label="Описание" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} fullWidth multiline rows={2} />
            <TextField label="Категория" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} fullWidth placeholder="например: договор, акт, заявление" />
            <TextField label="Переменные (через запятую)" value={form.variables} onChange={e => setForm(f => ({ ...f, variables: e.target.value }))} fullWidth placeholder="client_name, date, amount" />
            <Box>
              <Button variant="outlined" component="label" startIcon={<CloudUploadIcon />} sx={{ mt: 1 }}>
                {file ? file.name : "Загрузить файл шаблона"}
                <input type="file" hidden accept=".html,.docx,.xlsx,.pptx" onChange={e => setFile(e.target.files?.[0] || null)} />
              </Button>
              {file && <Button size="small" sx={{ ml: 1 }} onClick={() => setFile(null)}>Убрать</Button>}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog({ open: false })}>Отмена</Button>
          <Button onClick={handleSave} variant="contained" disabled={!form.name}>{dialog.edit ? "Сохранить" : "Создать"}</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Удалить шаблон?</DialogTitle>
        <DialogContent>
          <Typography>Шаблон «{deleteTarget?.name}» будет удалён.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Отмена</Button>
          <Button onClick={handleDelete} color="error">Удалить</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={snackbar.open} autoHideDuration={4000} onClose={() => setSnackbar(s => ({ ...s, open: false }))}>
        <Alert severity={snackbar.severity} onClose={() => setSnackbar(s => ({ ...s, open: false }))}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  );
};
