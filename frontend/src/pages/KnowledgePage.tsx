import { useState, useEffect, useCallback } from "react";
import {
  Box, Typography, TextField, Button, List, ListItem, ListItemText,
  ListItemIcon, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  LinearProgress, Select, MenuItem, FormControl, InputLabel,
  IconButton, InputAdornment, Breadcrumbs, Link, Snackbar, Alert,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import UploadIcon from "@mui/icons-material/Upload";
import DownloadIcon from "@mui/icons-material/Download";
import DescriptionIcon from "@mui/icons-material/Description";
import FolderIcon from "@mui/icons-material/Folder";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { api } from "../services/api";

const LIMIT = 50;

interface DocItem {
  id: string; title: string; filename: string; content_type: string;
  folder: string; file_path: string; ad_group_dn: string | null;
  status: string; created_at: string;
}

interface Department { dn: string; ou: string; description: string; }

export const KnowledgePage = () => {
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [folder, setFolder] = useState("");
  const [folders, setFolders] = useState<string[]>([]);
  const [openUpload, setOpenUpload] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [uploadFolder, setUploadFolder] = useState("");
  const [departments, setDepartments] = useState<Department[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<{filename:string;success:boolean;error?:string}[] | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [openMkdir, setOpenMkdir] = useState(false);
  const [mkdirName, setMkdirName] = useState("");
  const [mkdirDept, setMkdirDept] = useState("");
  const [snack, setSnack] = useState<{msg:string;severity:"success"|"error"}|null>(null);

  const doLoadDocs = useCallback(async (f: string, p: number) => {
    setLoading(true);
    try {
      let url = `/knowledge/documents?limit=${LIMIT}&skip=${p * LIMIT}`;
      if (f) url += `&folder=${encodeURIComponent(f)}`;
      const data: any = await api("GET", url);
      const items = Array.isArray(data) ? data : [];
      setDocs(items);
      setHasMore(items.length >= LIMIT);
    } catch { setDocs([]); }
    setLoading(false);
  }, []);

  const doLoadFolders = useCallback(async () => {
    try {
      const data: any = await api("GET", "/knowledge/folders");
      setFolders(data.folders || []);
    } catch { setFolders([]); }
  }, []);

  const [hiddenFolders, setHiddenFolders] = useState<string[]>([]);
  const doLoadDepts = useCallback(async () => {
    try {
      const data: any = await api("GET", "/knowledge/departments");
      setDepartments(data.departments || []);
      setHiddenFolders(data.hidden_folders || []);
    } catch { setDepartments([]); }
  }, []);

  useEffect(() => {
    setPage(0);
    doLoadDocs(folder, 0);
    doLoadFolders();
  }, [folder, doLoadDocs, doLoadFolders]);

  const goPage = (p: number) => {
    setPage(p);
    doLoadDocs(folder, p);
  };

  const visibleDepts = departments.filter(d => !hiddenFolders.includes(d.ou));
  const parts = folder ? folder.split("/") : [];
  const topFolders = [...new Set(folders.map(f => f.split("/")[0]))];
  const subFolders = folder ? folders.filter(f => f.startsWith(folder + "/")).map(f => f.slice(folder.length + 1)) : [];
  const filtered = search
    ? docs.filter(d => d.title.toLowerCase().includes(search.toLowerCase()) || (d.folder || "").toLowerCase().includes(search.toLowerCase()))
    : docs;

  const handleMkdir = async () => {
    let target = "";
    if (folder) {
      if (!mkdirName.trim()) return;
      target = folder + "/" + mkdirName.trim();
    } else {
      target = mkdirDept;
      if (!target) return;
    }
    try {
      const res: any = await api("POST", "/knowledge/folders/mkdir", { folder: target });
      if (res.success) {
        setSnack({ msg: "Папка создана", severity: "success" });
        setOpenMkdir(false);
        setMkdirName("");
        setMkdirDept("");
        doLoadFolders();
      } else {
        setSnack({ msg: res.error || "Ошибка", severity: "error" });
      }
    } catch {
      setSnack({ msg: "Ошибка создания папки", severity: "error" });
    }
  };

  const handleUploadOpen = () => {
    doLoadDepts();
    setFiles([]);
    setUploadFolder("");
    setResults(null);
    setOpenUpload(true);
  };

  const handleUpload = async () => {
    if (!files.length) return;
    setUploading(true);
    setResults(null);
    try {
      const fd = new FormData();
      for (const f of files) fd.append("files", f);
      const target = uploadFolder || folder;
      fd.append("folder", target);
      if (uploadFolder) {
        const dept = departments.find(d => d.ou === uploadFolder);
        if (dept) fd.append("ad_group_dn", dept.dn);
      }
      const token = localStorage.getItem("token");
      const res = await fetch("/api/v1/knowledge/upload-batch", {
        method: "POST",
        headers: token ? { Authorization: "Bearer " + token } : {},
        body: fd,
      });
      const data = await res.json();
      if (data.success && data.results) {
        setResults(data.results);
        if (data.results.every((r: any) => r.success)) {
          setOpenUpload(false);
          doLoadDocs(folder, page);
          doLoadFolders();
        }
      }
    } catch {}
    setUploading(false);
  };

  const openMkdirDialog = () => {
    setMkdirName("");
    setMkdirDept("");
    if (!folder) doLoadDepts();
    setOpenMkdir(true);
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2, flexWrap: "wrap" }}>
        <Typography variant="h5" fontWeight={700} sx={{ flex: "1 1 auto", minWidth: 120 }}>База знаний</Typography>
        <TextField size="small" placeholder="Поиск..." value={search}
          onChange={e => setSearch(e.target.value)}
          slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
          sx={{ minWidth: 200 }} />
        <Button size="small" variant="outlined" startIcon={<CreateNewFolderIcon />} onClick={openMkdirDialog}>
          + Папка
        </Button>
        <Button size="small" variant="contained" startIcon={<UploadIcon />} onClick={handleUploadOpen}>
          Загрузить
        </Button>
      </Box>

      <Breadcrumbs sx={{ mb: 2 }}>
        <Link underline="hover" color="inherit" sx={{ cursor: "pointer" }} onClick={() => { setFolder(""); setPage(0); }}>
          Все отделы
        </Link>
        {parts.map((p, i) => {
          const path = parts.slice(0, i + 1).join("/");
          const last = i === parts.length - 1;
          return last
            ? <Typography key={path} color="text.primary">{p}</Typography>
            : <Link key={path} underline="hover" color="inherit" sx={{ cursor: "pointer" }} onClick={() => { setFolder(path); setPage(0); }}>{p}</Link>;
        })}
      </Breadcrumbs>

      <Box sx={{ display: "flex", gap: 1, mb: 2, flexWrap: "wrap" }}>
        {!folder && topFolders.map(f => (
          <Chip key={f} label={f} size="small" variant="outlined" color="primary"
            onClick={() => { setFolder(f); setPage(0); }} icon={<FolderIcon />} />
        ))}
        {folder && subFolders.map(f => (
          <Chip key={f} label={f} size="small" variant="outlined"
            onClick={() => { setFolder(folder + "/" + f); setPage(0); }} icon={<FolderIcon />} />
        ))}
      </Box>

      {loading ? (
        <LinearProgress />
      ) : !filtered.length ? (
        <Typography color="text.secondary" sx={{ textAlign: "center", py: 6 }}>
          {search ? "Ничего не найдено" : "В этой папке нет документов"}
        </Typography>
      ) : (
        <>
          <List disablePadding sx={{ border: 1, borderColor: "divider", borderRadius: 2, overflow: "hidden" }}>
            {filtered.map(doc => (
              <ListItem key={doc.id} divider sx={{ bgcolor: "background.paper" }}>
                <ListItemIcon><DescriptionIcon /></ListItemIcon>
                <ListItemText
                  primary={doc.title}
                  secondary={(doc.folder || "Корневая") + " · " + doc.content_type.toUpperCase() + " · " + new Date(doc.created_at).toLocaleDateString()} />
                <Chip label={doc.status === "ready" ? "Готов" : doc.status === "indexing" ? "Индексация" : doc.status}
                  size="small"
                  color={doc.status === "ready" ? "success" : doc.status === "indexing" ? "warning" : "default"}
                  sx={{ mr: 1 }} />
                <IconButton size="small" href={"/" + doc.file_path} target="_blank" title="Скачать">
                  <DownloadIcon fontSize="small" />
                </IconButton>
              </ListItem>
            ))}
          </List>
          <Box sx={{ display: "flex", justifyContent: "center", gap: 2, mt: 2, alignItems: "center" }}>
            <Button size="small" startIcon={<ChevronLeftIcon />} disabled={page === 0}
              onClick={() => goPage(page - 1)}>Назад</Button>
            <Typography variant="body2" color="text.secondary">Страница {page + 1}</Typography>
            <Button size="small" endIcon={<ChevronRightIcon />} disabled={!hasMore}
              onClick={() => goPage(page + 1)}>Вперед</Button>
          </Box>
        </>
      )}

      <Dialog open={openUpload} onClose={() => !uploading && setOpenUpload(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Загрузка документов</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
            <Button variant="outlined" component="label">
              {files.length ? "Выбрано файлов: " + files.length : "Выбрать файлы"}
              <input type="file" multiple hidden accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
                onChange={e => { if (e.target.files) setFiles(Array.from(e.target.files)); }} />
            </Button>
            {!!files.length && (
              <Box sx={{ maxHeight: 200, overflowY: "auto", border: 1, borderColor: "divider", borderRadius: 1, p: 1 }}>
                {files.map((f, i) => <Typography key={i} variant="caption" display="block" noWrap>{f.name}</Typography>)}
              </Box>
            )}
            <FormControl size="small" fullWidth>
              <InputLabel>Папка</InputLabel>
              <Select value={uploadFolder} label="Папка" onChange={e => setUploadFolder(e.target.value)}>
                <MenuItem value=""><em>Текущая ({folder || "Корневая"})</em></MenuItem>
                {visibleDepts.map(d => <MenuItem key={d.dn} value={d.ou}>{d.ou}</MenuItem>)}
              </Select>
            </FormControl>
            {results && (
              <Box sx={{ maxHeight: 200, overflowY: "auto", border: 1, borderColor: "divider", borderRadius: 1, p: 1 }}>
                {results.map((r, i) => (
                  <Box key={i} sx={{ display: "flex", gap: 1 }}>
                    <Typography variant="caption" noWrap sx={{ flex: 1 }}>{r.filename}</Typography>
                    <Typography variant="caption" color={r.success ? "success.main" : "error.main"}>
                      {r.success ? "OK" : r.error || "Ошибка"}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setOpenUpload(false); setFiles([]); setResults(null); }} disabled={uploading}>Отмена</Button>
          <Button variant="contained" onClick={handleUpload} disabled={!files.length || uploading}>
            {uploading ? "Загрузка (" + files.length + ")..." : "Загрузить"}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openMkdir} onClose={() => setOpenMkdir(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Создать папку</DialogTitle>
        <DialogContent>
          {folder ? (
            <TextField autoFocus fullWidth size="small" label="Имя папки" value={mkdirName}
              onChange={e => setMkdirName(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") handleMkdir(); }}
              sx={{ mt: 1 }}
              helperText={"Будет создана в " + folder} />
          ) : (
            <FormControl fullWidth size="small" sx={{ mt: 1 }}>
              <InputLabel>Выберите отдел</InputLabel>
              <Select value={mkdirDept} label="Выберите отдел" onChange={e => setMkdirDept(e.target.value)}>
                {visibleDepts.map(d => <MenuItem key={d.dn} value={d.ou}>{d.ou}</MenuItem>)}
              </Select>
            </FormControl>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenMkdir(false)}>Отмена</Button>
          <Button variant="contained" onClick={handleMkdir}
            disabled={folder ? !mkdirName.trim() : !mkdirDept}>Создать</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={3000} onClose={() => setSnack(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
        {snack ? <Alert severity={snack.severity} onClose={() => setSnack(null)}>{snack.msg}</Alert> : undefined}
      </Snackbar>
    </Box>
  );
};
