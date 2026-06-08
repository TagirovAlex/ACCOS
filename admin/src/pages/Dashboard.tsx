import { Card, CardContent, Typography, Grid, Box, Button, Skeleton } from "@mui/material";
import { useGetList } from "react-admin";
import { useNavigate } from "react-router-dom";

const INFO_BOXES = [
  { resource: "users", label: "Пользователи", icon: "👥", color: "#448aff", to: "/users" },
  { resource: "groups", label: "Группы доступа", icon: "🔐", color: "#43a047", to: "/groups" },
  { resource: "chats", label: "Чаты", icon: "💬", color: "#ffa726", to: "/chats" },
  { resource: "generations", label: "Генерации", icon: "🎨", color: "#ab47bc", to: "/generations" },
  { resource: "assets", label: "Ресурсы", icon: "🖼", color: "#26c6da", to: "/assets" },
  { resource: "settings", label: "Настройки", icon: "⚙", color: "#78909c", to: "/settings" },
];

const InfoBox = ({ icon, label, value, color, to }: { icon: string; label: string; value: number | undefined; color: string; to?: string }) => {
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
      </Box>
    </Box>
  );
};

export const Dashboard = () => {
  const navigate = useNavigate();
  const { total: users } = useGetList("users", { pagination: { page: 1, perPage: 1 } });
  const { total: groups } = useGetList("groups", { pagination: { page: 1, perPage: 1 } });
  const { total: chats } = useGetList("chats", { pagination: { page: 1, perPage: 1 } });
  const { total: generations } = useGetList("generations", { pagination: { page: 1, perPage: 1 } });
  const { total: assets } = useGetList("assets", { pagination: { page: 1, perPage: 1 } });

  const totals: Record<string, number | undefined> = { users, groups, chats, generations, assets };

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={700}>ACCOS Admin</Typography>
        <Typography variant="body2" color="text.secondary">Панель управления системой генерации контента</Typography>
      </Box>

      <Grid container spacing={2} mb={4}>
        {INFO_BOXES.map(box => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={box.resource}>
            <InfoBox
              icon={box.icon}
              label={box.label}
              value={totals[box.resource]}
              color={box.color}
              to={box.to}
            />
          </Grid>
        ))}
      </Grid>

      <Card sx={{ mb: 3 }}>
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
