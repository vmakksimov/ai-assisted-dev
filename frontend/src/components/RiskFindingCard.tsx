import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import type { RiskFinding } from '../api/types';
import { SeverityChip } from './SeverityChip';

export function RiskFindingCard({ finding }: { finding: RiskFinding }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" spacing={1} alignItems="center" mb={1} flexWrap="wrap">
          <SeverityChip severity={finding.severity} />
          <Chip label={finding.category} size="small" variant="outlined" />
          {finding.file_path && (
            <Typography variant="caption" color="text.secondary">
              {finding.file_path}
              {finding.line_hint ? `:${finding.line_hint}` : ''}
            </Typography>
          )}
        </Stack>
        <Typography variant="subtitle1" fontWeight={600}>
          {finding.title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {finding.description}
        </Typography>
        {finding.recommendation && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            <strong>Recommendation:</strong> {finding.recommendation}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
