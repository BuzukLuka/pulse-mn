# Pulse.mn — Тестийн үр дүнгийн тайлан

- **Огноо:** 2026.11.19 16:33 (Улаанбаатар)
- **Орчин:** Django 5.1.15 · Python 3.12.10 · SQLite (тестийн DB)
- **Нийт:** 83 тест · 145.357 сек · **OK**
- **Тэнцсэн:** 83 · **Унасан:** 0

Дахин үүсгэх: `cd backend && python manage.py test apps -v 2 > ../docs/testlog.txt 2>&1 && cd .. && python docs/make_test_results.py docs/testlog.txt`

## Frontend

| Шалгалт | Үр дүн |
|---|---|
| `tsc --noEmit` — platform, admin, shared | ✅ Алдаагүй |
| `next build` — platform | ✅ Compiled successfully |
| `next build` — admin | ✅ Compiled successfully |

## Хураангуй (модуль бүрээр)

| Модуль / анги | Тест | Тэнцсэн | Үр дүн |
|---|---:|---:|---|
| `ai` · TrustTests | 5 | 5 | ✅ |
| `common` · CommentTests | 3 | 3 | ✅ |
| `common` · ComplianceTests | 5 | 5 | ✅ |
| `common` · CorrectionAndTakedownTests | 4 | 4 | ✅ |
| `common` · DataRightsTests | 3 | 3 | ✅ |
| `common` · FeaturedTests | 2 | 2 | ✅ |
| `common` · JournalistTopicsTests | 1 | 1 | ✅ |
| `common` · NewsFilterTests | 1 | 1 | ✅ |
| `common` · NewsroomReviewTests | 5 | 5 | ✅ |
| `common` · NewsroomStaffEditorTests | 4 | 4 | ✅ |
| `common` · PaymentTests | 8 | 8 | ✅ |
| `common` · PermissionMatrixTests | 2 | 2 | ✅ |
| `common` · PledgeProgressTests | 4 | 4 | ✅ |
| `common` · QueryCountTests | 1 | 1 | ✅ |
| `common` · RegistrationConsentTests | 6 | 6 | ✅ |
| `common` · ViewsAndBulkTests | 2 | 2 | ✅ |
| `common` · WorldNewsTests | 10 | 10 | ✅ |
| `content` · AdminTests | 5 | 5 | ✅ |
| `content` · WorkflowTests | 4 | 4 | ✅ |
| `newsroom` · NewsroomFlowTests | 4 | 4 | ✅ |
| `pledges` · PledgeStatsComplaintTests | 4 | 4 | ✅ |

## TrustTests — `apps.ai.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-001 | `test_claim_mismatch_and_pii` | claim mismatch and pii | ✅ Тэнцсэн |
| TC-002 | `test_image_phash_duplicate` | image phash duplicate | ✅ Тэнцсэн |
| TC-003 | `test_publish_requires_checklist_and_public_trust` | publish requires checklist and public trust | ✅ Тэнцсэн |
| TC-004 | `test_submit_stores_verification_and_version` | submit stores verification and version | ✅ Тэнцсэн |
| TC-005 | `test_text_duplicate_flagged` | text duplicate flagged | ✅ Тэнцсэн |

## CommentTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-006 | `test_anonymous_citizen_comment` | anonymous citizen comment | ✅ Тэнцсэн |
| TC-007 | `test_only_citizen_can_be_anonymous_and_published_only` | only citizen can be anonymous and published only | ✅ Тэнцсэн |
| TC-008 | `test_rate_limit_delete_and_admin_hide` | rate limit delete and admin hide | ✅ Тэнцсэн |

## ComplianceTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-009 | `test_compliance_declarations_required` | compliance declarations required | ✅ Тэнцсэн |
| TC-010 | `test_editor_must_tick_all_legal_checks` | editor must tick all legal checks | ✅ Тэнцсэн |
| TC-011 | `test_minors_and_sponsor_rules` | minors and sponsor rules | ✅ Тэнцсэн |
| TC-012 | `test_public_disclosure_shown_raw_compliance_hidden` | public disclosure shown raw compliance hidden | ✅ Тэнцсэн |
| TC-013 | `test_unknown_compliance_keys_dropped` | unknown compliance keys dropped | ✅ Тэнцсэн |

## CorrectionAndTakedownTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-014 | `test_correction_only_on_published` | correction only on published | ✅ Тэнцсэн |
| TC-015 | `test_editor_publishes_correction_visible_to_public` | editor publishes correction visible to public | ✅ Тэнцсэн |
| TC-016 | `test_hide_requires_legal_basis_and_notifies_author` | hide requires legal basis and notifies author | ✅ Тэнцсэн |
| TC-017 | `test_right_of_reply_via_complaint` | right of reply via complaint | ✅ Тэнцсэн |

## DataRightsTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-018 | `test_delete_account_anonymizes_and_keeps_published_news` | delete account anonymizes and keeps published news | ✅ Тэнцсэн |
| TC-019 | `test_export_contains_own_data_only` | export contains own data only | ✅ Тэнцсэн |
| TC-020 | `test_last_admin_cannot_delete_self` | last admin cannot delete self | ✅ Тэнцсэн |

## FeaturedTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-021 | `test_journalist_requests_newsroom_decides` | journalist requests newsroom decides | ✅ Тэнцсэн |
| TC-022 | `test_pulse_editor_features_independent_and_expiry` | pulse editor features independent and expiry | ✅ Тэнцсэн |

## JournalistTopicsTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-023 | `test_top_categories_on_cards_and_profile` | top categories on cards and profile | ✅ Тэнцсэн |

## NewsFilterTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-024 | `test_category_slug_and_fresh` | category slug and fresh | ✅ Тэнцсэн |

## NewsroomReviewTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-025 | `test_member_news_routed_to_verified_newsroom` | member news routed to verified newsroom | ✅ Тэнцсэн |
| TC-026 | `test_newsroom_decides_with_legal_checklist` | newsroom decides with legal checklist | ✅ Тэнцсэн |
| TC-027 | `test_non_member_or_unverified_newsroom_goes_to_pulse` | non member or unverified newsroom goes to pulse | ✅ Тэнцсэн |
| TC-028 | `test_other_newsroom_cannot_access` | other newsroom cannot access | ✅ Тэнцсэн |
| TC-029 | `test_return_and_resubmit_stays_with_newsroom` | return and resubmit stays with newsroom | ✅ Тэнцсэн |

## NewsroomStaffEditorTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-030 | `test_newsroom_creates_editor_account` | newsroom creates editor account | ✅ Тэнцсэн |
| TC-031 | `test_only_newsroom_role_manages_editors` | only newsroom role manages editors | ✅ Тэнцсэн |
| TC-032 | `test_other_newsroom_staff_and_deactivation` | other newsroom staff and deactivation | ✅ Тэнцсэн |
| TC-033 | `test_staff_editor_reviews_only_own_newsroom` | staff editor reviews only own newsroom | ✅ Тэнцсэн |

## PaymentTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-034 | `test_admin_refund_and_permissions` | admin refund and permissions | ✅ Тэнцсэн |
| TC-035 | `test_cancel_only_own_pending` | cancel only own pending | ✅ Тэнцсэн |
| TC-036 | `test_exclusive_license_blocks_other_buyers` | exclusive license blocks other buyers | ✅ Тэнцсэн |
| TC-037 | `test_exclusive_not_possible_after_standard_sale` | exclusive not possible after standard sale | ✅ Тэнцсэн |
| TC-038 | `test_not_for_sale_and_unpublished` | not for sale and unpublished | ✅ Тэнцсэн |
| TC-039 | `test_quote_and_terms_required` | quote and terms required | ✅ Тэнцсэн |
| TC-040 | `test_standard_purchase_confirm_issues_receipt` | standard purchase confirm issues receipt | ✅ Тэнцсэн |
| TC-041 | `test_vat_and_fee_breakdown` | vat and fee breakdown | ✅ Тэнцсэн |

## PermissionMatrixTests — `apps.common.tests`

_Endpoint бүрт аль persona хандах ёстойг шалгана (401/403 эсвэл амжилттай)._

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-042 | `test_matrix` | matrix | ✅ Тэнцсэн |
| TC-043 | `test_visibility_of_content_by_persona` | visibility of content by persona | ✅ Тэнцсэн |

## PledgeProgressTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-044 | `test_admin_sets_deadline_progress_location` | admin sets deadline progress location | ✅ Тэнцсэн |
| TC-045 | `test_citizen_update_ai_check_and_verify` | citizen update ai check and verify | ✅ Тэнцсэн |
| TC-046 | `test_constituency_filter_and_list` | constituency filter and list | ✅ Тэнцсэн |
| TC-047 | `test_import_parliament` | import parliament | ✅ Тэнцсэн |

## QueryCountTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-048 | `test_list_endpoints_constant_queries` | list endpoints constant queries | ✅ Тэнцсэн |

## RegistrationConsentTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-049 | `test_admin_and_editor_roles_cannot_self_register` | admin and editor roles cannot self register | ✅ Тэнцсэн |
| TC-050 | `test_citizen_registers_with_consent_timestamps` | citizen registers with consent timestamps | ✅ Тэнцсэн |
| TC-051 | `test_journalist_must_accept_code_of_ethics` | journalist must accept code of ethics | ✅ Тэнцсэн |
| TC-052 | `test_newsroom_needs_legal_entity_details` | newsroom needs legal entity details | ✅ Тэнцсэн |
| TC-053 | `test_terms_and_privacy_required_for_everyone` | terms and privacy required for everyone | ✅ Тэнцсэн |
| TC-054 | `test_verification_prerequisites_per_persona` | verification prerequisites per persona | ✅ Тэнцсэн |

## ViewsAndBulkTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-055 | `test_notifications_read_many` | notifications read many | ✅ Тэнцсэн |
| TC-056 | `test_views_counted_except_author` | views counted except author | ✅ Тэнцсэн |

## WorldNewsTests — `apps.common.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-057 | `test_failing_source_does_not_break_others` | failing source does not break others | ✅ Тэнцсэн |
| TC-058 | `test_fill_images_once` | fill images once | ✅ Тэнцсэн |
| TC-059 | `test_gemini_enrichment_used_when_configured` | gemini enrichment used when configured | ✅ Тэнцсэн |
| TC-060 | `test_nso_api_disabled_without_permission` | nso api disabled without permission | ✅ Тэнцсэн |
| TC-061 | `test_og_image_respects_robots_and_parses_meta` | og image respects robots and parses meta | ✅ Тэнцсэн |
| TC-062 | `test_parse_rss_strips_html_and_skips_bad_items` | parse rss strips html and skips bad items | ✅ Тэнцсэн |
| TC-063 | `test_public_list_and_refresh_permissions` | public list and refresh permissions | ✅ Тэнцсэн |
| TC-064 | `test_refresh_stores_only_relevant_and_respects_staleness` | refresh stores only relevant and respects staleness | ✅ Тэнцсэн |
| TC-065 | `test_rss_image_sources` | rss image sources | ✅ Тэнцсэн |
| TC-066 | `test_rules_relevance_category_and_language` | rules relevance category and language | ✅ Тэнцсэн |

## AdminTests — `apps.content.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-067 | `test_deactivated_user_cannot_login_and_sessions_revoked` | deactivated user cannot login and sessions revoked | ✅ Тэнцсэн |
| TC-068 | `test_last_admin_protected_409` | last admin protected 409 | ✅ Тэнцсэн |
| TC-069 | `test_non_admin_forbidden` | non admin forbidden | ✅ Тэнцсэн |
| TC-070 | `test_register_cannot_pick_admin_role` | register cannot pick admin role | ✅ Тэнцсэн |
| TC-071 | `test_uc03_access_change` | uc03 access change | ✅ Тэнцсэн |

## WorkflowTests — `apps.content.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-072 | `test_ai_fallback_rules` | ai fallback rules | ✅ Тэнцсэн |
| TC-073 | `test_media_upload_and_duplicate_detection` | media upload and duplicate detection | ✅ Тэнцсэн |
| TC-074 | `test_uc01_validation_400_then_submit` | uc01 validation 400 then submit | ✅ Тэнцсэн |
| TC-075 | `test_uc02_decide_rules` | uc02 decide rules | ✅ Тэнцсэн |

## NewsroomFlowTests — `apps.newsroom.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-076 | `test_demo_purchase_and_ratings` | demo purchase and ratings | ✅ Тэнцсэн |
| TC-077 | `test_membership_newsroom_notified_and_sees_content` | membership newsroom notified and sees content | ✅ Тэнцсэн |
| TC-078 | `test_submit_to_newsroom_without_membership_and_send_later` | submit to newsroom without membership and send later | ✅ Тэнцсэн |
| TC-079 | `test_unverified_cannot_submit_until_admin_verifies` | unverified cannot submit until admin verifies | ✅ Тэнцсэн |

## PledgeStatsComplaintTests — `apps.pledges.tests`

| # | Test case | Тайлбар | Үр дүн |
|---:|---|---|---|
| TC-080 | `test_complaint_flow` | complaint flow | ✅ Тэнцсэн |
| TC-081 | `test_percent_excludes_insufficient` | percent excludes insufficient | ✅ Тэнцсэн |
| TC-082 | `test_public_stats_and_backup_admin_only` | public stats and backup admin only | ✅ Тэнцсэн |
| TC-083 | `test_status_change_needs_reason_and_evidence` | status change needs reason and evidence | ✅ Тэнцсэн |
