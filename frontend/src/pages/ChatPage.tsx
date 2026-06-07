import { useState, useEffect, useRef } from "react";
import { Box, TextField, Button, Typography, Paper, List, ListItem, ListItemText, Divider, IconButton } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AddIcon from "@mui/icons-material/Add";
import { api } from "../services/api";

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
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { loadChats(); }, []);
  useEffect(() => { if (activeChat) loadMessages(activeChat); }, [activeChat]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const loadChats = async () => {
    try {
      const res: any = await api("GET", "/chat/list");
      setChats(res.chats || []);
    } catch { /* ignore */ }
  };

  const loadMessages = async (id: string) => {
    try {
      const res: any = await api("GET", `/chat/${id}`);
      setMessages(res.messages || []);
    } catch { setMessages([]); }
  };

  const createChat = async () => {
    try {
      const res: any = await api("POST", "/chat/create", { title: `Chat ${chats.length + 1}` });
      if (res.chat?.id) {
        setChats(prev => [...prev, res.chat]);
        setActiveChat(res.chat.id);
      }
    } catch { /* ignore */ }
  };

  const sendMessage = async () => {
    if (!input.trim() || !activeChat) return;
    setLoading(true);
    const msg = input;
    setInput("");
    try {
      const res: any = await api("POST", `/chat/${activeChat}/send`, { message: msg });
      setMessages(res.messages || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  return (
    <Box sx={{ display: "flex", height: "calc(100vh - 100px)", gap: 2 }}>
      <Paper sx={{ width: 260, p: 2, overflow: "auto", flexShrink: 0 }}>
        <Button variant="outlined" startIcon={<AddIcon />} fullWidth onClick={createChat} sx={{ mb: 2 }}>Новый чат</Button>
        <List dense>
          {chats.map(c => (
            <ListItem key={c.id} component="button" onClick={() => setActiveChat(c.id)}
              sx={{ cursor: "pointer", bgcolor: activeChat === c.id ? "action.selected" : "transparent", borderRadius: 1, mb: 0.5, textAlign: "left", display: "block" }}>
              <ListItemText primary={c.title} primaryTypographyProps={{ noWrap: true }} />
            </ListItem>
          ))}
        </List>
      </Paper>
      <Paper sx={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {activeChat ? (
          <>
            <Box sx={{ flex: 1, overflow: "auto", p: 2 }}>
              {messages.map(m => (
                <Box key={m.id} sx={{ mb: 2, textAlign: m.role === "user" ? "right" : "left" }}>
                  <Paper sx={{ display: "inline-block", p: 1.5, bgcolor: m.role === "user" ? "primary.main" : "background.paper", color: m.role === "user" ? "primary.contrastText" : "text.primary" }}>
                    <Typography variant="body2">{m.content}</Typography>
                  </Paper>
                </Box>
              ))}
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
    </Box>
  );
};
