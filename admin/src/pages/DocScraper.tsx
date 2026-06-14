import { useState, useEffect } from "react";
import {
  Card, CardContent, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Button,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  Box, Snackbar, Alert, Chip, IconButton, Tooltip,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import DeleteIcon from "@mui/icons-material/Delete";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import CancelIcon from "@mui/icons-material/Cancel";
import AddIcon from "@mui/icons-material/Add";
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
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [snack, setSnack] = useState<{ msg: string; severity: "success" | "error" } | null>(null);
  const [form, setForm] = useState({ site_url: "", site_name: "", max_pages: 500, max_depth: 10 });

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await apiRequest("/admin/doc-scraper/jobs");
      setJobs(data.jobs || []);
    } catch (e: any) {
      setSnack({ msg: `Load failed: ${e.message}`, severity: "error" });
    }
    setLoading(false);
  };

  useEffect(() => { loadJobs(); }, []);

  const startScrape = async () => {
    try {
      await apiRequest("/admin/doc-scraper/scrape", "POST", form);
      setSnack({ msg: "Scrape job started", severity: "success" });
      setCreateOpen(false);
      setForm({ site_url: "", site_name: "", max_pages: 500, max_depth: 10 });
      loadJobs();
    } catch (e: any) {
      setSnack({ msg: `Error: ${e.message}`, severity: "error" });
    }
  };

  const cancelJob = async (id: string) => {
    try {
      await apiRequest(`/admin/doc-scraper/jobs/${id}/cancel`, "POST");
      setSnack({ msg: "Job cancelled", severity: "success" });
      loadJobs();
    } catch (e: any) {
      setSnack({ msg: `Error: ${e.message}`, severity: "error" });
    }
  };

  const retryJob = async (id: string) => {
    try {
      await apiRequest(`/admin/doc-scraper/jobs/${id}/retry`, "POST");
      setSnack({ msg: "Job retrying", severity: "success" });
      loadJobs();
    } catch (e: any) {
      setSnack({ msg: `Error: ${e.message}`, severity: "error" });
    }
  };

  const deleteSite = async (site_name: string) => {
    try {
      await apiRequest(`/admin/doc-scraper/sites/${encodeURIComponent(site_name)}`, "DELETE");
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
          <Typography variant="h5">Documentation Scraper</Typography>
          <Box>
            <Button startIcon={<RefreshIcon />} onClick={loadJobs} sx={{ mr: 1 }}>Refresh</Button>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>New Scrape</Button>
          </Box>
        </Box>
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
                    {job.status === "queued" || job.status === "crawling" ? (
                      <Tooltip title="Cancel"><IconButton size="small" onClick={() => cancelJob(job.id)}><CancelIcon fontSize="small" /></IconButton></Tooltip>
                    ) : null}
                    {job.status === "failed" ? (
                      <Tooltip title="Retry"><IconButton size="small" onClick={() => retryJob(job.id)}><PlayArrowIcon fontSize="small" /></IconButton></Tooltip>
                    ) : null}
                    {job.status === "completed" ? (
                      <Tooltip title="Delete from RAG"><IconButton size="small" onClick={() => deleteSite(job.site_name)}><DeleteIcon fontSize="small" /></IconButton></Tooltip>
                    ) : null}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>

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
