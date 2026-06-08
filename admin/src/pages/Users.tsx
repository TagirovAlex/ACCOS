import { useState } from "react";
import {
  List, Datagrid, TextField, BooleanField, NumberField,
  Edit, SimpleForm, TextInput, NumberInput, BooleanInput, Create,
  ReferenceInput, SelectInput, FunctionField, useRecordContext,
  WithListContext, Pagination, Show, SimpleShowLayout, useRedirect,
  ReferenceField, DateField,
} from "react-admin";
import { Chip, Avatar, ToggleButtonGroup, ToggleButton, Card, CardContent, Box, Typography, Grid as MuiGrid, Button } from "@mui/material";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

const AuthSourceField = ({ record }: { record?: any }) => {
  if (!record) return null;
  return record.auth_source === "ldap"
    ? <Chip label="Доменный" size="small" color="primary" variant="outlined" />
    : <Chip label="Локальный" size="small" variant="outlined" />
};

const PasswordInput = () => {
  const record = useRecordContext();
  if (record?.auth_source === "ldap") return null;
  return (
    <TextInput
      source="password"
      label="Новый пароль"
      type="password"
      helperText="Оставьте пустым, чтобы не менять"
    />
  );
};

const UserAvatarField = ({ record }: { record?: any }) => {
  if (!record) return null;
  const avatarUrl = record.avatar_path ? `/${record.avatar_path}` : null;
  return (
    <Avatar src={avatarUrl || undefined} sx={{ width: 36, height: 36, fontSize: 14 }}>
      {record.full_name?.[0] || record.username?.[0] || "U"}
    </Avatar>
  );
};

