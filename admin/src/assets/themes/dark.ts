import { defaultTheme } from "react-admin";

export const darkTheme = {
  ...defaultTheme,
  palette: {
    mode: "dark" as const,
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
    fontFamily: "'Source Sans 3', 'Inter', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
    h5: { fontWeight: 700, letterSpacing: "-0.02em" },
    h6: { fontWeight: 600, letterSpacing: "-0.01em" },
    body2: { letterSpacing: "0.01em" },
  },
  shape: { borderRadius: 6 },
  sidebar: {
    width: 250,
    closedWidth: 64,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          border: "1px solid rgba(255,255,255,0.06)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
          borderRadius: 6,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: "none" },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600, borderRadius: 4 },
        contained: { boxShadow: "none", "&:hover": { boxShadow: "0 2px 8px rgba(0,0,0,0.3)" } },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 4, fontWeight: 500 },
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
    MuiList: {
      styleOverrides: {
        root: {
          "& .MuiMenuItem-root": {
            borderRadius: 4,
            margin: "2px 8px",
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: "#1e2126",
          borderRight: "1px solid rgba(255,255,255,0.06)",
        },
      },
    },
    RaMenuItem: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          margin: "2px 8px",
          "&.Mui-selected": {
            backgroundColor: "rgba(86, 179, 240, 0.15)",
            "&:hover": { backgroundColor: "rgba(86, 179, 240, 0.25)" },
          },
        },
      },
    },
    RaDatagrid: {
      styleOverrides: {
        root: {
          "& .RaDatagrid-headerCell": {
            fontWeight: 700,
            fontSize: "0.8rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#9aa0a6",
          },
        },
      },
    },
  },
};
