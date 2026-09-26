import art from "../../assets/assessment/interest_art_painting_girl_canvas_studio.webp";
import data from "../../assets/assessment/interest_data_analysis_girl_laptop_charts.webp";
import tutoring from "../../assets/assessment/interest_helping_tutoring_older_girl_younger_boy.webp";
import tutoring2 from "../../assets/assessment/interest_helping_tutoring_older_girl_younger_girl.webp";
import leadership2 from "../../assets/assessment/interest_leadership_group_presentation_whiteboard_black_shirt.webp";
import leadership from "../../assets/assessment/interest_leadership_group_presentation_whiteboard_green_sweater.webp";
import gardening from "../../assets/assessment/interest_nature_gardening_girl_planting_outdoors.webp";
import productDesign from "../../assets/assessment/interest_product_design_backpack_prototype_girl_workshop.webp";
import science from "../../assets/assessment/interest_science_microscope_girl_lab_overalls.webp";
import robotics from "../../assets/assessment/interest_technology_robotics_boy_workshop.webp";
import roboticsGirl from "../../assets/assessment/interest_technology_robotics_girl_workshop.webp";
import mountain from "../../assets/dashboard/dashboard_returning_hero.webp";
import microscope from "../../assets/ecosystem/microscope_card.webp";
import microscopeWide from "../../assets/ecosystem/opportunity_microscope.webp";

/** `cover_key` (set in Django admin) → bundled image. Unknown keys fall back to a calm default. */
export const COVERS: Record<string, string> = {
  art_studio: art,
  data,
  tutoring,
  tutoring_2: tutoring2,
  leadership,
  leadership_2: leadership2,
  gardening,
  product_design: productDesign,
  science_lab: science,
  robotics,
  robotics_girl: roboticsGirl,
  mountain,
  microscope,
};

export const coverFor = (key: string) => COVERS[key] ?? mountain;

/** Wide variants for detail headers, where available. */
const WIDE: Record<string, string> = { microscope: microscopeWide };

export const heroCoverFor = (key: string) => WIDE[key] ?? coverFor(key);
