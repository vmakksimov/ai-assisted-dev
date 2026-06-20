import { useRef, useState } from 'react';
import type { DragEvent } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';
import { decodeDiffFile } from './diffFileDecoder';

const MAX_DIFF_BYTES = 200_000;
const ALLOWED_EXTENSIONS = ['.diff', '.patch', '.txt'];
const COMPACT_ROWS = 12;
const EXPANDED_ROWS = 32;

export interface DiffSubmission {
  kind: 'paste' | 'upload';
  diffText: string;
  file?: File;
  title?: string;
}

function byteLength(text: string): number {
  return new TextEncoder().encode(text).length;
}

function hasAllowedExtension(name: string): boolean {
  return ALLOWED_EXTENSIONS.some((ext) => name.toLowerCase().endsWith(ext));
}

export function DiffInput({
  onSubmit,
  submitting,
}: {
  onSubmit: (submission: DiffSubmission) => void;
  submitting: boolean;
}) {
  const [diffText, setDiffText] = useState('');
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptFile = (selected: File) => {
    if (!hasAllowedExtension(selected.name)) {
      setError('Unsupported file type. Use a .diff, .patch, or .txt file.');
      return;
    }
    if (selected.size > MAX_DIFF_BYTES * 5) {
      setError('File is too large to analyze.');
      return;
    }
    setError(null);
    setFile(selected);
    void selected
      .arrayBuffer()
      .then(decodeDiffFile)
      .then(setDiffText)
      .catch(() => {
        setError('Could not read the selected file.');
      });
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) acceptFile(dropped);
  };

  const handleSubmit = () => {
    if (!diffText.trim()) {
      setError('Paste a diff or upload a .diff/.patch file.');
      return;
    }
    if (byteLength(diffText) > MAX_DIFF_BYTES * 5) {
      setError('Diff is too large to analyze.');
      return;
    }
    setError(null);
    if (file) {
      onSubmit({ kind: 'upload', diffText, file, title: title || undefined });
    } else {
      onSubmit({ kind: 'paste', diffText, title: title || undefined });
    }
  };

  return (
    <Stack spacing={2}>
      <TextField
        label="Title (optional)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        fullWidth
        size="small"
      />

      <Box
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        sx={{
          border: '2px dashed',
          borderColor: dragOver ? 'primary.main' : 'divider',
          borderRadius: 2,
          p: 2,
          bgcolor: dragOver ? 'action.hover' : 'transparent',
          transition: 'all 0.15s',
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1} mb={1}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<UploadFileIcon />}
            onClick={() => inputRef.current?.click()}
          >
            Upload .diff / .patch
          </Button>
          <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
            {file ? file.name : 'or drag a file here, or paste below'}
          </Typography>
          <Tooltip title={expanded ? 'Collapse diff view' : 'Expand diff view'}>
            <IconButton
              size="small"
              aria-label={expanded ? 'Collapse diff view' : 'Expand diff view'}
              onClick={() => setExpanded((prev) => !prev)}
            >
              {expanded ? <FullscreenExitIcon /> : <FullscreenIcon />}
            </IconButton>
          </Tooltip>
          <input
            ref={inputRef}
            type="file"
            accept=".diff,.patch,.txt"
            hidden
            onChange={(e) => {
              const selected = e.target.files?.[0];
              if (selected) acceptFile(selected);
            }}
          />
        </Stack>

        <TextField
          label="Unified diff"
          placeholder="diff --git a/file b/file&#10;@@ -1,3 +1,4 @@ ..."
          value={diffText}
          onChange={(e) => {
            setDiffText(e.target.value);
            setFile(null);
          }}
          multiline
          minRows={expanded ? EXPANDED_ROWS : COMPACT_ROWS}
          maxRows={expanded ? EXPANDED_ROWS : undefined}
          fullWidth
          slotProps={{
            input: {
              sx: {
                fontFamily: 'monospace',
                fontSize: 13,
                '& textarea': { resize: 'vertical' },
              },
            },
          }}
        />
      </Box>

      {error && (
        <Typography color="error" variant="body2">
          {error}
        </Typography>
      )}

      <Box>
        <Button
          variant="contained"
          size="large"
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? 'Analyzing…' : 'Analyze diff'}
        </Button>
      </Box>
    </Stack>
  );
}
