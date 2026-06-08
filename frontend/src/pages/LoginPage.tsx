import { useState } from "react";
import { Box, Card, CardContent, TextField, Button, Typography, Alert, Avatar } from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import { login } from "../services/auth";

import type { User } from "../services/auth";

interface Props {
  onLogin: (user: User) => void;
}

export const LoginPage = ({ onLogin }: Props) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const user = await login(username, password);
      onLogin(user);
    } catch (err: any) {
      setError(err.message || "Login failed");
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #1a237e 0%, #1976d2 50%, #42a5f5 100%)" }}>
      <Card sx={{ maxWidth: 400, width: "100%", mx: 2, overflow: "visible" }}>
        <CardContent sx={{ p: 4, display: "flex", flexDirection: "column", alignItems: "center" }}>
          <Avatar sx={{ bgcolor: "primary.main", width: 64, height: 64, mb: 2, boxShadow: "0 4px 12px rgba(25,118,210,0.3)" }}>
            <AutoAwesomeIcon sx={{ fontSize: 32 }} />
          </Avatar>
          <Typography variant="h5" fontWeight={700} gutterBottom>ACCOS</Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>AI Content & Chat Orchestrator</Typography>
          {error && <Alert severity="error" sx={{ mb: 2, width: "100%" }}>{error}</Alert>}
          <form onSubmit={handleSubmit} style={{ width: "100%" }}>
            <TextField label="Логин" fullWidth required margin="normal" value={username} onChange={e => setUsername(e.target.value)} autoFocus />
            <TextField label="Пароль" type="password" fullWidth required margin="normal" value={password} onChange={e => setPassword(e.target.value)} />
            <Button type="submit" variant="contained" fullWidth sx={{ mt: 3, py: 1.2 }} size="large">Войти</Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};
