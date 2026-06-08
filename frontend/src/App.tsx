import { useState, useEffect, useMemo } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { ThemeProvider, CssBaseline, createTheme, AppBar, Toolbar, Typography, Button, Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Switch, FormControlLabel, Chip, Avatar } from "@mui/material";
import HomeIcon from "@mui/icons-material/Home";
import ChatIcon from "@mui/icons-material/Chat";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import HistoryIcon from "@mui/icons-material/History";
import LogoutIcon from "@mui/icons-material/Logout";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import SettingsIcon from "@mui/icons-material/Settings";
import { lightTheme, darkTheme } from "./assets/themes";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ChatPage } from "./pages/ChatPage";
import { GenerationPage } from "./pages/GenerationPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { getMe, logout, type User } from "./services/auth";

const DRAWER_WIDTH = 220;

const navItems = [
  { path: "/", label: "Дашборд", icon: <HomeIcon /> },
  { path: "/chat", label: "Чат", icon: <ChatIcon /> },
  { path: "/generate", label: "Новая генерация", icon: <AutoAwesomeIcon /> },
  { path: "/history", label: "История", icon: <HistoryIcon /> },
  { path: "/profile", label: "Профиль", icon: <SettingsIcon /> },
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
      <Box sx={{ display: "flex", height: "100vh" }}>
        <AppBar position="fixed" sx={{ zIndex: 1201 }} elevation={0}>
          <Toolbar>
            <AutoAwesomeIcon sx={{ mr: 1.5 }} />
            <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>ACCOS</Typography>
            <Chip icon={<AccountBalanceWalletIcon />} label={`${user.balance} MS`} size="small" sx={{ mr: 2, bgcolor: "rgba(255,255,255,0.15)", color: "inherit", fontWeight: 600 }} />
            <FormControlLabel control={<Switch checked={darkMode} onChange={handleTheme} size="small" />} label="" sx={{ mr: 1 }} />
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mr: 2 }}>
              <Avatar sx={{ width: 28, height: 28, bgcolor: "rgba(255,255,255,0.25)", fontSize: 14 }}>{user.full_name?.[0] || user.username[0]}</Avatar>
              <Typography variant="body2" sx={{ display: { xs: "none", sm: "block" } }}>{user.full_name || user.username}</Typography>
            </Box>
            <Button color="inherit" onClick={onLogout} startIcon={<LogoutIcon />} sx={{ display: { xs: "none", sm: "flex" } }}>Выйти</Button>
          </Toolbar>
        </AppBar>
        <Drawer variant="permanent" sx={{ width: DRAWER_WIDTH, flexShrink: 0, "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box", borderRight: "none", boxShadow: "1px 0 3px rgba(0,0,0,0.05)" } }}>
          <Toolbar />
          <List sx={{ px: 1, flex: "1 1 auto", overflow: "auto" }}>
            {navItems.map(item => (
              <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton component={Link} to={item.path} selected={location.pathname === item.path} sx={{ borderRadius: 2 }}>
                  <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Drawer>
        <Box component="main" sx={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", overflowY: "auto", pt: "64px", px: 3, pb: 3, minHeight: 0 }}>
          <Routes>
            <Route path="/" element={<ErrorBoundary><DashboardPage user={user} /></ErrorBoundary>} />
            <Route path="/chat" element={<ErrorBoundary><ChatPage /></ErrorBoundary>} />
            <Route path="/generate" element={<ErrorBoundary><GenerationPage /></ErrorBoundary>} />
            <Route path="/history" element={<ErrorBoundary><GenerationPage viewHistory /></ErrorBoundary>} />
            <Route path="/profile" element={<ErrorBoundary><ProfilePage user={user} /></ErrorBoundary>} />
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
        <LoginPage onLogin={(u) => { setUser(u); }} />
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
