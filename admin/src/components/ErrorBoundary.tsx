import { Component } from "react";
import { Box, Typography, Button, Paper } from "@mui/material";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  info?: string;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(_error: Error, info: any) {
    this.setState({ info: info?.componentStack || "" });
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh", p: 3 }}>
          <Paper sx={{ maxWidth: 640, width: "100%", p: 4, textAlign: "center" }}>
            <ErrorOutlineIcon color="error" sx={{ fontSize: 64, mb: 2 }} />
            <Typography variant="h4" gutterBottom>Критическая ошибка</Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2, fontFamily: "monospace", bgcolor: "action.hover", p: 2, borderRadius: 1, textAlign: "left", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {this.state.error?.message || "Неизвестная ошибка"}
            </Typography>
            {this.state.info && (
              <Box sx={{ textAlign: "left", mt: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: "block" }}>Component stack:</Typography>
                <Box component="pre" sx={{ fontSize: 11, bgcolor: "grey.900", color: "grey.100", p: 2, borderRadius: 1, overflow: "auto", maxHeight: 300, whiteSpace: "pre-wrap" }}>
                  {this.state.info}
                </Box>
              </Box>
            )}
            <Box sx={{ mt: 3, display: "flex", gap: 2, justifyContent: "center" }}>
              <Button variant="outlined" onClick={() => window.history.back()}>Назад</Button>
              <Button variant="contained" onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}>Обновить страницу</Button>
            </Box>
          </Paper>
        </Box>
      );
    }
    return this.props.children;
  }
}
