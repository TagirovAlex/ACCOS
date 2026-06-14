import { useState, useEffect } from "react";
import {
  Box, Typography, TextField as MuiTextField, Button, Switch, FormControlLabel,
  Select, MenuItem, FormControl, InputLabel,
  Alert, Snackbar, CircularProgress, Paper, List, ListItemButton, ListItemIcon, ListItemText,
} from "@mui/material";
import ExtensionIcon from "@mui/icons-material/Extension";
import { getToken } from "../services/api";

interface SettingDef {
  module_name: string;
  key: string;
  label: string;
  type: string;
  category: string;
  default: any;
  description: string;
  is_admin_setting: boolean;
  is_user_setting: boolean;
  validation: Record<string, any> | null;
  value: string | null;
}

function SettingField({ def, value, onChange }: {
  def: SettingDef;
  value: string;
  onChange: (key: string, val: string) => void;
}) {
  const label = def.label || def.key;
  const desc = def.description || def.key;
  const handle = (v: string) => onChange(def.key, v);

  if (def.type === "boolean") {
    return (
      <FormControlLabel
        control={<Switch checked={value === "true"} onChange={(e) => handle(e.target.checked ? "true" : "false")} />}
        label={<Box><Typography variant="body2">{label}</Typography><Typography variant="caption" color="text.secondary">{desc}</Typography></Box>}
        sx={{ mb: 1.5, display: "flex", alignItems: "center", gap: 1 }}
      />
    );
  }

  if (def.type === "select" && def.validation?.options) {
    return (
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>{label}</InputLabel>
        <Select value={value || ""} label={label} onChange={(e) => handle(e.target.value)}>
          {def.validation.options.map((opt: string) => (
            <MenuItem key={opt} value={opt}>{opt}</MenuItem>
          ))}
        </Select>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>{desc}</Typography>
      </FormControl>
    );
  }

  return (
    <MuiTextField
      label={label}
      helperText={desc}
      value={value ?? ""}
      onChange={(e) => handle(e.target.value)}
      fullWidth
      multiline={def.type === "textarea" || (value ?? "").length > 80}
      minRows={def.type === "textarea" ? 3 : (value ?? "").length > 80 ? 2 : undefined}
      type={def.type === "password" ? "password" : def.type === "number" ? "number" : "text"}
      slotProps={{ htmlInput: def.type === "number" ? { step: "any" } : undefined }}
      sx={{ mb: 2 }}
    />
  );
}

