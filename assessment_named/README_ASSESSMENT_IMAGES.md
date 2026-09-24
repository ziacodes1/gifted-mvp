# Gifted Assessment Visual Asset Map

These images are visual prompts for assessment choices. **Do not expose internal signal/category names to the learner.** The filename/category is for implementation only.

## Usage rules

- Prefer a different image for each option in a question.
- Do not keep repeating the exact same 4 images across every question.
- The visible answer text should describe a concrete action or situation, not labels such as “Science & Investigation” or “Leadership & Organizing”.
- Keep scoring/category mappings hidden in backend data.
- Use the image whose scene best matches the concrete answer option.
- Reuse an image only when the underlying activity truly repeats; otherwise create/add a new scene.
- Do not use these images for aptitude/pattern/spatial questions; those need purpose-built diagrams/tasks.

## Assets

| File | Internal intent | Best use |
|---|---|---|
| `interest_technology_robotics_boy_workshop.png` | Technology / Building | Hands-on robotics, electronics, fixing/building; use for a practical technology choice. |
| `interest_science_microscope_girl_lab_dark_cardigan.png` | Science / Investigation | Microscope investigation in a school lab; use for curiosity, biology, research choices. |
| `interest_art_painting_girl_sketchbook_studio.png` | Art / Creative Expression | Painting/sketchbook work in an art studio; use for visual creativity or making artwork. |
| `interest_helping_tutoring_older_girl_younger_girl.png` | Helping / Teaching | Older student helping a younger girl with schoolwork; use for mentoring, teaching, support. |
| `interest_leadership_group_presentation_whiteboard_black_shirt.png` | Leadership / Organizing | Teen leading a team discussion at a whiteboard; use for coordination, presenting, organizing. |
| `interest_technology_robotics_girl_workshop.png` | Technology / Building | Girl assembling a robot in a maker workshop; alternate tech/building scene. |
| `interest_science_microscope_girl_lab_overalls.png` | Science / Investigation | Girl using microscope with lab materials; alternate science/investigation scene. |
| `interest_art_painting_girl_canvas_studio.png` | Art / Creative Expression | Girl painting a large canvas; use for fine art, visual creativity, aesthetic expression. |
| `interest_helping_tutoring_older_girl_younger_boy.png` | Helping / Teaching | Older student tutoring a younger boy; alternate mentoring/helping scene. |
| `interest_leadership_group_presentation_whiteboard_green_sweater.png` | Leadership / Organizing | Girl presenting ideas to peers at a whiteboard; alternate leadership/group coordination scene. |
| `interest_nature_gardening_girl_planting_outdoors.png` | Nature / Environment | Teen planting in a garden; use for nature, environment, hands-on outdoor activity. |
| `interest_product_design_backpack_prototype_girl_workshop.png` | Product Design / Making | Teen prototyping or modifying a backpack from sketches; use for design thinking, practical creation. |
| `interest_data_analysis_girl_laptop_charts.png` | Analysis / Data / Planning | Teen studying charts on a laptop; use for data analysis, research, planning, problem solving. |

## Example

Visible learner option:
> Build a small robot that solves a classroom problem.

Use:
`interest_technology_robotics_girl_workshop.png`

Hidden backend mapping may map that option to a technology/building interest signal. The learner should not see that category label.
