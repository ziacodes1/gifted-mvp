# Gifted UI Asset Map

This folder is prepared for implementation with Claude.

## Naming rule

All files use lowercase `snake_case` names and describe **what the image is for**, not when it was generated.

### Main folders

- `screens/public/` — landing and authentication screens.
- `screens/student/` — student-facing MVP pages.
- `screens/parent/` — parent-facing MVP pages.
- `assets/hero_and_backgrounds/` — reusable photo backgrounds and decorative banners.
- `assets/branding/` — Gifted logo variants.
- `assets/passport/` — standalone Gifted Passport object.
- `assets/passport_ui/` — detailed Passport UI design references.

## Important implementation guidance

1. Treat files in `screens/` as **UI/UX references**, not as raster images to place directly into the app.
2. Rebuild the layouts as real React components and use the assets from `assets/` where appropriate.
3. Preserve the Gifted visual system: deep emerald, warm gold, soft cream, spacious layouts, rounded cards, and minimal clutter.
4. Use `gifted_logo_light_mode.png` on light surfaces.
5. Use `gifted_logo_dark_mode.png` on dark green / dark surfaces.
6. Use `gifted_logo_icon_only.png` where only the symbol is needed.
7. `gifted_passport_book_cover_3d.png` is the standalone 3D Passport object.
8. `ASSET_MANIFEST.csv` maps every original filename to its cleaned filename.
9. One exact duplicate logo file from the original ZIP was removed intentionally to avoid confusion.

## Core MVP screen flow

Suggested reference order:

`public_landing_home`
→ `auth_login_student_parent_split`
→ `student_onboarding_interest_selection`
→ `student_dashboard_first_session_good_morning`
→ `student_my_journey_overview`
→ `student_assessments_overview`
→ `student_interests_assessment_question`
→ `student_assessment_activity_choice`
→ `student_assessment_session_insights_results`
→ `student_session_complete_summary`
→ `student_passport_profile_overview`
→ `student_opportunities_explore_listing`
→ `student_opportunity_detail_young_innovators_fellowship`

Parent flow:

`auth_login_student_parent_split`
→ `parent_dashboard_growth_overview`
→ `parent_insights_dashboard`
→ `parent_support_at_home_dashboard`
