import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import type { ReviewComment } from '../api/types';
import { commentColor } from '../theme';

export function ReviewCommentList({ comments }: { comments: ReviewComment[] }) {
  if (comments.length === 0) {
    return (
      <Typography color="text.secondary" variant="body2">
        No review comments.
      </Typography>
    );
  }
  return (
    <List disablePadding>
      {comments.map((c, i) => (
        <ListItem key={c.id ?? i} alignItems="flex-start" divider>
          <ListItemText
            primary={
              <span>
                <Chip
                  label={c.severity}
                  size="small"
                  color={commentColor(c.severity)}
                  sx={{ mr: 1 }}
                />
                {c.file_path && (
                  <Typography component="span" variant="caption" color="text.secondary">
                    {c.file_path}
                    {c.line_hint ? `:${c.line_hint}` : ''}
                  </Typography>
                )}
              </span>
            }
            secondary={c.comment}
          />
        </ListItem>
      ))}
    </List>
  );
}
