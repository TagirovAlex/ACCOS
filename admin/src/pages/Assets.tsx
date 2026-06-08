import { useState } from "react";
import { List, Datagrid, TextField, DateField, Show, SimpleShowLayout, ReferenceField, FunctionField, WithListContext, useRedirect } from "react-admin";
import { Box, IconButton, Chip, Card, CardContent, Typography, ToggleButtonGroup, ToggleButton, Grid as MuiGrid, Button } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useRecordContext } from "react-admin";
import DeleteIcon from "@mui/icons-material/Delete";

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

const ThumbnailField = ({ size = 48 }: { size?: number }) => {
  const record = useRecordContext();
  if (!record?.file_path) return null;
  return (
    <img src={`/${record.file_path}`} alt=""
      style={{ width: size, height: size, borderRadius: 4, objectFit: "cover" }}
      onError={(e: any) => { e.target.style.display = "none"; }} />
  );
};

const FileSizeField = () => {
  const record = useRecordContext();
  return <span>{formatFileSize(record?.file_size)}</span>;
};

const DimField = () => {
  const record = useRecordContext();
  const w = record?.width;
  const h = record?.height;
  if (w == null || h == null) return <span style={{ color: "#999" }}>—</span>;
  return <span>{w}×{h}</span>;
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

const StatusChip = () => {
  const record = useRecordContext();
  if (!record?.deleted_at) {
    return <Chip label="Активен" size="small" color="success" variant="outlined" />;
  }
  return <Chip label="Удалён" size="small" color="error" icon={<DeleteIcon />} />;
};

const AssetListView = () => (
  <Datagrid rowClick="show" sx={{ "& .column-thumb": { width: 58 } }}>
    <FunctionField label="" render={() => <ThumbnailField />} />
    <TextField source="filename" label="Файл" />
    <FunctionField label="Размер" render={() => <FileSizeField />} />
    <FunctionField label="Разрешение" render={() => <DimField />} />
    <ReferenceField source="user_id" reference="users" label="Пользователь" link="show">
      <TextField source="username" />
    </ReferenceField>
    <ReferenceField source="generation_id" reference="generations" label="Генерация" link="show">
      <TextField source="id" />
    </ReferenceField>
    <DateField source="created_at" label="Создан" showTime />
    <FunctionField label="Статус" render={() => <StatusChip />} />
    <FunctionField label="" render={() => <DownloadButton />} />
  </Datagrid>
);

const AssetTileView = () => {
  const redirect = useRedirect();
  return (
    <WithListContext render={({ data }) => (
      <MuiGrid container spacing={2} sx={{ p: 2 }}>
        {data?.map((record: any) => (
          <MuiGrid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={record.id}>
            <Card onClick={() => redirect("show", "assets", record.id)}
              sx={{ cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}>
              <Box sx={{ width: "100%", height: 140, overflow: "hidden", bgcolor: "#1a1a1a" }}>
                {record.file_path ? (
                  <img src={`/${record.file_path}`} alt=""
                    style={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }}
                    onError={(e: any) => { e.target.style.display = "none"; }} />
                ) : (
                  <Box sx={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Typography variant="caption" color="text.disabled">Нет изображения</Typography>
                  </Box>
                )}
              </Box>
              <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
                <Typography variant="body2" fontWeight={600} noWrap>{record.filename}</Typography>
                <Box sx={{ display: "flex", gap: 1, alignItems: "center", mb: 0.5 }}>
                  <StatusChip />
                  <Typography variant="caption" color="text.secondary">{formatFileSize(record.file_size)}</Typography>
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                  {record.width != null && record.height != null
                    ? `${record.width}×${record.height}`
                    : ""}
                  {record.username ? ` · ${record.username}` : ""}
                </Typography>
              </CardContent>
            </Card>
          </MuiGrid>
        ))}
      </MuiGrid>
    )} />
  );
};

export const AssetList = () => {
  const [view, setView] = useState<"list" | "tiles">(() => (localStorage.getItem("assets_view") as "list" | "tiles") ?? "list");
  return (
    <List actions={false}>
      <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}>
        <ToggleButtonGroup value={view} exclusive size="small" onChange={(_, v) => { if (v) { setView(v); localStorage.setItem("assets_view", v); } }}>
          <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
          <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
        </ToggleButtonGroup>
      </Box>
      {view === "list" ? <AssetListView /> : <AssetTileView />}
    </List>
  );
};

const ShowActions = ({ listLabel, listPath }: { listLabel: string; listPath: string }) => {
  const redirect = useRedirect();
  return (
    <Box sx={{ display: "flex", gap: 1, p: 1 }}>
      <Button startIcon={<ArrowBackIcon />} size="small" onClick={() => redirect("list", listPath)}>
        {listLabel}
      </Button>
    </Box>
  );
};

export const AssetShow = () => (
  <Show actions={<ShowActions listLabel="← Ресурсы" listPath="assets" />}>
    <SimpleShowLayout>
      <TextField source="filename" label="Файл" />
      <TextField source="file_path" label="Путь" />
      <FunctionField label="Размер" render={() => <FileSizeField />} />
      <FunctionField label="Разрешение" render={() => <DimField />} />
      <ReferenceField source="user_id" reference="users" label="Пользователь" link="show">
        <TextField source="username" />
      </ReferenceField>
      <ReferenceField source="generation_id" reference="generations" label="Генерация" link="show">
        <TextField source="id" />
      </ReferenceField>
      <DateField source="created_at" label="Создан" showTime />
      <ImagePreview />
    </SimpleShowLayout>
  </Show>
);
