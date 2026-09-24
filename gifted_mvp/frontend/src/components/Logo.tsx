import lightLogo from "../assets/branding/gifted_logo_light_mode.png";
import darkLogo from "../assets/branding/gifted_logo_dark_mode.png";
import iconLogo from "../assets/branding/gifted_logo_icon_only.png";

type Variant = "light" | "dark" | "icon";

const SRC: Record<Variant, string> = {
  light: lightLogo, // use on light/cream surfaces
  dark: darkLogo, //  use on dark green surfaces
  icon: iconLogo,
};

/** The official Gifted logo. Do not restyle — variant only picks the correct asset. */
export function Logo({
  variant = "light",
  className = "h-8 w-auto",
}: {
  variant?: Variant;
  className?: string;
}) {
  return <img src={SRC[variant]} alt="Gifted" className={className} />;
}
