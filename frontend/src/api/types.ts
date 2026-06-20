// TypeScript types mirroring the backend DTOs (app/api/schemas.py) and enums
// (app/domain/enums.py). Keep these in sync with the backend contract.

export type RiskSeverity = 'low' | 'medium' | 'high' | 'critical';
export type ReviewStatus = 'pending' | 'completed' | 'failed' | 'partial';
export type DiffSource = 'paste' | 'upload';
export type RiskCategory =
  | 'security'
  | 'performance'
  | 'correctness'
  | 'maintainability'
  | 'style';
export type CommentSeverity = 'info' | 'minor' | 'major';
export type TestType = 'unit' | 'integration';
export type Priority = 'low' | 'medium' | 'high';

export interface RiskFinding {
  id: string | null;
  severity: RiskSeverity;
  category: RiskCategory;
  title: string;
  description: string;
  file_path: string | null;
  line_hint: string | null;
  recommendation: string | null;
}

export interface ReviewComment {
  id: string | null;
  severity: CommentSeverity;
  comment: string;
  file_path: string | null;
  line_hint: string | null;
}

export interface TestSuggestion {
  id: string | null;
  test_type: TestType;
  target: string;
  description: string;
  priority: Priority;
  example_code: string | null;
}

export interface DiffStats {
  files_changed: number;
  additions: number;
  deletions: number;
}

export interface Review {
  id: string;
  title: string | null;
  status: ReviewStatus;
  diff_source: DiffSource;
  overall_risk: RiskSeverity | null;
  summary: string | null;
  error_message: string | null;
  model_name: string;
  stats: DiffStats;
  diff_text: string;
  risk_findings: RiskFinding[];
  review_comments: ReviewComment[];
  test_suggestions: TestSuggestion[];
  created_at: string | null;
  updated_at: string | null;
}

export interface ReviewSummary {
  id: string;
  title: string | null;
  status: ReviewStatus;
  overall_risk: RiskSeverity | null;
  diff_source: DiffSource;
  files_changed: number;
  created_at: string;
}

export interface PaginatedReviews {
  items: ReviewSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiErrorBody {
  error: {
    type: string;
    message: string;
    detail?: unknown;
  };
}

export interface ListReviewsParams {
  limit?: number;
  offset?: number;
  status?: ReviewStatus;
  overall_risk?: RiskSeverity;
}
