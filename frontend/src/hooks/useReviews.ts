import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import {
  analyzeDiff,
  analyzeUploadedDiff,
  deleteReview,
  getReview,
  listReviews,
} from '../api/reviews';
import type { ApiError } from '../api/client';
import type { ListReviewsParams, Review } from '../api/types';

export const reviewKeys = {
  all: ['reviews'] as const,
  list: (params: ListReviewsParams) => ['reviews', 'list', params] as const,
  detail: (id: string) => ['reviews', 'detail', id] as const,
};

type AnalyzeInput =
  | { kind: 'paste'; diffText: string; title?: string }
  | { kind: 'upload'; file: File; title?: string };

export function useAnalyzeDiff() {
  const queryClient = useQueryClient();
  return useMutation<Review, ApiError, AnalyzeInput>({
    mutationFn: (input) =>
      input.kind === 'paste'
        ? analyzeDiff(input.diffText, input.title)
        : analyzeUploadedDiff(input.file, input.title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.all });
    },
  });
}

export function useReviewList(params: ListReviewsParams) {
  return useQuery({
    queryKey: reviewKeys.list(params),
    queryFn: () => listReviews(params),
  });
}

export function useReview(id: string) {
  return useQuery({
    queryKey: reviewKeys.detail(id),
    queryFn: () => getReview(id),
    enabled: Boolean(id),
  });
}

export function useDeleteReview() {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: (id) => deleteReview(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.all });
    },
  });
}
