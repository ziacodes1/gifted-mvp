import { SidebarLayout, type NavItem } from "../components/SidebarLayout";
import { TrophyIcon } from "../features/rewards/art";
import { BriefcaseIcon, OpenBookIcon, PeopleIcon } from "../features/ecosystem/icons";
import { NudgeBell } from "../features/today/NudgeBell";
import { BookIcon, ChartIcon, CompassIcon, DocIcon, HomeIcon, SparkIcon } from "../features/passport/icons";

// Only finished, demo-ready sections are linked (no placeholder routes).
const items: NavItem[] = [
  { to: "/app", label: "nav.home", end: true, icon: <HomeIcon /> },
  { to: "/app/assessment", label: "nav.assessments", icon: <ChartIcon /> },
  { to: "/app/passport", label: "nav.passport", icon: <DocIcon /> },
  { to: "/app/missions", label: "nav.missions", icon: <CompassIcon /> },
  { to: "/app/opportunities", label: "nav.opportunities", icon: <BriefcaseIcon /> },
  { to: "/app/resources", label: "nav.resources", icon: <OpenBookIcon /> },
  { to: "/app/community", label: "nav.community", icon: <PeopleIcon /> },
  { to: "/app/companion", label: "nav.companion", icon: <SparkIcon className="h-5 w-5" /> },
  { to: "/app/diary", label: "nav.diary", icon: <BookIcon /> },
  { to: "/app/rewards", label: "nav.rewards", icon: <TrophyIcon className="h-5 w-5" /> },
];

export function StudentLayout() {
  return <SidebarLayout items={items} topRight={<NudgeBell />} />;
}
