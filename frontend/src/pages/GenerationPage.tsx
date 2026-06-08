import { useState, useRef, useCallback, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Box, Card, CardContent, Typography, TextField, Button, MenuItem, Alert, LinearProgress, Chip, Skeleton, IconButton, ToggleButtonGroup, ToggleButton, Dialog, DialogTitle, DialogContent, DialogActions } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import HistoryIcon from "@mui/icons-material/History";
import RefreshIcon from "@mui/icons-material/Refresh";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
import EditIcon from "@mui/icons-material/Edit";
import VideoFileIcon from "@mui/icons-material/VideoFile";
import LandscapeIcon from "@mui/icons-material/Landscape";
import PortraitIcon from "@mui/icons-material/Portrait";
import CropSquareIcon from "@mui/icons-material/CropSquare";
import TuneIcon from "@mui/icons-material/Tune";
import { api } from "../services/api";

const WORKFLOWS = [
  { value: "z_image", label: "Z-Image (текст → изображение)", needsRefs: false },
  { value: "qwen_edit_1", label: "Qwen Edit (1 референс)", needsRefs: true, maxRefs: 1 },
  { value: "qwen_edit_2", label: "Qwen Edit (2 референса)", needsRefs: true, maxRefs: 2 },
  { value: "qwen_edit_3", label: "Qwen Edit (3 референса)", needsRefs: true, maxRefs: 3 },
];

const RESOLUTION_PRESETS = [
  { label: "512×512", w: 512, h: 512, icon: <CropSquareIcon fontSize="small" /> },
  { label: "768×1024", w: 768, h: 1024, icon: <PortraitIcon fontSize="small" /> },
  { label: "864×1152", w: 864, h: 1152, icon: <PortraitIcon fontSize="small" /> },
  { label: "1024×1024", w: 1024, h: 1024, icon: <CropSquareIcon fontSize="small" /> },
  { label: "1024×768", w: 1024, h: 768, icon: <LandscapeIcon fontSize="small" /> },
  { label: "1152×864", w: 1152, h: 864, icon: <LandscapeIcon fontSize="small" /> },
  { label: "1216×832", w: 1216, h: 832, icon: <LandscapeIcon fontSize="small" /> },
  { label: "1344×768", w: 1344, h: 768, icon: <LandscapeIcon fontSize="small" /> },
];

const CUSTOM = "custom";

interface ImageAsset {
  id: string;
  filename: string;
  file_path: string;
}

interface GenResult {
  generation_id: string;
  cost: number;
  status: string;
  images?: ImageAsset[];
}

interface HistoryItem {
  id: string;
  workflow_type: string;
  prompt: string;
  status: string;
  cost: number;
  created_at: string;
  images: ImageAsset[];
}

