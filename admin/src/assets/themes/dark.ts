import { defaultTheme } from "react-admin";

export const darkTheme = {
  ...defaultTheme,
  palette: {
    mode: "dark" as const,
    primary: { main: "#90caf9" },
    secondary: { main: "#f48fb1" },
    background: { default: "#121212", paper: "#1e1e1e" },
  },
  typography: { fontFamily: 'Arial, Helvetica, sans-serif' },
};
