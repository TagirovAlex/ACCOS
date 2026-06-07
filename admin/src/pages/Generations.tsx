import { List, Datagrid, TextField, DateField, NumberField } from "react-admin";

export const GenerationList = () => (
  <List>
    <Datagrid>
      <TextField source="username" label="Пользователь" />
      <TextField source="workflow_type" label="Тип" />
      <TextField source="status" label="Статус" />
      <NumberField source="cost" label="Стоимость" />
      <DateField source="created_at" label="Создана" />
    </Datagrid>
  </List>
);
