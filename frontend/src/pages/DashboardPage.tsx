import { useState, useEffect } from "react";
import { Box, Card, CardContent, Typography, Grid, Chip, Button, Skeleton, Avatar, ToggleButtonGroup, ToggleButton } from "@mui/material";
import { useNavigate } from "react-router-dom";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import EditIcon from "@mui/icons-material/Edit";
import MovieIcon from "@mui/icons-material/Movie";
import ChatIcon from "@mui/icons-material/Chat";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
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

function HistorySection({ title, generations, loaded, viewMode, setViewMode, navigate, emptyLabel, createLink }: {
  title: string;
  generations: HistoryGen[];
  loaded: boolean;
  viewMode: "list" | "tiles";
  setViewMode: (v: "list" | "tiles") => void;
  navigate: (p: string) => void;
  emptyLabel: string;
  createLink: string;
}) {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>{title}</Typography>
          <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
            <ToggleButtonGroup value={viewMode} exclusive size="small" onChange={(_, v) => v && setViewMode(v)}>
              <ToggleButton value="list" sx={{ px: 1, py: 0.25, textTransform: "none" }}>
                <ViewListIcon fontSize="small" />
              </ToggleButton>
              <ToggleButton value="tiles" sx={{ px: 1, py: 0.25, textTransform: "none" }}>
                <GridViewIcon fontSize="small" />
              </ToggleButton>
            </ToggleButtonGroup>
            <Button size="small" onClick={() => navigate("/history")}>Все</Button>
          </Box>
        </Box>

        {!loaded ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Box key={i} sx={{ mb: 1.5, display: "flex", gap: 2 }}>
              <Skeleton variant="rounded" width={56} height={56} sx={{ borderRadius: 1.5 }} />
              <Box sx={{ flex: 1 }}>
                <Skeleton variant="text" width="40%" />
                <Skeleton variant="text" width="80%" />
                <Skeleton variant="rounded" width={80} height={24} />
              </Box>
            </Box>
          ))
        ) : generations.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <Typography color="text.secondary" mb={1}>{emptyLabel}</Typography>
            <Button variant="outlined" size="small" onClick={() => navigate(createLink)}>Создать</Button>
          </Box>
        ) : viewMode === "list" ? (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
            {generations.map(g => {
              const thumb = g.images?.[0];
              return (
                <Box key={g.id} onClick={() => navigate("/history")}
                  sx={{ display: "flex", gap: 1.5, p: 1.5, bgcolor: "action.hover", borderRadius: 2, cursor: "pointer" }}>
                  {thumb ? (
                    <Box sx={{ width: 64, height: 64, flexShrink: 0, borderRadius: 1.5, overflow: "hidden", bgcolor: "background.paper" }}>
                      <img src={`/${thumb.file_path}`} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    </Box>
                  ) : (
                    <Box sx={{ width: 64, height: 64, flexShrink: 0, borderRadius: 1.5, bgcolor: "background.paper", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <AutoAwesomeIcon sx={{ fontSize: 20, color: "text.disabled" }} />
                    </Box>
                  )}
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" fontWeight={600} noWrap>{g.workflow_type}</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }} noWrap>{g.prompt}</Typography>
                    <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                      <Chip label={statusLabels[g.status] || g.status} size="small"
                        color={g.status === "completed" ? "success" : g.status === "failed" ? "error" : "default"} />
                      <Typography variant="caption" color="text.secondary">{g.cost} кр.</Typography>
                    </Box>
                  </Box>
                </Box>
              );
            })}
          </Box>
        ) : (
          <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 1.5 }}>
            {generations.map(g => {
              const thumb = g.images?.[0];
              return (
                <Card key={g.id} onClick={() => navigate("/history")} sx={{ cursor: "pointer" }}>
                  {thumb ? (
                    <Box sx={{ width: "100%", height: 120, overflow: "hidden" }}>
                      <img src={`/${thumb.file_path}`} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    </Box>
                  ) : (
                    <Box sx={{ width: "100%", height: 120, display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "action.hover" }}>
                      <AutoAwesomeIcon sx={{ fontSize: 40, color: "text.disabled" }} />
                    </Box>
                  )}
                  <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
                    <Typography variant="body2" fontWeight={600} noWrap gutterBottom>{g.workflow_type}</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }} noWrap>{g.prompt}</Typography>
                    <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                      <Chip label={statusLabels[g.status] || g.status} size="small"
                        color={g.status === "completed" ? "success" : g.status === "failed" ? "error" : "default"} />
                      <Typography variant="caption" color="text.secondary">{g.cost} кр.</Typography>
                    </Box>
                  </CardContent>
                </Card>
              );
            })}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export const DashboardPage = ({ user }: Props) => {
  const navigate = useNavigate();
  const [generations, setGenerations] = useState<HistoryGen[]>([]);
  const [edits, setEdits] = useState<HistoryGen[]>([]);
  const [videos, setVideos] = useState<HistoryGen[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [viewModeGen, setViewModeGen] = useState<"list" | "tiles">(() => (localStorage.getItem("dashGenView") as "list" | "tiles") ?? "list");
  const [viewModeEdit, setViewModeEdit] = useState<"list" | "tiles">(() => (localStorage.getItem("dashEditView") as "list" | "tiles") ?? "list");
  const [viewModeVideo, setViewModeVideo] = useState<"list" | "tiles">(() => (localStorage.getItem("dashVideoView") as "list" | "tiles") ?? "list");

  useEffect(() => {
    localStorage.setItem("dashGenView", viewModeGen);
  }, [viewModeGen]);
  useEffect(() => {
    localStorage.setItem("dashEditView", viewModeEdit);
  }, [viewModeEdit]);
  useEffect(() => {
    localStorage.setItem("dashVideoView", viewModeVideo);
  }, [viewModeVideo]);

  const canGenerate = user.permissions?.includes("generate");
  const canEdit = user.permissions?.includes("edit");
  const canVideo = user.permissions?.includes("video");
  const canChat = user.permissions?.includes("chat");

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [g, e, v] = await Promise.all([
          api("GET", "/generate/history?workflow_type=generate"),
          api("GET", "/generate/history?workflow_type=edit"),
          api("GET", "/generate/history?workflow_type=video"),
        ]);
        setGenerations(((g as any)?.generations || []).slice(0, 6));
        setEdits(((e as any)?.generations || []).slice(0, 6));
        setVideos(((v as any)?.generations || []).slice(0, 6));
      } catch { /* ignore */ }
      setLoaded(true);
    };
    fetchAll();
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
                <Typography variant="h5" fontWeight={700}>{(user.balance ?? 0).toFixed(2)}</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        {canGenerate && (
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card onClick={() => navigate("/generate")} sx={{ cursor: "pointer" }}>
              <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, py: 2.5 }}>
                <Avatar sx={{ bgcolor: "success.main", width: 48, height: 48 }}>
                  <AutoAwesomeIcon />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">Быстрый доступ</Typography>
                  <Typography variant="h6" fontWeight={600}>Генерация</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
        {canEdit && (
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card onClick={() => navigate("/edit")} sx={{ cursor: "pointer" }}>
              <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, py: 2.5 }}>
                <Avatar sx={{ bgcolor: "warning.main", width: 48, height: 48 }}>
                  <EditIcon />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">Быстрый доступ</Typography>
                  <Typography variant="h6" fontWeight={600}>Редактирование</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
        {canVideo && (
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card onClick={() => navigate("/video")} sx={{ cursor: "pointer" }}>
              <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, py: 2.5 }}>
                <Avatar sx={{ bgcolor: "error.main", width: 48, height: 48 }}>
                  <MovieIcon />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">Быстрый доступ</Typography>
                  <Typography variant="h6" fontWeight={600}>Видео</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
        {canChat && (
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
        )}
      </Grid>

      {canGenerate && (
        <HistorySection title="Последние генерации" generations={generations} loaded={loaded}
          viewMode={viewModeGen} setViewMode={setViewModeGen} navigate={navigate}
          emptyLabel="Нет генераций" createLink="/generate" />
      )}
      {canEdit && (
        <HistorySection title="Последние редакции" generations={edits} loaded={loaded}
          viewMode={viewModeEdit} setViewMode={setViewModeEdit} navigate={navigate}
          emptyLabel="Нет редакций" createLink="/edit" />
      )}
      {canVideo && (
        <HistorySection title="Последние видео" generations={videos} loaded={loaded}
          viewMode={viewModeVideo} setViewMode={setViewModeVideo} navigate={navigate}
          emptyLabel="Нет видео" createLink="/video" />
      )}
    </Box>
  );
};