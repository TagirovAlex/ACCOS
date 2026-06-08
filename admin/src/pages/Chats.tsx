import { List, Datagrid, TextField, BooleanField, DateField, Show, SimpleShowLayout, ReferenceField } from "react-admin";
import { Box, Typography, Paper } from "@mui/material";
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
          </Paper>
        </Box>
      ))}
      </Box>
    </Box>
  );
};

export const ChatList = () => (
  <List>
    <Datagrid rowClick="show">
      <ReferenceField source="user_id" reference="users" label="Пользователь">
        <TextField source="username" />
      </ReferenceField>
      <TextField source="title" label="Название" />
      <BooleanField source="is_active" label="Статус" />
      <DateField source="created_at" label="Создан" />
      <DateField source="updated_at" label="Обновлён" />
    </Datagrid>
  </List>
);

export const ChatShow = () => (
  <Show>
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
