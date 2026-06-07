import { List, Datagrid, TextField, EmailField, BooleanField, NumberField, Edit, SimpleForm, TextInput, NumberInput, Create } from "react-admin";

export const UserList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="username" label="Логин" />
      <EmailField source="email" label="Email" />
      <NumberField source="balance" label="Баланс" />
      <BooleanField source="is_admin" label="Админ" />
      <BooleanField source="is_active" label="Активен" />
    </Datagrid>
  </List>
);

export const UserEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="username" label="Логин" disabled />
      <TextInput source="email" label="Email" disabled />
      <NumberInput source="balance" label="Баланс" />
      <TextInput source="permissions" label="Права" />
    </SimpleForm>
  </Edit>
);

export const UserCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="username" label="Логин" required />
      <TextInput source="email" label="Email" required />
      <NumberInput source="balance" label="Начальный баланс" defaultValue={0} />
    </SimpleForm>
  </Create>
);
