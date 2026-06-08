import { List, Datagrid, TextField, DateField, NumberField, Show, SimpleShowLayout, ReferenceField } from "react-admin";
import { Box } from "@mui/material";
import { useRecordContext } from "react-admin";

const ImagePreview = () => {
  const record = useRecordContext();
  if (!record?.file_path) return null;
  return (
    <Box sx={{ mt: 1 }}>
      <img src={`/${record.file_path}`} alt={record.filename}
        style={{ maxWidth: "100%", maxHeight: 400, borderRadius: 8, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
        onError={(e: any) => { e.target.style.display = "none"; }} />
    </Box>
  );
};

export const AssetList = () => (
  <List>
    <Datagrid rowClick="show">
      <ReferenceField source="user_id" reference="users" label="Пользователь">
        <TextField source="username" />
      </ReferenceField>
      <TextField source="filename" label="Файл" />
      <ReferenceField source="generation_id" reference="generations" label="Генерация">
        <TextField source="id" />
      </ReferenceField>
      <NumberField source="file_size" label="Размер" />
      <DateField source="created_at" label="Создан" />
    </Datagrid>
  </List>
);

export const AssetShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="filename" label="Файл" />
      <TextField source="file_path" label="Путь" />
      <ReferenceField source="user_id" reference="users" label="Пользователь">
        <TextField source="username" />
      </ReferenceField>
      <ReferenceField source="generation_id" reference="generations" label="Генерация">
        <TextField source="id" />
      </ReferenceField>
      <NumberField source="file_size" label="Размер (байт)" />
      <NumberField source="width" label="Ширина" />
      <NumberField source="height" label="Высота" />
      <DateField source="created_at" label="Создан" />
      <ImagePreview />
    </SimpleShowLayout>
  </Show>
);
