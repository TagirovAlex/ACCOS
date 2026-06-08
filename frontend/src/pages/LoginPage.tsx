import { useState } from "react";
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from "@mui/material";
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
    <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "background.default" }}>
      <Card sx={{ maxWidth: 400, width: "100%", mx: 2 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom textAlign="center">ACCOS</Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center" mb={3}>AI Content & Chat Orchestrator</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <form onSubmit={handleSubmit}>
            <TextField label="Логин" fullWidth required margin="normal" value={username} onChange={e => setUsername(e.target.value)} />
            <TextField label="Пароль" type="password" fullWidth required margin="normal" value={password} onChange={e => setPassword(e.target.value)} />
            <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }} size="large">Войти</Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};
