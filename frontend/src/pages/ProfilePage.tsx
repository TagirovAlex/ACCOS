import { useState, useEffect, useRef } from "react";
import {
  Box, Card, CardContent, Typography, TextField, Button, Avatar,
  Snackbar, Alert, CircularProgress,
} from "@mui/material";
import PhotoCameraIcon from "@mui/icons-material/PhotoCamera";
import SaveIcon from "@mui/icons-material/Save";
import type { User } from "../services/auth";
import { getProfile, updateProfile, uploadAvatar } from "../services/user";

interface Props {
  user: User;
}

export const ProfilePage = ({ user }: Props) => {
  const [fullName, setFullName] = useState(user.full_name || "");
  const [email, setEmail] = useState(user.email || "");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarError, setAvatarError] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savingPrompt, setSavingPrompt] = useState(false);
  const [savingAvatar, setSavingAvatar] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: "success" | "error" }>({ open: false, message: "", severity: "success" });
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getProfile().then((data: any) => {
      const p = data.user || data;
      setFullName(p.full_name || "");
      setEmail(p.email || "");
      setSystemPrompt(p.default_system_prompt || "");
    }).catch(() => {
    });
  }, [user]);

  const handleAvatarSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
    setAvatarError(false);
  };

  const handleAvatarUpload = async () => {
    if (!avatarFile) return;
    setSavingAvatar(true);
    try {
      await uploadAvatar(avatarFile);
      setSnackbar({ open: true, message: "Аватар обновлён", severity: "success" });
      setAvatarPreview(null);
      setAvatarFile(null);
      setAvatarError(false);
    } catch {
      setSnackbar({ open: true, message: "Ошибка загрузки аватара", severity: "error" });
    } finally {
      setSavingAvatar(false);
    }
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      await updateProfile({ full_name: fullName, email });
      setSnackbar({ open: true, message: "Профиль сохранён", severity: "success" });
    } catch {
      setSnackbar({ open: true, message: "Ошибка сохранения профиля", severity: "error" });
    } finally {
      setSaving(false);
    }
  };

  const handleSavePrompt = async () => {
    setSavingPrompt(true);
    try {
      await updateProfile({ default_system_prompt: systemPrompt });
      setSnackbar({ open: true, message: "Промпт сохранён", severity: "success" });
    } catch {
      setSnackbar({ open: true, message: "Ошибка сохранения промпта", severity: "error" });
    } finally {
      setSavingPrompt(false);
    }
  };

  const isLdap = user.auth_source === "ldap";
  const avatarUrl = user.avatar_path ? `/${user.avatar_path}` : null;

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} mb={3}>Профиль</Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: "flex", alignItems: "center", gap: 3, py: 3 }}>
          <Box sx={{ position: "relative" }}>
            {avatarPreview ? (
              <Avatar src={avatarPreview} sx={{ width: 100, height: 100 }} />
            ) : (
              <Avatar
                src={avatarError ? undefined : (avatarUrl || undefined)}
                onError={() => setAvatarError(true)}
                sx={{ width: 100, height: 100, bgcolor: "primary.main", fontSize: 36 }}
              >
                {user.full_name?.[0] || user.username[0]}
              </Avatar>
            )}
          </Box>
          <Box>
            <Typography variant="subtitle1" fontWeight={600}>{user.full_name || user.username}</Typography>
            <Typography variant="body2" color="text.secondary" mb={1.5}>{user.username}</Typography>
            {isLdap ? (
              <Typography variant="caption" color="text.secondary">Аватар загружается из домена Active Directory</Typography>
            ) : (
              <Box sx={{ display: "flex", gap: 1 }}>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<PhotoCameraIcon />}
                  onClick={() => fileInputRef.current?.click()}
                >
                  {avatarFile ? "Изменить" : "Загрузить"}
                </Button>
                {avatarFile && (
                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleAvatarUpload}
                    disabled={savingAvatar}
                  >
                    {savingAvatar ? <CircularProgress size={16} /> : "Сохранить"}
                  </Button>
                )}
              </Box>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              hidden
              onChange={handleAvatarSelect}
            />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 3 }}>
          <Typography variant="subtitle1" fontWeight={600} mb={2}>Информация профиля</Typography>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, maxWidth: 480 }}>
            <TextField
              label="Имя пользователя"
              value={user.username}
              size="small"
              disabled
            />
            <TextField
              label="Полное имя"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              size="small"
            />
            <TextField
              label="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              size="small"
              type="email"
            />
            <Box>
              <Button
                variant="contained"
                onClick={handleSaveProfile}
                disabled={saving}
                startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
              >
                Сохранить
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent sx={{ py: 3 }}>
          <Typography variant="subtitle1" fontWeight={600} mb={1}>Системный промпт по умолчанию</Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Этот промпт будет автоматически добавляться в каждый новый чат
          </Typography>
          <TextField
            multiline
            rows={4}
            fullWidth
            value={systemPrompt}
            onChange={e => setSystemPrompt(e.target.value)}
            size="small"
            sx={{ maxWidth: 640 }}
          />
          <Box mt={2}>
            <Button
              variant="contained"
              onClick={handleSavePrompt}
              disabled={savingPrompt}
              startIcon={savingPrompt ? <CircularProgress size={16} /> : <SaveIcon />}
            >
              Сохранить промпт
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={snackbar.severity} variant="filled" sx={{ width: "100%" }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};
