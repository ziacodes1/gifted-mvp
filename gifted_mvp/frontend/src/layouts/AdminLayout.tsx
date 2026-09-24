import { SidebarLayout, type NavItem } from "../components/SidebarLayout";

const items: NavItem[] = [{ to: "/admin", label: "Overview", end: true }];

export function AdminLayout() {
  return <SidebarLayout items={items} />;
}
