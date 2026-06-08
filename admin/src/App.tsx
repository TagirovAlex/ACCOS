import { useState, useMemo } from "react";
import { Admin, Resource, Layout, type LayoutProps } from "react-admin";
import { CssBaseline, ThemeProvider, createTheme, Switch, FormControlLabel, Box } from "@mui/material";
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
import { ErrorBoundary } from "./components/ErrorBoundary";

const CustomLayout = (props: LayoutProps) => {
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("theme") === "dark");

  const theme = useMemo(() => createTheme(darkMode ? darkTheme : lightTheme), [darkMode]);

  const handleToggle = () => {
    const next = !darkMode;
    setDarkMode(next);
    localStorage.setItem("theme", next ? "dark" : "light");
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ position: "fixed", top: 8, right: 16, zIndex: 9999 }}>
        <FormControlLabel
          control={<Switch checked={darkMode} onChange={handleToggle} />}
          label={darkMode ? "Dark" : "Light"}
        />
      </Box>
      <Layout {...props} />
    </ThemeProvider>
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
  </Admin></ErrorBoundary>
);

export default App;
