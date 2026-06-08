import { Admin, Resource, Layout, AppBar, UserMenu, useTheme, Logout, ToggleThemeButton, LoadingIndicator, type LayoutProps, type AppBarProps } from "react-admin";
import { MenuItem, ListItemIcon, ListItemText, Box, Typography } from "@mui/material";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import { authProvider } from "./services/authProvider";
import { dataProvider } from "./services/dataProvider";
import { lightTheme } from "./assets/themes/light";
import { darkTheme } from "./assets/themes/dark";
import { Dashboard } from "./pages/Dashboard";
import { UserList, UserEdit, UserCreate, UserShow } from "./pages/Users";
import { GroupList, GroupEdit, GroupCreate } from "./pages/Groups";
import { ChatList, ChatShow } from "./pages/Chats";
import { GenerationList, GenerationShow } from "./pages/Generations";
import { AssetList, AssetShow } from "./pages/Assets";
import { SettingsList, SettingsEdit, SettingsCreate } from "./pages/Settings";
import { BackupList } from "./pages/Backups";
import "./App.css";

const ThemeMenuItem = () => {
  const [theme, setTheme] = useTheme();
  return (
    <MenuItem onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      <ListItemIcon>{theme === "dark" ? <LightModeIcon fontSize="small" /> : <DarkModeIcon fontSize="small" />}</ListItemIcon>
      <ListItemText>{theme === "dark" ? "Светлая тема" : "Тёмная тема"}</ListItemText>
    </MenuItem>
  );
};

const CustomUserMenu = () => (
  <UserMenu>
    <ThemeMenuItem />
    <Logout />
  </UserMenu>
);

const CustomToolbar = () => (
  <Box sx={{ display: "flex", alignItems: "center", mr: 2, gap: 1 }}>
    <LoadingIndicator />
    <ToggleThemeButton />
  </Box>
);

const CustomAppBar = (props: AppBarProps) => (
  <AppBar {...props} userMenu={<CustomUserMenu />} toolbar={<CustomToolbar />}>
    <Typography variant="h6" fontWeight={700} noWrap sx={{ ml: 1, letterSpacing: "-0.01em" }}>
      ACCOS Admin
    </Typography>
  </AppBar>
);

const CustomLayout = (props: LayoutProps) => (
  <Layout {...props} appBar={CustomAppBar} />
);

const App = () => (
  <Admin
    authProvider={authProvider}
    dataProvider={dataProvider}
    dashboard={Dashboard}
    layout={CustomLayout}
    theme={lightTheme}
    darkTheme={darkTheme}
    requireAuth
  >
    {(permissions: string) => {
      const adminRole = localStorage.getItem("admin_role") || (permissions === "admin" ? "super_admin" : "none");
      const isSuperAdmin = adminRole === "super_admin";
      return (
        <>
          <Resource name="users" options={{ label: "👥 Пользователи" }} list={UserList} edit={UserEdit} create={UserCreate} show={UserShow} />
          {isSuperAdmin && <Resource name="groups" options={{ label: "🔐 Группы доступа" }} list={GroupList} edit={GroupEdit} create={GroupCreate} />}
          {isSuperAdmin && <Resource name="chats" options={{ label: "💬 Чаты" }} list={ChatList} show={ChatShow} />}
          {isSuperAdmin && <Resource name="generations" options={{ label: "🎨 Генерации" }} list={GenerationList} show={GenerationShow} />}
          {isSuperAdmin && <Resource name="assets" options={{ label: "🖼 Ресурсы" }} list={AssetList} show={AssetShow} />}
          {isSuperAdmin && <Resource name="settings" options={{ label: "⚙ Настройки" }} list={SettingsList} edit={SettingsEdit} create={SettingsCreate} />}
          {isSuperAdmin && <Resource name="backups" options={{ label: "📦 Бэкапы" }} list={BackupList} />}
        </>
      );
    }}
  </Admin>
);

export default App;
