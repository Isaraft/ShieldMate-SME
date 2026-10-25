"""Versioned CSV contracts. Templates contain headers only, never invented sessions."""

BETA_COLUMNS = (
    "evidence_class",
    "participant_id",
    "session_id",
    "local_datetime",
    "language",
    "moderator_code",
    "role_segment",
    "target_eligible",
    "relationship",
    "eligibility_reason",
    "familiarity",
    "consent",
    "screenshot_consent",
    "audio_consent",
    "quote_consent",
    "scenario_id",
    "scenario_sha256",
    "build_id",
    "session_status",
    "primary_started",
    "timing_method",
    "protocol_variant",
    "elapsed_seconds",
    "paused",
    "hint_given",
    "top_issue_correct",
    "next_action_correct",
    "evidence_navigation_unaided",
    "done_vs_resolved_correct",
    "clarity_rating",
    "usefulness_rating",
    "error_count",
    "notes_evidence_id",
)
ALPHA_COLUMNS = (
    "evidence_class",
    "tester_code",
    "session_id",
    "local_datetime",
    "language",
    "build_id",
    "scenario_id",
    "environment",
    "data_context",
    "check_id",
    "consent",
    "screenshot_consent",
    "audio_consent",
    "quote_consent",
    "result",
    "severity",
    "issue_ref",
    "evidence_id",
)
MANIFEST_COLUMNS = (
    "evidence_id",
    "evidence_class",
    "participant_id",
    "session_id",
    "kind",
    "captured_at",
    "relative_path",
    "sha256",
    "redaction_status",
)
LANGUAGES = {"en", "ru", "kk"}
ROLES = {"sme_owner", "operations", "it_generalist", "outsourced_it", "other"}
SCENARIO = "shieldmate-demo-usability-1"
INTERNAL = "INTERNAL_TEST_DATA"
LIMIT = 120
MIN_SAMPLE = 5  # Proposed study plan, NOT a course-mandated minimum.
