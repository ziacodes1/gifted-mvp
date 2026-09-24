import { SidebarLayout, type NavItem } from "../components/SidebarLayout";
import { ChartIcon, CompassIcon, DocIcon, HomeIcon } from "../features/passport/icons";

// Only finished, demo-ready sections are linked (journey/opportunities/profile are placeholders).
const items: NavItem[] = [
  { to: "/app", label: "Home", end: true, icon: <HomeIcon /> },
  { to: "/app/assessment", label: "Assessments", icon: <ChartIcon /> },
  { to: "/app/passport", label: "My Passport", icon: <DocIcon /> },
  { to: "/app/missions", label: "Missions", icon: <CompassIcon /> },
];

export function StudentLayout() {
  return <SidebarLayout items={items} />;
}
