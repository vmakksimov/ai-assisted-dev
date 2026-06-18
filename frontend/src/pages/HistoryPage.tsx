import { useState } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import { useNavigate } from 'react-router-dom';
import type { ReviewStatus, RiskSeverity } from '../api/types';
import { SeverityChip } from '../components/SeverityChip';
import { useDeleteReview, useReviewList } from '../hooks/useReviews';

const PAGE_SIZE = 10;

export function HistoryPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [risk, setRisk] = useState<RiskSeverity | ''>('');
  const [status, setStatus] = useState<ReviewStatus | ''>('');

  const { data, isLoading, isError, error } = useReviewList({
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
    overall_risk: risk || undefined,
    status: status || undefined,
  });
  const remove = useDeleteReview();

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Review history
      </Typography>

      <Stack direction="row" spacing={2} mb={2}>
        <TextField
          select
          label="Risk"
          size="small"
          value={risk}
          onChange={(e) => {
            setRisk(e.target.value as RiskSeverity | '');
            setPage(0);
          }}
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="">All</MenuItem>
          {(['low', 'medium', 'high', 'critical'] as const).map((r) => (
            <MenuItem key={r} value={r}>
              {r}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Status"
          size="small"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as ReviewStatus | '');
            setPage(0);
          }}
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="">All</MenuItem>
          {(['completed', 'failed', 'partial', 'pending'] as const).map((s) => (
            <MenuItem key={s} value={s}>
              {s}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {isError && <Alert severity="error">{error.message}</Alert>}

      <Paper>
        {isLoading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Created</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Risk</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Files</TableCell>
                  <TableCell align="right" />
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.items.map((item) => (
                  <TableRow
                    key={item.id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/reviews/${item.id}`)}
                  >
                    <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
                    <TableCell>{item.title ?? '—'}</TableCell>
                    <TableCell>
                      <SeverityChip severity={item.overall_risk} />
                    </TableCell>
                    <TableCell>{item.status}</TableCell>
                    <TableCell align="right">{item.files_changed}</TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm('Delete this review?')) remove.mutate(item.id);
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {data && data.items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography color="text.secondary" py={3}>
                        No reviews yet. Analyze a diff to get started.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
            <TablePagination
              component="div"
              count={data?.total ?? 0}
              page={page}
              onPageChange={(_, p) => setPage(p)}
              rowsPerPage={PAGE_SIZE}
              rowsPerPageOptions={[PAGE_SIZE]}
            />
          </>
        )}
      </Paper>
    </Box>
  );
}
