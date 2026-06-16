import { ToggleButtonGroup, ToggleButton } from "@mui/material";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
import { useState } from "react";

interface ViewToggleProps {
  view: "list" | "tiles";
  onChange: (view: "list" | "tiles") => void;
}

export const ViewToggle = ({ view, onChange }: ViewToggleProps) => (
  <div style={{ display: "flex", justifyContent: "flex-end", padding: "4px 16px" }}>
    <ToggleButtonGroup
      value={view}
      exclusive
      size="small"
      onChange={(_, v) => { if (v) onChange(v as "list" | "tiles"); }}
    >
      <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
      <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
    </ToggleButtonGroup>
  </div>
);

const getView = (key: string): "list" | "tiles" =>
  (localStorage.getItem(key) as "list" | "tiles") ?? "list";

export const useView = (storageKey: string) => {
  const [view, setView] = useState<"list" | "tiles">(() => getView(storageKey));
  const handleChange = (v: "list" | "tiles") => {
    setView(v);
    localStorage.setItem(storageKey, v);
  };
  return {
    view,
    ViewToggleEl: <ViewToggle view={view} onChange={handleChange} />,
    setView: handleChange,
  };
};
