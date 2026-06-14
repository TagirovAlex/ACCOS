import { useState, useEffect } from "react";
import {
  Card, CardContent, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Button,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  Box, Snackbar, Alert, Chip, IconButton, Tooltip, ToggleButtonGroup, ToggleButton,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import DeleteIcon from "@mui/icons-material/Delete";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import AddIcon from "@mui/icons-material/Add";
import ViewListIcon from "@mui/icons-material/ViewList";
import GridViewIcon from "@mui/icons-material/GridView";
import LanguageIcon from "@mui/icons-material/Language";
import { apiRequest } from "../services/api";

interface ScrapeJob {
  id: string;
  site_url: string;
  site_name: string;
  status: string;
  pages_found: number;
  pages_scraped: number;
  chunks_created: number;
  chunks_ingested: number;
  errors: string[];
  max_pages: number;
  max_depth: number;
  created_at: string;
  completed_at: string | null;
}

const statusColors: Record<string, string> = {
  queued: "warning",
  crawling: "info",
  processing: "secondary",
  ingesting: "primary",
  completed: "success",
  failed: "error",
  cancelled: "default",
};

export const DocScraperAccess = () => {
  const [jobs, setJobs] = useState<ScrapeJob[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [snack, setSnack] = useState<{ msg: string; severity: "success" | "error" } | null>(null);
  const [form, setForm] = useState({ site_url: "", site_name: "", max_pages: 500, max_depth: 10 });
  const [view, setView] = useState<"list" | "tiles">(() => (localStorage.getItem("doc_scraper_view") as "list" | "tiles") ?? "list");

  const loadJobs = async () => {
    try {
      const data: any = await apiRequest("GET", "/admin/doc-scraper/jobs");
      setJobs(data.jobs || []);
    } catch (e: any) {
      setSnack({ msg: `Load failed: ${e.message}`, severity: "error" });
    }
  };

  useEffect(() => { loadJobs(); }, []);

  const startScrape = async () => {
    try {
      await apiRequest("POST", "/admin/doc-scraper/scrape", form);
      setSnack({ msg: "Scrape job started", severity: "success" });
      setCreateOpen(false);
      setForm({ site_url: "", site_name: "", max_pages: 500, max_depth: 10 });
      loadJobs();
    } catch (e: any) {
      setSnack({ msg: `Error: ${e.message}`, severity: "error" });
    }
  };

  const [confirmDelete, setConfirmDelete] = useState<{ id: string; name: string; type: "job" | "rag" } | null>(null);

  const pauseJob = async (id: string) => {
    try {
      await apiRequest("POST", `/admin/doc-scraper/jobs/${id}/cancel`);
      setSnack({ msg: "Job paused", severity: "success" });
      loadJobs();
    } catch (e: any) {
      setSnack({ msg: `Error: ${e.message}`, severity: "error" });
    }
  };

  const runJob = async (id: string) => {
    try {
      await apiRequest("POST", `/admin/doc-scraper/jobs/${id}/retry`);
      setSnack({ msg: "Job started", severity: "success" });
      loadJobs();
    } catch (e: any) {
      setSnack({ msg: `Error: ${e.message}`, severity: "error" });
    }
  };

  const deleteJob = async (id: string) => {
    try {
      await apiRequest("DELETE", `/admin/doc-scraper/jobs/${id}`);
      setSnack({ msg: "Job deleted", severity: "success" });
      loadJobs();
    } catch (e: any) {
      setSnack({ msg: `Error: ${e.message}`, severity: "error" });
    }
  };

  const deleteSite = async (site_name: string) => {
    try {
      await apiRequest("DELETE", `/admin/doc-scraper/sites/${encodeURIComponent(site_name)}`);
      setSnack({ msg: "Site data removed from RAG", severity: "success" });
      loadJobs();
    } catch (e: any) {
      setSnack({ msg: `Error: ${e.message}`, severity: "error" });
    }
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <LanguageIcon color="primary" fontSize="large" />
            <Typography variant="h5">Documentation Scraper</Typography>
          </Box>
          <Box display="flex" gap={1} alignItems="center">
            <ToggleButtonGroup value={view} exclusive size="small" onChange={(_, v) => { if (v) { setView(v); localStorage.setItem("doc_scraper_view", v); }}}>
              <ToggleButton value="list"><ViewListIcon fontSize="small" /></ToggleButton>
              <ToggleButton value="tiles"><GridViewIcon fontSize="small" /></ToggleButton>
            </ToggleButtonGroup>
            <Button startIcon={<RefreshIcon />} onClick={loadJobs} sx={{ mr: 1 }}>Refresh</Button>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>New Scrape</Button>
          </Box>
        </Box>
        {view === "list" ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Site</TableCell>
                <TableCell>URL</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Found</TableCell>
                <TableCell align="right">Scraped</TableCell>
                <TableCell align="right">Chunks</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {jobs.length === 0 ? (
                <TableRow><TableCell colSpan={7} align="center">No scrape jobs yet</TableCell></TableRow>
              ) : jobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell>{job.site_name}</TableCell>
                  <TableCell style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>{job.site_url}</TableCell>
                  <TableCell><Chip label={job.status} color={(statusColors[job.status] as any) || "default"} size="small" /></TableCell>
                  <TableCell align="right">{job.pages_found}</TableCell>
                  <TableCell align="right">{job.pages_scraped}</TableCell>
                  <TableCell align="right">{job.chunks_ingested}</TableCell>
                  <TableCell align="right">
                    {["queued","crawling","processing","ingesting"].includes(job.status) && (
                      <Tooltip title="Pause"><IconButton size="small" onClick={() => pauseJob(job.id)}><PauseIcon fontSize="small" /></IconButton></Tooltip>
                    )}
                    {["failed","cancelled"].includes(job.status) && (
                      <Tooltip title="Run"><IconButton size="small" onClick={() => runJob(job.id)}><PlayArrowIcon fontSize="small" /></IconButton></Tooltip>
                    )}
                    <Tooltip title="Delete job"><IconButton size="small" onClick={() => setConfirmDelete({id: job.id, name: job.site_name, type: "job"})}><DeleteIcon fontSize="small" /></IconButton></Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        ) : (
          <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 2 }}>
            {jobs.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 2, gridColumn: "1/-1", textAlign: "center" }}>No scrape jobs yet</Typography>
            ) : jobs.map((job) => (
              <Card key={job.id} sx={{ height: "100%", display: "flex", flexDirection: "column", "&:hover": { transform: "translateY(-2px)", boxShadow: 2 } }}>
                <CardContent sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 0.5 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle1" fontWeight={600}>{job.site_name}</Typography>
                    <Chip label={job.status} color={(statusColors[job.status] as any) || "default"} size="small" />
                  </Box>
                  <Typography variant="caption" color="text.secondary" noWrap>{job.site_url}</Typography>
                  <Box display="flex" gap={1} flexWrap="wrap" mt={1}>
                    <Chip label={`${job.pages_found} found`} size="small" variant="outlined" />
                    <Chip label={`${job.pages_scraped} scraped`} size="small" variant="outlined" />
                    <Chip label={`${job.chunks_ingested} chunks`} size="small" variant="outlined" />
                  </Box>
                  <Box display="flex" gap={0.5} mt="auto" pt={1}>
                    {["queued","crawling","processing","ingesting"].includes(job.status) && (
                      <Button size="small" color="warning" startIcon={<PauseIcon />} onClick={() => pauseJob(job.id)}>Pause</Button>
                    )}
                    {["failed","cancelled"].includes(job.status) && (
                      <Button size="small" color="primary" startIcon={<PlayArrowIcon />} onClick={() => runJob(job.id)}>Run</Button>
                    )}
                    <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => setConfirmDelete({id: job.id, name: job.site_name, type: "job"})}>Delete</Button>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Box>
        )}
      </CardContent>

      <Dialog open={!!confirmDelete} onClose={() => setConfirmDelete(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Delete?</DialogTitle>
        <DialogContent>
          <Typography>{confirmDelete?.type === "rag" ? `Remove all RAG data for "${confirmDelete?.name}"?` : `Delete job "${confirmDelete?.name}"?`}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDelete(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={async () => {
            if (confirmDelete?.type === "rag") await deleteSite(confirmDelete.id);
            else await deleteJob(confirmDelete!.id);
            setConfirmDelete(null);
          }}>Delete</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Start Documentation Scrape</DialogTitle>
        <DialogContent>
          <TextField label="Site URL" fullWidth margin="dense" value={form.site_url} onChange={(e) => setForm({ ...form, site_url: e.target.value })} placeholder="https://docs.example.com" />
          <TextField label="Site Name" fullWidth margin="dense" value={form.site_name} onChange={(e) => setForm({ ...form, site_name: e.target.value })} placeholder="Example Docs" />
          <TextField label="Max Pages" type="number" fullWidth margin="dense" value={form.max_pages} onChange={(e) => setForm({ ...form, max_pages: parseInt(e.target.value) || 500 })} />
          <TextField label="Max Depth" type="number" fullWidth margin="dense" value={form.max_depth} onChange={(e) => setForm({ ...form, max_depth: parseInt(e.target.value) || 10 })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={startScrape} disabled={!form.site_url || !form.site_name}>Start</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
        {snack ? <Alert severity={snack.severity} onClose={() => setSnack(null)}>{snack.msg}</Alert> : undefined}
      </Snackbar>
    </Card>
  );
};
