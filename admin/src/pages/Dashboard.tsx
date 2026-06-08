import { Card, CardContent, Typography, Grid, Box, Button, Skeleton, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from "@mui/material";
import { useGetOne } from "react-admin";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

const INFO_BOXES = [
  { key: "users", label: "Пользователи", icon: "👥", color: "#448aff", to: "/users" },
  { key: "groups", label: "Группы доступа", icon: "🔐", color: "#43a047", to: "/groups" },
  { key: "chats", label: "Чаты", icon: "💬", color: "#ffa726", to: "/chats" },
  { key: "generations", label: "Генерации", icon: "🎨", color: "#ab47bc", to: "/generations" },
  { key: "assets", label: "Ресурсы", icon: "🖼", color: "#26c6da", to: "/assets" },
  { key: "settings", label: "Настройки", icon: "⚙", color: "#78909c", to: "/settings" },
];

const InfoBox = ({ icon, label, value, secondary, color, to }: { icon: string; label: string; value: number | undefined; secondary?: string; color: string; to?: string }) => {
  const nav = useNavigate();
  return (
    <Box
      onClick={() => to && nav(to)}
      sx={{
        display: "flex", bgcolor: "background.paper",
        border: 1, borderColor: "divider", borderRadius: 1,
        cursor: to ? "pointer" : "default",
        transition: "all 0.15s ease",
        "&:hover": to ? { boxShadow: "0 4px 12px rgba(0,0,0,0.12)" } : {},
      }}
    >
      <Box sx={{
        width: 80, minHeight: 80,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 32, bgcolor: color, color: "#fff",
      }}>
        {icon}
      </Box>
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", px: 2 }}>
        {value === undefined
          ? <Skeleton variant="text" width={50} height={32} />
          : <Typography variant="h5" fontWeight={700} lineHeight={1.2}>{value}</Typography>
        }
        <Typography variant="body2" color="text.secondary" fontSize="0.85rem">{label}</Typography>
        {secondary && <Typography variant="caption" color="text.secondary">{secondary}</Typography>}
      </Box>
    </Box>
  );
};

const ActivityChart = ({ data }: { data: { date: string; count: number }[] }) => {
  if (!data || data.length === 0) return <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 4 }}>Нет данных</Typography>;
  const maxCount = Math.max(...data.map(d => d.count), 1);
  return (
    <Box sx={{ display: "flex", alignItems: "flex-end", gap: 0.5, height: 120, pt: 2, pb: 1 }}>
      {data.map(d => (
        <Box key={d.date} sx={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 0.5 }}>
          <Typography variant="caption" fontSize={10} fontWeight={600}>{d.count || ""}</Typography>
          <Box sx={{
            width: "100%", bgcolor: "#ab47bc", borderRadius: "4px 4px 0 0",
            height: `${Math.max((d.count / maxCount) * 80, 4)}px`,
            opacity: 0.8, transition: "height 0.3s",
          }} />
          <Typography variant="caption" fontSize={9} color="text.secondary" sx={{ writingMode: "vertical-lr", transform: "rotate(180deg)", fontSize: 8 }}>
            {d.date.slice(5)}
          </Typography>
        </Box>
      ))}
    </Box>
  );
};

const statusLabels: Record<string, string> = {
  queued: "В очереди", processing: "Обработка", completed: "Завершено", failed: "Ошибка",
};

const statusColors: Record<string, "default" | "primary" | "success" | "error" | "info" | "warning"> = {
  queued: "default", processing: "info", completed: "success", failed: "error",
};

export const Dashboard = () => {
  const navigate = useNavigate();
  const { data: dash } = useGetOne("dashboard", { id: "stats" });
  const [activity, setActivity] = useState<{ date: string; count: number }[]>([]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    fetch("/api/v1/admin/dashboard/activity", { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(d => { if (d?.activity) setActivity(d.activity); }).catch(() => {});
  }, []);

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={700}>ACCOS Admin</Typography>
        <Typography variant="body2" color="text.secondary">Панель управления системой генерации контента</Typography>
      </Box>

      <Grid container spacing={2} mb={4}>
        {INFO_BOXES.map(box => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={box.key}>
            <InfoBox
              icon={box.icon}
              label={box.label}
              value={(dash as any)?.[box.key]}
              color={box.color}
              to={box.to}
            />
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2} mb={4}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <InfoBox icon="🎨" label="За сегодня" value={(dash as any)?.generations_today} color="#ab47bc" secondary="новых генераций" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <InfoBox icon="🖼" label="Всего ресурсов" value={(dash as any)?.assets} color="#26c6da" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <InfoBox icon="💬" label="Всего чатов" value={(dash as any)?.chats} color="#ffa726" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <InfoBox icon="👥" label="Всего пользователей" value={(dash as any)?.users} color="#448aff" />
        </Grid>
      </Grid>

      <Grid container spacing={2} mb={4}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>Последние генерации</Typography>
                <Button size="small" onClick={() => navigate("/generations")}>Все</Button>
              </Box>
              {!(dash as any)?.recent_generations?.length ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 3 }}>Нет генераций</Typography>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Тип</TableCell>
                        <TableCell>Статус</TableCell>
                        <TableCell>Время</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(dash as any).recent_generations.map((g: any) => (
                        <TableRow key={g.id} hover sx={{ cursor: "pointer" }} onClick={() => navigate(`/generations/${g.id}/show`)}>
                          <TableCell>{g.workflow_type}</TableCell>
                          <TableCell><Chip label={statusLabels[g.status] || g.status} size="small" color={statusColors[g.status] || "default"} /></TableCell>
                          <TableCell><Typography variant="caption">{new Date(g.created_at).toLocaleString()}</Typography></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>Последние пользователи</Typography>
                <Button size="small" onClick={() => navigate("/users")}>Все</Button>
              </Box>
              {!(dash as any)?.recent_users?.length ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 3 }}>Нет пользователей</Typography>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Имя</TableCell>
                        <TableCell>Зарегистрирован</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(dash as any).recent_users.map((u: any) => (
                        <TableRow key={u.id} hover sx={{ cursor: "pointer" }} onClick={() => navigate(`/users/${u.id}/show`)}>
                          <TableCell>{u.username}</TableCell>
                          <TableCell><Typography variant="caption">{new Date(u.created_at).toLocaleString()}</Typography></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2} mb={4}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>Последние чаты</Typography>
                <Button size="small" onClick={() => navigate("/chats")}>Все</Button>
              </Box>
              {!(dash as any)?.recent_chats?.length ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 3 }}>Нет чатов</Typography>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Название</TableCell>
                        <TableCell>Создан</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(dash as any).recent_chats.map((c: any) => (
                        <TableRow key={c.id} hover sx={{ cursor: "pointer" }} onClick={() => navigate(`/chats/${c.id}/show`)}>
                          <TableCell>{c.title}</TableCell>
                          <TableCell><Typography variant="caption">{new Date(c.created_at).toLocaleString()}</Typography></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={2}>Активность генераций (14 дней)</Typography>
              <ActivityChart data={activity} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight={600} mb={2}>Быстрые действия</Typography>
          <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
            <Button variant="contained" onClick={() => navigate("/users/create")} sx={{ px: 3, py: 1 }}>
              + Создать пользователя
            </Button>
            <Button variant="outlined" onClick={() => navigate("/groups/create")} sx={{ px: 3, py: 1 }}>
              + Создать группу
            </Button>
            <Button variant="outlined" onClick={() => navigate("/settings")} sx={{ px: 3, py: 1 }}>
              Настройки
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
