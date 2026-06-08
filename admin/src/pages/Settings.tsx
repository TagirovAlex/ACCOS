import { useState, useEffect } from "react";
import {
  Box, Typography, TextField as MuiTextField,
  Button, Switch, FormControlLabel, Alert, Snackbar, CircularProgress,
  Paper, List, ListItemButton, ListItemIcon, ListItemText,
} from "@mui/material";
import DnsIcon from "@mui/icons-material/Dns";
import ChatIcon from "@mui/icons-material/Chat";
import ImageIcon from "@mui/icons-material/Image";
import AttachMoneyIcon from "@mui/icons-material/AttachMoney";
import EditIcon from "@mui/icons-material/Edit";
import MovieIcon from "@mui/icons-material/Movie";
import PeopleIcon from "@mui/icons-material/People";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import { getToken } from "../services/api";

const API = "/api/v1/admin/settings";

interface Setting {
  key: string;
  value: string;
  description: string;
}

interface CategoryDef {
  key: string;
  label: string;
  icon: React.ReactNode;
}

const CATEGORIES: CategoryDef[] = [
  { key: "Домен", label: "LDAP / Домен", icon: <DnsIcon /> },
  { key: "LLM", label: "LLM / Чат", icon: <ChatIcon /> },
  { key: "Генерация", label: "Генерация изображений", icon: <ImageIcon /> },
  { key: "Цены: LLM", label: "Цены: LLM", icon: <AttachMoneyIcon /> },
  { key: "Цены: Генерация", label: "Цены: генерация", icon: <ImageIcon /> },
  { key: "Цены: Редактирование", label: "Цены: редактирование", icon: <EditIcon /> },
  { key: "Цены: Видео", label: "Цены: видео", icon: <MovieIcon /> },
  { key: "Пользователи", label: "Пользователи", icon: <PeopleIcon /> },
  { key: "Экономика", label: "Экономика", icon: <AccountBalanceIcon /> },
];

const CATEGORY_ORDER = CATEGORIES.map((c) => c.key);

function parseCategory(desc: string): string {
  const m = desc.match(/^\[(.+?)\]/);
  return m ? m[1] : "Прочее";
}

function stripCategory(desc: string): string {
  return desc.replace(/^\[.+?\]\s*/, "");
}

const BOOLEAN_KEYS = new Set(["require_ad_group_for_login", "ldap_enabled"]);

function isBoolean(key: string, v: string): boolean {
  if (!BOOLEAN_KEYS.has(key)) return false;
  return ["true", "false", "1", "0", "yes", "no"].includes(v.toLowerCase());
}

function isNumeric(key: string): boolean {
  return /^(cost_|auto_accrual|default_start_balance|comfyui_poll_interval)/.test(key);
}

const FIELD_DISPLAY_NAMES: Record<string, string> = {
  ldap_server: "Адрес LDAP-сервера",
  ldap_domain: "NetBIOS-имя домена",
  ldap_base_dn: "Базовый DN",
  ldap_bind_dn: "Учётная запись для поиска (DN, устаревший формат)",
  ldap_bind_username: "Учётная запись для поиска (имя пользователя)",
  ldap_bind_password: "Пароль учётной записи",
  require_ad_group_for_login: "Требовать группу AD для входа",
  default_permissions: "Права доступа по умолчанию",
  default_start_balance: "Стартовый баланс",
  llm_api: "API-адрес LLM",
  llm_api_key: "API-ключ LLM",
  llm_model: "Модель LLM",
  llm_system_prompt: "Системный промпт",
  comfy_api: "API-адрес ComfyUI",
  comfy_workflow_zit: "Workflow ZIT",
  comfy_workflow_qwen_edit_1: "Workflow Qwen edit 1 pic",
  comfy_workflow_qwen_edit_2: "Workflow Qwen edit 2 pic",
  comfy_workflow_qwen_edit_3: "Workflow Qwen edit 3 pic",
  comfy_workflow_text_to_video: "Workflow text-to-video",
  comfy_workflow_image_to_video: "Workflow image-to-video",
  cost_llm_input_1k: "Стоимость входных токенов (за 1K)",
  cost_llm_output_1k: "Стоимость выходных токенов (за 1K)",
  cost_image_generation: "Стоимость генерации изображения",
  cost_image_edit_qwen: "Стоимость редактирования (Qwen)",
  cost_video_gen: "Стоимость генерации видео",
  cost_video_img2video: "Стоимость image-to-video",
  auto_accrual_amount: "Сумма начисления (MS)",
  auto_accrual_interval_minutes: "Интервал начисления (минуты)",
  auto_accrual_time: "Время начисления (HH:MM, по серверу)",
};

const MASKED_KEYS = new Set(["ldap_bind_password", "llm_api_key"]);

