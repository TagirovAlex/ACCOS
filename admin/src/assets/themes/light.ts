import { defaultTheme } from "react-admin";

export const lightTheme = {
  ...defaultTheme,
  palette: {
    mode: "light" as const,
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
          boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
          border: "1px solid rgba(0,0,0,0.04)",
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
        contained: { boxShadow: "0 1px 4px rgba(0,0,0,0.08)", "&:hover": { boxShadow: "0 2px 8px rgba(0,0,0,0.12)" } },
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
          backgroundColor: "#ffffff",
          color: "#1a2332",
          borderBottom: "1px solid rgba(0,0,0,0.06)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
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
          backgroundColor: "#ffffff",
          borderRight: "1px solid rgba(0,0,0,0.06)",
        },
      },
    },
    RaMenuItem: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          margin: "2px 8px",
          "&.Mui-selected": {
            backgroundColor: "rgba(68, 138, 255, 0.08)",
            "&:hover": { backgroundColor: "rgba(68, 138, 255, 0.16)" },
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
            color: "#6b7a8d",
          },
        },
      },
    },
  },
};
