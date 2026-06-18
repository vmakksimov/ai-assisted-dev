import Chip from '@mui/material/Chip';
import type { RiskSeverity } from '../api/types';
import { riskColor } from '../theme';

export function SeverityChip({
  severity,
  size = 'small',
}: {
  severity: RiskSeverity | null;
  size?: 'small' | 'medium';
}) {
  const label = severity ? severity.toUpperCase() : 'N/A';
  return <Chip label={label} color={riskColor(severity)} size={size} />;
}
