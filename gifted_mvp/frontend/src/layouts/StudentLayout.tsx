import { SidebarLayout, type NavItem } from "../components/SidebarLayout";
import { ChartIcon, CompassIcon, DocIcon, HomeIcon } from "../features/passport/icons";

// Only finished, demo-ready sections are linked (journey/opportunities/profile are placeholders).
const items: NavItem[] = [
  { to: "/app", label: "nav.home", end: true, icon: <HomeIcon /> },
  { to: "/app/assessment", label: "nav.assessments", icon: <ChartIcon /> },
  { to: "/app/passport", label: "nav.passport", icon: <DocIcon /> },
  { to: "/app/missions", label: "nav.missions", icon: <CompassIcon /> },
];

export function StudentLayout() {
  return <SidebarLayout items={items} />;
}
