import { useState, useEffect } from "react";
import {
  Edit, SimpleForm, TextInput,
  Create, useRefresh, useNotify,
} from "react-admin";
import {
  Box, Card, CardContent, Typography, Accordion, AccordionSummary,
  AccordionDetails, Chip, Dialog, DialogTitle, DialogContent,
  DialogActions, Button, TextField as MuiTextField,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { getToken } from "../services/api";

const API = "/api/v1/admin/settings";

const CATEGORIES: Record<string, { label: string; color: string }> = {
  Домен: { label: "LDAP / Домен", color: "#1976d2" },
  LLM: { label: "LLM / Чат", color: "#2e7d32" },
  Генерация: { label: "Генерация изображений", color: "#e65100" },
  "Цены: LLM": { label: "Стоимость: LLM", color: "#6a1b9a" },
  "Цены: Генерация": { label: "Стоимость: генерация", color: "#00838f" },
  "Цены: Редактирование": { label: "Стоимость: редактирование", color: "#ad1457" },
  "Цены: Видео": { label: "Стоимость: видео", color: "#283593" },
  Пользователи: { label: "Пользователи", color: "#4e342e" },
  Экономика: { label: "Экономика", color: "#558b2f" },
};

function parseCategory(desc: string): string {
  const m = desc.match(/^\[(.+?)\]/);
  return m ? m[1] : "Прочее";
}

function stripCategory(desc: string): string {
  return desc.replace(/^\[.+?\]\s*/, "");
}

interface Setting {
  key: string;
  value: string;
  description: string;
}

async function fetchSettings(): Promise<Setting[]> {
  const token = getToken();
  const res = await fetch(API, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const json = await res.json();
  return (json.settings || []).map((s: Setting) => ({
    ...s,
    id: s.key,
  }));
}

async function saveSetting(key: string, value: string, description: string): Promise<void> {
  const token = getToken();
  await fetch(`${API}/${key}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ value, description }),
  });
}

export const SettingsList = () => {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [expanded, setExpanded] = useState<string | false>(false);
  const [editKey, setEditKey] = useState<string | null>(null);
  const [editVal, setEditVal] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const refresh = useRefresh();
  const notify = useNotify();

  useEffect(() => {
    fetchSettings().then(setSettings);
  }, [refresh]);

  const grouped: Record<string, Setting[]> = {};
  for (const s of settings) {
    const cat = parseCategory(s.description);
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(s);
  }

  const handleSave = async () => {
    if (!editKey) return;
    await saveSetting(editKey, editVal, editDesc);
    setEditKey(null);
    notify("Сохранено", { type: "success" });
    const updated = await fetchSettings();
    setSettings(updated);
  };

  return (
    <Box>
      {/* Edit dialog */}
      <Dialog open={!!editKey} onClose={() => setEditKey(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Редактирование: {editKey}</DialogTitle>
        <DialogContent>
          <MuiTextField
            label="Значение" fullWidth multiline minRows={2}
            value={editVal} onChange={(e) => setEditVal(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <MuiTextField
            label="Описание" fullWidth multiline minRows={2}
            value={editDesc} onChange={(e) => setEditDesc(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditKey(null)}>Отмена</Button>
          <Button variant="contained" onClick={handleSave}>Сохранить</Button>
        </DialogActions>
      </Dialog>

      {/* Category sections */}
      {Object.entries(CATEGORIES).map(([catKey, catVal]) => {
        const items = grouped[catKey];
        if (!items || items.length === 0) return null;
        return (
          <Accordion
            key={catKey}
            expanded={expanded === catKey}
            onChange={() => setExpanded(expanded === catKey ? false : catKey)}
            sx={{ mb: 1 }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Chip label={catVal.label} size="small" sx={{ bgcolor: catVal.color, color: "#fff" }} />
                <Typography variant="body2" color="text.secondary">
                  {items.length} {items.length === 1 ? "параметр" : items.length < 5 ? "параметра" : "параметров"}
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {items.map((s) => (
                <Card key={s.key} variant="outlined" sx={{ mb: 1 }}>
                  <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                          {s.key}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, fontSize: "0.8rem" }}>
                          {stripCategory(s.description)}
                        </Typography>
                        <Typography variant="body1" sx={{ mt: 0.5, fontWeight: 500, wordBreak: "break-all" }}>
                          {s.value}
                        </Typography>
                      </Box>
                      <Button
                        size="small"
                        variant="outlined"
                        sx={{ ml: 2, minWidth: 70 }}
                        onClick={() => {
                          setEditKey(s.key);
                          setEditVal(s.value);
                          setEditDesc(s.description);
                        }}
                      >
                        Изменить
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </AccordionDetails>
          </Accordion>
        );
      })}
    </Box>
  );
};

export const SettingsEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="key" label="Ключ" disabled />
      <TextInput source="value" label="Значение" multiline fullWidth />
      <TextInput source="description" label="Описание" fullWidth />
    </SimpleForm>
  </Edit>
);

export const SettingsCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="key" label="Ключ" required />
      <TextInput source="value" label="Значение" multiline fullWidth required />
      <TextInput source="description" label="Описание" fullWidth />
    </SimpleForm>
  </Create>
);
