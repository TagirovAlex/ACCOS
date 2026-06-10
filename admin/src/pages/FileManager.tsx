import { useEffect, useState } from "react";
import { useRedirect } from "react-admin";
import {
  Box, Typography, List, ListItem, ListItemButton, ListItemIcon, ListItemText,
  Breadcrumbs, Link, LinearProgress, IconButton, Chip, Button, Card, CardContent,
  Dialog, DialogContent, DialogActions, ToggleButtonGroup, ToggleButton, Grid as MuiGrid,
} from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import ImageIcon from "@mui/icons-material/Image";
import RefreshIcon from "@mui/icons-material/Refresh";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import CloseIcon from "@mui/icons-material/Close";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";

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

const SYSTEM_DIRS = new Set(["css", "js", "templates", "images", "generated"]);

const CHIP_DIRS = [
  { label: "generations/", path: "generations" },
  { label: "uploads/", path: "uploads" },
  { label: "edits/", path: "edits" },
  { label: "videos/", path: "videos" },
  { label: "avatars/", path: "avatars" },
  { label: "knowledge/", path: "knowledge" },
];

function formatSize(bytes: number): string {
  if (bytes === 0) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
  return `${size.toFixed(1)} ${units[i]}`;
}

function formatDate(mtime: number | string): string {
  if (!mtime) return "—";
  return new Date(Number(mtime) * 1000).toLocaleString();
}

export const FileManager = () => {
  const redirect = useRedirect();
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [currentPath, setCurrentPath] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"list" | "tiles">(() => (localStorage.getItem("files_view") as "list" | "tiles") ?? "tiles");
  const [previewEntry, setPreviewEntry] = useState<FileEntry | null>(null);

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
        }
        setEntries(filtered);
        setCurrentPath(data.current_path || "");
      } else {
        setError(data.error || "Не удалось загрузить папку");
      }
    } catch (e) {
      setError("Ошибка загрузки: папка не найдена");
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
    if (!window.confirm(`Удалить ${entry.is_dir ? "папку" : "файл"} "${entry.name}"?`)) return;
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

  const ext = (name: string) => name.includes(".") ? "." + name.split(".").pop()?.toLowerCase() : "";
  const isImage = (name: string) => IMAGE_EXTS.has(ext(name));

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Button startIcon={<ArrowBackIcon />} size="small" onClick={() => redirect("dashboard")}>
          Дашборд
        </Button>
        <Typography variant="h5" fontWeight={700} sx={{ flex: 1 }}>
          Файловый менеджер
        </Typography>
        <ToggleButtonGroup value={viewMode} exclusive size="small"
          onChange={(_, v) => { if (v) { setViewMode(v); localStorage.setItem("files_view", v); } }}>
          <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
          <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
        </ToggleButtonGroup>
        <IconButton onClick={() => load(currentPath)} title="Обновить">
          <RefreshIcon />
        </IconButton>
      </Box>

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
        {CHIP_DIRS.map(d => (
          <Chip key={d.path} label={d.label} size="small" variant="outlined" onClick={() => load(d.path)} />
        ))}
      </Box>

      {loading ? <LinearProgress /> : error ? (
        <Typography variant="body2" color="error" sx={{ textAlign: "center", py: 4 }}>
          {error}
        </Typography>
      ) : entries.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 4 }}>
          Папка пуста
        </Typography>
      ) : viewMode === "list" ? (
          <List disablePadding>
            {currentPath && (
              <ListItem disablePadding>
                <ListItemButton onClick={() => { const parent = parts.slice(0, -1).join("/"); load(parent); }}>
                  <ListItemIcon><ArrowBackIcon /></ListItemIcon>
                  <ListItemText primary=".." />
                </ListItemButton>
              </ListItem>
            )}
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
                      <ListItemText primary={entry.name} secondary={isImg ? "Изображение" : "Файл"} />
                    </ListItemButton>
                  )}
                </ListItem>
              );
            })}
          </List>
        ) : (
          <MuiGrid container spacing={2}>
            {currentPath && (
              <MuiGrid size={{ xs: 6, sm: 4, md: 3, lg: 2 }}>
                <Card sx={{ cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}
                  onClick={() => { const parent = parts.slice(0, -1).join("/"); load(parent); }}>
                  <Box sx={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "action.hover" }}>
                    <ArrowBackIcon sx={{ fontSize: 40, color: "text.disabled" }} />
                  </Box>
                  <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
                    <Typography variant="body2" noWrap textAlign="center">..</Typography>
                  </CardContent>
                </Card>
              </MuiGrid>
            )}
            {entries.map((entry) => {
              const isImg = isImage(entry.name);
              return entry.is_dir ? (
                <MuiGrid key={entry.path} size={{ xs: 6, sm: 4, md: 3, lg: 2 }}>
                  <Card sx={{ cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}
                    onClick={() => navigateDir(entry.path)}>
                    <Box sx={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "action.hover" }}>
                      <FolderIcon sx={{ fontSize: 48, color: "primary.main" }} />
                    </Box>
                    <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
                      <Typography variant="body2" noWrap>{entry.name}/</Typography>
                    </CardContent>
                  </Card>
                </MuiGrid>
              ) : (
                <MuiGrid key={entry.path} size={{ xs: 6, sm: 4, md: 3, lg: 2 }}>
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
                </MuiGrid>
              );
            })}
          </MuiGrid>
        )
      )}

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
    </Box>
  );
};
