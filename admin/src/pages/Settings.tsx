import { List, Datagrid, TextField, Edit, SimpleForm, TextInput, Create } from "react-admin";

export const SettingsList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="key" label="Ключ" />
      <TextField source="value" label="Значение" />
      <TextField source="description" label="Описание" />
    </Datagrid>
  </List>
);

export const SettingsEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="key" label="Ключ" disabled />
      <TextInput source="value" label="Значение" multiline fullWidth />
      <TextInput source="description" label="Описание" fullWidth />
    </SimpleForm>
  </Edit>
);

export const SettingsCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="key" label="Ключ" required />
      <TextInput source="value" label="Значение" multiline fullWidth required />
      <TextInput source="description" label="Описание" fullWidth />
    </SimpleForm>
  </Create>
);
