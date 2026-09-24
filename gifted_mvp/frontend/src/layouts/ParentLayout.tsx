import { SidebarLayout, type NavItem } from "../components/SidebarLayout";
import { ChartIcon, UserIcon } from "../features/passport/icons";

const items: NavItem[] = [
  { to: "/parent", label: "My Child", end: true, icon: <UserIcon /> },
  { to: "/parent/insights", label: "Parent Insights", icon: <ChartIcon /> },
];

export function ParentLayout() {
  return <SidebarLayout items={items} />;
}
