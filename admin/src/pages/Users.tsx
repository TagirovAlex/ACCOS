import {
  List, Datagrid, TextField, EmailField, BooleanField, NumberField,
  Edit, SimpleForm, TextInput, NumberInput, BooleanInput, Create,
  ReferenceInput, SelectInput,
} from "react-admin";

export const UserList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="username" label="Логин" />
      <EmailField source="email" label="Email" />
      <TextField source="full_name" label="Полное имя" />
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
      <TextInput source="full_name" label="Полное имя" />
      <TextInput source="password" label="Новый пароль" type="password" helperText="Оставьте пустым, чтобы не менять" />
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
