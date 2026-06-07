import { defaultTheme } from "react-admin";

export const lightTheme = {
  ...defaultTheme,
  palette: {
    mode: "light" as const,
    primary: { main: "#1976d2" },
    secondary: { main: "#dc004e" },
    background: { default: "#f5f5f5", paper: "#ffffff" },
  },
};
