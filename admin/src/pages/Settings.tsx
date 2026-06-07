import { Edit, SimpleForm, TextInput } from "react-admin";

export const SettingsEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="key" label="Ключ" disabled />
      <TextInput source="value" label="Значение" multiline fullWidth />
      <TextInput source="description" label="Описание" fullWidth />
    </SimpleForm>
  </Edit>
);
