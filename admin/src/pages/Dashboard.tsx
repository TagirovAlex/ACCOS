import { Card, CardContent, Typography, Grid, Box, Button, Skeleton, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Avatar } from "@mui/material";
import { useGetOne, useNotify } from "react-admin";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

const INFO_BOXES = [
  { key: "users", label: "Пользователи", icon: "👥", color: "#448aff", to: "/users" },
  { key: "groups", label: "Группы доступа", icon: "🔐", color: "#43a047", to: "/groups" },
  { key: "chats", label: "Чаты", icon: "💬", color: "#ffa726", to: "/chats" },
  { key: "generations", label: "Генерации", icon: "🎨", color: "#ab47bc", to: "/generations" },
  { key: "assets", label: "Ресурсы", icon: "🖼", color: "#26c6da", to: "/assets" },
  { key: "settings", label: "Настройки", icon: "⚙", color: "#78909c", to: "/settings" },
  { key: "queue", label: "Очередь", icon: "⏳", color: "#ff6f00", to: "/generation-queue" },
];

const StatCard = ({ icon, label, value, color, to, secondary }: { icon: string; label: string; value: number | string | undefined; color: string; to?: string; secondary?: string }) => {
  const nav = useNavigate();
  return (
    <Card
      onClick={() => to && nav(to)}
      sx={{
        cursor: to ? "pointer" : "default",
        transition: "all 0.2s ease",
        "&:hover": to ? { transform: "translateY(-2px)", boxShadow: "0 6px 20px rgba(0,0,0,0.12)" } : {},
      }}
    >
      <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, py: 2.5, "&:last-child": { pb: 2.5 } }}>
        <Box sx={{
          width: 56, height: 56, borderRadius: 2,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 28, bgcolor: color + "18", color: color, flexShrink: 0,
        }}>
          {icon}
        </Box>
        <Box sx={{ minWidth: 0 }}>
          {value === undefined
            ? <Skeleton variant="text" width={60} height={32} />
            : <Typography variant="h5" fontWeight={700} lineHeight={1.2}>{value}</Typography>
          }
          <Typography variant="body2" color="text.secondary" noWrap>{label}</Typography>
          {secondary && <Typography variant="caption" color="text.secondary">{secondary}</Typography>}
        </Box>
      </CardContent>
    </Card>
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

const adminRole = () => localStorage.getItem("admin_role") || "none";
const isSuperAdmin = () => adminRole() === "super_admin";


export const Dashboard = () => {
  const navigate = useNavigate();
  const notify = useNotify();
  const { data: dash, error } = useGetOne("dashboard", { id: "stats" });
  const [activity, setActivity] = useState<{ date: string; count: number }[]>([]);

  useEffect(() => {
    if (error) notify("Ошибка загрузки дашборда: " + (error?.message || "неизвестная"), { type: "error" });
  }, [error, notify]);

  useEffect(() => {
    const token = localStorage.getItem("admin_token") || localStorage.getItem("token");
    if (!token) return;
    fetch("/api/v1/admin/dashboard/activity", { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(d => { if (d?.activity) setActivity(d.activity); }).catch(() => {});
  }, []);

  const d = dash as any;

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={700}>ACCOS Admin</Typography>
        <Typography variant="body2" color="text.secondary">Панель управления системой генерации контента</Typography>
      </Box>

      <Grid container spacing={2} mb={3}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <StatCard icon="👥" label="Всего пользователей" value={d?.users} color="#448aff" to="/users" />
        </Grid>
        {isSuperAdmin() && (
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <StatCard icon="💬" label="Всего чатов" value={d?.chats} color="#ffa726" to="/chats" />
          </Grid>
        )}
        {isSuperAdmin() && (
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <StatCard icon="🎨" label="Генераций сегодня" value={d?.generations_today} color="#ab47bc" secondary="новых генераций" />
          </Grid>
        )}
      </Grid>

      <Grid container spacing={2} mb={3}>
        {INFO_BOXES.filter(box => box.key === "users" || box.key === "settings" || isSuperAdmin()).map(box => (
          <Grid size={{ xs: 6, sm: 4, md: 3, lg: 12 / 7 }} key={box.key}>
            <StatCard icon={box.icon} label={box.label} value={d?.[box.key] ?? ""} color={box.color} to={box.to} />
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2} mb={3}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard icon="📄" label="Документов всего" value={d?.documents} color="#43a047" />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard icon="✅" label="Проиндексировано" value={d?.documents_indexed} color="#2e7d32" />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard icon="📊" label="Токенов ввода" value={d?.total_tokens_input !== undefined ? Number(d.total_tokens_input).toLocaleString() : undefined} color="#ffa000" />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard icon="📊" label="Токенов вывода" value={d?.total_tokens_output !== undefined ? Number(d.total_tokens_output).toLocaleString() : undefined} color="#e65100" />
        </Grid>
      </Grid>

      <Grid container spacing={2} mb={3}>
        {isSuperAdmin() && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                  <Typography variant="h6" fontWeight={600}>Последние генерации</Typography>
                  <Button size="small" onClick={() => navigate("/generations")}>Все</Button>
                </Box>
                {!d?.recent_generations?.length ? (
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
                        {d.recent_generations.map((g: any) => (
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
        )}

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>Последние пользователи</Typography>
                <Button size="small" onClick={() => navigate("/users")}>Все</Button>
              </Box>
              {!d?.recent_users?.length ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 3 }}>Нет пользователей</Typography>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Пользователь</TableCell>
                        <TableCell>Зарегистрирован</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {d.recent_users.map((u: any) => (
                        <TableRow key={u.id} hover sx={{ cursor: "pointer" }} onClick={() => navigate(`/users/${u.id}/show`)}>
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                              <Avatar src={u.avatar_path ? `/${u.avatar_path}` : undefined} sx={{ width: 28, height: 28, fontSize: 14 }}>
                                {(u.full_name || u.username || "?").charAt(0).toUpperCase()}
                              </Avatar>
                              <Box>
                                <Typography variant="body2">{u.full_name || u.username}</Typography>
                                {u.full_name && <Typography variant="caption" color="text.secondary">{u.username}</Typography>}
                              </Box>
                            </Box>
                          </TableCell>
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

      {isSuperAdmin() && (
        <Grid container spacing={2} mb={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                  <Typography variant="h6" fontWeight={600}>Последние чаты</Typography>
                  <Button size="small" onClick={() => navigate("/chats")}>Все</Button>
                </Box>
                {!d?.recent_chats?.length ? (
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
                        {d.recent_chats.map((c: any) => (
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
      )}

      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight={600} mb={2}>Быстрые действия</Typography>
          <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
            <Button variant="contained" onClick={() => navigate("/users/create")} sx={{ px: 3, py: 1 }}>
              + Создать пользователя
            </Button>
            {isSuperAdmin() && (
              <Button variant="outlined" onClick={() => navigate("/groups/create")} sx={{ px: 3, py: 1 }}>
                + Создать группу
              </Button>
            )}
            <Button variant="outlined" onClick={() => navigate("/settings")} sx={{ px: 3, py: 1 }}>
              Настройки
            </Button>
            {isSuperAdmin() && (
              <Button variant="outlined" onClick={() => navigate("/generation-queue")} sx={{ px: 3, py: 1 }}>
                ⏳ Очередь
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
