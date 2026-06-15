import { useState, useEffect, useCallback } from "react";
import {
  Box, Typography, List, ListItem, ListItemText,
  Breadcrumbs, Link, LinearProgress, IconButton, Chip, Button, Card, CardContent,
  Dialog, DialogContent, DialogTitle, DialogActions,
  Grid as MuiGrid, Select, MenuItem, FormControl, InputLabel, Alert,
  ToggleButtonGroup, ToggleButton,
  Tooltip, Checkbox, FormGroup, FormControlLabel,
  TableContainer, Table, TableHead, TableRow, TableCell, TableBody, Paper,
  TextField as MuiTextField, Switch, FormControlLabel as MuiFormControlLabel,
  Snackbar, CircularProgress,
} from "@mui/material";
import DescriptionIcon from "@mui/icons-material/Description";
import RefreshIcon from "@mui/icons-material/Refresh";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import UploadIcon from "@mui/icons-material/Upload";
import AutorenewIcon from "@mui/icons-material/Autorenew";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import ErrorIcon from "@mui/icons-material/Error";
import PreviewIcon from "@mui/icons-material/Preview";
import SegmentIcon from "@mui/icons-material/Segment";
import HomeIcon from "@mui/icons-material/Home";
import BusinessIcon from "@mui/icons-material/Business";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
import VisibilityIcon from "@mui/icons-material/Visibility";
import SettingsIcon from "@mui/icons-material/Settings";
import { getToken } from "../services/api";

interface Department { dn: string; ou: string; description: string; }
interface KnowledgeDoc {
  id: string; title: string; filename: string; content_type: string;
  status: string; error_message?: string; ad_group_dn?: string | null;
  file_path: string; folder: string; doc_number?: string | null;
  doc_date?: string | null; is_active: boolean;
  created_by: string; created_at: string; updated_at: string;
}
interface SettingDef {
  module_name: string; key: string; label: string; type: string;
  category: string; default: any; description: string;
  is_admin_setting: boolean; is_user_setting: boolean;
  validation: Record<string, any> | null; value: string | null;
}

function adminToken() { return localStorage.getItem("admin_token") || localStorage.getItem("token") || null; }
const fdate = (mtime: string) => mtime ? new Date(mtime).toLocaleString() : "\u2014";
const SCLR: Record<string, string> = { pending: "#f57c00", indexing: "#1976d2", ready: "#2e7d32", error: "#d32f2f" };
const SLBL: Record<string, string> = { pending: "Ожидает", indexing: "Индексация", ready: "Готов", error: "Ошибка" };
const IMG = new Set([".png", ".jpg", ".jpeg", ".gif", ".webp"]);
const ext = (name: string) => name.includes(".") ? "." + name.split(".").pop()?.toLowerCase() : "";
const TLB: Record<string, string> = { pdf: "PDF", docx: "DOCX", txt: "TXT", md: "MD", png: "PNG", jpg: "JPEG", jpeg: "JPEG" };

const CAT_LABELS: Record<string, string> = {
  general: "Общие", connection: "Подключение", pricing: "Стоимость", llm: "LLM",
  indexing: "Индексация", retrieval: "Поиск", embedding: "Эмбеддинги",
  scheduling: "Расписание", display: "Отображение", restrictions: "Ограничения",
};

function SettingField({ def, value, onChange }: { def: SettingDef; value: string; onChange: (key: string, val: string) => void }) {
  const handle = (v: string) => onChange(def.key, v);
  if (def.type === "boolean") {
    return (
      <MuiFormControlLabel
        control={<Switch checked={value === "true"} onChange={(e) => handle(e.target.checked ? "true" : "false")} />}
        label={<Box><Typography variant="body2">{def.label}</Typography><Typography variant="caption" color="text.secondary">{def.description}</Typography></Box>}
        sx={{ mb: 1.5, display: "flex", alignItems: "center", gap: 1 }}
      />
    );
  }
  if (def.type === "select" && def.validation?.options) {
    return (
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>{def.label}</InputLabel>
        <Select value={value || ""} label={def.label} onChange={(e) => handle(e.target.value)}>
          {def.validation.options.map((opt: string) => (<MenuItem key={opt} value={opt}>{opt}</MenuItem>))}
        </Select>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>{def.description}</Typography>
      </FormControl>
    );
  }
  return (
    <MuiTextField
      label={def.label} helperText={def.description}
      value={value ?? ""} onChange={(e) => handle(e.target.value)}
      fullWidth
      multiline={def.type === "textarea" || (value ?? "").length > 80}
      minRows={def.type === "textarea" ? 3 : (value ?? "").length > 80 ? 2 : undefined}
      type={def.type === "password" ? "password" : def.type === "number" ? "number" : "text"}
      slotProps={{ htmlInput: def.type === "number" ? { step: "any" } : undefined }}
      sx={{ mb: 2 }}
    />
  );
}

