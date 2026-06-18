import { useState } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Typography from '@mui/material/Typography';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { RiskFindingCard } from '../components/RiskFindingCard';
import { ReviewCommentList } from '../components/ReviewCommentList';
import { SeverityChip } from '../components/SeverityChip';
import { TestSuggestionList } from '../components/TestSuggestionList';
import { useReview } from '../hooks/useReviews';

export function ReviewDetailPage() {
  const { id = '' } = useParams();
  const { data: review, isLoading, isError, error } = useReview(id);
  const [tab, setTab] = useState(0);
  const [showDiff, setShowDiff] = useState(false);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={6}>
        <CircularProgress />
      </Box>
    );
  }
  if (isError || !review) {
    return <Alert severity="error">{error?.message ?? 'Review not found.'}</Alert>;
  }

  return (
    <Box>
      <Button component={RouterLink} to="/history" sx={{ mb: 2 }}>
        ← Back to history
      </Button>

      {review.status === 'failed' && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Analysis failed: {review.error_message}
        </Alert>
      )}
      {review.status === 'partial' && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Partial analysis — some sections may be incomplete.
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
          <SeverityChip severity={review.overall_risk} size="medium" />
          <Typography variant="h5" fontWeight={700}>
            {review.title ?? 'Untitled review'}
          </Typography>
        </Stack>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {review.summary ?? 'No summary available.'}
        </Typography>
        <Stack direction="row" spacing={3} sx={{ mt: 2 }}>
          <Typography variant="body2">Files: {review.stats.files_changed}</Typography>
          <Typography variant="body2" color="success.main">
            +{review.stats.additions}
          </Typography>
          <Typography variant="body2" color="error.main">
            −{review.stats.deletions}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {review.model_name}
          </Typography>
        </Stack>
        <Box sx={{ mt: 2 }}>
          <Button size="small" onClick={() => setShowDiff((v) => !v)}>
            {showDiff ? 'Hide diff' : 'Show diff'}
          </Button>
          <Collapse in={showDiff}>
            <Box
              component="pre"
              sx={{
                mt: 1,
                p: 2,
                bgcolor: 'grey.900',
                color: 'grey.100',
                borderRadius: 1,
                overflowX: 'auto',
                fontSize: 12,
                fontFamily: 'monospace',
              }}
            >
              {review.diff_text}
            </Box>
          </Collapse>
        </Box>
      </Paper>

      <Paper>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ px: 2 }}>
          <Tab label={`Risk findings (${review.risk_findings.length})`} />
          <Tab label={`Review comments (${review.review_comments.length})`} />
          <Tab label={`Test suggestions (${review.test_suggestions.length})`} />
        </Tabs>
        <Divider />
        <Box sx={{ p: 3 }}>
          {tab === 0 && (
            <Stack spacing={2}>
              {review.risk_findings.length === 0 ? (
                <Typography color="text.secondary">No risk findings.</Typography>
              ) : (
                review.risk_findings.map((f, i) => (
                  <RiskFindingCard key={f.id ?? i} finding={f} />
                ))
              )}
            </Stack>
          )}
          {tab === 1 && <ReviewCommentList comments={review.review_comments} />}
          {tab === 2 && <TestSuggestionList tests={review.test_suggestions} />}
        </Box>
      </Paper>
    </Box>
  );
}
