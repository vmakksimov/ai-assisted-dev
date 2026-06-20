import { createTheme } from '@mui/material/styles';
import type { RiskSeverity, CommentSeverity } from './api/types';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#2e5cff' },
    background: { default: '#f6f7fb' },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

/** Map a risk severity to an MUI palette color name. */
export function riskColor(
  severity: RiskSeverity | null,
): 'success' | 'info' | 'warning' | 'error' | 'default' {
  switch (severity) {
    case 'low':
      return 'success';
    case 'medium':
      return 'info';
    case 'high':
      return 'warning';
    case 'critical':
      return 'error';
    default:
      return 'default';
  }
}

export function commentColor(
  severity: CommentSeverity,
): 'default' | 'info' | 'warning' {
  switch (severity) {
    case 'info':
      return 'info';
    case 'minor':
      return 'default';
    case 'major':
      return 'warning';
  }
}
