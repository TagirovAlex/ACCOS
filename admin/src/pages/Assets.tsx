import { List, Datagrid, TextField, DateField } from "react-admin";

export const AssetList = () => (
  <List>
    <Datagrid>
      <TextField source="user_id" label="ID пользователя" />
      <TextField source="filename" label="Файл" />
      <TextField source="generation_id" label="ID генерации" />
      <DateField source="created_at" label="Создан" />
    </Datagrid>
  </List>
);
