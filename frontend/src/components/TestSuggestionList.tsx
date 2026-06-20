import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import type { TestSuggestion } from '../api/types';

function priorityColor(p: TestSuggestion['priority']): 'default' | 'info' | 'error' {
  if (p === 'high') return 'error';
  if (p === 'medium') return 'info';
  return 'default';
}

export function TestSuggestionList({ tests }: { tests: TestSuggestion[] }) {
  if (tests.length === 0) {
    return (
      <Typography color="text.secondary" variant="body2">
        No test suggestions.
      </Typography>
    );
  }
  return (
    <Stack spacing={2}>
      {tests.map((t, i) => (
        <Paper key={t.id ?? i} variant="outlined" sx={{ p: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center" mb={1} flexWrap="wrap">
            <Chip label={t.test_type} size="small" color="primary" variant="outlined" />
            <Chip label={`priority: ${t.priority}`} size="small" color={priorityColor(t.priority)} />
            <Typography variant="subtitle2">{t.target}</Typography>
          </Stack>
          <Typography variant="body2" color="text.secondary">
            {t.description}
          </Typography>
          {t.example_code && (
            <Box
              component="pre"
              sx={{
                mt: 1,
                p: 1.5,
                bgcolor: 'grey.100',
                borderRadius: 1,
                overflowX: 'auto',
                fontSize: 12,
                fontFamily: 'monospace',
              }}
            >
              {t.example_code}
            </Box>
          )}
        </Paper>
      ))}
    </Stack>
  );
}
