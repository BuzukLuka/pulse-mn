export type Role = "journalist" | "editor" | "newsroom" | "citizen" | "admin";
export type ContentStatus =
  | "draft" | "under_review" | "changes_requested" | "published" | "rejected" | "hidden";

export interface User {
  id: number; email: string; full_name: string; phone: string; organization: string;
  bio: string; role: Role; is_active: boolean; created_at: string; last_login?: string | null;
  is_verified?: boolean; verification_requested_at?: string | null; province?: number | null;
  press_card_no?: string; legal_name?: string; registry_no?: string; responsible_editor?: string;
  newsroom_org?: number | null; newsroom_org_name?: string | null;
  terms_accepted_at?: string | null; privacy_consent_at?: string | null; ethics_accepted_at?: string | null; province_name?: string | null; district?: number | null;
  show_email?: boolean; show_phone?: boolean; show_org?: boolean;
  experiences?: Experience[]; portfolio?: PortfolioItem[];
}
export interface Experience { id?: number; organization: string; position: string; period: string }
export interface PortfolioItem { id?: number; title: string; kind: string; year: number | null; url: string }
export interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[] }
export interface Option { id: number; name: string }
export interface Category { id: number; slug: string; name: string }
export interface District extends Option { province: number }
export interface Media {
  id: number; kind: "image" | "video" | "document"; original_name: string;
  size: number; sha256: string; phash?: string; url: string;
}
export interface AiReview {
  verdict: "ok" | "needs_attention" | "risky"; score: number; issues: string[];
  summary: string; source: "gemini" | "rules";
}
export interface AiSuggestion {
  category: string | null; category_id: number | null; tags: string[]; summary: string;
  source: "gemini" | "rules";
}
export type CheckStatus = "ok" | "warn" | "fail" | "info";
export interface TrustCheck {
  key: string; label: string; status: CheckStatus; detail?: string; items?: any[]; score?: number; source?: string;
}
export interface Verification {
  score: number; level: "high" | "medium" | "low"; stage: "precheck" | "full"; ai_used: boolean;
  generated_at: string; checks: TrustCheck[]; editor_verified?: boolean;
  related_pledges?: { id: number; text: string; politician: string; score: number }[];
}
export interface PublicTrust {
  editor_verified: boolean; score: number | null; level: string | null; ai_used: boolean;
  checks: { label: string; status: CheckStatus }[]; verified_at?: string | null;
  verified_by?: string | null; verified_by_newsroom?: boolean;
  claims: { indicator: string; unit: string; claimed: number; official: number; year: number; source: string; mismatch: boolean }[];
}
export interface ContentVersion { id: number; number: number; title: string; body: string; source: string; tags: string[]; created_at: string }
export interface Content {
  content_type?: string; event_time?: string | null; location_detail?: string; license?: string;
  copyright_declared?: boolean; verification?: Verification | null; trust?: PublicTrust;
  review_checklist?: Record<string, boolean> | null; pledges?: number[];
  pledge_items?: { id: number; text: string; politician: string; politician_id: number }[];
  versions?: ContentVersion[]; checklist_items?: { key: string; label: string; required: boolean }[];
  newsroom?: number | null; newsroom_name?: string | null; price?: number;
  compliance?: Compliance; corrections?: Correction[]; review_by?: "pulse" | "newsroom"; can_decide?: boolean;
  disclosure?: { sponsored: boolean; political_ad: boolean; sponsor_name: string; conflict_of_interest: string };
  id: number; title: string; body: string;
  category: number | null; category_name: string | null; category_slug: string | null;
  province: number | null; province_name: string | null;
  district: number | null; district_name: string | null;
  event_date: string | null; source: string; tags: string[]; ai_summary: string;
  ai_suggestion?: AiSuggestion | null; ai_review?: AiReview | null;
  status: ContentStatus; status_label: string; review_reason?: string;
  reviewed_at?: string | null; submitted_at?: string | null; published_at: string | null;
  created_at: string; updated_at: string; author?: number; author_name: string; media: Media[];
  duplicates?: { id: number; title: string; reason: string; status: ContentStatus }[];
}
export interface AuditEntry {
  id: number; actor_email: string | null; action: string; entity_type: string; entity_id: string;
  before: unknown; after: unknown; reason: string; created_at: string;
}
export interface Notification {
  id: number; title: string; body: string; content_id: number | null; is_read: boolean; created_at: string;
}
export interface Stats {
  content_by_status: Record<string, number>; users_by_role: Record<string, number>;
  users_total: number; content_total: number;
}

