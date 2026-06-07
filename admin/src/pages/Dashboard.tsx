import { Card, CardContent, Typography } from "@mui/material";
import { useGetList } from "react-admin";

export const Dashboard = () => {
  const { total: users } = useGetList("users");
  const { total: groups } = useGetList("groups");
  const { total: chats } = useGetList("chats");
  const { total: generations } = useGetList("generations");

  return (
    <Card>
      <CardContent>
        <Typography variant="h5">ACCOS Admin</Typography>
        <Typography>Users: {users ?? "..."}</Typography>
        <Typography>Groups: {groups ?? "..."}</Typography>
        <Typography>Chats: {chats ?? "..."}</Typography>
        <Typography>Generations: {generations ?? "..."}</Typography>
      </CardContent>
    </Card>
  );
};
