import { useState } from "react";
import { List, Datagrid, TextField, DateField, NumberField, Show, SimpleShowLayout, ReferenceField, FunctionField } from "react-admin";
import { Box, Typography, Chip, Collapse, Button, IconButton } from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import { useRecordContext } from "react-admin";

const PromptField = () => {
  const record = useRecordContext();
  const [expanded, setExpanded] = useState(false);
  const prompt = record?.prompt || "";
  const isLong = prompt.length > 80;
  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "flex-start", gap: 0.5 }}>
        <Typography variant="body2" sx={{
          flex: 1, overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: expanded ? "normal" : "nowrap",
          wordBreak: "break-word",
        }}>
          {prompt}
        </Typography>
        {isLong && (
          <IconButton size="small" onClick={() => setExpanded(!expanded)} sx={{ mt: -0.25 }}>
            {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
          </IconButton>
        )}
      </Box>
    </Box>
  );
};

const ImagesGrid = ({ source, label }: { source: string; label: string }) => {
  const record = useRecordContext();
  const images = record?.[source] || [];
  if (!images.length) return null;
  return (
    <Box>
      <Typography variant="subtitle2" fontWeight={600} sx={{ mt: 2, mb: 1 }}>{label} ({images.length})</Typography>
      <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
        {images.map((img: any) => (
          <Box key={img.id} sx={{ maxWidth: 200 }}>
            <img src={`/${img.file_path}`} alt={img.filename}
              style={{ width: "100%", borderRadius: 6, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
              onError={(e: any) => { e.target.style.display = "none"; }} />
            <Typography variant="caption" display="block" sx={{ mt: 0.25 }}>{img.filename}</Typography>
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
    <Box sx={{ mt: 2, p: 2, bgcolor: "action.hover", borderRadius: 1 }}>
      <Typography variant="subtitle2" fontWeight={600} gutterBottom>Исходная генерация</Typography>
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
      <FunctionField label="Промпт" render={() => <PromptField />} />
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
