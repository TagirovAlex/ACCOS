import { List, Datagrid, TextField, DateField, NumberField, Show, SimpleShowLayout, ReferenceField } from "react-admin";
import { Box, Typography } from "@mui/material";
import { useRecordContext } from "react-admin";

const ImagesGrid = () => {
  const record = useRecordContext();
  const images = record?.images || [];
  if (!images.length) return <Typography color="text.secondary" sx={{ mt: 1 }}>Нет изображений</Typography>;
  return (
    <Box>
      <Typography variant="h6" sx={{ mt: 2 }}>Изображения ({images.length})</Typography>
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mt: 1 }}>
        {images.map((img: any) => (
          <Box key={img.id} sx={{ maxWidth: 200 }}>
            <img src={`/${img.file_path}`} alt={img.filename}
              style={{ width: "100%", borderRadius: 8, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
              onError={(e: any) => { e.target.style.display = "none"; }} />
            <Typography variant="caption" display="block">{img.filename}</Typography>
            {img.file_size != null && <Typography variant="caption" color="text.secondary">{img.file_size} bytes</Typography>}
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export const GenerationList = () => (
  <List>
    <Datagrid rowClick="show">
      <ReferenceField source="user_id" reference="users" label="Пользователь">
        <TextField source="username" />
      </ReferenceField>
      <TextField source="workflow_type" label="Тип" />
      <TextField source="status" label="Статус" />
      <NumberField source="cost" label="Стоимость" />
      <DateField source="created_at" label="Создана" />
    </Datagrid>
  </List>
);

export const GenerationShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="workflow_type" label="Тип" />
      <ReferenceField source="user_id" reference="users" label="Пользователь">
        <TextField source="username" />
      </ReferenceField>
      <TextField source="prompt" label="Промпт" />
      <TextField source="status" label="Статус" />
      <NumberField source="cost" label="Стоимость" />
      <TextField source="width" label="Ширина" />
      <TextField source="height" label="Высота" />
      <TextField source="error_message" label="Ошибка" />
      <DateField source="created_at" label="Создана" />
      <DateField source="updated_at" label="Обновлена" />
      <ImagesGrid />
    </SimpleShowLayout>
  </Show>
);
