import { useEffect, useState } from "react";
import { useRedirect } from "react-admin";
import {
  Box, Typography, List, ListItem, ListItemButton, ListItemIcon, ListItemText,
  Breadcrumbs, Link, LinearProgress, IconButton, Chip, Button, Card, CardContent,
  Dialog, DialogContent, DialogTitle, DialogActions,
 TextField, Select, MenuItem, FormControl, InputLabel,
} from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import ImageIcon from "@mui/icons-material/Image";
import RefreshIcon from "@mui/icons-material/Refresh";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import CloseIcon from "@mui/icons-material/Close";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import UploadIcon from "@mui/icons-material/Upload";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import { CardGrid } from "../components/CardGrid";
import { useView } from "../components/ViewToggle";

interface FileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  modified: number;
}

function adminToken(): string | null {
  return localStorage.getItem("admin_token") || localStorage.getItem("token") || null;
}

const IMAGE_EXTS = new Set([".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"]);

const SYSTEM_DIRS = new Set(["css", "js", "templates", "images", "generated", "knowledge"]);

const CHIP_DIRS = [
  { label: "generations/", path: "generations" },
  { label: "uploads/", path: "uploads" },
  { label: "edits/", path: "edits" },
  { label: "videos/", path: "videos" },
  { label: "avatars/", path: "avatars" },
];

function formatSize(bytes: number): string {
  if (bytes === 0) return "\u2014";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
  return `${size.toFixed(1)} ${units[i]}`;
}

function formatDate(mtime: number | string): string {
  if (!mtime) return "\u2014";
  return new Date(Number(mtime) * 1000).toLocaleString();
}

