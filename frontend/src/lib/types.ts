// Updated TypeScript type definitions for Academic Research Agent Frontend

export type JobStatus = "queued" | "in_progress" | "completed" | "failed";
export type OutputFormat = "bullets" | "full_report";

// Enhanced Research Request with new academic features
export interface ResearchRequest {
  topic: string;
  output_format: OutputFormat;
  deadline?: string; // ISO 8601 datetime string
  // Enhanced academic options
  email?: string; // For PubMed API access
  preferred_sources?: ("arxiv" | "pubmed" | "grounding")[];
  research_depth?: "quick" | "comprehensive" | "deep_dive";
  date_range?: {
    start_year?: number;
    end_year?: number;
  };
  academic_fields?: string[]; // e.g., ["computer science", "biology"]
}

// Enhanced Reference with academic source information
export interface Reference {
  title: string;
  url: string;
  accessed_date: string; // ISO 8601 datetime string
  snippet?: string;
  // Academic source metadata
  source_type?: "arxiv" | "pubmed" | "web" | "unknown";
  authors?: string[];
  doi?: string;
  pmid?: string; // PubMed ID
  journal?: string;
  published_year?: number;
  categories?: string[]; // arXiv categories or MeSH terms
  confidence_score?: number; // Source quality score
}

// Enhanced Research Result with academic metrics
export interface ResearchResult {
  job_id?: string; // Optional for backwards compatibility
  topic: string;
  content: string; // Formatted content (bullets or full report)
  references: Reference[];
  output_format: OutputFormat;
  generated_at: string; // ISO 8601 datetime string
  word_count: number;
  confidence_score: number; // 0.0 to 1.0
  // Academic research metrics
  academic_source_breakdown?: {
    arxiv_papers: number;
    pubmed_papers: number;
    web_sources: number;
    total_sources: number;
  };
  research_quality_indicators?: {
    peer_reviewed_percentage: number;
    recent_sources_percentage: number; // Within last 5 years
    authoritative_sources_percentage: number;
  };
  key_findings?: string[]; // Extracted key insights
  research_gaps?: string[]; // Identified gaps in literature
  related_topics?: string[]; // Suggested related research areas
}

// Enhanced Job Status with research progress details
export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress?: number; // 0.0 to 1.0
  current_step?: string; // e.g., "Searching arXiv", "Analyzing results"
  estimated_completion?: string; // ISO 8601 datetime
  error_message?: string; // Error message if job failed
  sources_found?: {
    arxiv: number;
    pubmed: number;
    web: number;
  };
}

// Batch Research for multiple topics
export interface BatchResearchRequest {
  topics: string[];
  output_format: OutputFormat;
  email?: string;
  research_type?: "summary" | "trends" | "comparison" | "deep_dive";
}

export interface BatchResearchResult {
  batch_id: string;
  total_topics: number;
  completed_topics: number;
  failed_topics: number;
  results: Record<string, ResearchResult>; // topic -> result
  overall_confidence: number;
  processing_time_seconds: number;
}

// Live Research Session Types
export interface LiveResearchSession {
  session_id: string;
  topic: string;
  status: "active" | "ended" | "error";
  started_at: string;
  modalities: string[];
  participants?: number;
}

export interface LiveResearchStartRequest {
  topic: string;
  modalities?: string[];
  system_instructions?: string[];
}

export interface LiveResearchMessage {
  session_id: string;
  message: string;
  message_type?: "text" | "audio";
  sender: "user" | "assistant" | "system";
  timestamp: string;
}

export interface LiveResearchSummary {
  session_id: string;
  topic: string;
  duration_minutes: number;
  total_interactions: number;
  key_findings: Array<{
    finding: string;
    timestamp: string;
    confidence: number;
  }>;
  questions_explored: Array<{
    question: string;
    status: "exploring" | "answered" | "pending";
  }>;
  research_report?: string; // Generated session report
}

// Enhanced API Response Types
export interface JobSubmitResponse {
  job_id: string;
  status: JobStatus;
  estimated_duration_minutes?: number;
  sources_to_search?: string[];
}

// Research Analytics
export interface ResearchAnalytics {
  total_research_requests: number;
  successful_completions: number;
  average_confidence_score: number;
  most_researched_topics: Array<{
    topic: string;
    count: number;
    avg_confidence: number;
  }>;
  source_performance: {
    arxiv_success_rate: number;
    pubmed_success_rate: number;
    grounding_success_rate: number;
  };
  recent_research_trends: Array<{
    date: string;
    topic_categories: Record<string, number>;
  }>;
}

// Search and Filter Types
export interface ResearchSearchFilters {
  date_range?: {
    start: string;
    end: string;
  };
  confidence_threshold?: number;
  source_types?: ("arxiv" | "pubmed" | "web")[];
  output_format?: OutputFormat;
  min_word_count?: number;
  academic_fields?: string[];
}

export interface ResearchHistoryItem {
  job_id: string;
  topic: string;
  output_format: OutputFormat;
  status: JobStatus;
  confidence_score?: number;
  word_count?: number;
  source_count?: number;
  generated_at: string;
  preview?: string; // First 200 characters of content
}

// Error and Notification Types
export interface ResearchError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
  recoverable: boolean;
  suggested_actions?: string[];
}

export interface ResearchNotification {
  id: string;
  type: "success" | "warning" | "error" | "info";
  title: string;
  message: string;
  timestamp: string;
  action_url?: string;
  auto_dismiss?: boolean;
}

// User Preferences and Settings
export interface UserResearchPreferences {
  default_output_format: OutputFormat;
  preferred_sources: ("arxiv" | "pubmed" | "grounding")[];
  email_for_pubmed?: string;
  research_depth: "quick" | "comprehensive" | "deep_dive";
  notification_preferences: {
    email_on_completion: boolean;
    browser_notifications: boolean;
    progress_updates: boolean;
  };
  ui_preferences: {
    theme: "light" | "dark" | "auto";
    results_per_page: number;
    auto_save_results: boolean;
  };
}

// Export utility type for form validation
export type FormErrors<T> = Partial<Record<keyof T, string>>;

// Legacy types for backward compatibility
export interface LegacyResearchResult {
  job_id: string;
  title: string;
  summary: string[] | string;
  references: Array<{
    title: string;
    url?: string;
    author?: string;
    date?: string;
    publisher?: string;
  }>;
  conclusion: string;
  output_format: OutputFormat;
  status: JobStatus;
}