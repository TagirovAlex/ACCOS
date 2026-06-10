import { useState, useEffect, useRef, useCallback } from "react";
import { Box, TextField, Button, Typography, Paper, List, ListItem, ListItemText, Divider, IconButton, Alert, Snackbar, CircularProgress, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Avatar, Chip } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import SettingsIcon from "@mui/icons-material/Settings";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import StopIcon from "@mui/icons-material/Stop";
import { api } from "../services/api";
import { SimpleMarkdown } from "../components/SimpleMarkdown";

interface Chat {
  id: string;
  title: string;
  system_prompt?: string;
}

interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
  tokens_input?: number;
  tokens_output?: number;
  cost?: number;
}

interface ChatPageProps {
  user?: { avatar_path?: string | null; full_name?: string; username: string };
}

export const ChatPage = ({ user }: ChatPageProps) => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [createDialog, setCreateDialog] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newSystemPrompt, setNewSystemPrompt] = useState("");
  const [settingsDialog, setSettingsDialog] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editSystemPrompt, setEditSystemPrompt] = useState("");
  const [avatarError, setAvatarError] = useState(false);
  const avatarUrl = user?.avatar_path ? `/${user.avatar_path}` : null;

  useEffect(() => { loadChats(); return () => stopPolling(); }, []);
  useEffect(() => { if (activeChat) loadMessages(activeChat); return () => stopPolling(); }, [activeChat]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, typing]);

  const loadChats = async () => {
    try {
      const res: any = await api("GET", "/chat/list");
      setChats(res.chats || []);
    } catch {
      setError("Не удалось загрузить чаты");
    }
  };

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const loadMessages = async (id: string) => {
    stopPolling();
    try {
      const res: any = await api("GET", `/chat/${id}`);
      setMessages(res.messages || []);
      if (res.has_pending) {
        setTyping(true);
        setLoading(true);
        pollingRef.current = setInterval(async () => {
          try {
            const r: any = await api("GET", `/chat/${id}`);
            setMessages(r.messages || []);
            if (!r.has_pending) {
              setTyping(false);
              setLoading(false);
              stopPolling();
            }
          } catch {
            stopPolling();
          }
        }, 3000);
      } else {
        setTyping(false);
        setLoading(false);
      }
    } catch {
      setMessages([]);
      setError("Не удалось загрузить сообщения");
    }
  };

  const openCreate = () => {
    setNewTitle("");
    setNewSystemPrompt("");
    setCreateDialog(true);
  };

  const createChat = async () => {
    try {
      const body: any = { title: newTitle.trim() || `Chat ${chats.length + 1}` };
      if (newSystemPrompt.trim()) body.system_prompt = newSystemPrompt.trim();
      const res: any = await api("POST", "/chat/create", body);
      if (res.id) {
        setChats(prev => [...prev, res]);
        setActiveChat(res.id);
      }
    } catch {
      setError("Не удалось создать чат");
    }
    setCreateDialog(false);
  };

  const openSettings = () => {
    const chat = chats.find(c => c.id === activeChat);
    if (!chat) return;
    setEditTitle(chat.title);
    setEditSystemPrompt(chat.system_prompt || "");
    setSettingsDialog(true);
  };

  const saveSettings = async () => {
    if (!activeChat) return;
    try {
      const body: any = {};
      if (editTitle.trim()) body.title = editTitle.trim();
      body.system_prompt = editSystemPrompt.trim() || null;
      const res: any = await api("PATCH", `/chat/${activeChat}`, body);
      if (res.id) {
        setChats(prev => prev.map(c => c.id === res.id ? { ...c, title: res.title, system_prompt: res.system_prompt } : c));
      }
    } catch {
      setError("Не удалось сохранить настройки");
    }
    setSettingsDialog(false);
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
      await api("POST", `/chat/${activeChat}/send`, { message: msg });
      // reload messages to get server-assigned IDs and start typing polling
      loadMessages(activeChat);
    } catch (e: any) {
      setMessages(prev => prev.map(m => m.id === userMsg.id ? { ...m, content: `${m.content}\n\n⚠️ Ошибка отправки: ${e.message}` } : m));
      setError("Ошибка отправки сообщения");
      setTyping(false);
      setLoading(false);
    }
  };

  const cancelGeneration = async () => {
    if (!activeChat) return;
    try {
      await api("POST", `/chat/${activeChat}/cancel`);
    } catch {
      // ignore
    }
    setTyping(false);
    setLoading(false);
    stopPolling();
  };

  const activeChatData = chats.find(c => c.id === activeChat);

  return (
    <Box sx={{ display: "flex", height: "100%", minHeight: 0, gap: 2 }}>
      <Paper sx={{ width: 260, p: 2, overflow: "auto", flexShrink: 0, borderRadius: 2, display: "flex", flexDirection: "column" }}>
        <Button variant="outlined" startIcon={<AddIcon />} fullWidth onClick={openCreate} sx={{ mb: 2 }}>Новый чат</Button>
        <List dense sx={{ flex: 1, overflow: "auto" }}>
          {chats.length === 0 && !loading && (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", mt: 2 }}>Нет чатов</Typography>
          )}
          {chats.map(c => (
            <ListItem key={c.id} component="button" onClick={() => setActiveChat(c.id)}
              sx={{ cursor: "pointer", bgcolor: activeChat === c.id ? "action.selected" : "transparent", borderRadius: 2, mb: 0.5, textAlign: "left", display: "flex", gap: 0.5, color: "text.primary" }}>
              <ListItemText primary={c.title} primaryTypographyProps={{ noWrap: true, color: "text.primary" }} sx={{ flex: 1 }} />
              <IconButton size="small" onClick={e => { e.stopPropagation(); setDeleteTarget(c.id); }} sx={{ opacity: 0.5, "&:hover": { opacity: 1 } }}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </ListItem>
          ))}
        </List>
      </Paper>
      <Paper sx={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", borderRadius: 2 }}>
        {activeChat ? (
          <>
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", px: 2, py: 1, borderBottom: 1, borderColor: "divider" }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Typography variant="subtitle2" color="text.primary">{activeChatData?.title}</Typography>
                {activeChatData?.system_prompt && (
                  <Chip label="System" size="small" color="info" variant="outlined" sx={{ height: 20, fontSize: 11, color: "info.light" }} />
                )}
              </Box>
              <IconButton size="small" onClick={openSettings} title="Настройки чата">
                <SettingsIcon fontSize="small" />
              </IconButton>
            </Box>
            <Box sx={{ flex: 1, overflow: "auto", p: 2 }}>
              {messages.length === 0 && (
                <Box sx={{ textAlign: "center", mt: 8 }}>
                  <SmartToyIcon sx={{ fontSize: 48, color: "text.disabled", mb: 2 }} />
                  <Typography variant="body2" color="text.secondary">Начните диалог</Typography>
                </Box>
              )}
              {messages.map(m => {
                const isUser = m.role === "user";
                return (
                  <Box key={m.id} sx={{ mb: 2, display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", gap: 1 }}>
                    {!isUser && <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.main", mt: 0.5 }}><SmartToyIcon sx={{ fontSize: 18 }} /></Avatar>}
                    <Box sx={{ maxWidth: "70%" }}>
                      <Paper sx={{ p: 1.5, bgcolor: isUser ? "primary.main" : "background.paper", color: isUser ? "primary.contrastText" : "text.primary", borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px" }}>
                        {isUser ? (
                          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{m.content}</Typography>
                        ) : (
                          <SimpleMarkdown text={m.content} />
                        )}
                      </Paper>
                      <Typography variant="caption" sx={{ display: "block", mt: 0.25, opacity: 0.5, textAlign: isUser ? "right" : "left", px: 1 }}>
                        {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        {!isUser && (m.tokens_input != null || m.tokens_output != null) && (
                          <> · ↑{m.tokens_input ?? 0} ↓{m.tokens_output ?? 0}</>
                        )}
                        {!isUser && m.cost != null && (
                          <> · {Number(m.cost.toFixed(2))} MS</>
                        )}
                      </Typography>
                    </Box>
                    {isUser && <Avatar src={avatarError ? undefined : (avatarUrl || undefined)} onError={() => setAvatarError(true)} sx={{ width: 32, height: 32, bgcolor: "success.main", mt: 0.5 }}>{user?.full_name?.[0] || user?.username?.[0] || "U"}</Avatar>}
                  </Box>
                );
              })}
              {typing && (
                <Box sx={{ display: "flex", gap: 1, mb: 2, alignItems: "center" }}>
                  <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.main" }}><SmartToyIcon sx={{ fontSize: 18 }} /></Avatar>
                  <Paper sx={{ p: 1.5, borderRadius: "16px 16px 16px 4px", bgcolor: "background.paper", display: "flex", alignItems: "center", gap: 1 }}>
                    <CircularProgress size={12} />
                    <Typography variant="body2" color="text.secondary">ассистент печатает...</Typography>
                    <IconButton size="small" onClick={cancelGeneration} sx={{ ml: 1, color: "error.main", bgcolor: "action.hover", "&:hover": { bgcolor: "error.main", color: "white" } }} title="Остановить">
                      <StopIcon fontSize="small" />
                    </IconButton>
                  </Paper>
                </Box>
              )}
              <div ref={bottomRef} />
            </Box>
            <Divider />
            <Box sx={{ p: 2, display: "flex", gap: 1 }}>
              <TextField fullWidth size="small" placeholder="Введите сообщение..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage()} disabled={loading} sx={{ "& .MuiOutlinedInput-root": { borderRadius: 3 } }} />
              <IconButton color="primary" onClick={sendMessage} disabled={loading || !input.trim()} sx={{ bgcolor: "primary.main", color: "primary.contrastText", "&:hover": { bgcolor: "primary.dark" }, "&.Mui-disabled": { bgcolor: "action.disabledBackground" } }}>
                <SendIcon />
              </IconButton>
            </Box>
          </>
        ) : (
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", flexDirection: "column", gap: 2 }}>
            <SmartToyIcon sx={{ fontSize: 64, color: "text.disabled" }} />
            <Typography color="text.secondary">Выберите или создайте чат</Typography>
          </Box>
        )}
      </Paper>

      {/* Create dialog */}
      <Dialog open={createDialog} onClose={() => setCreateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ color: "text.primary" }}>Новый чат</DialogTitle>
        <DialogContent>
          <TextField autoFocus label="Название" fullWidth value={newTitle} onChange={e => setNewTitle(e.target.value)} sx={{ mb: 2, mt: 1 }} />
          <TextField label="Системный промпт (необязательно)" fullWidth multiline minRows={3} value={newSystemPrompt} onChange={e => setNewSystemPrompt(e.target.value)} placeholder="Например: Ты — профессиональный помощник..." />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialog(false)}>Отмена</Button>
          <Button variant="contained" onClick={createChat}>Создать</Button>
        </DialogActions>
      </Dialog>

      {/* Settings dialog */}
      <Dialog open={settingsDialog} onClose={() => setSettingsDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ color: "text.primary" }}>Настройки чата</DialogTitle>
        <DialogContent>
          <TextField autoFocus label="Название" fullWidth value={editTitle} onChange={e => setEditTitle(e.target.value)} sx={{ mb: 2, mt: 1 }} />
          <TextField label="Системный промпт" fullWidth multiline minRows={3} value={editSystemPrompt} onChange={e => setEditSystemPrompt(e.target.value)} placeholder="Оставьте пустым, чтобы убрать системный промпт" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialog(false)}>Отмена</Button>
          <Button variant="contained" onClick={saveSettings}>Сохранить</Button>
        </DialogActions>
      </Dialog>

      {/* Delete dialog */}
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
