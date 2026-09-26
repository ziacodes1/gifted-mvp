import { PlaceholderPage } from "../../components/PlaceholderPage";

export { DashboardPage as StudentOverview } from "./DashboardPage";
export { AssessmentPage as StudentAssessment } from "./AssessmentPage";
export { AssessmentResultPage } from "./AssessmentResultPage";
export { PassportPage as StudentPassport } from "./PassportPage";
export { MissionsPage as StudentMissions } from "./MissionsPage";
export { MissionPage as StudentMission } from "./MissionPage";
export { CompanionPage as StudentCompanion } from "./CompanionPage";
export { DiaryPage as StudentDiary } from "./DiaryPage";
export { DiaryEntryRoute as StudentDiaryEntry } from "./DiaryEntryPage";
export { RewardsPage as StudentRewards } from "./RewardsPage";

export const StudentJourney = () => (
  <PlaceholderPage title="My Journey" description="A timeline of milestones as you discover, explore, and grow." />
);
export const StudentOpportunities = () => (
  <PlaceholderPage title="Opportunities" description="Courses, events, competitions and programs recommended for you." />
);
export const StudentProfile = () => (
  <PlaceholderPage title="Profile" description="Your details and preferences." />
);
