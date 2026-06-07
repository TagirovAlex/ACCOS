import { Box, Card, CardContent, Typography, Grid } from "@mui/material";
import type { User } from "../services/auth";

interface Props {
  user: User;
}

export const DashboardPage = ({ user }: Props) => (
  <Box>
    <Typography variant="h5" mb={3}>Дашборд</Typography>
    <Grid container spacing={2}>
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
  </Box>
);
