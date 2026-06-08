import { useState, useEffect, useRef } from "react";
import { Box, TextField, Button, Typography, Paper, List, ListItem, ListItemText, Divider, IconButton, Alert, Snackbar, CircularProgress, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import { api } from "../services/api";
import { SimpleMarkdown } from "../components/SimpleMarkdown";

interface Chat {
  id: string;
  title: string;
}

interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

export const ChatPage = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  useEffect(() => { loadChats(); }, []);
  useEffect(() => { if (activeChat) loadMessages(activeChat); }, [activeChat]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, typing]);

  const loadChats = async () => {
    try {
      const res: any = await api("GET", "/chat/list");
      setChats(res.chats || []);
    } catch (e: any) {
      setError("Не удалось загрузить чаты");
    }
  };

  const loadMessages = async (id: string) => {
    try {
      const res: any = await api("GET", `/chat/${id}`);
      setMessages(res.messages || []);
    } catch {
      setMessages([]);
      setError("Не удалось загрузить сообщения");
    }
  };

  const createChat = async () => {
    try {
      const res: any = await api("POST", "/chat/create", { title: `Chat ${chats.length + 1}` });
      if (res.chat?.id) {
        setChats(prev => [...prev, res.chat]);
        setActiveChat(res.chat.id);
      }
    } catch {
      setError("Не удалось создать чат");
    }
  };

  const deleteChat = async (id: string) => {
    try {
      await api("DELETE", `/chat/${id}`);
      setChats(prev => prev.filter(c => c.id !== id));
      if (activeChat === id) setActiveChat(null);
    } catch {
      setError("Не удалось удалить чат");
    }
    setDeleteTarget(null);
  };

  const sendMessage = async () => {
    if (!input.trim() || !activeChat) return;
    const msg = input;
    setInput("");
    setLoading(true);
    setTyping(true);
    const userMsg: Message = { id: `temp-${Date.now()}`, role: "user", content: msg, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    try {
      const res: any = await api("POST", `/chat/${activeChat}/send`, { message: msg });
      const reply: Message = { id: res.id || `resp-${Date.now()}`, role: "assistant", content: res.message || res.content, created_at: new Date().toISOString() };
      setMessages(prev => [...prev, reply]);
    } catch (e: any) {
      setMessages(prev => prev.map(m => m.id === userMsg.id ? { ...m, content: `${m.content}\n\n⚠️ Ошибка отправки: ${e.message}` } : m));
      setError("Ошибка отправки сообщения");
    }
    setTyping(false);
    setLoading(false);
  };

  return (
    <Box sx={{ display: "flex", height: "calc(100vh - 100px)", gap: 2 }}>
      <Paper sx={{ width: 260, p: 2, overflow: "auto", flexShrink: 0 }}>
        <Button variant="outlined" startIcon={<AddIcon />} fullWidth onClick={createChat} sx={{ mb: 2 }}>Новый чат</Button>
        <List dense>
          {chats.length === 0 && !loading && (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", mt: 2 }}>Нет чатов</Typography>
          )}
          {chats.map(c => (
            <ListItem key={c.id} component="button" onClick={() => setActiveChat(c.id)}
              sx={{ cursor: "pointer", bgcolor: activeChat === c.id ? "action.selected" : "transparent", borderRadius: 1, mb: 0.5, textAlign: "left", display: "flex", gap: 0.5 }}>
              <ListItemText primary={c.title} primaryTypographyProps={{ noWrap: true }} sx={{ flex: 1 }} />
              <IconButton size="small" onClick={e => { e.stopPropagation(); setDeleteTarget(c.id); }} sx={{ opacity: 0.5, "&:hover": { opacity: 1 } }}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </ListItem>
          ))}
        </List>
      </Paper>
      <Paper sx={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {activeChat ? (
          <>
            <Box sx={{ flex: 1, overflow: "auto", p: 2 }}>
              {messages.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", mt: 4 }}>Начните диалог</Typography>
              )}
              {messages.map(m => (
                <Box key={m.id} sx={{ mb: 2, textAlign: m.role === "user" ? "right" : "left" }}>
                  <Paper sx={{ display: "inline-block", p: 1.5, maxWidth: "80%", bgcolor: m.role === "user" ? "primary.main" : "background.paper", color: m.role === "user" ? "primary.contrastText" : "text.primary", wordBreak: "break-word" }}>
                    {m.role === "assistant" ? <SimpleMarkdown text={m.content} /> : <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{m.content}</Typography>}
                    <Typography variant="caption" sx={{ display: "block", mt: 0.5, opacity: 0.6, textAlign: "right" }}>
                      {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </Typography>
                  </Paper>
                </Box>
              ))}
              {typing && (
                <Box sx={{ mb: 2, textAlign: "left" }}>
                  <Paper sx={{ display: "inline-flex", p: 1.5, bgcolor: "background.paper" }}>
                    <Typography variant="body2" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <CircularProgress size={12} /> ассистент печатает...
                    </Typography>
                  </Paper>
                </Box>
              )}
              <div ref={bottomRef} />
            </Box>
            <Divider />
            <Box sx={{ p: 2, display: "flex", gap: 1 }}>
              <TextField fullWidth size="small" placeholder="Введите сообщение..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage()} disabled={loading} />
              <IconButton color="primary" onClick={sendMessage} disabled={loading || !input.trim()}><SendIcon /></IconButton>
            </Box>
          </>
        ) : (
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
            <Typography color="text.secondary">Выберите или создайте чат</Typography>
          </Box>
        )}
      </Paper>
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Удалить чат?</DialogTitle>
        <DialogContent><DialogContentText>Это действие нельзя отменить. Все сообщения будут удалены.</DialogContentText></DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Отмена</Button>
          <Button color="error" onClick={() => deleteTarget && deleteChat(deleteTarget)}>Удалить</Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={!!error} autoHideDuration={4000} onClose={() => setError("")}>
        <Alert severity="warning" onClose={() => setError("")} variant="filled">{error}</Alert>
      </Snackbar>
    </Box>
  );
};