function ModuleSettingsForm({ moduleName, onSaved }: { moduleName: string; onSaved: () => void }) {
  const [settings, setSettings] = useState<SettingDef[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [snack, setSnack] = useState<{ msg: string; sev: "success" | "error" } | null>(null);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const token = getToken();
      const res = await fetch(`/api/v1/admin/modules/${moduleName}/settings`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      const list: SettingDef[] = (data.settings || []).filter((s: SettingDef) => s.is_admin_setting);
      setSettings(list);
      const v: Record<string, string> = {};
      for (const s of list) v[s.key] = s.value ?? "";
      setValues(v);
    } catch {
      setSnack({ msg: "Ошибка загрузки", sev: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSettings(); }, [moduleName]);

  const handleChange = (key: string, val: string) => {
    setValues((prev) => ({ ...prev, [key]: val }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = getToken();
      for (const s of settings) {
        const newVal = values[s.key] ?? "";
        if (newVal !== (s.value ?? "")) {
          await fetch(`/api/v1/admin/modules/${moduleName}/settings/${s.key}`, {
            method: "PUT",
            headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
            body: JSON.stringify({ value: newVal }),
          });
        }
      }
      setSnack({ msg: "Настройки сохранены", sev: "success" });
      onSaved();
    } catch (e: any) {
      setSnack({ msg: e.message || "Ошибка сохранения", sev: "error" });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>;
  }

  if (settings.length === 0) {
    return <Typography color="text.secondary">У этого модуля нет настроек</Typography>;
  }

  const categories = [...new Set(settings.map((s) => s.category || "general"))].sort();
  const hasChanges = settings.some((s) => (values[s.key] ?? "") !== (s.value ?? ""));

  return (
    <Box>
      {categories.map((cat) => (
        <Box key={cat} sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="primary" sx={{ mb: 1.5, textTransform: "capitalize" }}>
            {cat === "general" ? "Общие" : cat === "connection" ? "Подключение" : cat === "pricing" ? "Стоимость" : cat === "llm" ? "LLM" : cat === "indexing" ? "Индексация" : cat === "retrieval" ? "Поиск" : cat === "embedding" ? "Эмбеддинги" : cat === "scheduling" ? "Расписание" : cat === "display" ? "Отображение" : cat === "restrictions" ? "Ограничения" : cat}
          </Typography>
          {settings.filter((s) => (s.category || "general") === cat).map((s) => (
            <SettingField key={s.key} def={s} value={values[s.key] ?? ""} onChange={handleChange} />
          ))}
        </Box>
      ))}
      <Box sx={{ mt: 3, display: "flex", gap: 1 }}>
        <Button variant="contained" onClick={handleSave} disabled={!hasChanges || saving}>
          {saving ? <CircularProgress size={20} /> : "Сохранить"}
        </Button>
        <Button variant="outlined" onClick={() => {
          const v: Record<string, string> = {};
          for (const s of settings) v[s.key] = s.value ?? "";
          setValues(v);
        }} disabled={!hasChanges}>
          Сбросить
        </Button>
      </Box>
      {snack && (
        <Snackbar open autoHideDuration={3000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
          <Alert severity={snack.sev} onClose={() => setSnack(null)}>{snack.msg}</Alert>
        </Snackbar>
      )}
    </Box>
  );
}

export const ModuleSettings = () => {
  const [modules, setModules] = useState<{ name: string; label: string }[]>([]);
  const [tab, setTab] = useState(0);

  useEffect(() => {
    (async () => {
      try {
        const token = getToken();
        const res = await fetch("/api/v1/admin/modules", { headers: { Authorization: `Bearer ${token}` } });
        const data = await res.json();
        const names: Record<string, string> = {
          chat: "Чат", comfyui: "ComfyUI", rag: "База знаний",
          web_fetch: "Web Fetch", doc_scraper: "Doc Scraper",
          files: "Файлы", documents: "Документы",
        };
        if (data.modules) {
          setModules(data.modules.map((m: any) => ({ name: m.name, label: names[m.name] || m.name })));
        }
      } catch {}
    })();
  }, []);

  if (modules.length === 0) return <CircularProgress sx={{ display: "block", mx: "auto", mt: 4 }} />;
  if (tab >= modules.length) setTab(0);

  const current = modules[tab] || modules[0];

  return (
    <Box sx={{ display: "flex", gap: 3 }}>
      <Paper sx={{ width: 240, flexShrink: 0, borderRadius: 2, overflow: "hidden" }}>
        <List dense disablePadding>
          {modules.map((m, i) => (
            <ListItemButton
              key={m.name}
              selected={tab === i}
              onClick={() => setTab(i)}
              sx={{
                px: 2, py: 1.5,
                borderLeft: tab === i ? 3 : 0,
                borderColor: "primary.main",
                "&.Mui-selected": {
                  bgcolor: (t: any) => t.palette.mode === "dark" ? "rgba(86,179,240,0.08)" : "rgba(68,138,255,0.06)",
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: tab === i ? "primary.main" : undefined }}>
                <ExtensionIcon />
              </ListItemIcon>
              <ListItemText
                primary={m.label}
                primaryTypographyProps={{ variant: "body2", fontWeight: tab === i ? 600 : 400 }}
              />
            </ListItemButton>
          ))}
        </List>
      </Paper>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="h6" fontWeight={600} mb={3}>{current.label}</Typography>
        <ModuleSettingsForm moduleName={current.name} onSaved={() => {}} />
      </Box>
    </Box>
  );
};
