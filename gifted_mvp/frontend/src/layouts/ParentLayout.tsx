import { SidebarLayout, type NavItem } from "../components/SidebarLayout";
import { ChartIcon, UserIcon } from "../features/passport/icons";

const items: NavItem[] = [
  { to: "/parent", label: "nav.myChild", end: true, icon: <UserIcon /> },
  { to: "/parent/insights", label: "nav.parentInsights", icon: <ChartIcon /> },
];

export function ParentLayout() {
  return <SidebarLayout items={items} />;
}