export const KnowledgePage = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [currentFolder, setCurrentFolder] = useState<string | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDoc[]>([]);
  const [viewMode, setViewMode] = useState<"list" | "tiles">(() => (localStorage.getItem("docs_view") as "list" | "tiles") ?? "list");
  const [rootViewMode, setRootViewMode] = useState<"list" | "tiles">(() => (localStorage.getItem("docs_root_view") as "list" | "tiles") ?? "tiles");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploadFolder, setUploadFolder] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResults, setUploadResults] = useState<{ filename: string; success: boolean; error?: string }[] | null>(null);
  const [reindexing, setReindexing] = useState<string | null>(null);
  const [batchReindexing, setBatchReindexing] = useState<string | null>(null);
  const [batchResult, setBatchResult] = useState<string | null>(null);
  const [chunksOpen, setChunksOpen] = useState(false);
  const [chunksDoc, setChunksDoc] = useState<KnowledgeDoc | null>(null);
  const [chunks, setChunks] = useState<any[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);
  const [hiddenFolders, setHiddenFolders] = useState<string[]>([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [draftHidden, setDraftHidden] = useState<string[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [ragSettings, setRagSettings] = useState<SettingDef[]>([]);
  const [ragValues, setRagValues] = useState<Record<string, string>>({});
  const [ragLoading, setRagLoading] = useState(false);
  const [savingRag, setSavingRag] = useState(false);
  const [snack, setSnack] = useState<{ msg: string; sev: "success" | "error" } | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [mkdirOpen, setMkdirOpen] = useState(false);
  const [mkdirName, setMkdirName] = useState("");
  const PAGE_SIZE = 50;
  const [reindexRunning, setReindexRunning] = useState<string | null>(null);
  const [reindexResult, setReindexResult] = useState<{ msg: string; success: boolean } | null>(null);

  const loadHiddenFolders = async () => {
    try {
      const token = adminToken();
      const res = await fetch("/api/v1/admin/settings", { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      const setting = (data.settings || []).find((s: any) => s.key === "hidden_doc_folders");
      if (setting && setting.value) setHiddenFolders(setting.value.split(",").map((s: string) => s.trim()).filter(Boolean));
    } catch {}
  };
  const saveHiddenFolders = async (folders: string[]) => {
    try {
      const token = adminToken();
      await fetch("/api/v1/admin/settings/hidden_doc_folders", { method: "PUT", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ value: folders.join(",") }) });
      setHiddenFolders(folders);
    } catch {}
  };
  const loadDepartments = async () => {
    try {
      const token = adminToken();
      const res = await fetch("/api/v1/knowledge/departments", { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setDepartments(data.departments || []);
    } catch {}
  };
  const loadDocuments = async (folder: string, p = 0) => {
    setLoading(true); setError(null); setPage(p);
    try {
      const token = adminToken();
      const q = `?folder=${encodeURIComponent(folder)}&skip=${p * PAGE_SIZE}&limit=${PAGE_SIZE}`;
      const res = await fetch(`/api/v1/knowledge/documents${q}`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      const docs = Array.isArray(data) ? data : [];
      setDocuments(docs);
      setHasMore(docs.length === PAGE_SIZE);
    } catch { setError("Ошибка загрузки документов"); }
    setLoading(false);
  };
  const loadRagSettings = useCallback(async () => {
    setRagLoading(true);
    try {
      const token = getToken();
      const res = await fetch("/api/v1/admin/modules/rag/settings", { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      const list: SettingDef[] = (data.settings || []).filter((s: SettingDef) => s.is_admin_setting);
      setRagSettings(list);
      const v: Record<string, string> = {};
      for (const s of list) v[s.key] = s.value ?? "";
      setRagValues(v);
    } catch { setSnack({ msg: "Ошибка загрузки настроек", sev: "error" }); }
    setRagLoading(false);
  }, []);

  useEffect(() => { loadDepartments(); loadHiddenFolders(); loadRagSettings(); }, [loadRagSettings]);

  const visibleDepartments = departments.filter((d) => !hiddenFolders.includes(d.ou));
  const navigateFolder = (folder: string | null) => { setCurrentFolder(folder); setPage(0); if (folder !== null) loadDocuments(folder, 0); };
  const handleBack = () => { setCurrentFolder(null); setDocuments([]); };

  const handleMkdir = async () => {
    if (!mkdirName.trim()) return;
    const folder = currentFolder === "" ? mkdirName.trim() : `${currentFolder}/${mkdirName.trim()}`;
    try {
      const token = adminToken();
      const res = await fetch("/api/v1/knowledge/folders/mkdir", { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ folder }) });
      const data = await res.json();
      if (data.success) { setSnack({ msg: "Папка создана", sev: "success" }); setMkdirOpen(false); setMkdirName(""); }
      else setSnack({ msg: data.error || "Ошибка", sev: "error" });
    } catch { setSnack({ msg: "Ошибка сети", sev: "error" }); }
  };
  const handleDelete = async (doc: KnowledgeDoc) => {
    if (!window.confirm(`Удалить "${doc.filename}"? Файл и эмбеддинги будут удалены.`)) return;
    try {
      const token = adminToken();
      const res = await fetch(`/api/v1/knowledge/documents/${doc.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      if (data.success) loadDocuments(currentFolder!);
    } catch {}
  };
  const handleBatchReindex = async (action: string) => {
    setBatchReindexing(action); setBatchResult(null);
    try {
      const token = adminToken();
      const res = await fetch(`/api/v1/knowledge/${action}`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setBatchResult(data.success ? `Готово: ${data.succeeded || 0} успешно, ${data.failed || 0} с ошибками` : data.error || "Ошибка");
      if (data.success) loadDocuments(currentFolder!);
    } catch (e: any) { setBatchResult(e.message || "Ошибка"); }
    setBatchReindexing(null);
  };
  const handleShowChunks = async (doc: KnowledgeDoc) => {
    setChunksDoc(doc); setChunks([]); setChunksLoading(true); setChunksOpen(true);
    try {
      const token = adminToken();
      const res = await fetch(`/api/v1/knowledge/${doc.id}/chunks`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setChunks(data.chunks || []);
    } catch {}
    setChunksLoading(false);
  };
  const handleReindex = async (doc: KnowledgeDoc) => {
    setReindexing(doc.id);
    try {
      const token = adminToken();
      await fetch(`/api/v1/knowledge/documents/${doc.id}/reindex`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      loadDocuments(currentFolder!);
    } catch {}
    setReindexing(null);
  };
  const handleUpload = async () => {
    if (uploadFiles.length === 0) return;
    setUploading(true); setUploadError(null); setUploadResults(null);
    try {
      const token = adminToken();
      const form = new FormData();
      for (const f of uploadFiles) form.append("files", f);
      form.append("folder", uploadFolder);
      const res = await fetch("/api/v1/knowledge/upload-batch", { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: form });
      const data = await res.json();
      if (data.success && data.results) {
        setUploadResults(data.results);
        if (data.results.some((r: any) => !r.success)) setUploadError("Некоторые файлы не загрузились");
        else { setUploadOpen(false); setUploadFiles([]); setUploadFolder(""); if (currentFolder !== null) loadDocuments(currentFolder); }
      } else setUploadError(data.error || data.detail || "Ошибка загрузки");
    } catch (e) { setUploadError("Ошибка сети: " + (e instanceof Error ? e.message : String(e))); }
    setUploading(false);
  };
  const handleDownload = async (doc: KnowledgeDoc) => {
    try {
      const token = adminToken();
      const path = doc.file_path.replace(/^static\//, "");
      const res = await fetch(`/api/v1/admin/files/download?path=${encodeURIComponent(path)}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) return;
      const blob = await res.blob(); const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = doc.filename;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {}
  };
  const handleReindexAction = async (action: string) => {
    setReindexRunning(action); setReindexResult(null);
    try {
      const token = getToken();
      const res = await fetch(`/api/v1/knowledge/${action}`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setReindexResult({
        success: data.success,
        msg: data.success ? `Готово: ${data.succeeded || 0} успешно, ${data.failed || 0} с ошибками` : data.error || "Ошибка",
      });
      if (data.success && currentFolder !== null) loadDocuments(currentFolder!);
    } catch (e: any) { setReindexResult({ success: false, msg: e.message || "Ошибка" }); }
    setReindexRunning(null);
  };
  const handleSaveRag = async () => {
    setSavingRag(true);
    try {
      const token = getToken();
      for (const s of ragSettings) {
        const newVal = ragValues[s.key] ?? "";
        if (newVal !== (s.value ?? "")) {
          await fetch(`/api/v1/admin/modules/rag/settings/${s.key}`, { method: "PUT", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ value: newVal }) });
        }
      }
      setSnack({ msg: "Настройки сохранены", sev: "success" });
    } catch (e: any) { setSnack({ msg: e.message || "Ошибка сохранения", sev: "error" }); }
    setSavingRag(false);
  };

  const folderLabel = currentFolder === "" ? "Общий доступ" : (currentFolder || "");
  const imgUrl = (doc: KnowledgeDoc) => `/static/${doc.file_path.replace(/^static\//, "")}`;

  const listView = (
    <List disablePadding>
      <ListItem sx={{ bgcolor: "action.hover", borderRadius: 1, mb: 1 }}>
        <ListItemText primary={<Typography variant="caption" fontWeight={700}>Название</Typography>} sx={{ flex: "0 0 40%" }} />
        <ListItemText primary={<Typography variant="caption" fontWeight={700}>Тип</Typography>} sx={{ flex: "0 0 60px" }} />
        <ListItemText primary={<Typography variant="caption" fontWeight={700}>Статус</Typography>} sx={{ flex: "0 0 100px" }} />
        <ListItemText primary={<Typography variant="caption" fontWeight={700}>Дата</Typography>} sx={{ flex: "0 0 150px" }} />
        <Box sx={{ flex: "0 0 140px" }} />
      </ListItem>
      {documents.map((doc) => (
        <ListItem key={doc.id} disablePadding sx={{ "&:hover": { bgcolor: "action.hover" }, borderRadius: 1 }}>
          <ListItemText primary={
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              {IMG.has(ext(doc.filename)) ? (<img src={imgUrl(doc)} alt="" style={{ width: 32, height: 32, objectFit: "cover", borderRadius: 2 }} />) : (<DescriptionIcon />)}
              <Typography variant="body2" noWrap>{doc.title}</Typography>
            </Box>
          } sx={{ flex: "0 0 40%", pl: 1 }} />
          <ListItemText primary={<Chip label={TLB[doc.content_type] || doc.content_type.toUpperCase()} size="small" variant="outlined" />} sx={{ flex: "0 0 60px" }} />
          <ListItemText primary={<Chip label={SLBL[doc.status] || doc.status} size="small" sx={{ bgcolor: SCLR[doc.status] || "#888", color: "white" }} />} sx={{ flex: "0 0 100px" }} />
          <ListItemText primary={<Typography variant="caption" color="text.secondary">{fdate(doc.created_at)}</Typography>} sx={{ flex: "0 0 150px" }} />
          <Box sx={{ flex: "0 0 200px", display: "flex", gap: 0.5 }}>
            <Tooltip title="Просмотр"><IconButton size="small" onClick={() => window.open(`/api/v1/knowledge/${doc.id}/preview`, "preview", "width=900,height=700,scrollbars=yes,resizable=yes")}><PreviewIcon fontSize="small" /></IconButton></Tooltip>
            <Tooltip title="Чанки"><IconButton size="small" onClick={() => handleShowChunks(doc)}><SegmentIcon fontSize="small" /></IconButton></Tooltip>
            <Tooltip title="Скачать"><IconButton size="small" onClick={() => handleDownload(doc)}><DownloadIcon fontSize="small" /></IconButton></Tooltip>
            <Tooltip title="Переиндексировать"><IconButton size="small" onClick={() => handleReindex(doc)} disabled={reindexing === doc.id || doc.status === "indexing"}><AutorenewIcon fontSize="small" className={reindexing === doc.id ? "spin" : ""} /></IconButton></Tooltip>
            <Tooltip title="Удалить"><IconButton size="small" color="error" onClick={() => handleDelete(doc)}><DeleteIcon fontSize="small" /></IconButton></Tooltip>
          </Box>
        </ListItem>
      ))}
    </List>
  );

  const tilesView = (
    <MuiGrid container spacing={2}>
      {documents.map((doc) => {
        const isImg = IMG.has(ext(doc.filename));
        return (
          <MuiGrid key={doc.id} size={{ xs: 6, sm: 4, md: 3, lg: 2 }}>
            <Card sx={{ "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}>
              <Box sx={{ height: 140, overflow: "hidden", bgcolor: "#1a1a1a", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }} onClick={() => handleDownload(doc)}>
                {isImg ? (<img src={imgUrl(doc)} alt={doc.filename} style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain", display: "block" }} onError={(e: any) => { e.target.style.display = "none"; }} />) : (<DescriptionIcon sx={{ fontSize: 48, color: "text.disabled" }} />)}
              </Box>
              <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
                <Typography variant="body2" noWrap>{doc.title}</Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 0.5 }}>
                  <Chip label={TLB[doc.content_type] || doc.content_type.toUpperCase()} size="small" variant="outlined" sx={{ height: 20 }} />
                  <Chip label={SLBL[doc.status] || doc.status} size="small" sx={{ height: 20, bgcolor: SCLR[doc.status] || "#888", color: "white" }} />
                </Box>
                <Box sx={{ display: "flex", gap: 0.5, mt: 1 }}>
                  <Tooltip title="Просмотр"><IconButton size="small" onClick={() => window.open(`/api/v1/knowledge/${doc.id}/preview`, "preview", "width=900,height=700,scrollbars=yes,resizable=yes")}><PreviewIcon fontSize="small" /></IconButton></Tooltip>
                  <Tooltip title="Чанки"><IconButton size="small" onClick={() => handleShowChunks(doc)}><SegmentIcon fontSize="small" /></IconButton></Tooltip>
                  <Tooltip title="Скачать"><IconButton size="small" onClick={() => handleDownload(doc)}><DownloadIcon fontSize="small" /></IconButton></Tooltip>
                  <Tooltip title="Переиндексировать"><IconButton size="small" onClick={() => handleReindex(doc)} disabled={reindexing === doc.id || doc.status === "indexing"}><AutorenewIcon fontSize="small" className={reindexing === doc.id ? "spin" : ""} /></IconButton></Tooltip>
                  <Tooltip title="Удалить"><IconButton size="small" color="error" onClick={() => handleDelete(doc)}><DeleteIcon fontSize="small" /></IconButton></Tooltip>
                </Box>
              </CardContent>
            </Card>
          </MuiGrid>
        );
      })}
    </MuiGrid>
  );

  const rootTilesView = (
    <MuiGrid container spacing={2}>
      <MuiGrid size={{ xs: 6, sm: 4, md: 3, lg: 2 }}>
        <Card sx={{ cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }} onClick={() => navigateFolder("")}>
          <Box sx={{ height: 100, display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "action.hover" }}><HomeIcon sx={{ fontSize: 48, color: "primary.main" }} /></Box>
          <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}><Typography variant="body2" noWrap textAlign="center">Общий доступ</Typography></CardContent>
        </Card>
      </MuiGrid>
      {visibleDepartments.map((dep) => (
        <MuiGrid key={dep.dn} size={{ xs: 6, sm: 4, md: 3, lg: 2 }}>
          <Card sx={{ cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }} onClick={() => navigateFolder(dep.ou)}>
            <Box sx={{ height: 100, display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "action.hover" }}><BusinessIcon sx={{ fontSize: 48, color: "secondary.main" }} /></Box>
            <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
              <Typography variant="body2" noWrap textAlign="center">{dep.ou}</Typography>
              {dep.description && (<Typography variant="caption" color="text.secondary" sx={{ display: "block", textAlign: "center", mt: 0.5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{dep.description}</Typography>)}
            </CardContent>
          </Card>
        </MuiGrid>
      ))}
    </MuiGrid>
  );

  const rootListView = (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead><TableRow><TableCell>Папка</TableCell><TableCell>Описание</TableCell></TableRow></TableHead>
        <TableBody>
          <TableRow hover sx={{ cursor: "pointer" }} onClick={() => navigateFolder("")}>
            <TableCell><Box sx={{ display: "flex", alignItems: "center", gap: 1 }}><HomeIcon fontSize="small" color="primary" /><Typography variant="body2">Общий доступ</Typography></Box></TableCell>
            <TableCell><Typography variant="caption" color="text.secondary">Общедоступные документы</Typography></TableCell>
          </TableRow>
          {visibleDepartments.map((dep) => (
            <TableRow key={dep.dn} hover sx={{ cursor: "pointer" }} onClick={() => navigateFolder(dep.ou)}>
              <TableCell><Box sx={{ display: "flex", alignItems: "center", gap: 1 }}><BusinessIcon fontSize="small" color="secondary" /><Typography variant="body2">{dep.ou}</Typography></Box></TableCell>
              <TableCell><Typography variant="caption" color="text.secondary">{dep.description || "\u2014"}</Typography></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {visibleDepartments.length === 0 && departments.length > 0 && (
        <Box sx={{ p: 2, textAlign: "center" }}><Typography variant="body2" color="text.secondary">Все папки скрыты. Измените настройку отображения папок.</Typography></Box>
      )}
    </TableContainer>
  );

  const rootView = (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
        <Typography variant="h6" sx={{ flex: 1 }}>Папки документов</Typography>
        <ToggleButtonGroup value={rootViewMode} exclusive size="small" onChange={(_, v) => { if (v) { setRootViewMode(v); localStorage.setItem("docs_root_view", v); } }}>
          <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
          <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
        </ToggleButtonGroup>
        <Button size="small" startIcon={<VisibilityIcon />} onClick={() => { setDraftHidden([...hiddenFolders]); setSettingsOpen(true); }}>Настройка папок</Button>
      </Box>
      {rootViewMode === "list" ? rootListView : rootTilesView}
    </Box>
  );

  const ragCats = [...new Set(ragSettings.map((s) => s.category || "general"))].sort();
  const hasRagChanges = ragSettings.some((s) => (ragValues[s.key] ?? "") !== (s.value ?? ""));

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2, flexWrap: "wrap" }}>
        <Typography variant="h5" fontWeight={700} sx={{ flex: 1 }}>
          {currentFolder !== null ? `База знаний — ${folderLabel}` : "База знаний"}
        </Typography>
        {currentFolder !== null && (
          <>
            <ToggleButtonGroup value={viewMode} exclusive size="small" onChange={(_, v) => { if (v) { setViewMode(v); localStorage.setItem("docs_view", v); } }}>
              <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
              <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
            </ToggleButtonGroup>
            <Button startIcon={<UploadIcon />} variant="contained" size="small"
              onClick={() => { setUploadFiles([]); setUploadFolder(currentFolder === "" ? "" : currentFolder!); setUploadError(null); setUploadResults(null); setUploadOpen(true); }}>
              Загрузить
            </Button>
            <Button startIcon={<CreateNewFolderIcon />} variant="outlined" size="small"
              onClick={() => { setMkdirName(""); setMkdirOpen(true); }}>
              + Папка
            </Button>
            <Tooltip title="Переиндексировать все документы"><Button startIcon={<AutorenewIcon />} variant="outlined" size="small" disabled={batchReindexing !== null} onClick={() => handleBatchReindex("reindex-all")}>{batchReindexing === "reindex-all" ? "..." : "Всё"}</Button></Tooltip>
            <Tooltip title="Индексировать новые документы"><Button startIcon={<PlayArrowIcon />} variant="outlined" size="small" disabled={batchReindexing !== null} onClick={() => handleBatchReindex("reindex-new")}>{batchReindexing === "reindex-new" ? "..." : "Новые"}</Button></Tooltip>
            <Tooltip title="Переиндексировать упавшие"><Button startIcon={<ErrorIcon />} variant="outlined" size="small" color="warning" disabled={batchReindexing !== null} onClick={() => handleBatchReindex("reindex-new?only_failed=true")}>{batchReindexing === "reindex-new?only_failed=true" ? "..." : "Упавшие"}</Button></Tooltip>
            <IconButton onClick={() => loadDocuments(currentFolder!)} title="Обновить"><RefreshIcon /></IconButton>
          </>
        )}
      </Box>

      {currentFolder !== null && (
        <Breadcrumbs sx={{ mb: 2 }}>
          <Link underline="hover" color="inherit" sx={{ cursor: "pointer" }} onClick={handleBack}>База знаний</Link>
          <Typography color="text.primary">{folderLabel}</Typography>
        </Breadcrumbs>
      )}

      {batchResult && (
        <Alert severity={batchResult.includes("Ошибка") ? "error" : "success"} sx={{ mb: 2 }} onClose={() => setBatchResult(null)}>{batchResult}</Alert>
      )}

      {currentFolder === null ? rootView : (
        loading ? <LinearProgress /> : error ? (
          <Typography variant="body2" color="error" sx={{ textAlign: "center", py: 4 }}>{error}</Typography>
        ) : documents.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 4 }}>В этой папке нет документов</Typography>
        ) : (<>{viewMode === "list" ? listView : tilesView}{documents.length > 0 && (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 2, mt: 2, pt: 2 }}>
            <Button size="small" disabled={page === 0} onClick={() => loadDocuments(currentFolder!, page - 1)}>Назад</Button>
            <Typography variant="body2">Страница {page + 1}</Typography>
            <Button size="small" disabled={!hasMore} onClick={() => loadDocuments(currentFolder!, page + 1)}>Вперёд</Button>
          </Box>
        )}</>)
      )}

      <Box sx={{ mt: 4, borderTop: "1px solid", borderColor: "divider", pt: 2 }}>
        <Button startIcon={<SettingsIcon />} onClick={() => setShowSettings(!showSettings)} sx={{ mb: 2 }}>
          {showSettings ? "Скрыть настройки" : "Настройки базы знаний"}
        </Button>

        {showSettings && (
          <Box>
            {ragLoading ? <CircularProgress /> : (
              <Box sx={{ maxWidth: 600 }}>
                {ragCats.map((cat) => (
                  <Box key={cat} sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" color="primary" sx={{ mb: 1.5, textTransform: "capitalize" }}>{CAT_LABELS[cat] || cat}</Typography>
                    {ragSettings.filter((s) => (s.category || "general") === cat).map((s) => (
                      <SettingField key={s.key} def={s} value={ragValues[s.key] ?? ""} onChange={(k, v) => setRagValues((p) => ({ ...p, [k]: v }))} />
                    ))}
                  </Box>
                ))}
                <Button variant="contained" onClick={handleSaveRag} disabled={!hasRagChanges || savingRag} sx={{ mr: 1 }}>
                  {savingRag ? <CircularProgress size={20} /> : "Сохранить настройки"}
                </Button>
                <Button variant="outlined" onClick={() => { const v: Record<string, string> = {}; for (const s of ragSettings) v[s.key] = s.value ?? ""; setRagValues(v); }} disabled={!hasRagChanges}>
                  Сбросить
                </Button>
              </Box>
            )}

            <Box sx={{ mt: 3, pt: 3, borderTop: "1px solid", borderColor: "divider" }}>
              <Typography variant="subtitle1" fontWeight={600} mb={2}>Управление индексацией</Typography>
              <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
                <Button variant="contained" startIcon={<AutorenewIcon />} disabled={reindexRunning !== null} onClick={() => handleReindexAction("reindex-all")}>
                  {reindexRunning === "reindex-all" ? <CircularProgress size={18} /> : "Переиндексировать всё"}
                </Button>
                <Button variant="outlined" startIcon={<PlayArrowIcon />} disabled={reindexRunning !== null} onClick={() => handleReindexAction("reindex-new")}>
                  {reindexRunning === "reindex-new" ? <CircularProgress size={18} /> : "Индексировать новые"}
                </Button>
                <Button variant="outlined" color="warning" startIcon={<ErrorIcon />} disabled={reindexRunning !== null} onClick={() => handleReindexAction("reindex-new?only_failed=true")}>
                  {reindexRunning === "reindex-new?only_failed=true" ? <CircularProgress size={18} /> : "Переиндексировать упавшие"}
                </Button>
              </Box>
              {reindexResult && (
                <Alert severity={reindexResult.success ? "success" : "error"} sx={{ maxWidth: 600 }}>{reindexResult.msg}</Alert>
              )}
            </Box>
          </Box>
        )}
      </Box>

      <Dialog open={chunksOpen} onClose={() => setChunksOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Чанки: {chunksDoc?.title || chunksDoc?.filename || ""}</DialogTitle>
        <DialogContent>
          {chunksLoading ? <LinearProgress /> : chunks.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: "center" }}>Чанки не найдены. Документ ещё не проиндексирован.</Typography>
          ) : (
            <List disablePadding>
              {chunks.map((chunk: any, idx: number) => (
                <ListItem key={chunk.id || idx} divider sx={{ flexDirection: "column", alignItems: "flex-start", py: 1.5 }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                    <Chip label={`#${chunk.chunk_index + 1}`} size="small" color="primary" />
                    {chunk.meta?.total_chunks && <Typography variant="caption" color="text.secondary">из {chunk.meta.total_chunks}</Typography>}
                  </Box>
                  <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word", fontSize: 13 }}>
                    {chunk.content.length > 500 ? chunk.content.slice(0, 500) + "..." : chunk.content}
                  </Typography>
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions><Button onClick={() => setChunksOpen(false)}>Закрыть</Button></DialogActions>
      </Dialog>

      <Dialog open={uploadOpen} onClose={() => !uploading && setUploadOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Загрузка документов {currentFolder !== null ? `в ${folderLabel}` : ""}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
            <Button variant="outlined" component="label">
              {uploadFiles.length > 0 ? `Выбрано файлов: ${uploadFiles.length}` : "Выберите файлы"}
              <input type="file" multiple hidden accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg" onChange={(e) => { const files = e.target.files; if (files) setUploadFiles(Array.from(files)); }} />
            </Button>
            {uploadFiles.length > 0 && (
              <Box sx={{ maxHeight: 200, overflowY: "auto", border: "1px solid", borderColor: "divider", borderRadius: 1, p: 1 }}>
                {uploadFiles.map((f, i) => (<Typography key={i} variant="caption" display="block" noWrap>{f.name}</Typography>))}
              </Box>
            )}
            <FormControl size="small" fullWidth>
              <InputLabel>Отдел</InputLabel>
              <Select value={uploadFolder} label="Отдел" onChange={(e) => setUploadFolder(e.target.value)}>
                <MenuItem value=""><em>Общий доступ</em></MenuItem>
                {departments.map((dep) => (<MenuItem key={dep.dn} value={dep.ou}>{dep.ou}</MenuItem>))}
              </Select>
            </FormControl>
            {uploadResults && (
              <Box sx={{ maxHeight: 200, overflowY: "auto", border: "1px solid", borderColor: "divider", borderRadius: 1, p: 1 }}>
                {uploadResults.map((r, i) => (<Box key={i} sx={{ display: "flex", alignItems: "center", gap: 1 }}><Typography variant="caption" noWrap sx={{ flex: 1 }}>{r.filename}</Typography><Typography variant="caption" color={r.success ? "success.main" : "error.main"}>{r.success ? "OK" : r.error || "Ошибка"}</Typography></Box>))}
              </Box>
            )}
            {uploadError && <Typography variant="caption" color="error">{uploadError}</Typography>}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setUploadOpen(false); setUploadFiles([]); setUploadResults(null); }} disabled={uploading}>Отмена</Button>
          <Button variant="contained" onClick={handleUpload} disabled={uploadFiles.length === 0 || uploading}>
            {uploading ? `Загрузка (${uploadFiles.length})...` : "Загрузить"}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={mkdirOpen} onClose={() => setMkdirOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Создать папку</DialogTitle>
        <DialogContent>
          <MuiTextField
            autoFocus label="Имя папки" fullWidth value={mkdirName}
            onChange={(e) => setMkdirName(e.target.value)}
            helperText={currentFolder === "" ? "В общем доступе" : `Внутри ${currentFolder}`}
            sx={{ mt: 1 }}
            onKeyDown={(e) => { if (e.key === "Enter" && mkdirName.trim()) handleMkdir(); }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMkdirOpen(false)}>Отмена</Button>
          <Button variant="contained" onClick={handleMkdir} disabled={!mkdirName.trim()}>Создать</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Настройка отображения папок</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>Отметьте папки, которые нужно скрыть из списка:</Typography>
          <FormGroup>
            {departments.map((dep) => (
              <FormControlLabel key={dep.dn} control={<Checkbox checked={!draftHidden.includes(dep.ou)} onChange={(e) => { if (e.target.checked) setDraftHidden(draftHidden.filter((f) => f !== dep.ou)); else setDraftHidden([...draftHidden, dep.ou]); }} />} label={dep.ou} />
            ))}
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Отмена</Button>
          <Button variant="contained" onClick={() => { saveHiddenFolders(draftHidden); setSettingsOpen(false); }}>Сохранить</Button>
        </DialogActions>
      </Dialog>

      {snack && (
        <Snackbar open autoHideDuration={3000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
          <Alert severity={snack.sev} onClose={() => setSnack(null)}>{snack.msg}</Alert>
        </Snackbar>
      )}
    </Box>
  );
};
