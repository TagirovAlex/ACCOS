import { useState, useRef, useCallback } from "react";
import { Box, Card, CardContent, Typography, TextField, Button, MenuItem, Alert, LinearProgress, Chip, Skeleton } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { api } from "../services/api";

const WORKFLOWS = [
  { value: "z_image", label: "Z-Image (текст → изображение)", needsRefs: false },
  { value: "qwen_edit_1", label: "Qwen Edit (1 референс)", needsRefs: true, maxRefs: 1 },
  { value: "qwen_edit_2", label: "Qwen Edit (2 референса)", needsRefs: true, maxRefs: 2 },
  { value: "qwen_edit_3", label: "Qwen Edit (3 референса)", needsRefs: true, maxRefs: 3 },
];

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

export const GenerationPage = () => {
  const [workflow, setWorkflow] = useState("z_image");
  const [prompt, setPrompt] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenResult | null>(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<any[]>([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const selectedWorkflow = WORKFLOWS.find(w => w.value === workflow);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const res: any = await api("GET", "/generate/history");
      setHistory(res.generations || []);
    } catch { /* ignore */ }
    setHistoryLoading(false);
  }, []);

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
      setFiles(Array.from(e.target.files).slice(0, max));
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <Box>
      <Typography variant="h5" mb={3}>Генерация</Typography>

      <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
        <Box sx={{ flex: "1 1 60%", minWidth: 300 }}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <TextField select label="Workflow" fullWidth value={workflow} onChange={e => { setWorkflow(e.target.value); setFiles([]); }} margin="normal">
                {WORKFLOWS.map(w => <MenuItem key={w.value} value={w.value}>{w.label}</MenuItem>)}
              </TextField>

              <TextField label="Промпт" fullWidth multiline rows={3} value={prompt} onChange={e => setPrompt(e.target.value)} margin="normal" placeholder="Опишите, что хотите получить..." />

              {selectedWorkflow?.needsRefs && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" mb={1}>Референс-изображения ({files.length}/{selectedWorkflow.maxRefs})</Typography>
                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 1 }}>
                    {files.map((f, i) => (
                      <Chip key={i} label={f.name} onDelete={() => removeFile(i)} deleteIcon={<CloseIcon fontSize="small" />} size="small" />
                    ))}
                  </Box>
                  <Button variant="outlined" size="small" component="label" disabled={files.length >= (selectedWorkflow.maxRefs || 3)}>
                    Выбрать файл
                    <input ref={fileRef} type="file" hidden accept="image/*" multiple={selectedWorkflow.maxRefs !== 1} onChange={handleFileChange} />
                  </Button>
                </Box>
              )}

              <Button variant="contained" onClick={handleGenerate} disabled={loading || !prompt.trim()} sx={{ mt: 2 }}>
                {loading ? "Генерация..." : "Сгенерировать"}
              </Button>
              {loading && <LinearProgress sx={{ mt: 2 }} />}
              {error && <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError("")}>{error}</Alert>}
            </CardContent>
          </Card>

          {result && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Результат</Typography>
                <Typography variant="body2" color="text.secondary">ID: {result.generation_id}</Typography>
                <Typography variant="body2" color="text.secondary">Списано: {result.cost} кредитов</Typography>
                <Typography variant="body2" color="text.secondary">Статус: {result.status === "completed" ? "✅ Готово" : result.status === "processing" ? "⏳ Обработка..." : result.status === "queued" ? "⏳ В очереди..." : "❌ " + result.status}</Typography>
                {result.images && result.images.length > 0 && (
                  <Box sx={{ mt: 2, display: "flex", gap: 2, flexWrap: "wrap" }}>
                    {result.images.map((img: ImageAsset) => (
                      <Box key={img.id} sx={{ maxWidth: 300 }}>
                        <img src={`/${img.file_path}`} alt={img.filename} style={{ width: "100%", borderRadius: 8, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }} />
                        <Typography variant="caption" color="text.secondary">{img.filename}</Typography>
                      </Box>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Box>

        <Box sx={{ flex: "1 1 35%", minWidth: 280 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                История
                <Button size="small" sx={{ ml: 1 }} onClick={() => { loadHistory(); setHistoryLoaded(true); }}>
                  {historyLoaded ? "Обновить" : "Загрузить"}
                </Button>
              </Typography>
              {historyLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <Box key={i} sx={{ mb: 1.5 }}>
                    <Skeleton variant="text" width="40%" />
                    <Skeleton variant="text" width="80%" />
                    <Skeleton variant="rounded" width={80} height={24} />
                  </Box>
                ))
              ) : !historyLoaded ? (
                <Typography variant="body2" color="text.secondary">Нажмите "Загрузить"</Typography>
              ) : history.length === 0 ? (
                <Typography variant="body2" color="text.secondary">Нет генераций</Typography>
              ) : (
                history.map((g: any) => (
                  <Box key={g.id} sx={{ mb: 1.5, p: 1, bgcolor: "action.hover", borderRadius: 1 }}>
                    <Typography variant="body2" noWrap><strong>{g.workflow_type}</strong></Typography>
                    <Typography variant="caption" color="text.secondary" noWrap>{g.prompt}</Typography>
                    <Box sx={{ display: "flex", gap: 1, mt: 0.5 }}>
                      <Chip label={g.status} size="small" color={g.status === "completed" ? "success" : g.status === "failed" ? "error" : "default"} />
                      <Typography variant="caption" color="text.secondary">{g.cost} кр.</Typography>
                    </Box>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};
