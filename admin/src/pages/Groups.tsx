import { useState, useEffect } from "react";
import { List, Datagrid, TextField, NumberField, Edit, SimpleForm, TextInput, NumberInput, BooleanInput, Create, AutocompleteInput, useNotify } from "react-admin";
import { getToken } from "../services/api";

const API_BASE = "/api/v1/admin/ldap-groups";

const AdGroupInput = (props: any) => {
  const [choices, setChoices] = useState<{ id: string; name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const notify = useNotify();

  useEffect(() => {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    fetch(API_BASE, { headers })
      .then(res => res.json())
      .then(data => {
        if (data.success && data.groups) {
          setChoices(data.groups.map((g: any) => ({ id: g.dn, name: `${g.cn} — ${g.dn}` })));
        }
        setLoading(false);
      })
      .catch(() => {
        notify("Не удалось загрузить группы AD", { type: "warning" });
        setLoading(false);
      });
  }, []);

  return <AutocompleteInput choices={choices} isLoading={loading} {...props} />;
};

export const GroupList = () => (
  <List>
    <Datagrid rowClick="edit">
      <TextField source="name" label="Название" />
      <TextField source="ad_group_dn" label="AD группа" />
      <TextField source="permissions" label="Права" />
      <NumberField source="start_balance" label="Стартовый баланс" />
      <TextField source="description" label="Описание" />
    </Datagrid>
  </List>
);

export const GroupEdit = () => (
  <Edit>
    <SimpleForm>
      <TextInput source="name" label="Название" fullWidth />
      <AdGroupInput source="ad_group_dn" label="AD группа (DN)" fullWidth />
      <TextInput source="permissions" label="Права доступа" fullWidth helperText="chat — чат, generate — генерация, chat,generate — оба" />
      <NumberInput source="start_balance" label="Стартовый баланс" />
      <TextInput source="description" label="Описание" fullWidth multiline rows={2} />
      <BooleanInput source="is_active" label="Активна" />
    </SimpleForm>
  </Edit>
);

export const GroupCreate = () => (
  <Create>
    <SimpleForm>
      <TextInput source="name" label="Название" required fullWidth />
      <AdGroupInput source="ad_group_dn" label="AD группа (DN)" required fullWidth />
      <TextInput source="permissions" label="Права доступа" required fullWidth helperText="chat — чат, generate — генерация, chat,generate — оба" />
      <NumberInput source="start_balance" label="Стартовый баланс" defaultValue={0} />
      <TextInput source="description" label="Описание" fullWidth multiline rows={2} />
    </SimpleForm>
  </Create>
);