const LastLoginField = ({ record }: { record?: any }) => {
  if (!record?.last_login) return <span style={{ color: "#999" }}>—</span>;
  const d = new Date(record.last_login);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const days = Math.floor(diff / (86400000));
  if (days === 0) return <span>{d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>;
  if (days === 1) return <span>Вчера</span>;
  if (days < 7) return <span>{days} дн. назад</span>;
  return <span>{d.toLocaleDateString()}</span>;
};

const UserCard = ({ record }: { record?: any }) => {
  const redirect = useRedirect();
  const avatarUrl = record.avatar_path ? `/${record.avatar_path}` : null;
  return (
    <Card onClick={() => redirect("edit", "users", record.id)}
      sx={{ cursor: "pointer", height: "100%", display: "flex", flexDirection: "column", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}>
      <CardContent sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1, pt: 3 }}>
        <Avatar src={avatarUrl || undefined} sx={{ width: 64, height: 64, fontSize: 24 }}>
          {record.full_name?.[0] || record.username?.[0] || "U"}
        </Avatar>
        <Typography variant="subtitle1" fontWeight={600}>{record.full_name || record.username}</Typography>
        <Typography variant="body2" color="text.secondary">@{record.username}</Typography>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", justifyContent: "center" }}>
          <AuthSourceField record={record} />
          {record.is_admin && <Chip label="Админ" size="small" color="warning" variant="outlined" />}
          {!record.is_active && <Chip label="Отключён" size="small" color="error" variant="outlined" />}
        </Box>
        <Box sx={{ textAlign: "center", mt: 1 }}>
          <Typography variant="body2"><b>{record.balance}</b> MS</Typography>
          {record.last_login && (
            <Typography variant="caption" color="text.secondary">
              Вход: <LastLoginField record={record} />
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

const UserListView = () => (
  <Datagrid rowClick="edit" sx={{ "& .column-avatar": { width: 50 } }}>
    <FunctionField label=" " render={(r: any) => <UserAvatarField record={r} />} />
    <TextField source="username" label="Логин" />
    <TextField source="email" label="Email" />
    <TextField source="full_name" label="Полное имя" />
    <NumberField source="balance" label="Баланс" />
    <FunctionField label="Тип" render={(r: any) => <AuthSourceField record={r} />} />
    <FunctionField label="Последний вход" render={(r: any) => <LastLoginField record={r} />} />
    <BooleanField source="is_admin" label="Админ" />
    <BooleanField source="is_active" label="Активен" />
  </Datagrid>
);

const UserTileView = () => (
  <WithListContext render={({ data }) => (
    <MuiGrid container spacing={2} sx={{ p: 2 }}>
      {data?.map(record => (
        <MuiGrid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={record.id}>
          <UserCard record={record} />
        </MuiGrid>
      ))}
    </MuiGrid>
  )} />
);

export const UserList = () => {
  const [view, setView] = useState<"list" | "tiles">(() => (localStorage.getItem("users_view") as "list" | "tiles") ?? "list");

  return (
    <List
      pagination={<Pagination rowsPerPageOptions={[10, 25, 50, 100]} />}
      perPage={25}
      actions={false}
    >
      <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}>
        <ToggleButtonGroup
          value={view}
          exclusive
          onChange={(_, v) => { if (v) { setView(v); localStorage.setItem("users_view", v); } }}
          size="small"
        >
          <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
          <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
        </ToggleButtonGroup>
      </Box>
      {view === "list" ? <UserListView /> : <UserTileView />}
    </List>
  );
};

export const UserEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="username" label="Логин" disabled />
      <TextInput source="email" label="Email" disabled />
      <TextInput source="full_name" label="Полное имя" />
      <FunctionField
        label="Тип"
        render={(record: any) => <AuthSourceField record={record} />}
      />
      <PasswordInput />
      <NumberInput source="balance" label="Баланс" />
      <ReferenceInput source="group_id" reference="groups" label="Группа AD">
        <SelectInput optionText="name" optionValue="id" emptyText="— Без группы —" />
      </ReferenceInput>
      <TextInput source="permissions" label="Права доступа" helperText="chat — чат, generate — генерация, chat,generate — оба" />
      <BooleanInput source="is_admin" label="Администратор" />
      <BooleanInput source="is_active" label="Активен" />
    </SimpleForm>
  </Edit>
);

const ShowActions = ({ listLabel, listPath }: { listLabel: string; listPath: string }) => {
  const redirect = useRedirect();
  return (
    <Box sx={{ display: "flex", gap: 1, p: 1 }}>
      <Button startIcon={<ArrowBackIcon />} size="small" onClick={() => redirect("list", listPath)}>
        {listLabel}
      </Button>
    </Box>
  );
};

export const UserShow = () => (
  <Show actions={<ShowActions listLabel="← Пользователи" listPath="users" />}>
    <SimpleShowLayout>
      <FunctionField label="Аватар" render={() => <UserAvatarField />} />
      <TextField source="username" label="Логин" />
    <TextField source="email" label="Email" />
      <TextField source="full_name" label="Полное имя" />
      <FunctionField label="Тип" render={() => <AuthSourceField />} />
      <NumberField source="balance" label="Баланс" />
      <TextField source="permissions" label="Права доступа" />
      <BooleanField source="is_admin" label="Администратор" />
      <BooleanField source="is_active" label="Активен" />
      <ReferenceField source="group_id" reference="groups" label="Группа AD">
        <TextField source="name" />
      </ReferenceField>
      <DateField source="created_at" label="Создан" showTime />
      <FunctionField label="Последний вход" render={() => <LastLoginField />} />
    </SimpleShowLayout>
  </Show>
);

export const UserCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="username" label="Логин" required />
      <TextInput source="email" label="Email" />
      <TextInput source="full_name" label="Полное имя" />
      <TextInput source="password" label="Пароль" type="password" required />
      <NumberInput source="balance" label="Начальный баланс" defaultValue={100} />
      <ReferenceInput source="group_id" reference="groups" label="Группа AD">
        <SelectInput optionText="name" optionValue="id" emptyText="— Без группы —" />
      </ReferenceInput>
      <TextInput source="permissions" label="Права доступа" defaultValue="chat" helperText="chat — чат, generate — генерация, chat,generate — оба" />
      <BooleanInput source="is_admin" label="Администратор" defaultValue={false} />
      <BooleanInput source="is_active" label="Активен" defaultValue={true} />
    </SimpleForm>
  </Create>
);