export type PledgeStatus = "fulfilled" | "in_progress" | "not_fulfilled" | "insufficient";
export interface PledgeStats {
  total: number; counts: Record<PledgeStatus, number>; base: number;
  percent: Record<string, number | null>; method: string;
}
export interface Politician {
  id: number; name: string; position: string; party: string; province: number | null; province_name: string | null;
  district: number | null; term_year: number; stats: PledgeStats; pledges?: Pledge[];
}
export interface Evidence { id: number; kind: string; source: string; date: string; url: string; note: string }
export interface Pledge {
  id: number; politician: number; politician_name: string; text: string; category: number; category_name: string;
  source: string; source_url: string; status: PledgeStatus; status_label: string; evidence_count: number;
  evidence?: Evidence[];
  history?: { id: number; old_status: PledgeStatus; new_status: PledgeStatus; reason: string; evidence: Evidence | null; changed_by_name?: string; created_at: string }[];
}
export interface Indicator {
  id: number; name: string; aliases: string; unit: string; category: number; category_name: string;
  source: number; source_name: string; frequency: string; is_active: boolean;
  value?: number; year?: number; change_pct?: number | null; updated_at?: string;
}
export interface DataSource {
  id: number; name: string; kind: string; url: string; frequency: string; last_synced_at: string | null;
  status: string; last_error: string; indicator_count: number;
}
export interface IndicatorValue {
  id: number; province: number | null; province_name: string | null; year: number; value: string;
  history: { id: number; old_value: string | null; new_value: string; reason: string; changed_by_name?: string; created_at: string }[];
}
export interface Complaint {
  id: number; target_type: string; target_id: number; kind: string; text: string; evidence_url: string;
  status: "open" | "resolved" | "dismissed"; resolution: string; created_at: string; reporter_email?: string;
}

export interface RatingSummary { avg: number | null; count: number; distribution: Record<string, number> }
export interface PersonCard {
  id: number; name: string; is_verified: boolean; province: string | null; rating: RatingSummary;
  email?: string; published?: number; organization?: string; bio?: string; members?: number;
}
export interface Membership {
  id: number; status: "pending" | "active" | "rejected" | "left"; status_label: string; message: string;
  created_at: string; decided_at: string | null; newsroom: { id: number; name: string }; journalist: PersonCard;
}
export interface Compliance {
  facts_verified?: boolean; no_defamation?: boolean; personal_data?: "none" | "consent" | "public_interest";
  minors_involved?: boolean; minors_protected?: boolean; conflict_of_interest?: string;
  sponsored?: boolean; sponsor_name?: string; political_ad?: boolean;
}
export interface Correction { id: number; kind: "correction" | "reply" | "update"; kind_label: string; text: string; created_at: string }
export interface ExternalArticle {
  id: number; source: string; source_name: string; url: string; title: string; title_mn: string; snippet: string;
  summary_mn: string; language: string; published_at: string | null; category: number | null; category_name: string | null;
  relevance: number; ai_source: "gemini" | "rules";
}
export interface PurchaseQuote {
  provider: string; live: boolean; fee_pct: number;
  options: { license_type: string; label: string; amount: number; vat_amount: number; platform_fee: number; author_net: number; available: boolean }[];
}
export interface Purchase {
  license_type: string; license_label: string; vat_amount: number; platform_fee: number; author_net: number;
  provider: string; provider_ref: string; ebarimt_no: string; refund_reason: string; demo: boolean;
  id: number; status: "pending" | "paid" | "cancelled" | "refunded"; status_label: string; amount: number; invoice_code: string;
  created_at: string; paid_at: string | null; content: { id: number; title: string; author_name: string };
  buyer: { id: number; name: string };
}
export interface RatingSuggestion { score: number; reasons: string[]; source: "gemini" | "rules"; metrics: Record<string, unknown> }
export interface HistoryItem { action: string; label: string; at: string; actor: string | null; reason: string; to?: string }
