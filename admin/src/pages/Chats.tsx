import { List, Datagrid, TextField, DateField } from "react-admin";

export const ChatList = () => (
  <List>
    <Datagrid>
      <TextField source="username" label="Пользователь" />
      <TextField source="title" label="Название" />
      <TextField source="is_active" label="Статус" />
      <DateField source="created_at" label="Создан" />
      <DateField source="updated_at" label="Обновлён" />
    </Datagrid>
  </List>
);
