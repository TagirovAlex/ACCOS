import { useState } from "react";
import { Box, Card, CardContent, Typography, TextField, Button, MenuItem, Alert, LinearProgress } from "@mui/material";
import { api } from "../services/api";

const WORKFLOWS = [
  { value: "ZIT.json", label: "Z-Image (текст → изображение)" },
  { value: "QWEN edit 1 pic.json", label: "Qwen Edit (1 референс)" },
  { value: "QWEN edit 2 pic.json", label: "Qwen Edit (2 референса)" },
  { value: "QWEN edit 3 pic.json", label: "Qwen Edit (3 референса)" },
];

export const GenerationPage = () => {
  const [workflow, setWorkflow] = useState("ZIT.json");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res: any = await api("POST", "/generate/", {
        workflow_type: workflow,
        prompt: prompt.trim(),
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <Box>
      <Typography variant="h5" mb={3}>Генерация</Typography>
      <Card sx={{ maxWidth: 600, mb: 3 }}>
        <CardContent>
          <TextField select label="Workflow" fullWidth value={workflow} onChange={e => setWorkflow(e.target.value)} margin="normal">
            {WORKFLOWS.map(w => <MenuItem key={w.value} value={w.value}>{w.label}</MenuItem>)}
          </TextField>
          <TextField label="Промпт" fullWidth multiline rows={3} value={prompt} onChange={e => setPrompt(e.target.value)} margin="normal" placeholder="Опишите, что хотите получить..." />
          <Button variant="contained" onClick={handleGenerate} disabled={loading || !prompt.trim()} sx={{ mt: 2 }}>
            {loading ? "Генерация..." : "Сгенерировать"}
          </Button>
          {loading && <LinearProgress sx={{ mt: 2 }} />}
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        </CardContent>
      </Card>
      {result && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Результат</Typography>
            <Typography variant="body2" color="text.secondary">ID: {result.generation?.id || result.id}</Typography>
            <Typography variant="body2" color="text.secondary">Списано: {result.cost || result.generation?.cost} кредитов</Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};
