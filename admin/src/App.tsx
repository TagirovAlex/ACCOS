import { useState, useMemo, useContext, createContext } from "react";
import { Admin, Resource, Layout, AppBar, UserMenu, type LayoutProps, type AppBarProps } from "react-admin";
import { CssBaseline, ThemeProvider, createTheme, MenuItem, ListItemIcon, ListItemText } from "@mui/material";
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

const ThemeCtx = createContext<{ dark: boolean; toggle: () => void }>({ dark: false, toggle: () => {} });

const ThemeMenuItem = () => {
  const { dark, toggle } = useContext(ThemeCtx);
  return (
    <MenuItem onClick={toggle}>
      <ListItemIcon>{dark ? <LightModeIcon fontSize="small" /> : <DarkModeIcon fontSize="small" />}</ListItemIcon>
      <ListItemText>{dark ? "Светлая тема" : "Тёмная тема"}</ListItemText>
    </MenuItem>
  );
};

const CustomUserMenu = () => (
  <UserMenu>
    <ThemeMenuItem />
  </UserMenu>
);

const CustomAppBar = (props: AppBarProps) => (
  <AppBar {...props} userMenu={<CustomUserMenu />} />
);

const CustomLayout = (props: LayoutProps) => {
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("theme") === "dark");
  const theme = useMemo(() => createTheme(darkMode ? darkTheme : lightTheme), [darkMode]);
  const toggle = () => {
    const next = !darkMode;
    setDarkMode(next);
    localStorage.setItem("theme", next ? "dark" : "light");
  };
  return (
    <ThemeCtx.Provider value={{ dark: darkMode, toggle }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Layout {...props} appBar={CustomAppBar} />
      </ThemeProvider>
    </ThemeCtx.Provider>
  );
};

const App = () => (
  <ErrorBoundary><Admin
    authProvider={authProvider}
    dataProvider={dataProvider}
    dashboard={Dashboard}
    layout={CustomLayout}
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
