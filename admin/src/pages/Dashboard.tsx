import { Card, CardContent, Typography, Grid, Box, Button, Skeleton } from "@mui/material";
import { useGetList } from "react-admin";
import PeopleIcon from "@mui/icons-material/People";
import GroupIcon from "@mui/icons-material/Group";
import ChatIcon from "@mui/icons-material/Chat";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import ImageIcon from "@mui/icons-material/Image";
import { useNavigate } from "react-router-dom";

const StatCard = ({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number | string | undefined; color: string }) => (
  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
    <Card sx={{ borderLeft: 4, borderColor: color }}>
      <CardContent sx={{ display: "flex", alignItems: "center", gap: 2 }}>
        <Box sx={{ color }}>{icon}</Box>
        <Box>
          {value === undefined ? <Skeleton variant="text" width={60} height={40} /> : <Typography variant="h4">{value}</Typography>}
          <Typography variant="body2" color="text.secondary">{label}</Typography>
        </Box>
      </CardContent>
    </Card>
  </Grid>
);

export const Dashboard = () => {
  const navigate = useNavigate();
  const { total: users } = useGetList("users", { pagination: { page: 1, perPage: 1 } });
  const { total: groups } = useGetList("groups", { pagination: { page: 1, perPage: 1 } });
  const { total: chats } = useGetList("chats", { pagination: { page: 1, perPage: 1 } });
  const { total: generations } = useGetList("generations", { pagination: { page: 1, perPage: 1 } });
  const { total: assets } = useGetList("assets", { pagination: { page: 1, perPage: 1 } });

  return (
    <Box>
      <Typography variant="h5" mb={3}>ACCOS Admin</Typography>
      <Grid container spacing={2} mb={3}>
        <StatCard icon={<PeopleIcon fontSize="large" />} label="Пользователи" value={users ?? "..."} color="#1976d2" />
        <StatCard icon={<GroupIcon fontSize="large" />} label="Группы доступа" value={groups ?? "..."} color="#388e3c" />
        <StatCard icon={<ChatIcon fontSize="large" />} label="Чаты" value={chats ?? "..."} color="#f57c00" />
        <StatCard icon={<AutoAwesomeIcon fontSize="large" />} label="Генерации" value={generations ?? "..."} color="#7b1fa2" />
        <StatCard icon={<ImageIcon fontSize="large" />} label="Ресурсы (изображения)" value={assets ?? "..."} color="#00796b" />
      </Grid>

      <Typography variant="h6" mb={2}>Быстрые действия</Typography>
      <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
        <Button variant="contained" onClick={() => navigate("/users/create")}>+ Создать пользователя</Button>
        <Button variant="outlined" onClick={() => navigate("/groups/create")}>+ Создать группу</Button>
        <Button variant="outlined" onClick={() => navigate("/settings/create")}>+ Добавить настройку</Button>
      </Box>
    </Box>
  );
};
