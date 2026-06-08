import { useState, useEffect } from "react";
import { Box, Card, CardContent, Typography, Grid, Chip, Button, Skeleton, Avatar } from "@mui/material";
import { useNavigate } from "react-router-dom";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import PersonIcon from "@mui/icons-material/Person";
import LockIcon from "@mui/icons-material/Lock";
import ChatIcon from "@mui/icons-material/Chat";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import type { User } from "../services/auth";
import { api } from "../services/api";

interface Props {
  user: User;
}

interface HistoryGen {
  id: string;
  workflow_type: string;
  prompt: string;
  status: string;
  cost: number;
  created_at: string;
  images: { id: string; filename: string; file_path: string }[];
}

const statusLabels: Record<string, string> = {
  completed: "Готово",
  processing: "Обработка",
  queued: "В очереди",
  failed: "Ошибка",
};

export const DashboardPage = ({ user }: Props) => {
  const navigate = useNavigate();
  const [generations, setGenerations] = useState<HistoryGen[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api("GET", "/generate/history").then((res: any) => {
      setGenerations((res.generations || []).slice(0, 10));
      setLoaded(true);
    }).catch(() => setLoaded(true));
  }, []);

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} mb={3}>Дашборд</Typography>
      <Grid container spacing={2.5} mb={4}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ "&:hover": { cursor: "default", transform: "none" } }}>
            <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, py: 2.5 }}>
              <Avatar sx={{ bgcolor: "primary.main", width: 48, height: 48 }}>
                <AccountBalanceWalletIcon />
              </Avatar>
              <Box>
                <Typography variant="body2" color="text.secondary">Баланс</Typography>
                <Typography variant="h5" fontWeight={700}>{user.balance}</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ "&:hover": { cursor: "default", transform: "none" } }}>
            <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, py: 2.5 }}>
              <Avatar sx={{ bgcolor: "success.main", width: 48, height: 48 }}>
                <PersonIcon />
              </Avatar>
              <Box>
                <Typography variant="body2" color="text.secondary">Пользователь</Typography>
                <Typography variant="h6" fontWeight={600}>{user.full_name || user.username}</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ "&:hover": { cursor: "default", transform: "none" } }}>
            <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, py: 2.5 }}>
              <Avatar sx={{ bgcolor: "warning.main", width: 48, height: 48 }}>
                <LockIcon />
              </Avatar>
              <Box>
                <Typography variant="body2" color="text.secondary">Права доступа</Typography>
                <Typography variant="h6" fontWeight={600}>{user.permissions === "chat" ? "Чат" : user.permissions === "generate" ? "Генерация" : "Полный доступ"}</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card onClick={() => navigate("/chat")} sx={{ cursor: "pointer" }}>
            <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, py: 2.5 }}>
              <Avatar sx={{ bgcolor: "info.main", width: 48, height: 48 }}>
                <ChatIcon />
              </Avatar>
              <Box>
                <Typography variant="body2" color="text.secondary">Быстрый доступ</Typography>
                <Typography variant="h6" fontWeight={600}>Чат</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h6" fontWeight={600}>История генераций</Typography>
        <Button size="small" onClick={() => navigate("/generate?view=history")} endIcon={<AutoAwesomeIcon />}>Все генерации</Button>
      </Box>

      {!loaded ? (
        Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} sx={{ mb: 1.5 }}>
            <CardContent sx={{ display: "flex", gap: 2, py: 1.5 }}>
              <Skeleton variant="rounded" width={64} height={64} sx={{ borderRadius: 2 }} />
              <Box sx={{ flex: 1 }}>
                <Skeleton variant="text" width="40%" />
                <Skeleton variant="text" width="80%" />
                <Skeleton variant="rounded" width={80} height={24} />
              </Box>
            </CardContent>
          </Card>
        ))
      ) : generations.length === 0 ? (
        <Card sx={{ "&:hover": { cursor: "default", transform: "none" } }}>
          <CardContent sx={{ textAlign: "center", py: 6 }}>
            <AutoAwesomeIcon sx={{ fontSize: 48, color: "text.disabled", mb: 2 }} />
            <Typography color="text.secondary">Нет генераций</Typography>
            <Button variant="outlined" size="small" sx={{ mt: 2 }} onClick={() => navigate("/generate")}>Создать первую</Button>
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          {generations.map(g => {
            const thumbnail = g.images?.[0];
            return (
              <Card key={g.id} sx={{ cursor: "pointer" }} onClick={() => navigate("/generate")}>
                <CardContent sx={{ display: "flex", gap: 2, alignItems: "center", py: 1.5 }}>
                  {thumbnail ? (
                    <Box sx={{ width: 64, height: 64, flexShrink: 0, borderRadius: 2, overflow: "hidden", bgcolor: "action.hover" }}>
                      <img src={`/${thumbnail.file_path}`} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    </Box>
                  ) : (
                    <Box sx={{ width: 64, height: 64, flexShrink: 0, borderRadius: 2, bgcolor: "action.hover", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <AutoAwesomeIcon sx={{ color: "text.disabled" }} />
                    </Box>
                  )}
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" fontWeight={600} noWrap>{g.workflow_type}</Typography>
                    <Typography variant="body2" color="text.secondary" noWrap sx={{ mt: 0.25 }}>{g.prompt}</Typography>
                    <Box sx={{ display: "flex", gap: 1, mt: 0.5, alignItems: "center" }}>
                      <Chip label={statusLabels[g.status] || g.status} size="small" color={g.status === "completed" ? "success" : g.status === "failed" ? "error" : "default"} />
                      <Typography variant="caption" color="text.secondary">{g.cost} кр.</Typography>
                      <Typography variant="caption" color="text.secondary">{new Date(g.created_at).toLocaleString()}</Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      )}
    </Box>
  );
};
