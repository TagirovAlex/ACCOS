import { useState, useEffect } from "react";
import { List, Datagrid, TextField, NumberField, Edit, SimpleForm, TextInput, NumberInput, BooleanInput, Create, AutocompleteInput, useNotify, WithListContext, CreateButton, TopToolbar, useRedirect } from "react-admin";
import { ToggleButtonGroup, ToggleButton, Box, Card, CardContent, Typography, Grid as MuiGrid, Chip } from "@mui/material";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
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

const GroupListView = () => (
  <Datagrid rowClick="edit">
    <TextField source="name" label="Название" />
    <TextField source="ad_group_dn" label="AD группа" />
    <TextField source="permissions" label="Права" />
    <NumberField source="start_balance" label="Стартовый баланс" />
    <TextField source="description" label="Описание" />
  </Datagrid>
);

const GroupTileView = () => {
  const redirect = useRedirect();
  return (
    <WithListContext render={({ data }) => (
      <MuiGrid container spacing={2} sx={{ p: 2 }}>
        {data?.map((record: any) => (
          <MuiGrid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={record.id}>
            <Card sx={{ cursor: "pointer", height: "100%", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}
              onClick={() => redirect("edit", "groups", record.id)}>
              <CardContent>
                <Typography variant="body1" fontWeight={600} noWrap>{record.name}</Typography>
                {record.description && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 1, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {record.description}
                  </Typography>
                )}
                <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 1 }}>
                  {(record.permissions || "").split(",").filter(Boolean).map((p: string) => (
                    <Chip key={p} label={p.trim()} size="small" color={p.trim() === "admin" ? "error" : "primary"} variant="outlined" />
                  ))}
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: "block" }} noWrap>{record.ad_group_dn}</Typography>
                {record.start_balance > 0 && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.5 }}>
                    Стартовый баланс: {record.start_balance}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </MuiGrid>
        ))}
      </MuiGrid>
    )} />
  );
};

const GroupListActions = ({ view, onViewChange }: { view: string; onViewChange: (v: "list" | "tiles") => void }) => (
  <TopToolbar>
    <CreateButton />
    <Box sx={{ flex: 1 }} />
    <ToggleButtonGroup value={view} exclusive size="small" onChange={(_, v) => { if (v) onViewChange(v); }}>
      <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
      <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
    </ToggleButtonGroup>
  </TopToolbar>
);

export const GroupList = () => {
  const [view, setView] = useState<"list" | "tiles">(() => (localStorage.getItem("groups_view") as "list" | "tiles") ?? "list");
  return (
    <List actions={<GroupListActions view={view} onViewChange={(v) => { setView(v); localStorage.setItem("groups_view", v); }} />}>
      {view === "list" ? <GroupListView /> : <GroupTileView />}
    </List>
  );
};

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
