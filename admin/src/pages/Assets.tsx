import { List, Datagrid, TextField, DateField, NumberField, Show, SimpleShowLayout, ReferenceField, FunctionField } from "react-admin";
import { Box, Typography, IconButton } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import { useRecordContext } from "react-admin";

const ImagePreview = () => {
  const record = useRecordContext();
  if (!record?.file_path) return null;
  return (
    <Box sx={{ mt: 1 }}>
      <img src={`/${record.file_path}`} alt={record.filename}
        style={{ maxWidth: "100%", maxHeight: 400, borderRadius: 6, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
        onError={(e: any) => { e.target.style.display = "none"; }} />
    </Box>
  );
};

const formatFileSize = (bytes: number | null | undefined): string => {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const ThumbnailField = () => {
  const record = useRecordContext();
  if (!record?.file_path) return null;
  return (
    <img src={`/${record.file_path}`} alt=""
      style={{ width: 48, height: 48, borderRadius: 4, objectFit: "cover" }}
      onError={(e: any) => { e.target.style.display = "none"; }} />
  );
};

const FileSizeField = () => {
  const record = useRecordContext();
  return <span>{formatFileSize(record?.file_size)}</span>;
};

const DownloadButton = () => {
  const record = useRecordContext();
  if (!record?.file_path) return null;
  return (
    <IconButton size="small" component="a" href={`/${record.file_path}`} download target="_blank"
      sx={{ color: "text.secondary", "&:hover": { color: "primary.main" } }}>
      <DownloadIcon fontSize="small" />
    </IconButton>
  );
};

export const AssetList = () => (
  <List>
    <Datagrid rowClick="show">
      <FunctionField label="" render={() => <ThumbnailField />} />
      <TextField source="filename" label="Файл" />
      <FunctionField label="Размер" render={() => <FileSizeField />} />
      <NumberField source="width" label="Ш × В" />
      <ReferenceField source="user_id" reference="users" label="Пользователь" link="show">
        <TextField source="username" />
      </ReferenceField>
      <ReferenceField source="generation_id" reference="generations" label="Генерация" link="show">
        <TextField source="id" />
      </ReferenceField>
      <DateField source="created_at" label="Создан" showTime />
      <FunctionField label="" render={() => <DownloadButton />} />
    </Datagrid>
  </List>
);

export const AssetShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="filename" label="Файл" />
      <TextField source="file_path" label="Путь" />
      <FunctionField label="Размер" render={() => <FileSizeField />} />
      <NumberField source="width" label="Ширина (px)" />
      <NumberField source="height" label="Высота (px)" />
      <ReferenceField source="user_id" reference="users" label="Пользователь">
        <TextField source="username" />
      </ReferenceField>
      <ReferenceField source="generation_id" reference="generations" label="Генерация">
        <TextField source="id" />
      </ReferenceField>
      <DateField source="created_at" label="Создан" showTime />
      <ImagePreview />
    </SimpleShowLayout>
  </Show>
);
