import axios, { AxiosError } from 'axios';
import type { ApiErrorBody } from './types';

const baseURL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8009/api/v1';

export const apiClient = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

/** A normalized error the UI can rely on, derived from the backend envelope. */
export class ApiError extends Error {
  readonly type: string;
  readonly status?: number;
  readonly detail?: unknown;

  constructor(type: string, message: string, status?: number, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.status = status;
    this.detail = detail;
  }
}

/** Convert any axios error into an ApiError using the backend error envelope. */
export function toApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const body = error.response?.data as ApiErrorBody | undefined;
    if (body?.error) {
      return new ApiError(
        body.error.type,
        body.error.message,
        error.response?.status,
        body.error.detail,
      );
    }
    return new ApiError('NetworkError', error.message, error.response?.status);
  }
  return new ApiError('UnknownError', 'An unexpected error occurred.');
}
