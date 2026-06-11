import { useState, useEffect, useMemo } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { ThemeProvider, CssBaseline, createTheme, AppBar, Toolbar, Typography, Button, Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Switch, FormControlLabel, Chip, Avatar } from "@mui/material";
import HomeIcon from "@mui/icons-material/Home";
import ChatIcon from "@mui/icons-material/Chat";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import EditIcon from "@mui/icons-material/Edit";
import MovieIcon from "@mui/icons-material/Movie";
import HistoryIcon from "@mui/icons-material/History";
import LogoutIcon from "@mui/icons-material/Logout";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import SettingsIcon from "@mui/icons-material/Settings";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { lightTheme, darkTheme } from "./assets/themes";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ChatPage } from "./pages/ChatPage";
import { GenerationPage } from "./pages/GenerationPage";
import { ProfilePage } from "./pages/ProfilePage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { HelpPage } from "./pages/HelpPage";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { getMe, logout, type User } from "./services/auth";
import { GenerationProvider, useGenerationStatus } from "./services/generationContext";

const DRAWER_WIDTH = 220;

function GlobalGenBar() {
  const { runningGen } = useGenerationStatus();
  if (!runningGen) return null;
  return (
    <Box sx={{ position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 1300, bgcolor: runningGen.status === "failed" ? "error.main" : "info.main", color: "white", px: 3, py: 0.75, display: "flex", alignItems: "center", gap: 2 }}>
      <Typography variant="caption" fontWeight={600}>
        Генерация {runningGen.status === "queued" ? "в очереди" : runningGen.status === "processing" ? "выполняется" : runningGen.status === "completed" ? "завершена" : "ошибка"}
      </Typography>
      <Typography variant="caption">ID: {runningGen.generation_id.slice(0, 8)}</Typography>
      {runningGen.status === "completed" && runningGen.cost > 0 && (
        <Typography variant="caption">{runningGen.cost} кр.</Typography>
      )}
      {runningGen.status === "processing" && <Box sx={{ width: 12, height: 12, border: "2px solid white", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />}
    </Box>
  );
}

function Layout({ user, onLogout }: { user: User; onLogout: () => void }) {
  const location = useLocation();
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("theme") === "dark");
  const [avatarError, setAvatarError] = useState(false);
  const theme = useMemo(() => createTheme(darkMode ? darkTheme : lightTheme), [darkMode]);

  const canGenerate = user.permissions?.includes("generate");
  const canEdit = user.permissions?.includes("edit");
  const canVideo = user.permissions?.includes("video");
  const canChat = user.permissions?.includes("chat");
  const canManageDocs = user.permissions?.includes("documents_manage");

  const navItems = [
    { path: "/", label: "Дашборд", icon: <HomeIcon /> },
    ...(canChat ? [{ path: "/chat", label: "Чат", icon: <ChatIcon /> }] : []),
    ...(canGenerate ? [{ path: "/generate", label: "Генерация", icon: <AutoAwesomeIcon /> }] : []),
    ...(canEdit ? [{ path: "/edit", label: "Редактирование", icon: <EditIcon /> }] : []),
    ...(canVideo ? [{ path: "/video", label: "Видео", icon: <MovieIcon /> }] : []),
    ...(canGenerate || canEdit || canVideo ? [{ path: "/history", label: "История", icon: <HistoryIcon /> }] : []),
    ...(canManageDocs ? [{ path: "/knowledge", label: "Документы", icon: <MenuBookIcon /> }] : []),
    { path: "/help", label: "Помощь", icon: <HelpOutlineIcon /> },
    { path: "/profile", label: "Профиль", icon: <SettingsIcon /> },
  ];

  const handleTheme = () => {
    const next = !darkMode;
    setDarkMode(next);
    localStorage.setItem("theme", next ? "dark" : "light");
  };

  const avatarUrl = user.avatar_path ? `/${user.avatar_path}` : null;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <Box sx={{ display: "flex", height: "100vh" }}>
        <AppBar position="fixed" sx={{ zIndex: 1201 }} elevation={0}>
          <Toolbar>
            <AutoAwesomeIcon sx={{ mr: 1.5 }} />
            <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>ACCOS</Typography>
            <Chip icon={<AccountBalanceWalletIcon />} label={`${(user.balance ?? 0).toFixed(2)} MS`} size="small" sx={{ mr: 2, bgcolor: "rgba(255,255,255,0.15)", color: "inherit", fontWeight: 600 }} />
            <FormControlLabel control={<Switch checked={darkMode} onChange={handleTheme} size="small" />} label="" sx={{ mr: 1 }} />
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mr: 2 }}>
              <Avatar
                src={avatarError ? undefined : (avatarUrl || undefined)}
                onError={() => setAvatarError(true)}
                sx={{ width: 28, height: 28, bgcolor: "rgba(255,255,255,0.25)", fontSize: 14 }}
              >{user.full_name?.[0] || user.username[0]}</Avatar>
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
          <GenerationProvider>
            <Routes>
              <Route path="/" element={<ErrorBoundary><DashboardPage user={user} /></ErrorBoundary>} />
              <Route path="/chat" element={<ErrorBoundary><ChatPage user={user} /></ErrorBoundary>} />
              <Route path="/generate" element={<ErrorBoundary key="generate"><GenerationPage key="generate" mode="generate" /></ErrorBoundary>} />
              <Route path="/edit" element={<ErrorBoundary key="edit"><GenerationPage key="edit" mode="edit" /></ErrorBoundary>} />
              <Route path="/video" element={<ErrorBoundary key="video"><GenerationPage key="video" mode="video" /></ErrorBoundary>} />
              <Route path="/history" element={<ErrorBoundary key="history"><GenerationPage key="history" mode="all" viewHistory /></ErrorBoundary>} />
              <Route path="/profile" element={<ErrorBoundary><ProfilePage user={user} /></ErrorBoundary>} />
              {canManageDocs && <Route path="/knowledge" element={<ErrorBoundary><KnowledgePage /></ErrorBoundary>} />}
              <Route path="/help" element={<ErrorBoundary><HelpPage /></ErrorBoundary>} />
            </Routes>
            <GlobalGenBar />
          </GenerationProvider>
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
