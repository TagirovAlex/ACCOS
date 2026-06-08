import { Admin, Resource, Layout, AppBar, UserMenu, useTheme, LoadingIndicator, type LayoutProps, type AppBarProps } from "react-admin";
import { MenuItem, ListItemIcon, ListItemText } from "@mui/material";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import { authProvider } from "./services/authProvider";
import { dataProvider } from "./services/dataProvider";
import { lightTheme } from "./assets/themes/light";
import { darkTheme } from "./assets/themes/dark";
import { Dashboard } from "./pages/Dashboard";
import { UserList, UserEdit, UserCreate } from "./pages/Users";
import { GroupList, GroupEdit, GroupCreate } from "./pages/Groups";
import { ChatList, ChatShow } from "./pages/Chats";
import { GenerationList, GenerationShow } from "./pages/Generations";
import { AssetList, AssetShow } from "./pages/Assets";
import { SettingsList, SettingsEdit, SettingsCreate } from "./pages/Settings";
import { BackupList } from "./pages/Backups";
import { ErrorBoundary } from "./components/ErrorBoundary";

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
  </UserMenu>
);

const CustomAppBar = (props: AppBarProps) => (
  <AppBar {...props} userMenu={<CustomUserMenu />} toolbar={<LoadingIndicator />} />
);

const CustomLayout = (props: LayoutProps) => (
  <Layout {...props} appBar={CustomAppBar} />
);

const App = () => (
  <ErrorBoundary><Admin
    authProvider={authProvider}
    dataProvider={dataProvider}
    dashboard={Dashboard}
    layout={CustomLayout}
    theme={lightTheme}
    darkTheme={darkTheme}
    requireAuth
  >
    <Resource
      name="users"
      options={{ label: "Пользователи" }}
      list={UserList}
      edit={UserEdit}
      create={UserCreate}
    />
    <Resource
      name="groups"
      options={{ label: "Группы доступа" }}
      list={GroupList}
      edit={GroupEdit}
      create={GroupCreate}
    />
    <Resource
      name="chats"
      options={{ label: "Чаты" }}
      list={ChatList}
      show={ChatShow}
    />
    <Resource
      name="generations"
      options={{ label: "Генерации" }}
      list={GenerationList}
      show={GenerationShow}
    />
    <Resource
      name="assets"
      options={{ label: "Ресурсы" }}
      list={AssetList}
      show={AssetShow}
    />
    <Resource
      name="settings"
      options={{ label: "Настройки" }}
      list={SettingsList}
      edit={SettingsEdit}
      create={SettingsCreate}
    />
    <Resource
      name="backups"
      options={{ label: "Бэкапы" }}
      list={BackupList}
    />
  </Admin></ErrorBoundary>
);

export default App;
