import { useState, useEffect, useCallback } from "react";
import { Box, Typography, TextField, Button, List, ListItem, ListItemText, ListItemIcon, Chip, Dialog, DialogTitle, DialogContent, DialogActions, LinearProgress, Select, MenuItem, FormControl, InputLabel, IconButton, InputAdornment } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import UploadIcon from "@mui/icons-material/Upload";
import DownloadIcon from "@mui/icons-material/Download";
import DescriptionIcon from "@mui/icons-material/Description";
import { api } from "../services/api";

interface DocItem {
  id: string;
  title: string;
  filename: string;
  content_type: string;
  folder: string;
  file_path: string;
  ad_group_dn: string | null;
  status: string;
  created_at: string;
}

interface Department {
  dn: string;
  ou: string;
  description: string;
}

export const KnowledgePage = () => {
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFileState, setUploadFileState] = useState<File | null>(null);
  const [uploadFolder, setUploadFolder] = useState("");
  const [departments, setDepartments] = useState<Department[]>([]);
  const [uploading, setUploading] = useState(false);

  const loadDocs = useCallback(async () => {
    setLoading(true);
    try {
      const data: any = await api("GET", `/knowledge/documents?limit=50`);
      setDocs(Array.isArray(data) ? data : []);
    } catch { setDocs([]); }
    setLoading(false);
  }, []);

  const loadDepartments = useCallback(async () => {
    try {
      const data: any = await api("GET", "/knowledge/departments");
      setDepartments(data.departments || []);
    } catch { setDepartments([]); }
  }, []);

  useEffect(() => { loadDocs(); }, [loadDocs]);

  const handleUploadOpen = () => {
    loadDepartments();
    setUploadFileState(null);
    setUploadFolder("");
    setUploadOpen(true);
  };

  const handleUpload = async () => {
    if (!uploadFileState) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", uploadFileState);
      form.append("title", uploadFileState.name);
      form.append("folder", uploadFolder);
      if (uploadFolder) {
        const dept = departments.find(d => d.ou === uploadFolder);
        if (dept) form.append("ad_group_dn", dept.dn);
      }
      const token = localStorage.getItem("token");
      await fetch("/api/v1/knowledge/upload", {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
      setUploadOpen(false);
      loadDocs();
    } catch { /* ignore */ }
    setUploading(false);
  };

  const filtered = search
    ? docs.filter(d => d.title.toLowerCase().includes(search.toLowerCase()) || d.folder?.toLowerCase().includes(search.toLowerCase()))
    : docs;

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
        <Typography variant="h5" fontWeight={700} sx={{ flex: 1 }}>База знаний</Typography>
        <TextField size="small" placeholder="Поиск документов..." value={search}
          onChange={e => setSearch(e.target.value)}
          slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
          sx={{ minWidth: 280 }} />
        <Button variant="contained" startIcon={<UploadIcon />} onClick={handleUploadOpen}>Загрузить</Button>
      </Box>

      {loading ? <LinearProgress /> : filtered.length === 0 ? (
        <Typography color="text.secondary" sx={{ textAlign: "center", py: 6 }}>Документы не найдены</Typography>
      ) : (
        <List disablePadding sx={{ border: 1, borderColor: "divider", borderRadius: 2, overflow: "hidden" }}>
          {filtered.map(doc => (
            <ListItem key={doc.id} divider sx={{ bgcolor: "background.paper" }}>
              <ListItemIcon><DescriptionIcon /></ListItemIcon>
              <ListItemText
                primary={doc.title}
                secondary={`${doc.folder || "Общий доступ"} · ${doc.content_type.toUpperCase()} · ${new Date(doc.created_at).toLocaleDateString()}`} />
              <Chip label={doc.status === "ready" ? "Готов" : doc.status === "indexing" ? "Индексация" : doc.status} size="small"
                color={doc.status === "ready" ? "success" : doc.status === "indexing" ? "warning" : "default"} sx={{ mr: 1 }} />
              <IconButton size="small" href={`/${doc.file_path}`} target="_blank" title="Скачать">
                <DownloadIcon fontSize="small" />
              </IconButton>
            </ListItem>
          ))}
        </List>
      )}

      <Dialog open={uploadOpen} onClose={() => !uploading && setUploadOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Загрузка документа</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
            <Button variant="outlined" component="label">
              {uploadFileState ? uploadFileState.name : "Выберите файл"}
              <input type="file" hidden accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
                onChange={e => setUploadFileState(e.target.files?.[0] || null)} />
            </Button>
            <FormControl size="small" fullWidth>
              <InputLabel>Отдел</InputLabel>
              <Select value={uploadFolder}
                label="Отдел"
                onChange={e => setUploadFolder(e.target.value)}>
                <MenuItem value=""><em>Общий доступ</em></MenuItem>
                {departments.map(d => (
                  <MenuItem key={d.dn} value={d.ou}>{d.ou}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadOpen(false)} disabled={uploading}>Отмена</Button>
          <Button variant="contained" onClick={handleUpload} disabled={!uploadFileState || uploading}>
            {uploading ? "Загрузка..." : "Загрузить"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