function SettingField({
  setting,
  value,
  onChange,
}: {
  setting: Setting;
  value: string;
  onChange: (key: string, val: string) => void;
}) {
  const label = FIELD_DISPLAY_NAMES[setting.key] || setting.key;
  const desc = stripCategory(setting.description);
  const helper = desc || setting.key;

  if (isBoolean(setting.key, value)) {
    const checked = ["true", "1", "yes"].includes(value.toLowerCase());
    return (
      <FormControlLabel
        control={<Switch checked={checked} onChange={(e) => onChange(setting.key, e.target.checked ? "true" : "false")} />}
        label={<><strong>{label}</strong><br /><Typography variant="caption" color="text.secondary">{helper}</Typography></>}
        sx={{ mb: 1 }}
      />
    );
  }

  if (isNumeric(setting.key)) {
    return (
      <MuiTextField
        label={label}
        helperText={helper}
        value={value}
        onChange={(e) => onChange(setting.key, e.target.value)}
        fullWidth
        type="number"
        slotProps={{ htmlInput: { step: "any", min: 0 } }}
        sx={{ mb: 2 }}
      />
    );
  }

  return (
    <MuiTextField
      label={label}
      helperText={helper}
      value={value}
      onChange={(e) => onChange(setting.key, e.target.value)}
      fullWidth
      multiline={value.length > 60}
      minRows={value.length > 60 ? 2 : undefined}
      type={MASKED_KEYS.has(setting.key) ? "password" : "text"}
      slotProps={MASKED_KEYS.has(setting.key) ? { htmlInput: { autoComplete: "new-password" } } : undefined}
      sx={{ mb: 2 }}
    />
  );
}

function CategoryForm({
  settings,
  onSaved,
}: {
  settings: Setting[];
  onSaved: () => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [snack, setSnack] = useState<{ msg: string; sev: "success" | "error" } | null>(null);

  useEffect(() => {
    const v: Record<string, string> = {};
    for (const s of settings) v[s.key] = s.value;
    setValues(v);
  }, [settings]);

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
          await fetch(`${API}/${s.key}`, {
            method: "PUT",
            headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
            body: JSON.stringify({ value: newVal, description: s.description }),
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

function LdapForm({ settings, onSaved }: { settings: Setting[]; onSaved: () => void }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const [snack, setSnack] = useState<{ msg: string; sev: "success" | "error" } | null>(null);

  useEffect(() => {
    const v: Record<string, string> = {};
    for (const s of settings) v[s.key] = s.value;
    setValues(v);
  }, [settings]);

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
          await fetch(`${API}/${s.key}`, {
            method: "PUT",
            headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
            body: JSON.stringify({ value: newVal, description: s.description }),
          });
        }
      }
      setSnack({ msg: "Настройки LDAP сохранены", sev: "success" });
      onSaved();
    } catch (e: any) {
      setSnack({ msg: e.message || "Ошибка", sev: "error" });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const token = getToken();
      const res = await fetch("/api/v1/admin/ldap-groups?search=*", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.success && data.groups) {
        setTestResult({ ok: true, msg: `Подключение успешно: найдено ${data.groups.length} групп` });
      } else {
        setTestResult({ ok: false, msg: data.error || "Ошибка подключения" });
      }
    } catch (e: any) {
      setTestResult({ ok: false, msg: e.message || "Ошибка подключения" });
    } finally {
      setTesting(false);
    }
  };

  const hasChanges = settings.some((s) => (values[s.key] ?? s.value) !== s.value);

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Alert severity="info" sx={{ borderRadius: 2 }}>
          Настройки подключения к Active Directory. После изменения сохраните настройки, затем нажмите "Проверить подключение".
        </Alert>
      </Box>

      <MuiTextField label="Адрес сервера" helperText="Например: ldap://dc.domain.local:389" value={values.ldap_server ?? ""}
        onChange={(e) => handleChange("ldap_server", e.target.value)} fullWidth sx={{ mb: 2 }} />

      <MuiTextField label="NetBIOS-имя домена" helperText="Например: DOMAIN" value={values.ldap_domain ?? ""}
        onChange={(e) => handleChange("ldap_domain", e.target.value)} fullWidth sx={{ mb: 2 }} />

      <MuiTextField label="Базовый DN" helperText="Например: DC=domain,DC=local" value={values.ldap_base_dn ?? ""}
        onChange={(e) => handleChange("ldap_base_dn", e.target.value)} fullWidth sx={{ mb: 2 }} />

      <MuiTextField label="Учётная запись для поиска (имя пользователя)"
        helperText={
          <span>
            Имя учётной записи для поиска в AD (без домена). Например: <code>svc-accos</code>.
            Используется форма <code>DOMAIN\username</code>. Если не указано — используется <code>ldap_bind_dn</code> (DN) или анонимный поиск.
          </span>
        }
        value={values.ldap_bind_username ?? ""}
        onChange={(e) => handleChange("ldap_bind_username", e.target.value)} fullWidth sx={{ mb: 2 }} />

      <MuiTextField label="Пароль" type="password" value={values.ldap_bind_password ?? ""}
        onChange={(e) => handleChange("ldap_bind_password", e.target.value)}
        fullWidth sx={{ mb: 2 }} slotProps={{ htmlInput: { autoComplete: "new-password" } }} />

      <FormControlLabel
        control={<Switch checked={values.ldap_enabled === "true"}
          onChange={(e) => handleChange("ldap_enabled", e.target.checked ? "true" : "false")} />}
        label={<><strong>Включить LDAP-аутентификацию</strong><br /><Typography variant="caption" color="text.secondary">Разрешить вход доменным пользователям</Typography></>}
        sx={{ mb: 2 }}
      />

      <FormControlLabel
        control={<Switch checked={values.require_ad_group_for_login === "true"}
          onChange={(e) => handleChange("require_ad_group_for_login", e.target.checked ? "true" : "false")} />}
        label="Требовать членство в AD-группе для входа"
        sx={{ mb: 2 }}
      />

      <Box sx={{ mt: 3, display: "flex", gap: 1, alignItems: "center" }}>
        <Button variant="contained" onClick={handleSave} disabled={!hasChanges || saving}>
          {saving ? <CircularProgress size={20} /> : "Сохранить"}
        </Button>
        <Button variant="outlined" onClick={handleTest} disabled={testing} startIcon={testing ? <CircularProgress size={16} /> : undefined}>
          {testing ? "Проверка..." : "Проверить подключение"}
        </Button>
        {testResult && (
          <Alert severity={testResult.ok ? "success" : "error"} sx={{ ml: 2, py: 0 }}>
            {testResult.msg}
          </Alert>
        )}
      </Box>

      {snack && (
        <Snackbar open autoHideDuration={3000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
          <Alert severity={snack.sev} onClose={() => setSnack(null)}>{snack.msg}</Alert>
        </Snackbar>
      )}
    </Box>
  );
}

