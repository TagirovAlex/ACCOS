import { useState, useEffect, useMemo } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { ThemeProvider, CssBaseline, createTheme, AppBar, Toolbar, Typography, Button, Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Switch, FormControlLabel } from "@mui/material";
import HomeIcon from "@mui/icons-material/Home";
import ChatIcon from "@mui/icons-material/Chat";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import LogoutIcon from "@mui/icons-material/Logout";
import { lightTheme, darkTheme } from "./assets/themes";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ChatPage } from "./pages/ChatPage";
import { GenerationPage } from "./pages/GenerationPage";
import { getMe, logout, type User } from "./services/auth";

const DRAWER_WIDTH = 220;

const navItems = [
  { path: "/", label: "Дашборд", icon: <HomeIcon /> },
  { path: "/chat", label: "Чат", icon: <ChatIcon /> },
  { path: "/generate", label: "Генерация", icon: <AutoAwesomeIcon /> },
];

function Layout({ user, onLogout }: { user: User; onLogout: () => void }) {
  const location = useLocation();
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("theme") === "dark");
  const theme = useMemo(() => createTheme(darkMode ? darkTheme : lightTheme), [darkMode]);

  const handleTheme = () => {
    const next = !darkMode;
    setDarkMode(next);
    localStorage.setItem("theme", next ? "dark" : "light");
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: "flex" }}>
        <AppBar position="fixed" sx={{ zIndex: 1201 }}>
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>ACCOS</Typography>
            <Typography variant="body2" sx={{ mr: 2 }}>{user.balance} кредитов</Typography>
            <FormControlLabel control={<Switch checked={darkMode} onChange={handleTheme} size="small" />} label="" sx={{ mr: 1 }} />
            <Button color="inherit" onClick={onLogout} startIcon={<LogoutIcon />}>Выйти</Button>
          </Toolbar>
        </AppBar>
        <Drawer variant="permanent" sx={{ width: DRAWER_WIDTH, flexShrink: 0, "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" } }}>
          <Toolbar />
          <List>
            {navItems.map(item => (
              <ListItem key={item.path} disablePadding>
                <ListItemButton component={Link} to={item.path} selected={location.pathname === item.path}>
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 64 }}>
          <Routes>
            <Route path="/" element={<DashboardPage user={user} />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/generate" element={<GenerationPage />} />
          </Routes>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

function AppContent() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      getMe().then(setUser).catch(() => localStorage.removeItem("token")).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) return null;

  if (!user) {
    return (
      <ThemeProvider theme={createTheme(lightTheme)}>
        <CssBaseline />
        <LoginPage onLogin={() => {
          getMe().then(setUser);
        }} />
      </ThemeProvider>
    );
  }

  return (
    <BrowserRouter>
      <Layout user={user} onLogout={() => { logout(); setUser(null); }} />
    </BrowserRouter>
  );
}

export default function App() {
  return <AppContent />;
}
