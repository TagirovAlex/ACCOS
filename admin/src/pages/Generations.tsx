import { useState } from "react";
import { ListBase, Datagrid, TextField, DateField, NumberField, Show, SimpleShowLayout, ReferenceField, FunctionField, WithListContext, useRedirect, useDelete, DeleteButton } from "react-admin";
import { Box, Typography, Chip, IconButton, Card, CardContent, Button, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions } from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import { CardGrid } from "../components/CardGrid";
import { useView } from "../components/ViewToggle";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import { useRecordContext } from "react-admin";

function imgUrl(fp: string): string {
  if (fp.startsWith("/")) return fp;
  return "/" + fp;
}

function downloadFile(url: string, name: string) {
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

const THUMB_SIZE = 56;

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
            <img src={imgUrl(img.file_path)} alt={img.filename}
              style={{ width: "100%", borderRadius: 6, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
              onError={(e: any) => { e.target.style.display = "none"; }} />
            <Typography variant="caption" display="block" sx={{ mt: 0.25 }}>{img.filename}</Typography>
            {img.file_size != null && <Typography variant="caption" color="text.secondary">{(img.file_size / 1024).toFixed(1)} KB</Typography>}
            <Button size="small" startIcon={<DownloadIcon />} sx={{ mt: 0.5 }}
              onClick={() => downloadFile(imgUrl(img.file_path), img.filename)}>
              Скачать
            </Button>
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
      <Box>
        <Typography variant="subtitle2" fontWeight={600} sx={{ mt: 2, mb: 1 }}>Исходные изображения ({(sg.images || []).length})</Typography>
        <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
          {(sg.images || []).map((img: any) => (
            <Box key={img.id} sx={{ maxWidth: 200 }}>
              <img src={imgUrl(img.file_path)} alt={img.filename}
                style={{ width: "100%", borderRadius: 6, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
                onError={(e: any) => { e.target.style.display = "none"; }} />
              <Typography variant="caption" display="block" sx={{ mt: 0.25 }}>{img.filename}</Typography>
              <Button size="small" startIcon={<DownloadIcon />} sx={{ mt: 0.5 }}
                onClick={() => downloadFile(imgUrl(img.file_path), img.filename)}>
                Скачать
              </Button>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
};

const ReferenceImagesBlock = () => {
  const record = useRecordContext();
  const refs = record?.reference_images || [];
  if (!refs.length) return null;
  return (
    <Box sx={{ mt: 2, p: 2, bgcolor: "action.hover", borderRadius: 1 }}>
      <Typography variant="subtitle2" fontWeight={600} gutterBottom>Референс-изображения (загружены пользователем)</Typography>
      <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
        {refs.map((fp: string, i: number) => {
          const name = fp.split("/").pop() || `ref-${i}`;
          return (
            <Box key={i} sx={{ maxWidth: 200 }}>
              <img src={fp} alt={`ref-${i}`}
                style={{ width: "100%", borderRadius: 6, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}
                onError={(e: any) => { e.target.style.display = "none"; }} />
              <Button size="small" startIcon={<DownloadIcon />} sx={{ mt: 0.5 }}
                onClick={() => downloadFile(fp, name)}>
                Скачать
              </Button>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};

const GenThumb = ({ record }: { record?: any }) => {
  if (!record?.thumbnail) return null;
  return (
    <img src={`/${record.thumbnail}`} alt=""
      style={{ width: THUMB_SIZE, height: THUMB_SIZE, borderRadius: 4, objectFit: "cover" }}
      onError={(e: any) => { e.target.style.display = "none"; }} />
  );
};

const StatusChip = ({ record }: { record?: any }) => {
  const status = record?.status || "";
  const color = status === "completed" ? "success" : status === "failed" ? "error" : "default";
  const labels: Record<string, string> = { completed: "Готово", processing: "Обработка", queued: "В очереди", failed: "Ошибка" };
  return <Chip label={labels[status] || status} size="small" color={color} />;
};

const GenerationListView = () => (
  <Datagrid rowClick="show" sx={{ "& .column-thumb": { width: 66 } }}>
    <FunctionField label="" render={(r: any) => <GenThumb record={r} />} />
    <ReferenceField source="user_id" reference="users" label="Пользователь" link="show">
      <TextField source="username" />
    </ReferenceField>
    <TextField source="workflow_type" label="Тип" />
    <FunctionField label="Статус" render={(r: any) => <StatusChip record={r} />} />
    <NumberField source="cost" label="Стоимость" />
    <TextField source="width" label="Ш×В" />
    <DateField source="created_at" label="Создана" showTime />
    <FunctionField label="Промпт" render={(r: any) => (
      <Typography variant="body2" sx={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.prompt}</Typography>
    )} />
  </Datagrid>
);

const GenerationTileView = () => {
  const redirect = useRedirect();
  const [deleteOne] = useDelete();
  const [deleteTarget, setDeleteTarget] = useState<any>(null);
  return (
  <>
    <WithListContext render={({ data }) => (
      <CardGrid>
        {data?.map((record: any) => (
          <Card key={record.id} sx={{ position: "relative", cursor: "pointer", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}>
            <Box sx={{
              position: "absolute", top: 0, left: 0, right: 0, height: 4, zIndex: 2,
              bgcolor: record.status === "completed" ? "success.main"
                : record.status === "failed" ? "error.main"
                : record.status === "processing" ? "info.main" : "grey.400",
              borderRadius: "4px 4px 0 0",
            }} />
            <IconButton size="small"
              sx={{ position: "absolute", top: 4, right: 4, zIndex: 1, color: "error.light" }}
              onClick={(e) => { e.stopPropagation(); setDeleteTarget(record); }}>
              <DeleteIcon fontSize="small" />
            </IconButton>
            <Box onClick={() => redirect("show", "generations", record.id)}
              sx={{ width: "100%", height: 140, overflow: "hidden", bgcolor: "#1a1a1a" }}>
              {record.thumbnail ? (
                <img src={imgUrl(record.thumbnail)} alt=""
                  style={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }}
                  onError={(e: any) => { e.target.style.display = "none"; }} />
              ) : (
                <Box sx={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Typography variant="caption" color="text.disabled">Нет изображения</Typography>
                </Box>
              )}
            </Box>
            <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
              <Typography variant="body2" fontWeight={600} noWrap>{record.workflow_type}</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }} noWrap>{record.prompt}</Typography>
              <Box sx={{ display: "flex", gap: 1, alignItems: "center", mb: 0.5 }}>
                <StatusChip record={record} />
                <Typography variant="caption" color="text.secondary">{Number(record.cost.toFixed(2))} кр.</Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                {record.username} · {new Date(record.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </CardGrid>
    )} />
    <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
      <DialogTitle>Удалить генерацию?</DialogTitle>
      <DialogContent>
        <DialogContentText>Генерация «{deleteTarget?.workflow_type}» будет удалена без возможности восстановления.</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setDeleteTarget(null)}>Отмена</Button>
        <Button onClick={() => { deleteOne("generations", { id: deleteTarget?.id }); setDeleteTarget(null); }} color="error">Удалить</Button>
      </DialogActions>
    </Dialog>
  </>
  );
};

export const GenerationList = () => {
  const { view, ViewToggleEl } = useView("generations_view");
  return (
    <div>
      {ViewToggleEl}
      <ListBase perPage={100}>
        {view === "list" ? <GenerationListView /> : <GenerationTileView />}
      </ListBase>
    </div>
  );
};

const ShowActions = ({ listLabel, listPath }: { listLabel: string; listPath: string }) => {
  const redirect = useRedirect();
  return (
    <Box sx={{ display: "flex", gap: 1, p: 1 }}>
      <Button startIcon={<ArrowBackIcon />} size="small" onClick={() => redirect("list", listPath)}>
        {listLabel}
      </Button>
      <DeleteButton mutationMode="pessimistic" />
    </Box>
  );
};

export const GenerationShow = () => (
  <Show actions={<ShowActions listLabel="← Генерации" listPath="generations" />}>
    <SimpleShowLayout>
      <TextField source="workflow_type" label="Тип" />
      <ReferenceField source="user_id" reference="users" label="Пользователь" link="show">
        <TextField source="username" />
      </ReferenceField>
      <FunctionField label="Промпт" render={() => <PromptField />} />
      <TextField source="status" label="Статус" />
      <NumberField source="cost" label="Стоимость" />
      <TextField source="width" label="Ширина" />
      <TextField source="height" label="Высота" />
      <NumberField source="seed" label="Seed" />
      <TextField source="error_message" label="Ошибка" />
      <DateField source="created_at" label="Создана" />
      <DateField source="updated_at" label="Обновлена" />
      <FunctionField label=" " render={() => <SourceGenerationBlock />} />
      <FunctionField label=" " render={() => <ReferenceImagesBlock />} />
      <ImagesGrid source="images" label="Изображения результата" />
    </SimpleShowLayout>
  </Show>
);
