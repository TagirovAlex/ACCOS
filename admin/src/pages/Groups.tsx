import { List, Datagrid, TextField, NumberField, Edit, SimpleForm, TextInput, NumberInput, BooleanInput, Create } from "react-admin";

export const GroupList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="name" label="Название" />
      <TextField source="ad_group_dn" label="AD группа" />
      <TextField source="permissions" label="Права" />
      <NumberField source="start_balance" label="Стартовый баланс" />
    </Datagrid>
  </List>
);

export const GroupEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="name" label="Название" fullWidth />
      <TextInput source="ad_group_dn" label="AD группа" fullWidth />
      <TextInput source="permissions" label="Права" fullWidth />
      <NumberInput source="start_balance" label="Стартовый баланс" />
      <BooleanInput source="is_active" label="Активна" />
    </SimpleForm>
  </Edit>
);

export const GroupCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="name" label="Название" required fullWidth />
      <TextInput source="ad_group_dn" label="AD группа" required fullWidth />
      <TextInput source="permissions" label="Права" required fullWidth />
      <NumberInput source="start_balance" label="Стартовый баланс" defaultValue={0} />
    </SimpleForm>
  </Create>
);