export const GenerationPage = ({ viewHistory: forceHistory }: { viewHistory?: boolean }) => {
  const [searchParams] = useSearchParams();
  const [viewHistory, setViewHistory] = useState(forceHistory || searchParams.get("view") === "history");
  const [workflow, setWorkflow] = useState("z_image");
  const [prompt, setPrompt] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenResult | null>(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState("1024×1024");
  const [customWidth, setCustomWidth] = useState(1024);
  const [customHeight, setCustomHeight] = useState(1024);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [selectedHistory, setSelectedHistory] = useState<HistoryItem | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [editPrompt, setEditPrompt] = useState("");
  const [editWorkflow, setEditWorkflow] = useState("qwen_edit_1");
  const [videoPrompt, setVideoPrompt] = useState("");
  const [videoDuration, setVideoDuration] = useState(5);
  const [actionDialog, setActionDialog] = useState<"" | "edit" | "video">("");
  const [actionLoading, setActionLoading] = useState(false);
  const [viewMode, setViewMode] = useState<"list" | "tiles">("tiles");
  const fileRef = useRef<HTMLInputElement>(null);

  const selectedWorkflow = WORKFLOWS.find(w => w.value === workflow);

  const currentResolution = selectedPreset === CUSTOM
    ? { w: customWidth, h: customHeight }
    : RESOLUTION_PRESETS.find(p => p.label === selectedPreset) || { w: 1024, h: 1024 };

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const res: any = await api("GET", "/generate/history");
      setHistory(res.generations || []);
    } catch { /* ignore */ }
    setHistoryLoading(false);
  }, []);

  useEffect(() => {
    loadHistory();
    return () => {
      previewUrls.forEach(u => URL.revokeObjectURL(u));
    };
  }, [loadHistory]);

  const pollStatus = useCallback(async (genId: string) => {
    let attempts = 0;
    const maxAttempts = 150;
    const poll = async (): Promise<any> => {
      if (attempts >= maxAttempts) return { success: false, error: "Timeout" };
      attempts++;
      const res: any = await api("GET", `/generate/${genId}/status`);
      if (res.status === "completed" || res.status === "failed") return res;
      await new Promise(r => setTimeout(r, 2000));
      return poll();
    };
    return poll();
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      let refImages: string[] = [];

      if (selectedWorkflow?.needsRefs && files.length > 0) {
        for (const file of files) {
          const formData = new FormData();
          formData.append("file", file);
          const token = localStorage.getItem("token");
          const headers: Record<string, string> = {};
          if (token) headers["Authorization"] = `Bearer ${token}`;
          const uploadRes = await fetch("/api/v1/generate/upload", { method: "POST", headers, body: formData });
          const uploadJson = await uploadRes.json();
          if (!uploadRes.ok || !uploadJson.success) throw new Error(uploadJson.error || "Upload failed");
          refImages.push(uploadJson.file_path);
        }
      }

      const genRes: any = await api("POST", "/generate/", {
        workflow_type: workflow,
        prompt: prompt.trim(),
        width: currentResolution.w,
        height: currentResolution.h,
        reference_images: refImages,
      });

      if (!genRes.success) {
        setError(genRes.error || "Generation failed");
        setLoading(false);
        return;
      }

      const statusRes = await pollStatus(genRes.generation_id);
      setResult({
        generation_id: genRes.generation_id,
        cost: genRes.cost,
        status: statusRes.status,
        images: statusRes.images || [],
      });

      if (statusRes.status === "failed") {
        setError(statusRes.error_message || "Generation failed");
      }

      loadHistory();
    } catch (err: any) {
      setError(err.message);
    }
    setLoading(false);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const max = selectedWorkflow?.maxRefs || 3;
      const selected = Array.from(e.target.files).slice(0, max);
      setFiles(selected);
      const urls = selected.map(f => URL.createObjectURL(f));
      setPreviewUrls(prev => {
        prev.forEach(u => URL.revokeObjectURL(u));
        return urls;
      });
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    setPreviewUrls(prev => {
      URL.revokeObjectURL(prev[index]);
      return prev.filter((_, i) => i !== index);
    });
  };

  const handleDelete = async (item: HistoryItem) => {
    setDeleting(true);
    try {
      const res: any = await api("DELETE", `/generate/${item.id}`);
      if (res.success) {
        setHistory(prev => prev.filter(h => h.id !== item.id));
        setSelectedHistory(null);
      }
    } catch { /* ignore */ }
    setDeleting(false);
  };

  const handleDownload = (img: ImageAsset) => {
    const a = document.createElement("a");
    a.href = `/${img.file_path}`;
    a.download = img.filename;
    a.click();
  };

  const handleSendToEdit = async () => {
    if (!selectedHistory || !editPrompt.trim() || actionLoading) return;
    setActionLoading(true);
    try {
      const qs = new URLSearchParams({ edit_workflow: editWorkflow, prompt: editPrompt.trim() });
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/v1/orchestrate/image-to-edit/${selectedHistory.id}?${qs}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await res.json();
      if (data.success) {
        setActionDialog("");
        setEditPrompt("");
        setSelectedHistory(null);
        pollStatus(data.generation_id).then(() => loadHistory());
      } else {
        setError(data.error || "Ошибка запуска редактирования");
      }
    } catch (err: any) {
      setError(err.message);
    }
    setActionLoading(false);
  };

  const handleSendToVideo = async () => {
    if (!selectedHistory || !videoPrompt.trim() || actionLoading) return;
    setActionLoading(true);
    try {
      const qs = new URLSearchParams({ prompt: videoPrompt.trim(), duration: String(videoDuration) });
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/v1/orchestrate/image-to-video/${selectedHistory.id}?${qs}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await res.json();
      if (data.success) {
        setActionDialog("");
        setVideoPrompt("");
        setSelectedHistory(null);
        pollStatus(data.generation_id).then(() => loadHistory());
      } else {
        setError(data.error || "Ошибка запуска видео");
      }
    } catch (err: any) {
      setError(err.message);
    }
    setActionLoading(false);
  };

  const statusLabels: Record<string, string> = {
    completed: "Готово",
    processing: "Обработка",
    queued: "В очереди",
    failed: "Ошибка",
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} mb={3}>Генерация</Typography>

      {viewHistory && (
        <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
          <Button size="small" startIcon={<AutoAwesomeIcon />} onClick={() => setViewHistory(false)}>
            Новая генерация
          </Button>
        </Box>
      )}

      <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
        {!viewHistory && (
        <Box sx={{ flex: "1 1 60%", minWidth: 300 }}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                <AutoAwesomeIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>Новая генерация</Typography>
              </Box>
              <TextField select label="Workflow" fullWidth value={workflow} onChange={e => { setWorkflow(e.target.value); setFiles([]); setPreviewUrls([]); }} margin="normal">
                {WORKFLOWS.map(w => <MenuItem key={w.value} value={w.value}>{w.label}</MenuItem>)}
              </TextField>

              <TextField label="Промпт" fullWidth multiline rows={3} value={prompt} onChange={e => setPrompt(e.target.value)} margin="normal" placeholder="Опишите, что хотите получить..." />

              {!workflow.startsWith("qwen_edit") && (
                <>
                  <Typography variant="body2" fontWeight={600} mt={2} mb={1}>Разрешение</Typography>
                  <ToggleButtonGroup
                    value={selectedPreset}
                    exclusive
                    onChange={(_, v) => { if (v !== null) setSelectedPreset(v); }}
                    size="small"
                    sx={{ flexWrap: "wrap", gap: 0.5, mb: selectedPreset === CUSTOM ? 1 : 0 }}
                  >
                    {RESOLUTION_PRESETS.map(p => (
                      <ToggleButton key={p.label} value={p.label} sx={{ px: 1.5, py: 0.5, textTransform: "none" }}>
                        {p.icon} <Box component="span" sx={{ ml: 0.5 }}>{p.label}</Box>
                      </ToggleButton>
                    ))}
                    <ToggleButton value={CUSTOM} sx={{ px: 1.5, py: 0.5, textTransform: "none", gap: 0.5 }}>
                      <TuneIcon fontSize="small" /> Свой
                    </ToggleButton>
                  </ToggleButtonGroup>
                  {selectedPreset === CUSTOM && (
                    <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
                      <TextField label="W" type="number" size="small" value={customWidth} onChange={e => setCustomWidth(Number(e.target.value))} sx={{ width: 100 }} />
                      <TextField label="H" type="number" size="small" value={customHeight} onChange={e => setCustomHeight(Number(e.target.value))} sx={{ width: 100 }} />
                    </Box>
                  )}
                </>
              )}

              {selectedWorkflow?.needsRefs && (
                <Box sx={{ mt: 2, p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
                  <Typography variant="body2" fontWeight={600} mb={1}>Референс-изображения ({files.length}/{selectedWorkflow.maxRefs})</Typography>
                  <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 1 }}>
                    {files.map((f, i) => (
                      <Box key={i} sx={{ position: "relative", borderRadius: 2, overflow: "hidden", border: "1px solid", borderColor: "divider", maxWidth: "100%", flex: "1 1 auto" }}>
                        <img src={previewUrls[i]} alt={f.name}
                          style={{ width: "100%", height: "auto", objectFit: "contain", display: "block", background: "repeating-conic-gradient(rgba(0,0,0,0.03) 0% 25%, transparent 0% 50%) 0px 0px / 20px 20px" }} />
                        <IconButton size="small" onClick={() => removeFile(i)}
                          sx={{ position: "absolute", top: 4, right: 4, bgcolor: "rgba(0,0,0,0.5)", color: "white", "&:hover": { bgcolor: "rgba(0,0,0,0.7)" } }}>
                          <CloseIcon fontSize="small" />
                        </IconButton>
                        <Typography variant="caption" sx={{ position: "absolute", bottom: 0, left: 0, right: 0, bgcolor: "rgba(0,0,0,0.6)", color: "white", px: 1, py: 0.5, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                          {f.name}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                  <Button variant="outlined" size="small" component="label" disabled={files.length >= (selectedWorkflow.maxRefs || 3)}>
                    Выбрать файл
                    <input ref={fileRef} type="file" hidden accept="image/*" multiple={selectedWorkflow.maxRefs !== 1} onChange={handleFileChange} />
                  </Button>
                </Box>
              )}

              <Box sx={{ display: "flex", gap: 2, alignItems: "center", mt: 2 }}>
                <Button variant="contained" onClick={handleGenerate} disabled={loading || !prompt.trim()} startIcon={<AutoAwesomeIcon />}>
                  {loading ? "Генерация..." : "Сгенерировать"}
                </Button>
                <Typography variant="caption" color="text.secondary">
                  {currentResolution.w}×{currentResolution.h}
                </Typography>
              </Box>
              {loading && <LinearProgress sx={{ mt: 2, borderRadius: 1 }} />}
              {error && <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError("")}>{error}</Alert>}
            </CardContent>
          </Card>

          {result && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight={600}>Результат</Typography>
                <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 2 }}>
                  <Chip label={`ID: ${result.generation_id.slice(0, 8)}...`} size="small" variant="outlined" />
                  <Chip label={`${result.cost} кредитов`} size="small" variant="outlined" />
                  <Chip label={statusLabels[result.status] || result.status} size="small" color={result.status === "completed" ? "success" : result.status === "failed" ? "error" : "default"} />
                </Box>
                {result.images && result.images.length > 0 && (
                  <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", maxHeight: 600, overflowY: "auto", p: 1 }}>
                    {result.images.map((img: ImageAsset) => (
                      <Box key={img.id} sx={{ maxWidth: 300 }}>
                        <Box sx={{ borderRadius: 2, overflow: "hidden", boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}>
                          <img src={`/${img.file_path}`} alt={img.filename} style={{ width: "100%", display: "block" }} />
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>{img.filename}</Typography>
                      </Box>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Box>
        )}

        <Box sx={{ flex: viewHistory ? "1 1 100%" : "1 1 35%", minWidth: 280 }}>
          <Card sx={{ position: viewHistory ? "static" : "sticky", top: 80 }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <HistoryIcon color="primary" />
                  <Typography variant="h6" fontWeight={600}>История</Typography>
                </Box>
                <Box sx={{ display: "flex", gap: 0.5 }}>
                  <ToggleButtonGroup value={viewMode} exclusive size="small" onChange={(_, v) => v && setViewMode(v)}>
                    <ToggleButton value="list" sx={{ px: 1, py: 0.25, textTransform: "none" }}>
                      <ViewListIcon fontSize="small" />
                    </ToggleButton>
                    <ToggleButton value="tiles" sx={{ px: 1, py: 0.25, textTransform: "none" }}>
                      <GridViewIcon fontSize="small" />
                    </ToggleButton>
                  </ToggleButtonGroup>
                  <IconButton size="small" onClick={() => loadHistory()} title="Обновить">
                    <RefreshIcon fontSize="small" />
                  </IconButton>
                </Box>
              </Box>
              {historyLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <Box key={i} sx={{ mb: 1.5 }}>
                    <Skeleton variant="text" width="40%" />
                    <Skeleton variant="text" width="80%" />
                    <Skeleton variant="rounded" width={80} height={24} />
                  </Box>
                ))
              ) : history.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 4 }}>Нет генераций</Typography>
              ) : viewMode === "list" ? (
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                  {history.map((g: HistoryItem) => (
                    <Box key={g.id} onClick={() => setSelectedHistory(g)}
                      sx={{ display: "flex", gap: 1.5, p: 1.5, bgcolor: "action.hover", borderRadius: 2, cursor: "pointer", "&:hover": { bgcolor: "action.selected" } }}>
                      {g.images?.[0] ? (
                        <Box sx={{ width: 56, height: 56, flexShrink: 0, borderRadius: 1.5, overflow: "hidden", bgcolor: "background.paper" }}>
                          <img src={`/${g.images[0].file_path}`} alt=""
                            style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                            onError={(e: any) => { e.target.style.display = "none"; }} />
                        </Box>
                      ) : (
                        <Box sx={{ width: 56, height: 56, flexShrink: 0, borderRadius: 1.5, bgcolor: "background.paper", display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <AutoAwesomeIcon sx={{ fontSize: 20, color: "text.disabled" }} />
                        </Box>
                      )}
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography variant="body2" fontWeight={600} noWrap>{g.workflow_type}</Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }} noWrap>{g.prompt}</Typography>
                        <Box sx={{ display: "flex", gap: 1 }}>
                          <Chip label={statusLabels[g.status] || g.status} size="small" color={g.status === "completed" ? "success" : g.status === "failed" ? "error" : "default"} />
                          <Typography variant="caption" color="text.secondary" sx={{ alignSelf: "center" }}>{g.cost} кр.</Typography>
                        </Box>
                      </Box>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 1.5 }}>
                  {history.map((g: HistoryItem) => (
                    <Card key={g.id} onClick={() => setSelectedHistory(g)}
                      sx={{ cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}>
                      {g.images?.[0] && (
                        <Box sx={{ width: "100%", height: 120, overflow: "hidden" }}>
                          <img src={`/${g.images[0].file_path}`} alt=""
                            style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                            onError={(e: any) => { e.target.style.display = "none"; }} />
                        </Box>
                      )}
                      <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
                        <Typography variant="body2" fontWeight={600} noWrap gutterBottom>{g.workflow_type}</Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }} noWrap>{g.prompt}</Typography>
                        <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                          <Chip label={statusLabels[g.status] || g.status} size="small" color={g.status === "completed" ? "success" : g.status === "failed" ? "error" : "default"} />
                          <Typography variant="caption" color="text.secondary">{g.cost} кр.</Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>

      <Dialog open={!!selectedHistory} onClose={() => setSelectedHistory(null)} maxWidth="md" fullWidth>
        {selectedHistory && (
          <>
            <DialogTitle>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Box>
                  <Typography variant="h6">{selectedHistory.workflow_type}</Typography>
                  <Typography variant="caption" color="text.secondary">{selectedHistory.prompt}</Typography>
                </Box>
                <IconButton onClick={() => setSelectedHistory(null)}><CloseIcon /></IconButton>
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              {selectedHistory.images.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  {selectedHistory.images.map(img => (
                    <Box key={img.id} sx={{ mb: 1 }}>
                      <img src={`/${img.file_path}`} alt={img.filename}
                        style={{ width: "100%", height: "auto", objectFit: "contain", display: "block", borderRadius: 8, maxHeight: "70vh", background: "repeating-conic-gradient(rgba(0,0,0,0.03) 0% 25%, transparent 0% 50%) 0px 0px / 20px 20px" }} />
                    </Box>
                  ))}
                </Box>
              )}
              <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
                <Chip label={`ID: ${selectedHistory.id.slice(0, 8)}...`} size="small" variant="outlined" />
                <Chip label={`${selectedHistory.cost} кредитов`} size="small" variant="outlined" />
                <Chip label={statusLabels[selectedHistory.status] || selectedHistory.status} size="small"
                  color={selectedHistory.status === "completed" ? "success" : selectedHistory.status === "failed" ? "error" : "default"} />
              </Box>

              <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                {selectedHistory.images.map(img => (
                  <Button key={img.id} variant="outlined" size="small" startIcon={<DownloadIcon />}
                    onClick={() => handleDownload(img)}>
                    Скачать
                  </Button>
                ))}
                <Button variant="outlined" size="small" color="error" startIcon={<DeleteIcon />}
                  onClick={() => handleDelete(selectedHistory)} disabled={deleting}>
                  {deleting ? "Удаление..." : "Удалить"}
                </Button>
                {selectedHistory.images.length > 0 && selectedHistory.status === "completed" && (
                  <>
                    <Button variant="outlined" size="small" startIcon={<EditIcon />}
                      onClick={() => setActionDialog("edit")}>
                      Редактировать
                    </Button>
                    <Button variant="outlined" size="small" startIcon={<VideoFileIcon />}
                      onClick={() => setActionDialog("video")}>
                      Создать видео
                    </Button>
                  </>
                )}
              </Box>
            </DialogContent>
          </>
        )}
      </Dialog>

      <Dialog open={actionDialog === "edit"} onClose={() => setActionDialog("")} maxWidth="sm" fullWidth>
        <DialogTitle>Редактирование изображения</DialogTitle>
        <DialogContent>
          <TextField select label="Workflow" fullWidth value={editWorkflow}
            onChange={e => setEditWorkflow(e.target.value)} margin="normal">
            <MenuItem value="qwen_edit_1">Qwen Edit (1 референс)</MenuItem>
            <MenuItem value="qwen_edit_2">Qwen Edit (2 референса)</MenuItem>
            <MenuItem value="qwen_edit_3">Qwen Edit (3 референса)</MenuItem>
          </TextField>
          <TextField label="Промпт" fullWidth multiline rows={3} value={editPrompt}
            onChange={e => setEditPrompt(e.target.value)} margin="normal" placeholder="Опишите, что изменить..." />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialog("")}>Отмена</Button>
          <Button variant="contained" onClick={handleSendToEdit} disabled={!editPrompt.trim() || actionLoading}>Запустить</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={actionDialog === "video"} onClose={() => setActionDialog("")} maxWidth="sm" fullWidth>
        <DialogTitle>Создание видео</DialogTitle>
        <DialogContent>
          <TextField label="Промпт" fullWidth multiline rows={3} value={videoPrompt}
            onChange={e => setVideoPrompt(e.target.value)} margin="normal" placeholder="Опишите сценарий..." />
          <TextField label="Длительность (сек)" type="number" size="small" value={videoDuration}
            onChange={e => setVideoDuration(Math.max(1, Number(e.target.value)))}
            inputProps={{ min: 1, max: 30 }} sx={{ width: 160, mt: 1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialog("")}>Отмена</Button>
          <Button variant="contained" onClick={handleSendToVideo} disabled={!videoPrompt.trim() || actionLoading}>Запустить</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};