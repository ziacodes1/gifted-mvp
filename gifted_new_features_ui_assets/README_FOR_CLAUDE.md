# Gifted — New Features UI Asset Pack

## IMPORTANT IMPLEMENTATION RULE
These screenshots are **VISUAL REFERENCES ONLY**.

**DO NOT embed the full screenshots as static UI.**
Rebuild the screens as real React components using the existing Gifted design system.

Dynamic UI must remain dynamic:
- text
- points
- streak counts
- day states
- progress rings/bars
- leaderboard rows
- badge locked/unlocked state
- reward availability and point cost
- buttons and links
- diary entry content
- AI chat messages

Only decorative/illustrative assets may be used as images where appropriate.

---

## 4 PRIMARY REFERENCE SCREENS

### `references/01_home_dashboard_reference.png`
Target: enhanced Student Home.
Main ideas:
- existing Gifted sidebar/header style
- AI Companion entry card
- My Diary preview card
- current streak preview
- rewards/badges preview
- leaderboard preview
- Today's Path

Do not copy unfinished menu items simply because they appear in the reference.
Use only implemented routes/features.

### `references/02_ai_companion_reference.png`
Target: AI Companion screen.
Main components:
- AI chat
- New Chat
- user context / About you
- suggested prompts
- Diary Moments
- "Add to My Diary" consent flow
- privacy reminder

AI must never save a chat/reflection to Diary without explicit user confirmation.

### `references/03_my_diary_reference.png`
Target: My Diary overview.
Main components:
- diary progress
- visual open-book preview
- recent entries
- mood/week visualization
- privacy card
- AI Companion suggestion to save a reflection
- Open Diary / Create New Entry

Diary is private by default.

### `references/04_streak_rewards_reference.png`
Target: Streak & Rewards screen.
Main components:
- current streak
- weekly consistency
- leaderboard
- top percentile motivational card
- unlocked/locked badges
- rewards catalog

---

## DIARY COMPONENT ASSETS

### `components/diary/diary_open_book_overview.png`
Decorative visual reference/asset for the diary overview state.
The app should still render diary metadata, buttons and progress as real UI.

### `components/diary/diary_open_book_editor.png`
Visual reference for the diary editing experience.
The final UI should support real editable content, photos, stickers, emoji/format controls and Save Entry.
Do not treat text inside this image as actual diary data.

---

## STREAK & REWARDS COMPONENT ASSETS

### `streak_current_7_day_card.png`
Reference for streak count + weekly day states.
Build as a dynamic component.

### `weekly_consistency_card.png`
Reference for 5/7 style weekly progress.
Build progress ring with CSS/SVG/component logic; do not hardcode the number from the image.

### `leaderboard_top_active_students.png`
Reference for leaderboard layout.
Build from data rows: rank, avatar, display name, points/activity score.

### `top_10_percent_motivation_card.png`
Reference for percentile/status encouragement.
Dynamic text/value.

### `badges_unlocked_collection.png`
Reference artwork/style for unlocked badge states.
Potential examples:
- Curious Learner
- Consistent Explorer
- Diary Champion
- Opportunity Seeker
- Global Thinker

Badge names/conditions should live in code/data, not inside screenshots.

### `badges_locked_collection.png`
Reference artwork/style for locked/future badges.
Potential examples:
- Community Contributor
- Ideas in Action
- Future Leader
- Gifted Explorer

### `rewards_catalog_physical.png`
Visual references for physical brand rewards:
- Gifted Sticker Pack
- Gifted Notebook
- Gifted Water Bottle

### `rewards_course_event_pass.png`
Visual references for:
- Free Expert Course
- Pro Event Pass

### `rewards_community_mentor.png`
Visual references for:
- Exclusive Community Access
- 1:1 Mentor Session

---

## COMPONENTIZATION EXPECTATION

Suggested frontend components:

```text
HomeDashboard
  AICompanionPreviewCard
  DiaryPreviewCard
  StreakPreviewCard
  RewardsPreviewCard
  LeaderboardPreview

AICompanionPage
  ChatThread
  SuggestedPrompts
  UserContextCard
  DiarySaveSuggestion
  PrivacyNotice

DiaryPage
  DiaryProgress
  DiaryBookPreview
  RecentEntries
  MoodWeek
  PrivacyCard

DiaryEditor
  DiaryCanvas
  PhotoTool
  StickerTool
  EmojiTool
  FormatTool
  SaveEntryButton

StreakRewardsPage
  CurrentStreakCard
  WeeklyConsistencyCard
  Leaderboard
  PercentileCard
  BadgeGrid
  RewardGrid
```

## PRODUCT RULES

1. Diary remains private by default.
2. AI may suggest saving something to Diary, but the student must confirm.
3. Streak should motivate, not punish. Missing a day does not delete progress/history.
4. Leaderboard should use activity/consistency points, not intelligence or "potential" scores.
5. Rewards can include brand merchandise, courses, event passes, community access and mentor sessions.
6. Keep EN/UZ/RU localization support on every new screen and AI interaction.
7. Preserve the existing Gifted cream / forest-green / gold / serif-display visual language.
8. Do not replace existing working MVP flows; extend them.
