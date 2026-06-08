import { List, Datagrid, TextField, EmailField, BooleanField, NumberField, Edit, SimpleForm, TextInput, NumberInput, BooleanInput, Create } from "react-admin";

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
      <TextInput source="password" label="Новый пароль" type="password" helperText="Оставьте пустым, чтобы не менять" />
      <NumberInput source="balance" label="Баланс" />
      <TextInput source="permissions" label="Права" />
      <BooleanInput source="is_admin" label="Администратор" />
      <BooleanInput source="is_active" label="Активен" />
    </SimpleForm>
  </Edit>
);

export const UserCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="username" label="Логин" required />
      <TextInput source="email" label="Email" />
      <TextInput source="password" label="Пароль" type="password" required />
      <NumberInput source="balance" label="Начальный баланс" defaultValue={100} />
      <TextInput source="permissions" label="Права" defaultValue="chat" />
      <BooleanInput source="is_admin" label="Администратор" defaultValue={false} />
      <BooleanInput source="is_active" label="Активен" defaultValue={true} />
    </SimpleForm>
  </Create>
);