export const SettingsList = () => {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = getToken();
      const res = await fetch(API, { headers: { Authorization: `Bearer ${token}` } });
      const json = await res.json();
      setSettings((json.settings || []).map((s: Setting) => ({ ...s, id: s.key })));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const grouped: Record<string, Setting[]> = {};
  const others: Setting[] = [];
  for (const s of settings) {
    const cat = parseCategory(s.description);
    if (cat && CATEGORY_ORDER.includes(cat)) {
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(s);
    } else {
      others.push(s);
    }
  }

  const currentTab = tab < CATEGORIES.length ? CATEGORIES[tab] : CATEGORIES[0];
  const currentSettings = grouped[currentTab.key] || [];
  const isLdapTab = currentTab.key === "Домен";
  const isEmpty = currentSettings.length === 0 && !isLdapTab;

  return (
    <Box sx={{ display: "flex", gap: 3 }}>
      <Paper sx={{ width: 240, flexShrink: 0, borderRadius: 2, overflow: "hidden" }}>
        <List dense disablePadding>
          {CATEGORIES.map((c, i) => {
            const hasSettings = !!grouped[c.key]?.length || c.key === "Домен";
            return (
              <ListItemButton
                key={c.key}
                selected={tab === i}
                disabled={!hasSettings}
                onClick={() => setTab(i)}
                sx={{
                  px: 2, py: 1.5,
                  borderLeft: tab === i ? 3 : 0,
                  borderColor: "primary.main",
                  "&.Mui-selected": {
                    bgcolor: (t) => t.palette.mode === "dark" ? "rgba(86,179,240,0.08)" : "rgba(68,138,255,0.06)",
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36, color: tab === i ? "primary.main" : undefined }}>
                  {c.icon}
                </ListItemIcon>
                <ListItemText
                  primary={c.label}
                  primaryTypographyProps={{ variant: "body2", fontWeight: tab === i ? 600 : 400 }}
                />
              </ListItemButton>
            );
          })}
        </List>
      </Paper>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="h6" fontWeight={600} mb={3}>{currentTab.label}</Typography>
        {loading ? (
          <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>
        ) : isEmpty ? (
          <Box sx={{ mt: 2, textAlign: "center" }}>
            <Typography color="text.secondary">Нет настроек в этой категории</Typography>
          </Box>
        ) : isLdapTab ? (
          <LdapForm settings={currentSettings} onSaved={fetchData} />
        ) : (
          <CategoryForm settings={currentSettings} onSaved={fetchData} />
        )}
      </Box>
    </Box>
  );
};

export const SettingsEdit = () => null;
export const SettingsCreate = () => null;
