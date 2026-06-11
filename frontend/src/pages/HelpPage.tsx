import { useEffect, useState } from "react";
import { Box, Typography, Card, CardContent, LinearProgress, Link as MuiLink, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Divider } from "@mui/material";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

const mdComponents: Components = {
  h1: ({ children }) => <Typography variant="h4" fontWeight={700} mt={3} mb={1.5}>{children}</Typography>,
  h2: ({ children }) => <Typography variant="h5" fontWeight={600} mt={3} mb={1}>{children}</Typography>,
  h3: ({ children }) => <Typography variant="h6" fontWeight={600} mt={2} mb={0.5}>{children}</Typography>,
  p: ({ children }) => <Typography variant="body2" sx={{ mb: 1, lineHeight: 1.7 }}>{children}</Typography>,
  a: ({ href, children }) => <MuiLink href={href} target="_blank" rel="noopener">{children}</MuiLink>,
  ul: ({ children }) => <Box component="ul" sx={{ pl: 3, mb: 1 }}>{children}</Box>,
  ol: ({ children }) => <Box component="ol" sx={{ pl: 3, mb: 1 }}>{children}</Box>,
  li: ({ children }) => <Typography variant="body2" component="li" sx={{ mb: 0.25, lineHeight: 1.7 }}>{children}</Typography>,
  code: ({ className, children, ...props }) => {
    const isInline = !className;
    if (isInline) {
      return <Box component="code" sx={{ bgcolor: "action.hover", px: 0.5, py: 0.25, borderRadius: 0.5, fontSize: "0.85em" }}>{children}</Box>;
    }
    return (
      <Paper variant="outlined" sx={{ p: 1.5, my: 1, bgcolor: "grey.900", overflow: "auto" }}>
        <Box component="pre" sx={{ m: 0, fontSize: "0.85rem", color: "grey.100", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          <code className={className} {...props}>{children}</code>
        </Box>
      </Paper>
    );
  },
  table: ({ children }) => (
    <TableContainer component={Paper} variant="outlined" sx={{ my: 1.5 }}>
      <Table size="small">{children}</Table>
    </TableContainer>
  ),
  thead: ({ children }) => <TableHead>{children}</TableHead>,
  tbody: ({ children }) => <TableBody>{children}</TableBody>,
  tr: ({ children }) => <TableRow>{children}</TableRow>,
  th: ({ children }) => <TableCell sx={{ fontWeight: 700 }}>{children}</TableCell>,
  td: ({ children }) => <TableCell>{children}</TableCell>,
  blockquote: ({ children }) => (
    <Box sx={{ borderLeft: 3, borderColor: "primary.main", pl: 2, my: 1, color: "text.secondary" }}>
      {children}
    </Box>
  ),
  hr: () => <Divider sx={{ my: 2 }} />,
  strong: ({ children }) => <strong>{children}</strong>,
  em: ({ children }) => <em>{children}</em>,
};

function adminToken(): string | null {
  return localStorage.getItem("token") || null;
}

export const HelpPage = () => {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = adminToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    fetch("/api/v1/help", { headers })
      .then(r => r.json())
      .then(data => { setContent(data.content || ""); })
      .catch(() => { setContent(""); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LinearProgress />;

  return (
    <Box sx={{ maxWidth: 800, mx: "auto", py: 3, px: 2 }}>
      <Typography variant="h5" fontWeight={700} mb={3}>Помощь</Typography>
      <Card>
        <CardContent>
          {content ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
              {content}
            </ReactMarkdown>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 4 }}>
              Раздел помощи пока не заполнен. Обратитесь к администратору.
            </Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};
