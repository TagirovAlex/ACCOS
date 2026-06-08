import type { RaThemeOptions } from "react-admin";

export const darkTheme: RaThemeOptions = {
  palette: {
    mode: "dark",
    primary: { main: "#56b3f0" },
    secondary: { main: "#00bc8c" },
    background: { default: "#1a1d21", paper: "#25282d" },
    divider: "rgba(255,255,255,0.08)",
    text: { primary: "#e8eaed", secondary: "#9aa0a6" },
    error: { main: "#f66" },
    warning: { main: "#f9a825" },
    success: { main: "#00bc8c" },
    info: { main: "#56b3f0" },
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
            color: "#9aa0a6",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
          },
          "& .RaDatagrid-row": {
            "&:hover": { backgroundColor: "rgba(86,179,240,0.04)" },
          },
          "& .RaDatagrid-rowCell": {
            borderBottom: "1px solid rgba(255,255,255,0.04)",
          },
        },
      },
    },
    RaShow: {
      styleOverrides: { card: { backgroundImage: "none" } },
    },
    RaSimpleShowLayout: {
      styleOverrides: { root: { backgroundImage: "none" } },
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
          backgroundImage: "none",
          border: "1px solid rgba(255,255,255,0.06)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
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
            color: "#9aa0a6",
          },
        },
      },
    },
    MuiTableBody: {
      styleOverrides: {
        root: {
          "& .MuiTableRow-root:hover": {
            backgroundColor: "rgba(86,179,240,0.04)",
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderBottom: "1px solid rgba(255,255,255,0.04)" },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600, borderRadius: 6 },
        contained: { boxShadow: "none", "&:hover": { boxShadow: "0 2px 8px rgba(0,0,0,0.3)" } },
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
          backgroundImage: "none",
          backgroundColor: "#1e2126",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          boxShadow: "none",
        },
      },
    },
    RaSidebar: {
      styleOverrides: {
        root: {
          "& .RaSidebar-fixed": {
            backgroundColor: "#1e2126",
            borderRight: "1px solid rgba(255,255,255,0.06)",
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
              backgroundColor: "rgba(86,179,240,0.12)",
              "& .MuiListItemIcon-root": { color: "#56b3f0" },
            },
            "&:hover:not(.active)": {
              backgroundColor: "rgba(255,255,255,0.04)",
            },
          },
        },
      },
    },
  },
};