export const FileManager = () => {
  const redirect = useRedirect();
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [currentPath, setCurrentPath] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { view: viewMode, ViewToggleEl: FileViewToggle } = useView("files_view");
  const [previewEntry, setPreviewEntry] = useState<FileEntry | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploadFolder, setUploadFolder] = useState("");
  const [uploadNewFolder, setUploadNewFolder] = useState(false);
  const [uploadFolderOptions, setUploadFolderOptions] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<{filename:string;success:boolean;error?:string}[] | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [createFolderOpen, setCreateFolderOpen] = useState(false);
  const [createFolderName, setCreateFolderName] = useState("");

  const adminRole = localStorage.getItem("admin_role") || "none";
  const isSuperAdmin = adminRole === "super_admin";

  const VISIBLE_CHIPS = CHIP_DIRS.filter(c => isSuperAdmin || c.path === "avatars");

  const GENERATION_DIRS = new Set(["generations", "uploads", "edits", "videos"]);

  const load = async (dirPath: string) => {
    setLoading(true);
    setError(null);
    try {
      const token = adminToken();
      const q = dirPath ? `?path=${encodeURIComponent(dirPath)}` : "";
      const res = await fetch(`/api/v1/admin/files${q}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.success) {
        let filtered = data.entries || [];
        if (!dirPath) {
          filtered = filtered.filter((e: FileEntry) => e.is_dir && !SYSTEM_DIRS.has(e.name));
          if (!isSuperAdmin) {
            filtered = filtered.filter((e: FileEntry) => !GENERATION_DIRS.has(e.name));
          }
        }
        setEntries(filtered);
        setCurrentPath(data.current_path || "");
      } else {
        setError(data.error || "\u041D\u0435 \u0443\u0434\u0430\u043B\u043E\u0441\u044C \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044C \u043F\u0430\u043F\u043A\u0443");
      }
    } catch (e) {
      setError("\u041E\u0448\u0438\u0431\u043A\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043A\u0438: \u043F\u0430\u043F\u043A\u0430 \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D\u0430");
    }
    setLoading(false);
  };

  useEffect(() => { load(""); }, []);

  const parts = currentPath ? currentPath.split("/") : [];

  const navigateDir = (dirPath: string) => load(dirPath);

  const handleDownload = async (entry: FileEntry) => {
    try {
      const token = adminToken();
      const res = await fetch(`/api/v1/admin/files/download?path=${encodeURIComponent(entry.path)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = entry.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch { /* ignore */ }
  };

  const imgUrl = (entry: FileEntry) => `/static/${entry.path}`;

  const handleDelete = async (entry: FileEntry) => {
    if (!window.confirm(`\u0423\u0434\u0430\u043B\u0438\u0442\u044C ${entry.is_dir ? "\u043F\u0430\u043F\u043A\u0443" : "\u0444\u0430\u0439\u043B"} "${entry.name}"?`)) return;
    try {
      const token = adminToken();
      const res = await fetch(`/api/v1/admin/files?path=${encodeURIComponent(entry.path)}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.success) {
        setPreviewEntry(null);
        load(currentPath);
      }
    } catch { /* ignore */ }
  };

  const ext = (name: string) => (name.includes(".") ? "." + name.split(".").pop()?.toLowerCase() : "");
  const isImage = (name: string) => IMAGE_EXTS.has(ext(name));

  const parentDir = () => { const p = parts.slice(0, -1).join("/"); load(p); };

  const listView = (
    <List disablePadding>
      {currentPath ? (
        <ListItem disablePadding>
          <ListItemButton onClick={parentDir}>
            <ListItemIcon><ArrowBackIcon /></ListItemIcon>
            <ListItemText primary=".." />
          </ListItemButton>
        </ListItem>
      ) : null}
      {entries.map((entry) => {
        const isImg = isImage(entry.name);
        return (
          <ListItem key={entry.path} disablePadding secondaryAction={
            <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
              <Typography variant="caption" color="text.secondary">{formatDate(entry.modified)}</Typography>
              <Typography variant="caption" color="text.secondary">{formatSize(entry.size)}</Typography>
            </Box>
          }>
            {entry.is_dir ? (
              <ListItemButton onClick={() => navigateDir(entry.path)}>
                <ListItemIcon><FolderIcon color="primary" /></ListItemIcon>
                <ListItemText primary={entry.name + "/"} />
              </ListItemButton>
            ) : (
              <ListItemButton onClick={isImg ? () => setPreviewEntry(entry) : () => handleDownload(entry)}>
                <ListItemIcon>{isImg ? <ImageIcon color="success" /> : <InsertDriveFileIcon />}</ListItemIcon>
                <ListItemText primary={entry.name} secondary={isImg ? "\u0418\u0437\u043E\u0431\u0440\u0430\u0436\u0435\u043D\u0438\u0435" : "\u0424\u0430\u0439\u043B"} />
              </ListItemButton>
            )}
          </ListItem>
        );
      })}
    </List>
  );

  const tilesView = (
    <CardGrid>
      {currentPath ? (
        <Box>
          <Card sx={{ cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}
            onClick={parentDir}>
            <Box sx={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "action.hover" }}>
              <ArrowBackIcon sx={{ fontSize: 40, color: "text.disabled" }} />
            </Box>
            <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
              <Typography variant="body2" noWrap textAlign="center">..</Typography>
            </CardContent>
          </Card>
          </Box>
          ) : null}
          {entries.map((entry) => {
          const isImg = isImage(entry.name);
          if (entry.is_dir) {
          return (
          <Box key={entry.path}>
          <Card sx={{ cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}
          onClick={() => navigateDir(entry.path)}>
          <Box sx={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "action.hover" }}>
          <FolderIcon sx={{ fontSize: 48, color: "primary.main" }} />
          </Box>
          <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
          <Typography variant="body2" noWrap>{entry.name}/</Typography>
          </CardContent>
          </Card>
          </Box>
          );
          }
          return (
          <Box key={entry.path}>
          <Card sx={{ cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}
          onClick={isImg ? () => setPreviewEntry(entry) : () => handleDownload(entry)}>
          <Box sx={{ height: 120, overflow: "hidden", bgcolor: "#1a1a1a", display: "flex", alignItems: "center", justifyContent: "center" }}>
          {isImg ? (
          <img src={imgUrl(entry)} alt={entry.name}
          style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain", display: "block" }}
          onError={(e: any) => { e.target.style.display = "none"; }} />
          ) : (
          <InsertDriveFileIcon sx={{ fontSize: 40, color: "text.disabled" }} />
          )}
          </Box>
          <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
          <Typography variant="body2" noWrap>{entry.name}</Typography>
          <Typography variant="caption" color="text.secondary">{formatSize(entry.size)}</Typography>
          </CardContent>
          </Card>
          </Box>
          );
          })}
          </CardGrid>
  );

  const canUpload = currentPath === "knowledge" || currentPath.startsWith("knowledge/");
  const currentFolder = currentPath.startsWith("knowledge/") ? currentPath.slice("knowledge/".length) : "";

  const fetchExistingFolders = async () => {
    try {
      const token = adminToken();
      const res = await fetch("/api/v1/admin/files?path=knowledge", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.success) {
        setUploadFolderOptions(
          (data.entries || []).filter((e: FileEntry) => e.is_dir).map((e: FileEntry) => e.name)
        );
      }
    } catch {}
  };

  const handleUpload = async () => {
    if (!uploadFiles.length) return;
    setUploading(true);
    setUploadError(null);
    setUploadResults(null);
    try {
      const token = adminToken();
      const form = new FormData();
      for (const f of uploadFiles) form.append("files", f);
      const targetFolder = uploadFolder
        ? (currentFolder ? `${currentFolder}/${uploadFolder}` : uploadFolder)
        : currentFolder;
      form.append("folder", targetFolder);
      const res = await fetch("/api/v1/knowledge/upload-batch", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      const data = await res.json();
      if (data.success) {
        setUploadResults(data.results || []);
      } else {
        setUploadError(data.error || data.detail || "Ошибка загрузки");
      }
    } catch (e) {
      setUploadError("Ошибка сети: " + (e instanceof Error ? e.message : String(e)));
    }
    setUploading(false);
  };

  const bodyContent = loading ? <LinearProgress /> : error ? (
    <Typography variant="body2" color="error" sx={{ textAlign: "center", py: 4 }}>{error}</Typography>
  ) : entries.length === 0 ? (
    <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 4 }}>Папка пуста</Typography>
  ) : viewMode === "list" ? listView : tilesView;

  return (
    <><Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Button startIcon={<ArrowBackIcon />} size="small" onClick={() => redirect("/")}>
          Дашборд
        </Button>
        <Typography variant="h5" fontWeight={700} sx={{ flex: 1 }}>
          Файловый менеджер
        </Typography>
        {FileViewToggle}
        {canUpload && (<>
          <Button startIcon={<CreateNewFolderIcon />} variant="outlined" size="small"
            onClick={() => { setCreateFolderOpen(true); setCreateFolderName(""); }}>
            + Папка
          </Button>
          <Button startIcon={<UploadIcon />} variant="contained" size="small"
            onClick={() => { setUploadFiles([]); setUploadFolder(""); setUploadNewFolder(false); setUploadResults(null);
              fetchExistingFolders(); setUploadOpen(true); }}>
            Загрузить
          </Button>
        </>)}
        <IconButton onClick={() => load(currentPath)} title="Обновить">
          <RefreshIcon />
        </IconButton>
      </Box>

      <Dialog open={createFolderOpen} onClose={() => setCreateFolderOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Новая папка</DialogTitle>
        <DialogContent>
          <TextField autoFocus fullWidth size="small" label="Имя папки" value={createFolderName}
            onChange={(e) => setCreateFolderName(e.target.value)}
            onKeyDown={async (e) => {
              if (e.key === "Enter" && createFolderName.trim()) {
                const token = adminToken();
                try {
                  const f = new FormData();
                  f.append("path", currentPath);
                  f.append("name", createFolderName.trim());
                  await fetch("/api/v1/admin/files/mkdir", { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: f });
                  setCreateFolderOpen(false);
                  load(currentPath);
                } catch (e) {}
              }
            }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateFolderOpen(false)}>Отмена</Button>
          <Button variant="contained" disabled={!createFolderName.trim()}
            onClick={async () => {
              const token = adminToken();
              try {
                const f = new FormData();
                f.append("path", currentPath);
                f.append("name", createFolderName.trim());
                await fetch("/api/v1/admin/files/mkdir", { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: f });
                setCreateFolderOpen(false);
                load(currentPath);
              } catch (e) {}
            }}>
            Создать
          </Button>
        </DialogActions>
      </Dialog>

      <Breadcrumbs sx={{ mb: 2 }}>
        <Link underline="hover" color="inherit" sx={{ cursor: "pointer" }} onClick={() => load("")}>
          static/
        </Link>
        {parts.map((part, i) => {
          const pathSoFar = parts.slice(0, i + 1).join("/");
          const isLast = i === parts.length - 1;
          return isLast ? (
            <Typography key={pathSoFar} color="text.primary">{part}/</Typography>
          ) : (
            <Link key={pathSoFar} underline="hover" color="inherit" sx={{ cursor: "pointer" }} onClick={() => load(pathSoFar)}>
              {part}/
            </Link>
          );
        })}
      </Breadcrumbs>

      <Box sx={{ display: "flex", gap: 1, mb: 2, flexWrap: "wrap" }}>
        {VISIBLE_CHIPS.map(d => (
          <Chip key={d.path} label={d.label} size="small" variant="outlined" onClick={() => load(d.path)} />
        ))}
      </Box>

      {bodyContent}

      <Dialog open={!!previewEntry} onClose={() => setPreviewEntry(null)} maxWidth="lg" fullWidth>
        <DialogContent sx={{ p: 1, position: "relative" }}>
          <IconButton onClick={() => setPreviewEntry(null)}
            sx={{ position: "absolute", top: 4, right: 4, bgcolor: "rgba(0,0,0,0.5)", color: "white", "&:hover": { bgcolor: "rgba(0,0,0,0.7)" } }}>
            <CloseIcon />
          </IconButton>
          {previewEntry && (
            <img src={imgUrl(previewEntry)} alt=""
              style={{ width: "100%", height: "auto", maxHeight: "90vh", objectFit: "contain", display: "block" }} />
          )}
        </DialogContent>
        {previewEntry && (
          <DialogActions>
            <Button startIcon={<DownloadIcon />} onClick={() => { handleDownload(previewEntry); setPreviewEntry(null); }}>
              Скачать
            </Button>
            <Button startIcon={<DeleteIcon />} color="error" onClick={() => handleDelete(previewEntry)}>
              Удалить
            </Button>
          </DialogActions>
        )}
      </Dialog>

      <Dialog open={uploadOpen} onClose={() => { if (!uploading) { setUploadOpen(false); if (uploadResults) load("knowledge"); } }} maxWidth="sm" fullWidth>
        <DialogTitle>{uploadResults ? "Результаты загрузки" : "Загрузка документов"}</DialogTitle>
        <DialogContent>
          {uploadResults ? (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1, pt: 1 }}>
              {uploadResults.map((r, i) => (
                <Box key={i} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Typography variant="body2" sx={{ flex: 1 }}>{r.filename}</Typography>
                  <Chip size="small" label={r.success ? "OK" : "Ошибка"}
                    color={r.success ? "success" : "error"} />
                  {r.error && <Typography variant="caption" color="error">{r.error}</Typography>}
                </Box>
              ))}
            </Box>
          ) : (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
            <Button variant="outlined" component="label">
              {uploadFiles.length ? `Выбрано файлов: ${uploadFiles.length}` : "Выберите файлы"}
              <input type="file" hidden multiple accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
                onChange={(e) => setUploadFiles(Array.from(e.target.files || []))} />
            </Button>
            {uploadFiles.length > 0 && (
              <Box sx={{ maxHeight: 200, overflow: "auto" }}>
                {uploadFiles.map((f, i) => (
                  <Typography key={i} variant="caption" display="block">{f.name}</Typography>
                ))}
              </Box>
            )}
            <FormControl size="small" fullWidth>
              <InputLabel>Отдел</InputLabel>
              <Select value={uploadNewFolder ? "__new__" : uploadFolder}
                label="Отдел"
                onChange={(e) => {
                  if (e.target.value === "__new__") {
                    setUploadNewFolder(true);
                    setUploadFolder("");
                  } else {
                    setUploadNewFolder(false);
                    setUploadFolder(e.target.value);
                  }
                }}>
                <MenuItem value=""><em>Текущая папка ({currentFolder || "Общий доступ"})</em></MenuItem>
                {uploadFolderOptions.map((f) => (
                  <MenuItem key={f} value={f}>{f}</MenuItem>
                ))}
                <MenuItem value="__new__">+ Новая папка</MenuItem>
              </Select>
            </FormControl>
            {uploadNewFolder && (
              <TextField label="Название новой папки" size="small" value={uploadFolder}
                onChange={(e) => setUploadFolder(e.target.value)} />
            )}
            {uploadError && (
              <Typography variant="caption" color="error">{uploadError}</Typography>
            )}
          </Box>
          )}
        </DialogContent>
        <DialogActions>
          {uploadResults ? (
            <Button onClick={() => { setUploadOpen(false); load("knowledge"); }} variant="contained">Готово</Button>
          ) : (
            <>
              <Button onClick={() => setUploadOpen(false)} disabled={uploading}>Отмена</Button>
              <Button variant="contained" onClick={handleUpload} disabled={!uploadFiles.length || uploading}>
                {uploading ? "Загрузка..." : `Загрузить (${uploadFiles.length})`}
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
 </> );
};
