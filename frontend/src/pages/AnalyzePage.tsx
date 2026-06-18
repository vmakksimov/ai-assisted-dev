import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useNavigate } from 'react-router-dom';
import { DiffInput, type DiffSubmission } from '../components/DiffInput';
import { useAnalyzeDiff } from '../hooks/useReviews';

export function AnalyzePage() {
  const navigate = useNavigate();
  const analyze = useAnalyzeDiff();

  const handleSubmit = (submission: DiffSubmission) => {
    const input =
      submission.kind === 'upload' && submission.file
        ? { kind: 'upload' as const, file: submission.file, title: submission.title }
        : { kind: 'paste' as const, diffText: submission.diffText, title: submission.title };

    analyze.mutate(input, {
      onSuccess: (review) => navigate(`/reviews/${review.id}`),
    });
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Analyze a Pull Request diff
      </Typography>
      <Typography color="text.secondary" mb={3}>
        Paste a unified diff or upload a .diff/.patch file. DevGuard AI will flag risky
        changes, write review comments, and suggest tests.
      </Typography>

      {analyze.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {analyze.error.message}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <DiffInput onSubmit={handleSubmit} submitting={analyze.isPending} />
      </Paper>
    </Box>
  );
}
