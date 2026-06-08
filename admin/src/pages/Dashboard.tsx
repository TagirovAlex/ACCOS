import { Card, CardContent, Typography, Grid, Box, Button, Skeleton } from "@mui/material";
import { useGetList } from "react-admin";
import { useNavigate } from "react-router-dom";
import PeopleIcon from "@mui/icons-material/People";
import GroupIcon from "@mui/icons-material/Group";
import ChatIcon from "@mui/icons-material/Chat";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import ImageIcon from "@mui/icons-material/Image";

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number | string | undefined;
  gradient: string;
  to?: string;
}

const StatCard = ({ icon, label, value, gradient, to }: StatCardProps) => {
  const nav = useNavigate();
  return (
    <Grid size={{ xs: 12, sm: 6, md: 4 }}>
      <Card
        onClick={() => to && nav(to)}
        sx={{
          position: "relative", overflow: "hidden", border: "none", borderRadius: 3,
          cursor: to ? "pointer" : "default",
          transition: "transform 0.15s ease, box-shadow 0.15s ease",
          "&:hover": to ? { transform: "translateY(-2px)", boxShadow: 4 } : {},
        }}
      >
        <Box sx={{
          position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
          background: gradient, opacity: 0.08,
        }} />
        <CardContent sx={{ position: "relative", display: "flex", alignItems: "center", gap: 2.5, py: 3, px: 3 }}>
          <Box sx={{
            width: 56, height: 56, borderRadius: 2.5, display: "flex", alignItems: "center", justifyContent: "center",
            background: gradient, color: "#fff", fontSize: 28,
          }}>
            {icon}
          </Box>
          <Box>
            {value === undefined
              ? <Skeleton variant="text" width={60} height={40} />
              : <Typography variant="h4" fontWeight={700}>{value}</Typography>
            }
            <Typography variant="body2" color="text.secondary" fontWeight={500}>{label}</Typography>
          </Box>
        </CardContent>
      </Card>
    </Grid>
  );
};

export const Dashboard = () => {
  const navigate = useNavigate();
  const { total: users } = useGetList("users", { pagination: { page: 1, perPage: 1 } });
  const { total: groups } = useGetList("groups", { pagination: { page: 1, perPage: 1 } });
  const { total: chats } = useGetList("chats", { pagination: { page: 1, perPage: 1 } });
  const { total: generations } = useGetList("generations", { pagination: { page: 1, perPage: 1 } });
  const { total: assets } = useGetList("assets", { pagination: { page: 1, perPage: 1 } });

  return (
    <Box>
      <Typography variant="h5" mb={0.5}>ACCOS Admin</Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>Панель управления системой генерации контента</Typography>

      <Grid container spacing={2.5} mb={4}>
        <StatCard icon={<PeopleIcon fontSize="large" />} label="Пользователи" value={users ?? "..."} gradient="linear-gradient(135deg, #448aff 0%, #7c4dff 100%)" to="/users" />
        <StatCard icon={<GroupIcon fontSize="large" />} label="Группы доступа" value={groups ?? "..."} gradient="linear-gradient(135deg, #43a047 0%, #00bfa5 100%)" to="/groups" />
        <StatCard icon={<ChatIcon fontSize="large" />} label="Чаты" value={chats ?? "..."} gradient="linear-gradient(135deg, #ffa726 0%, #ff7043 100%)" to="/chats" />
        <StatCard icon={<AutoAwesomeIcon fontSize="large" />} label="Генерации" value={generations ?? "..."} gradient="linear-gradient(135deg, #ab47bc 0%, #e040fb 100%)" to="/generations" />
        <StatCard icon={<ImageIcon fontSize="large" />} label="Ресурсы (изображения)" value={assets ?? "..."} gradient="linear-gradient(135deg, #26c6da 0%, #448aff 100%)" to="/assets" />
      </Grid>

      <Typography variant="h6" mb={2}>Быстрые действия</Typography>
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
    </Box>
  );
};
