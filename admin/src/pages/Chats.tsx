import { useState } from "react";
import { List, Datagrid, TextField, BooleanField, DateField, Show, SimpleShowLayout, ReferenceField, WithListContext, useRedirect, useDelete, DeleteButton } from "react-admin";
import { Box, Typography, Paper, Card, CardContent, ToggleButtonGroup, ToggleButton, Grid as MuiGrid, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button, IconButton } from "@mui/material";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
import DeleteIcon from "@mui/icons-material/Delete";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useRecordContext } from "react-admin";

const MessagesList = () => {
  const record = useRecordContext();
  const count = record?.messages?.length || 0;
  if (!record || !count) return <Typography color="text.secondary" sx={{ mt: 1 }}>Нет сообщений</Typography>;
  return (
    <Box>
      <Typography variant="h6" sx={{ mt: 2 }}>Сообщения ({count})</Typography>
      <Box sx={{ maxHeight: 400, overflow: "auto", display: "flex", flexDirection: "column", gap: 1, mt: 1 }}>
      {record.messages.map((m: any) => (
        <Box key={m.id} sx={{ textAlign: m.role === "user" ? "right" : "left" }}>
          <Paper sx={{ display: "inline-block", p: 1, maxWidth: "80%", bgcolor: (t) => m.role === "user" ? t.palette.primary.dark : t.palette.grey[t.palette.mode === "dark" ? 800 : 100], color: m.role === "user" ? "primary.contrastText" : "text.primary" }}>
            <Typography variant="caption" fontWeight={600}>{m.role === "user" ? "Пользователь" : "Ассистент"}</Typography>
            <Typography variant="body2" sx={{ mt: 0.25, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{m.content}</Typography>
            {m.cost != null && <Typography variant="caption" color="text.secondary">{m.cost} MS</Typography>}
            {m.tokens_input != null && <Typography variant="caption" color="text.secondary">input: {m.tokens_input} · output: {m.tokens_output}</Typography>}
          </Paper>
        </Box>
      ))}
      </Box>
    </Box>
  );
};

const ChatListView = () => (
  <Datagrid rowClick="show">
    <ReferenceField source="user_id" reference="users" label="Пользователь">
      <TextField source="username" />
    </ReferenceField>
    <TextField source="title" label="Название" />
    <BooleanField source="is_active" label="Статус" />
    <DateField source="created_at" label="Создан" />
    <DateField source="updated_at" label="Обновлён" />
  </Datagrid>
);

const ChatTileView = () => {
  const redirect = useRedirect();
  const [deleteOne] = useDelete();
  const [deleteTarget, setDeleteTarget] = useState<any>(null);
  return (
  <>
  <WithListContext render={({ data }) => (
    <MuiGrid container spacing={2} sx={{ p: 2 }}>
      {data?.map((record: any) => (
        <MuiGrid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={record.id}>
          <Card sx={{ position: "relative", cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}>
            <IconButton size="small"
              sx={{ position: "absolute", top: 4, right: 4, zIndex: 1, color: "error.light" }}
              onClick={(e) => { e.stopPropagation(); setDeleteTarget(record); }}>
              <DeleteIcon fontSize="small" />
            </IconButton>
            <CardContent onClick={() => redirect("show", "chats", record.id)}>
              <Typography variant="body2" fontWeight={600} noWrap>{record.title || "(без названия)"}</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>{record.username}</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                {record.is_active ? "Активен" : "Неактивен"} · {new Date(record.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>
        </MuiGrid>
      ))}
    </MuiGrid>
  )} />
  <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
    <DialogTitle>Удалить чат?</DialogTitle>
    <DialogContent>
      <DialogContentText>Чат «{deleteTarget?.title || "(без названия)"}» будет удалён без возможности восстановления.</DialogContentText>
    </DialogContent>
    <DialogActions>
      <Button onClick={() => setDeleteTarget(null)}>Отмена</Button>
      <Button onClick={() => { deleteOne("chats", { id: deleteTarget?.id }); setDeleteTarget(null); }} color="error">Удалить</Button>
    </DialogActions>
  </Dialog>
  </>
  );
};

export const ChatList = () => {
  const [view, setView] = useState<"list" | "tiles">(() => (localStorage.getItem("chats_view") as "list" | "tiles") ?? "list");
  return (
    <List actions={false}>
      <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}>
        <ToggleButtonGroup value={view} exclusive size="small" onChange={(_, v) => { if (v) { setView(v); localStorage.setItem("chats_view", v); } }}>
          <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
          <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
        </ToggleButtonGroup>
      </Box>
      {view === "list" ? <ChatListView /> : <ChatTileView />}
    </List>
  );
};

const ChatShowActions = () => {
  const redirect = useRedirect();
  return (
    <Box sx={{ display: "flex", gap: 1, p: 1 }}>
      <Button startIcon={<ArrowBackIcon />} size="small" onClick={() => redirect("list", "chats")}>
        ← Чаты
      </Button>
      <DeleteButton mutationMode="pessimistic" />
    </Box>
  );
};

export const ChatShow = () => (
  <Show actions={<ChatShowActions />}>
    <SimpleShowLayout>
      <TextField source="title" label="Название" />
      <ReferenceField source="user_id" reference="users" label="Пользователь">
        <TextField source="username" />
      </ReferenceField>
      <BooleanField source="is_active" label="Статус" />
      <TextField source="system_prompt" label="Системный промпт" />
      <DateField source="created_at" label="Создан" />
      <DateField source="updated_at" label="Обновлён" />
      <MessagesList />
    </SimpleShowLayout>
  </Show>
);
