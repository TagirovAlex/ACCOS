import { createTheme } from "@mui/material";

export const darkTheme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#90caf9" },
    secondary: { main: "#f48fb1" },
    background: { default: "#0f1115", paper: "#1a1d23" },
  },
  typography: { fontFamily: 'Arial, Helvetica, sans-serif' },
  shape: { borderRadius: 10 },
  components: {
    MuiCard: { styleOverrides: { root: { boxShadow: "0 1px 3px rgba(0,0,0,0.3)", transition: "box-shadow 0.2s, transform 0.2s", "&:hover": { boxShadow: "0 4px 12px rgba(0,0,0,0.4)", transform: "translateY(-1px)" } } } },
    MuiButton: { styleOverrides: { root: { textTransform: "none", fontWeight: 600, borderRadius: 8 } } },
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    MuiChip: { styleOverrides: { root: { fontWeight: 500 } } },
  },
});
