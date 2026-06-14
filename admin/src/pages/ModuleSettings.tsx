import { useState, useEffect } from "react";
import {
  Box, Typography, TextField as MuiTextField, Button, Switch, FormControlLabel,
  Alert, Snackbar, CircularProgress, Paper, List, ListItemButton, ListItemIcon, ListItemText,
} from "@mui/material";
import ExtensionIcon from "@mui/icons-material/Extension";
import { getToken } from "../services/api";

interface ModuleSetting {
  module_name: string;
  key: string;
  value: string;
}

const DEFINED_MODULES = [
  ["chat", "Чат"],
  ["comfyui", "ComfyUI"],
  ["rag", "База знаний"],
];

const SETTING_LABELS: Record<string, string> = {};

const MASKED_KEYS = new Set<string>();

function SettingField({
  setting, value, onChange,
}: {
  setting: ModuleSetting;
  value: string;
  onChange: (key: string, val: string) => void;
}) {
  const label = SETTING_LABELS[setting.key] || setting.key;
  return (
    <MuiTextField
      label={label}
      helperText={setting.key}
      value={value}
      onChange={(e) => onChange(setting.key, e.target.value)}
      fullWidth
      multiline={value.length > 60}
      minRows={value.length > 60 ? 2 : undefined}
      type={MASKED_KEYS.has(setting.key) ? "password" : "text"}
      sx={{ mb: 2 }}
    />
  );
}

function ModuleSettingsForm({ moduleName, onSaved }: { moduleName: string; onSaved: () => void }) {
  const [settings, setSettings] = useState<ModuleSetting[]>([]);
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
      const list: ModuleSetting[] = (data.settings || []);
      setSettings(list);
      const v: Record<string, string> = {};
      for (const s of list) v[s.key] = s.value;
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
        const newVal = values[s.key] ?? s.value;
        if (newVal !== s.value) {
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

  const hasChanges = settings.some((s) => (values[s.key] ?? s.value) !== s.value);

  return (
    <Box>
      {settings.map((s) => (
        <SettingField key={s.key} setting={s} value={values[s.key] ?? s.value} onChange={handleChange} />
      ))}
      <Box sx={{ mt: 3, display: "flex", gap: 1 }}>
        <Button variant="contained" onClick={handleSave} disabled={!hasChanges || saving}>
          {saving ? <CircularProgress size={20} /> : "Сохранить"}
        </Button>
        <Button variant="outlined" onClick={() => {
          const v: Record<string, string> = {};
          for (const s of settings) v[s.key] = s.value;
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
  const [tab, setTab] = useState(0);

  const currentModule = DEFINED_MODULES[tab] || DEFINED_MODULES[0];

  return (
    <Box sx={{ display: "flex", gap: 3 }}>
      <Paper sx={{ width: 240, flexShrink: 0, borderRadius: 2, overflow: "hidden" }}>
        <List dense disablePadding>
          {DEFINED_MODULES.map(([name, label], i) => (
            <ListItemButton
              key={name}
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
                primary={label}
                primaryTypographyProps={{ variant: "body2", fontWeight: tab === i ? 600 : 400 }}
              />
            </ListItemButton>
          ))}
        </List>
      </Paper>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="h6" fontWeight={600} mb={3}>{currentModule[1]}</Typography>
        <ModuleSettingsForm moduleName={currentModule[0]} onSaved={() => {}} />
      </Box>
    </Box>
  );
};
