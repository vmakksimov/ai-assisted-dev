import { apiClient, toApiError } from './client';
import type {
  ListReviewsParams,
  PaginatedReviews,
  Review,
} from './types';

export async function analyzeDiff(diffText: string, title?: string): Promise<Review> {
  try {
    const { data } = await apiClient.post<Review>('/reviews/analyze', {
      diff_text: diffText,
      title: title || null,
    });
    return data;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function analyzeUploadedDiff(file: File, title?: string): Promise<Review> {
  const form = new FormData();
  form.append('file', file);
  if (title) form.append('title', title);
  try {
    const { data } = await apiClient.post<Review>('/reviews/analyze/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function listReviews(
  params: ListReviewsParams = {},
): Promise<PaginatedReviews> {
  try {
    const { data } = await apiClient.get<PaginatedReviews>('/reviews', { params });
    return data;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function getReview(id: string): Promise<Review> {
  try {
    const { data } = await apiClient.get<Review>(`/reviews/${id}`);
    return data;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function deleteReview(id: string): Promise<void> {
  try {
    await apiClient.delete(`/reviews/${id}`);
  } catch (error) {
    throw toApiError(error);
  }
}
