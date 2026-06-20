import type { ReactNode } from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import ShieldIcon from '@mui/icons-material/Shield';
import { Link as RouterLink, useLocation } from 'react-router-dom';

export function Layout({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <ShieldIcon sx={{ mr: 1 }} />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
            DevGuard AI
          </Typography>
          <Button
            component={RouterLink}
            to="/"
            color="inherit"
            variant={pathname === '/' ? 'outlined' : 'text'}
          >
            Analyze
          </Button>
          <Button
            component={RouterLink}
            to="/history"
            color="inherit"
            variant={pathname.startsWith('/history') ? 'outlined' : 'text'}
          >
            History
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {children}
      </Container>
    </Box>
  );
}
