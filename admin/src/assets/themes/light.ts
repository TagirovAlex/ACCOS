import type { RaThemeOptions } from "react-admin";

export const lightTheme: RaThemeOptions = {
  palette: {
    mode: "light",
    primary: { main: "#448aff" },
    secondary: { main: "#7c4dff" },
    background: { default: "#f0f2f5", paper: "#ffffff" },
    divider: "rgba(0,0,0,0.06)",
    text: { primary: "#1a2332", secondary: "#6b7a8d" },
    error: { main: "#ff5252" },
    warning: { main: "#ffa726" },
    success: { main: "#43a047" },
    info: { main: "#448aff" },
  },
  typography: {
    fontFamily: "'Inter', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
    h5: { fontWeight: 700, letterSpacing: "-0.02em" },
    h6: { fontWeight: 600, letterSpacing: "-0.01em" },
    body2: { letterSpacing: "0.01em" },
  },
  shape: { borderRadius: 8 },
  components: {
    RaList: { defaultProps: { empty: false } },
    RaDatagrid: {
      styleOverrides: {
        root: {
          "& .RaDatagrid-headerCell": {
            fontWeight: 600,
            textTransform: "uppercase",
            fontSize: "0.72rem",
            letterSpacing: "0.08em",
            color: "#6b7a8d",
            borderBottom: "1px solid rgba(0,0,0,0.06)",
          },
          "& .RaDatagrid-row": {
            "&:hover": { backgroundColor: "rgba(68,138,255,0.03)" },
          },
          "& .RaDatagrid-rowCell": {
            borderBottom: "1px solid rgba(0,0,0,0.04)",
          },
        },
      },
    },
    RaShow: {
      styleOverrides: { card: { boxShadow: "0 1px 4px rgba(0,0,0,0.04)" } },
    },
    RaSimpleShowLayout: {
      styleOverrides: { root: { boxShadow: "none" } },
    },
    RaListToolbar: {
      styleOverrides: { root: { alignItems: "center" } },
    },
    RaSearchInput: {
      styleOverrides: { input: { borderRadius: 6 } },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
          border: "1px solid rgba(0,0,0,0.04)",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: "none" },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          "& .MuiTableCell-head": {
            fontWeight: 600,
            fontSize: "0.72rem",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "#6b7a8d",
          },
        },
      },
    },
    MuiTableBody: {
      styleOverrides: {
        root: {
          "& .MuiTableRow-root:hover": {
            backgroundColor: "rgba(68,138,255,0.03)",
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderBottom: "1px solid rgba(0,0,0,0.04)" },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600, borderRadius: 6 },
        contained: { boxShadow: "0 1px 4px rgba(0,0,0,0.08)", "&:hover": { boxShadow: "0 2px 8px rgba(0,0,0,0.12)" } },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 6, fontWeight: 500 },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: { textTransform: "none" },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600 },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "#ffffff",
          borderBottom: "1px solid rgba(0,0,0,0.06)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
        },
      },
    },
    RaSidebar: {
      styleOverrides: {
        root: {
          "& .RaSidebar-fixed": {
            backgroundColor: "#ffffff",
            borderRight: "1px solid rgba(0,0,0,0.06)",
          },
        },
      },
    },
    RaMenu: {
      styleOverrides: {
        root: {
          "& .RaMenu-item": {
            borderRadius: 6,
            margin: "2px 8px",
            "&.active": {
              backgroundColor: "rgba(68,138,255,0.08)",
              "& .MuiListItemIcon-root": { color: "#448aff" },
            },
            "&:hover:not(.active)": {
              backgroundColor: "rgba(0,0,0,0.03)",
            },
          },
        },
      },
    },
  },
};
