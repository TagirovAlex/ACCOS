import { List, Datagrid, TextField, DateField, NumberField, Show, SimpleShowLayout, ReferenceField, FunctionField } from "react-admin";
import { Box, Typography, Chip } from "@mui/material";
import { useRecordContext } from "react-admin";

const ImagesGrid = ({ source, label }: { source: string; label: string }) => {
  const record = useRecordContext();
  const images = record?.[source] || [];
  if (!images.length) return null;
  return (
    <Box>
      <Typography variant="h6" sx={{ mt: 2 }}>{label} ({images.length})</Typography>
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mt: 1 }}>
        {images.map((img: any) => (
          <Box key={img.id} sx={{ maxWidth: 200 }}>
            <img src={`/${img.file_path}`} alt={img.filename}
              style={{ width: "100%", borderRadius: 8, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
              onError={(e: any) => { e.target.style.display = "none"; }} />
            <Typography variant="caption" display="block">{img.filename}</Typography>
            {img.file_size != null && <Typography variant="caption" color="text.secondary">{(img.file_size / 1024).toFixed(1)} KB</Typography>}
          </Box>
        ))}
      </Box>
    </Box>
  );
};

const SourceGenerationBlock = () => {
  const record = useRecordContext();
  const sg = record?.source_generation;
  if (!sg) return null;
  return (
    <Box sx={{ mt: 2, p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
      <Typography variant="subtitle2" fontWeight={600} gutterBottom>
        Исходная генерация
      </Typography>
      <Chip label={sg.workflow_type} size="small" sx={{ mr: 1 }} />
      <Chip label={`ID: ${sg.id.slice(0, 8)}...`} size="small" variant="outlined" />
      <ImagesGrid source="images" label="Исходные изображения" />
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
      <FunctionField label=" " render={() => <SourceGenerationBlock />} />
      <ImagesGrid source="images" label="Изображения результата" />
    </SimpleShowLayout>
  </Show>
);
