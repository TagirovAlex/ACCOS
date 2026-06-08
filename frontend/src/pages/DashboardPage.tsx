import { useState, useEffect } from "react";
import { Box, Card, CardContent, Typography, Grid, Chip, Button, Skeleton } from "@mui/material";
import { useNavigate } from "react-router-dom";
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
      <Typography variant="h5" mb={3}>Дашборд</Typography>
      <Grid container spacing={2} mb={4}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Баланс</Typography>
              <Typography variant="h4">{user.balance} кредитов</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Пользователь</Typography>
              <Typography variant="h6">{user.username}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Права доступа</Typography>
              <Typography variant="h6">{user.permissions || "full"}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h6">История генераций</Typography>
        <Button size="small" onClick={() => navigate("/generate")}>Все генерации</Button>
      </Box>

      {!loaded ? (
        Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} sx={{ mb: 1.5 }}>
            <CardContent sx={{ display: "flex", gap: 2, py: 1.5 }}>
              <Skeleton variant="rounded" width={64} height={64} />
              <Box sx={{ flex: 1 }}>
                <Skeleton variant="text" width="40%" />
                <Skeleton variant="text" width="80%" />
                <Skeleton variant="rounded" width={80} height={24} />
              </Box>
            </CardContent>
          </Card>
        ))
      ) : generations.length === 0 ? (
        <Typography color="text.secondary">Нет генераций</Typography>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          {generations.map(g => {
            const thumbnail = g.images?.[0];
            return (
              <Card key={g.id} sx={{ cursor: "pointer" }} onClick={() => navigate("/generate")}>
                <CardContent sx={{ display: "flex", gap: 2, alignItems: "center", py: 1.5 }}>
                  {thumbnail ? (
                    <Box sx={{ width: 64, height: 64, flexShrink: 0, borderRadius: 1, overflow: "hidden", bgcolor: "action.hover" }}>
                      <img src={`/${thumbnail.file_path}`} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    </Box>
                  ) : (
                    <Box sx={{ width: 64, height: 64, flexShrink: 0, borderRadius: 1, bgcolor: "action.hover", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Typography variant="h6" color="text.disabled">?</Typography>
                    </Box>
                  )}
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" fontWeight={600} noWrap>{g.workflow_type}</Typography>
                    <Typography variant="body2" color="text.secondary" noWrap sx={{ mt: 0.25 }}>{g.prompt}</Typography>
                    <Box sx={{ display: "flex", gap: 1, mt: 0.5, alignItems: "center" }}>
                      <Chip label={g.status} size="small" color={g.status === "completed" ? "success" : g.status === "failed" ? "error" : "default"} />
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
