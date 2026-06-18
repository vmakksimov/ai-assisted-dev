import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DiffInput } from './DiffInput';

describe('DiffInput', () => {
  it('shows a validation error when submitting an empty diff', async () => {
    const onSubmit = vi.fn();
    render(<DiffInput onSubmit={onSubmit} submitting={false} />);

    await userEvent.click(screen.getByRole('button', { name: /analyze diff/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/paste a diff or upload/i)).toBeInTheDocument();
  });

  it('submits pasted diff text', async () => {
    const onSubmit = vi.fn();
    render(<DiffInput onSubmit={onSubmit} submitting={false} />);

    await userEvent.type(
      screen.getByLabelText(/unified diff/i),
      'diff --git a/x b/x',
    );
    await userEvent.click(screen.getByRole('button', { name: /analyze diff/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ kind: 'paste' }),
    );
  });

  it('disables the button while submitting', () => {
    render(<DiffInput onSubmit={vi.fn()} submitting />);
    expect(screen.getByRole('button', { name: /analyzing/i })).toBeDisabled();
  });
});
