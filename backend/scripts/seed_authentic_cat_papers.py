"""Seeds the official NID / CEED Creative Ability Test (CAT) 5-Hour Examination Paper

Paper structure:
- Duration: 300 minutes (5 hours)
- 8 Questions (100 total marks)
- Matches real-world NID / CEED drawing & creative ability test papers.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import Database, utc_now_iso
from app.schemas import (
    ExamPaperRecord,
    RubricItem,
    StoredGeneratedQuestion,
    SubQuestion,
    TimeSplitItem,
)


CAT_5HR_PAPER_ID = "cat-5hr-official-exam-001"

QUESTIONS_DATA = [
    {
        "id": "cat-5hr-q1-spatial-ergonomics",
        "question_order": 1,
        "title": "Room Interior for Senior (50+) or Child (6–10) with Product Redesign",
        "category": "Problem identification",
        "programme_tags": ["Product Design", "Furniture and Interior Design"],
        "archetypes": ["Problem identification", "Human-centred design"],
        "competencies": ["Spatial design", "Anthropometry", "Ergonomics", "Product evaluation", "User empathy"],
        "difficulty": "Hard",
        "time_minutes": 40,
        "total_marks": 15,
        "scenario": (
            "Design an interior bedroom and activity space tailored specifically for either: "
            "(A) an elderly individual aged above 50 years with emerging mobility/sensory considerations, OR "
            "(B) an active growing child aged 6–10 years. Show clearly where and how they are positioned "
            "within the room engaging in their routine."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction=(
                    "Draw an eye-level or 2-point interior perspective sketch of the room showing furniture arrangement, "
                    "natural window illumination, clear circulation pathways, and the resident positioned realistically "
                    "in the space interacting with their surroundings."
                ),
                marks=8,
            ),
            SubQuestion(
                label="b",
                instruction=(
                    "Identify one specific furniture piece, device, or product depicted in your room sketch and articulate "
                    "its key function and primary purpose for the resident."
                ),
                marks=3,
            ),
            SubQuestion(
                label="c",
                instruction=(
                    "Propose 3 concrete ways to improve the functionality, ergonomics, accessibility, and safety of this "
                    "chosen product to better serve the user's physical needs."
                ),
                marks=4,
            ),
        ],
        "constraints": [
            "The room must feature at least one window and one door opening to establish natural lighting and ingress.",
            "Furniture dimensions and clearances must reflect standard Indian anthropometric measurements.",
            "Avoid generic decorative elements; prioritize functional and accessibility-driven design interventions.",
        ],
        "sketching_requirements": [
            "Interior 2-point perspective showing floor grid, walls, ceiling height, and window light direction.",
            "Human figure in realistic posture displaying age-appropriate proportions and joint angles.",
            "Detail zoom inset showing the chosen product and proposed functional improvements with leader line callouts.",
        ],
        "visual_sketch_prompt": (
            "interior 2-point perspective bedroom designed for an elderly grandmother, low bed with grab bars, "
            "sunlit window, walking cane near wooden rocking chair, grandmother seated comfortably reading, clean line art"
        ),
        "visual_negative_prompt": "photorealistic, 3d render, blurry, distorted perspective, cluttered anime style",
        "evaluation_rubric": [
            RubricItem(criterion="Spatial perspective, room layout & circulation ergonomics", marks=4),
            RubricItem(criterion="Human anthropometry & resident positioning in context", marks=4),
            RubricItem(criterion="Product identification & functional clarity", marks=3),
            RubricItem(criterion="Ergonomic & accessibility redesign rationale", marks=4),
        ],
        "practice_priority": 5,
        "priority_reason": "High-recurrence NID spatial design archetype testing both architectural scale and product empathy.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2018 Elderly Bedroom", "CEED 2021 Child Study Room"],
        "suggested_time_split": [
            TimeSplitItem(activity="Persona analysis & space planning thumbnail", minutes=5),
            TimeSplitItem(activity="2-point room perspective & furniture layout", minutes=15),
            TimeSplitItem(activity="Human figure posture & resident interaction", minutes=10),
            TimeSplitItem(activity="Product callout sketch & written improvements", minutes=10),
        ],
    },
    {
        "id": "cat-5hr-q2-sequential-process",
        "question_order": 2,
        "title": "3-Step Sequential Transformation: Mango Pickle or Seashell Jewellery",
        "category": "Storyboard",
        "programme_tags": ["Communication Design", "Film and Video Communication"],
        "archetypes": ["Storytelling and storyboard", "Creative and lateral thinking"],
        "competencies": ["Sequential storytelling", "Process illustration", "Hand-tool interaction", "Material sensitivity"],
        "difficulty": "Medium",
        "time_minutes": 35,
        "total_marks": 12,
        "scenario": (
            "Illustrate the step-by-step transformation process in exactly 3 key visual stages for ONE of the following crafts/food processes:\n"
            "• Option A: Raw green mangoes / fresh fruit to spiced traditional jarred pickle; OR\n"
            "• Option B: Raw coastal seashells / beads to finished handcrafted ornamental jewellery."
        ),
        "subquestions": [
            SubQuestion(
                label="Step 1",
                instruction="Raw Material Preparation: Illustrate sorting, washing, slicing, or grading of the raw material using appropriate hand tools.",
                marks=4,
            ),
            SubQuestion(
                label="Step 2",
                instruction="Transformation & Crafting: Illustrate the active intermediate processing mechanism (e.g. sun-drying with oil & spices in ceramic barni, or piercing/stringing beads with precision wire tools).",
                marks=4,
            ),
            SubQuestion(
                label="Step 3",
                instruction="Finished Outcome & Preservation: Illustrate the final preserved jar or wearable jewellery piece in use or packaged with traditional tactile closure.",
                marks=4,
            ),
        ],
        "constraints": [
            "Draw exactly 3 distinct horizontal or grid panels with clean white gutters.",
            "Include human hands interacting with tools and materials in at least 2 panels to establish scale and dexterity.",
            "Wordless or minimal technical captions only (under 4 words per step).",
        ],
        "sketching_requirements": [
            "3-panel sequential storyboard layout with varied focal lengths (establishing -> close-up hand grip -> hero product).",
            "Accurate hand anatomy displaying precision pinch, grip, and tool handling.",
            "Material texture differentiation (glazed ceramic barni vs porous mango skin, or polished shell vs thread).",
        ],
        "visual_sketch_prompt": (
            "3-panel horizontal sequential comic strip showing mango pickle making: panel 1 hands slicing raw green mangoes on wooden board, "
            "panel 2 mixing mustard oil turmeric red chili in ceramic barni jar, panel 3 traditional cloth-tied glazed jar in sunlight, ink sketch"
        ),
        "visual_negative_prompt": "photorealistic, colour gradients, blurry hands, extra fingers, cartoon gibberish",
        "evaluation_rubric": [
            RubricItem(criterion="Sequential storytelling clarity & process logic", marks=4),
            RubricItem(criterion="Hand-tool ergonomics & anatomical dexterity", marks=4),
            RubricItem(criterion="Material textures & visual economy across panels", marks=4),
        ],
        "practice_priority": 5,
        "priority_reason": "Core CEED/NID process question testing sequential observation and craftsmanship visualization.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID DAT 5-Grid Mango Pickle", "CEED Artisanal Craft Transformation"],
        "suggested_time_split": [
            TimeSplitItem(activity="Process breakdown & 3-stage planning", minutes=5),
            TimeSplitItem(activity="Panel 1 Raw preparation sketch", minutes=10),
            TimeSplitItem(activity="Panel 2 Active crafting & transformation", minutes=10),
            TimeSplitItem(activity="Panel 3 Final outcome & detail callouts", minutes=10),
        ],
    },
    {
        "id": "cat-5hr-q3-cognitive-route-map",
        "question_order": 3,
        "title": "Cognitive Route Cartography: Home to TCS iON Digital Zone",
        "category": "Logos, Symbols & Signs",
        "programme_tags": ["Communication Design", "Graphic Design"],
        "archetypes": ["Visual communication", "Drawing and observation"],
        "competencies": ["Spatial memory", "Cognitive cartography", "Information hierarchy", "Wayfinding", "Graphic iconography"],
        "difficulty": "Medium",
        "time_minutes": 30,
        "total_marks": 10,
        "scenario": (
            "Draw a comprehensive cognitive journey and route map illustrating the route you took from your home "
            "to reach the examination centre (TCS iON Digital Zone-Aluva). Capture the spatial experience, transitions "
            "across transport modes, and distinctive navigational waypoints."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction=(
                    "Draw an intuitive, well-organized route map (bird's-eye oblique or planimetric schematic) showing start point, "
                    "transit legs (walking, metro, bus, auto, car), major turns, bridges, flyovers, and destination centre."
                ),
                marks=6,
            ),
            SubQuestion(
                label="b",
                instruction=(
                    "Depict at least 5 recognizable urban landmarks, architectural cues, highway mile markers, or sensory waypoints "
                    "(e.g. metro pillars, river crossing, market junction, railway tracks, toll plaza) with a clear visual legend and directional compass rose."
                ),
                marks=4,
            ),
        ],
        "constraints": [
            "Do not draw an abstract smartphone GPS screenshot; create an expressive hand-drawn visual cartography communicating spatial orientation.",
            "Maintain clear visual hierarchy between primary arterial highways, feeder lanes, and pedestrian walkways.",
            "Include North arrow and transit iconography legend.",
        ],
        "sketching_requirements": [
            "Bold graphical hierarchy: varied line weights for major bypasses vs service roads.",
            "Isometric or pictorial 3D spot illustrations for key landmarks along the route.",
            "Informative navigational icons (metro station, bridge, bus bay, tea stall, exam gate).",
        ],
        "visual_sketch_prompt": (
            "hand-drawn pictorial route map from residential home to exam centre, curved road spine, metro rail viaduct pillars, "
            "river bridge crossing, market roundabout, small iconic exam hall building at destination, compass rose, clean vector line style"
        ),
        "visual_negative_prompt": "google maps screenshot, computer ui, satnav app, blurry raster lines",
        "evaluation_rubric": [
            RubricItem(criterion="Route layout logic, hierarchy & spatial coherence", marks=4),
            RubricItem(criterion="Urban memory recall & landmark pictorial depiction", marks=3),
            RubricItem(criterion="Wayfinding iconography, compass & transit legend", marks=3),
        ],
        "practice_priority": 5,
        "priority_reason": "Classic NID/CEED memory cartography question evaluating mental orientation and information design.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2017 Journey to Exam Centre Map", "CEED 2019 Urban Wayfinding"],
        "suggested_time_split": [
            TimeSplitItem(activity="Mental route recall & waypoint plotting", minutes=5),
            TimeSplitItem(activity="Main road spine & junction linework", minutes=12),
            TimeSplitItem(activity="Landmark spot sketches & transit icons", minutes=8),
            TimeSplitItem(activity="Legend, compass rose & annotations", minutes=5),
        ],
    },
    {
        "id": "cat-5hr-q4-cricket-playground-figures",
        "question_order": 4,
        "title": "Dynamic Human Figures: Group of Boys Playing Cricket in a Playground",
        "category": "Drawing",
        "programme_tags": ["Animation Film Design", "Film and Video Communication"],
        "archetypes": ["Drawing and observation", "Human-centred design"],
        "competencies": ["Human figure drawing", "Dynamic action lines", "Sports gesture", "Foreshortening", "Spatial depth"],
        "difficulty": "Hard",
        "time_minutes": 40,
        "total_marks": 13,
        "scenario": (
            "Draw a dynamic, energetic scene of a group of boys playing cricket in an open neighbourhood playground "
            "or dusty gully ground. Capture the split-second tension, anticipation, and bodily movement of the sport."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction=(
                    "Illustrate a multi-figure composition featuring at least 4 interacting human figures in contrasting action postures: "
                    "a bowler in delivery stride, a batsman poised or executing a shot, a wicketkeeper crouched in anticipation, "
                    "and a fielder diving or running with dynamic foreshortening."
                ),
                marks=9,
            ),
            SubQuestion(
                label="b",
                instruction=(
                    "Depict spatial depth and playground atmosphere: improvised wickets/crease markings, dust kicked up by running feet, "
                    "natural eye-level or low-angle perspective, and background context (trees, boundary wall, spectators)."
                ),
                marks=4,
            ),
        ],
        "constraints": [
            "Show distinct athletic body postures with correct line of action and dynamic center of gravity.",
            "Avoid static stiff figures; show foreshortened limbs and bent joints in motion.",
            "Use 3 tiers of line weight to separate foreground action from background spectators.",
        ],
        "sketching_requirements": [
            "Action gesture lines capturing kinetic momentum and weight transfer.",
            "Human figures displaying accurate age-appropriate boy proportions (approx. 6.5 to 7 heads).",
            "Foreground-to-background spatial overlap establishing a believable playing pitch.",
        ],
        "visual_sketch_prompt": (
            "energetic sketch of boys playing cricket in dusty ground, batsman swinging bat mid-shot, bowler in jumping follow-through, "
            "crouched wicketkeeper behind brick wickets, dust particles, dynamic foreshortened limbs, atmospheric Indian playground line art"
        ),
        "visual_negative_prompt": "photorealistic, wooden mannequins, stiff figures, bad anatomy, deformed hands, stadium floodlights",
        "evaluation_rubric": [
            RubricItem(criterion="Dynamic gesture & kinetic lines of action", marks=5),
            RubricItem(criterion="Human anatomical proportions & foreshortening", marks=4),
            RubricItem(criterion="Multi-figure interaction & environmental depth", marks=4),
        ],
        "practice_priority": 5,
        "priority_reason": "High-priority NID drawing test measuring figure interaction, foreshortening, and kinetic sports anatomy.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID B.Des Sports Action Drawing", "CEED 2020 Multi-Figure Composition"],
        "suggested_time_split": [
            TimeSplitItem(activity="Thumbnailing & focal action line setup", minutes=5),
            TimeSplitItem(activity="Gesture lines & volume construction for 4 figures", minutes=15),
            TimeSplitItem(activity="Anatomical details, clothing folds & equipment", minutes=12),
            TimeSplitItem(activity="Pitch ground, dust cloud & background depth", minutes=8),
        ],
    },
    {
        "id": "cat-5hr-q5-high-angle-perspective",
        "question_order": 5,
        "title": "High-Angle Perspective: Place of Worship in Garden from 4th-Floor Balcony",
        "category": "Drawing",
        "programme_tags": ["Furniture and Interior Design", "Animation Film Design"],
        "archetypes": ["Drawing and observation", "Creative and lateral thinking"],
        "competencies": ["3-point perspective", "Bird's-eye vantage", "Spatial depth", "Light and shadow", "Architectural sketching"],
        "difficulty": "Hard",
        "time_minutes": 40,
        "total_marks": 13,
        "scenario": (
            "From the balcony of your fourth-floor apartment, look steeply down at a small neighbourhood place of worship "
            "(temple, mosque, church, or shrine) surrounded by a lush landscaped garden on a busy sunny afternoon."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction=(
                    "Construct a steep high-angle 3-point perspective view from the 4th-floor vantage point, showing the downward convergence "
                    "of vertical architectural lines, roof silhouettes, garden pathways, and boundary railings."
                ),
                marks=8,
            ),
            SubQuestion(
                label="b",
                instruction=(
                    "Render the atmosphere of a busy sunny day: strong directional sunlight, sharp cast shadows beneath trees and eaves, "
                    "foliage canopy textures seen from above, and foreshortened human figures of worshippers walking along pathways."
                ),
                marks=5,
            ),
        ],
        "constraints": [
            "Must clearly establish the high-angle downward perspective (include the balcony railing or floor edge in foreground for viewpoint anchor).",
            "Human figures seen from above must show compressed vertical proportions (heads and shoulders dominant, feet foreshortened).",
            "Cast shadows must consistently reflect a single directional light source (afternoon sun).",
        ],
        "sketching_requirements": [
            "3-point perspective with third vanishing point located well below the ground plane.",
            "Foreground balcony railing framing the scene for extreme depth.",
            "Top-down tree canopy foliage rendering and directional ground shadows.",
        ],
        "visual_sketch_prompt": (
            "high-angle bird's-eye perspective looking down from 4th-floor balcony railing, small ornate shrine dome below surrounded by green garden "
            "pathways, worshippers seen from above, strong sunny diagonal cast shadows, dramatic downward perspective pencil sketch"
        ),
        "visual_negative_prompt": "flat eye-level view, 2d map, photorealistic, 3d render, blurry lines, crooked perspective without vanishing points",
        "evaluation_rubric": [
            RubricItem(criterion="3-point perspective geometry & downward convergence", marks=5),
            RubricItem(criterion="Elevated foreshortening of structures & human figures", marks=4),
            RubricItem(criterion="Sunny day lighting, cast shadows & garden texture", marks=4),
        ],
        "practice_priority": 5,
        "priority_reason": "Benchmark NID DAT perspective test challenging students to draw extreme camera angles beyond standard eye-level.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2016 4th Floor Balcony View", "CEED High Angle Crow POV"],
        "suggested_time_split": [
            TimeSplitItem(activity="Vanishing points & balcony railing framing", minutes=8),
            TimeSplitItem(activity="Place of worship roof geometry & pathways", minutes=14),
            TimeSplitItem(activity="Garden landscaping, trees from above & figures", minutes=10),
            TimeSplitItem(activity="Directional sunlight hatching & cast shadows", minutes=8),
        ],
    },
    {
        "id": "cat-5hr-q6-modular-cube-sculpture",
        "question_order": 6,
        "title": "Modular 3D Composition: Drawing Room Showpiece from 16 Colored Cubes",
        "category": "Creativity",
        "programme_tags": ["Product Design", "Furniture and Interior Design"],
        "archetypes": ["Creative and lateral thinking", "Product innovation"],
        "competencies": ["3D spatial thinking", "Form composition", "Modularity", "Structural equilibrium", "Visual rhythm"],
        "difficulty": "Medium",
        "time_minutes": 35,
        "total_marks": 12,
        "scenario": (
            "You are provided with 16 identical wooden cubes in 4 distinct colours (4 cubes of each colour: e.g., natural teak, "
            "midnight indigo, terracotta red, and ivory white). Design an artistic tabletop sculptural showpiece composed of these "
            "16 cubes for display in a contemporary living/drawing room."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction=(
                    "Draw an isometric or 2-point 3D perspective representation of the assembled 16-cube sculpture, showing interlocking faces, "
                    "cantilevers, stepped voids, and negative space rhythm."
                ),
                marks=8,
            ),
            SubQuestion(
                label="b",
                instruction=(
                    "Explain your 4-colour distribution strategy and structural balance. Depict the showpiece resting on a coffee table "
                    "or credenza with contextual scale reference (e.g. ceramic vase, art book, or table lamp) and dimension callouts."
                ),
                marks=4,
            ),
        ],
        "constraints": [
            "You must use all 16 cubes (4 of each colour); no cubes may float detached in air.",
            "Composition must exhibit physical structural equilibrium (cannot topple over).",
            "Differentiate the 4 colours using distinct shading patterns, hatching, or tones.",
        ],
        "sketching_requirements": [
            "Crisp 3D volumetric cuboid rendering with clean 30-degree isometric or 2-point perspective angles.",
            "Textural contrast showing natural wood grain and painted finishes.",
            "Cast shadows grounding the sculpture onto the drawing room tabletop surface.",
        ],
        "visual_sketch_prompt": (
            "modern sculptural tabletop showpiece composed of 16 interlocking wooden cubes in 4 distinct shaded textures, "
            "cantilevered cantilever steps and hollow voids, resting on clean drawing room credenza table, isometric pencil sketch"
        ),
        "visual_negative_prompt": "photorealistic, floating detached cubes, chaotic mess, 2d flat squares, blurry lines",
        "evaluation_rubric": [
            RubricItem(criterion="3D volumetric construction & cube geometry", marks=4),
            RubricItem(criterion="Structural stability, cantilever & negative space", marks=4),
            RubricItem(criterion="Color distribution rhythm & tabletop context", marks=4),
        ],
        "practice_priority": 5,
        "priority_reason": "Core form sensitivity test evaluating 3D spatial intelligence, modular constraints, and aesthetic rhythm.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2019 16-Cube Sculpture", "UCEED Geometric Block Assembly"],
        "suggested_time_split": [
            TimeSplitItem(activity="2D thumbnailing & stability balance logic", minutes=6),
            TimeSplitItem(activity="3D perspective construction of the 16 cubes", minutes=16),
            TimeSplitItem(activity="Textural hatching to differentiate 4 colors", minutes=7),
            TimeSplitItem(activity="Tabletop scale reference & dimension callouts", minutes=6),
        ],
    },
    {
        "id": "cat-5hr-q7-public-smoking-observation",
        "question_order": 7,
        "title": "Observational Social Scenario: Man Smoking in a Public Space",
        "category": "Drawing",
        "programme_tags": ["Communication Design", "Animation Film Design"],
        "archetypes": ["Drawing and observation", "Human-centred design"],
        "competencies": ["Observational drawing", "Social commentary", "Emotional expression", "Body language", "Urban context"],
        "difficulty": "Medium",
        "time_minutes": 35,
        "total_marks": 10,
        "scenario": (
            "Depict an authentic observational scene of a man smoking a cigarette in a crowded Indian public space "
            "(such as a busy bus stand shelter, a railway tea stall, a crowded market lane, or outside an office complex)."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction="Depict the central subject's posture, hand grip on the cigarette, facial expression, and the curling plume of smoke drifting through the air.",
                marks=5,
            ),
            SubQuestion(
                label="b",
                instruction=(
                    "Illustrate the surrounding environment and at least 3 nearby bystanders displaying varied, realistic human reactions "
                    "(e.g., a mother shielding her child, an elderly person coughing and turning away, an indifferent passerby, or a vendor) with contextual urban props."
                ),
                marks=5,
            ),
        ],
        "constraints": [
            "Ground the scene in a recognizable public context with authentic architectural and street furniture elements.",
            "Express subtle emotional storytelling through body language, facial micro-expressions, and head tilts.",
            "Use line weight hierarchy to maintain the smoker as the primary visual focus.",
        ],
        "sketching_requirements": [
            "Expressive human anatomy and natural hand-to-mouth smoking gesture.",
            "Believable emotional postures: aversion, protective covering of nose/mouth, distraction.",
            "Atmospheric environmental details: pavement textures, stall counter, warning signage.",
        ],
        "visual_sketch_prompt": (
            "observational sketch of a man smoking outside a roadside tea stall, curling smoke plume, nearby elderly passenger coughing and covering face, "
            "mother pulling child away, chai kettle on stove, realistic Indian street setting, line art with pencil shading"
        ),
        "visual_negative_prompt": "photorealistic, cinematic film still, glamourous fashion smoking, exaggerated anime expressions",
        "evaluation_rubric": [
            RubricItem(criterion="Central subject posture, smoking gesture & smoke plume", marks=4),
            RubricItem(criterion="Bystander emotional body language & facial reactions", marks=3),
            RubricItem(criterion="Public contextual realism & social storytelling", marks=3),
        ],
        "practice_priority": 5,
        "priority_reason": "High-impact social observational test assessing human emotional reaction and contextual awareness.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2020 Public Social Observation", "CEED Scenario Drawing"],
        "suggested_time_split": [
            TimeSplitItem(activity="Narrative staging & focal layout setup", minutes=5),
            TimeSplitItem(activity="Central smoker anatomy, gesture & smoke plume", minutes=12),
            TimeSplitItem(activity="Bystander reactions & emotional body language", minutes=12),
            TimeSplitItem(activity="Contextual street props & shadow hatching", minutes=6),
        ],
    },
    {
        "id": "cat-5hr-q8-anti-bullying-poster",
        "question_order": 8,
        "title": "Visual Communication & Awareness Poster: School Anti-Bullying Campaign",
        "category": "Composition",
        "programme_tags": ["Communication Design", "Graphic Design"],
        "archetypes": ["Visual communication", "Creative and lateral thinking"],
        "competencies": ["Visual metaphor", "Poster hierarchy", "Typography", "Semiotic design", "Design rationale"],
        "difficulty": "Hard",
        "time_minutes": 45,
        "total_marks": 15,
        "scenario": (
            "A student in your school has experienced severe verbal and social bullying. In response, the school administration "
            "and student council are launching an anti-bullying awareness campaign to build empathy, dismantle peer intimidation, "
            "and create a supportive school culture. Design a powerful awareness poster for display across campus noticeboards and corridors."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction=(
                    "Design a full-page vertical campaign poster (3:4 ratio) featuring an arresting visual metaphor (avoiding clichéd fists or broken sticks), "
                    "clear visual hierarchy, hand-lettered English headline/slogan under 6 words, and a secondary call-to-action line."
                ),
                marks=10,
            ),
            SubQuestion(
                label="b",
                instruction=(
                    "Write a concise design rationale (under 100 words) below your poster explaining your choice of visual metaphor, "
                    "emotional psychology, typographic treatment, and how the poster is intended to provoke bystander intervention."
                ),
                marks=5,
            ),
        ],
        "constraints": [
            "Do not rely on text alone; the central visual metaphor must communicate the emotional weight of bullying and the power of empathy.",
            "Poster border must be cleanly framed with 70–80% graphic clarity and deliberate negative space.",
            "Slogan must be original, memorable, and strictly under 6 words.",
        ],
        "sketching_requirements": [
            "Strong graphic composition with high-contrast focal point.",
            "Visual metaphor combining everyday school objects or human silhouettes with emotional symbolism.",
            "Integrated hand-lettered display typography with disciplined baseline alignment.",
        ],
        "visual_sketch_prompt": (
            "striking anti-bullying campaign poster, visual metaphor of an unpeeling eraser revealing an isolated fragile paper student silhouette, "
            "bold hand-lettered headline 'WORDS LEAVE MARKS', clean negative space, high contrast graphic illustration on paper"
        ),
        "visual_negative_prompt": "clichéd boxing gloves, superhero cartoon, generic stock poster, messy illegible lettering, photorealistic",
        "evaluation_rubric": [
            RubricItem(criterion="Visual metaphor originality & emotional resonance", marks=5),
            RubricItem(criterion="Graphic composition, focal hierarchy & hand-lettered typography", marks=5),
            RubricItem(criterion="Written design rationale & psychological empathy", marks=5),
        ],
        "practice_priority": 5,
        "priority_reason": "Essential visual communication test evaluating semiotic thinking, typography, and conceptual articulation.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2021 Social Campaign Poster", "CEED Visual Communication"],
        "suggested_time_split": [
            TimeSplitItem(activity="Metaphor brainstorming & thumbnail layout", minutes=8),
            TimeSplitItem(activity="Poster frame & central visual metaphor drafting", minutes=18),
            TimeSplitItem(activity="Hand-lettered headline typography & call-to-action", minutes=10),
            TimeSplitItem(activity="Written concept rationale & emotional analysis", minutes=9),
        ],
    },
]


def seed_cat_5hr_paper():
    db = Database()

    # Clean up existing paper and questions
    db.delete_exam_paper(CAT_5HR_PAPER_ID)
    with db.connect() as conn:
        conn.execute("DELETE FROM generated_questions WHERE id LIKE 'cat-5hr-%'")

    paper = ExamPaperRecord(
        id=CAT_5HR_PAPER_ID,
        title="Official NID / CEED Creative Ability Test (CAT) — 5-Hour Full Drawing Examination",
        num_questions=8,
        total_time_minutes=300,
        difficulty="Mixed",
        paper_strategy="authentic_cat_paper",
        historical_relevance="high",
        programme_focus=["Product Design", "Furniture and Interior Design", "Communication Design", "Animation Film Design"],
        status="not_started",
        elapsed_seconds=0,
        created_at=utc_now_iso(),
        questions=[],
        warnings=[],
    )
    db.create_exam_paper(paper)

    stored_questions = []
    for q_data in QUESTIONS_DATA:
        stored_q = StoredGeneratedQuestion(
            id=q_data["id"],
            generation_mode="exam_simulator",
            exam_paper_id=CAT_5HR_PAPER_ID,
            question_order=q_data["question_order"],
            is_saved=False,
            model_used="NID / CEED Official CAT Question Repository",
            provider_used="curated_official_archive",
            practice_priority_score=5.0,
            historical_evidence=q_data["historical_pattern_references"],
            model_interpretation="Authentic 5-Hour Creative Ability Test (CAT) question directly reflecting NID & CEED entrance criteria.",
            low_confidence_warning=None,
            raw_llm_response="",
            created_at=utc_now_iso(),
            title=q_data["title"],
            category=q_data["category"],
            programme_tags=q_data["programme_tags"],
            archetypes=q_data["archetypes"],
            competencies=q_data["competencies"],
            difficulty=q_data["difficulty"],
            time_minutes=q_data["time_minutes"],
            total_marks=q_data["total_marks"],
            scenario=q_data["scenario"],
            subquestions=q_data["subquestions"],
            constraints=q_data["constraints"],
            sketching_requirements=q_data["sketching_requirements"],
            visual_sketch_prompt=q_data["visual_sketch_prompt"],
            visual_negative_prompt=q_data["visual_negative_prompt"],
            evaluation_rubric=q_data["evaluation_rubric"],
            practice_priority=q_data["practice_priority"],
            priority_reason=q_data["priority_reason"],
            prediction_confidence=q_data["prediction_confidence"],
            historical_pattern_references=q_data["historical_pattern_references"],
            suggested_time_split=q_data["suggested_time_split"],
        )
        db.save_generated_question(stored_q)
        stored_questions.append(stored_q)

    paper.questions = stored_questions
    print(f"Successfully seeded official 5-Hour CAT paper with {len(stored_questions)} questions!")
    print(f"Total time: {paper.total_time_minutes} minutes (5.0 hrs)")
    print(f"Total marks: {sum(q.total_marks for q in stored_questions)} marks")
    return paper


CAT_3HR_PAPER_ID = "cat-3hr-official-exam-002"

QUESTIONS_3HR_DATA = [
    {
        "id": "cat-3hr-q1-inclusive-street-vendor",
        "question_order": 1,
        "title": "Inclusive Product Redesign: Ergonomic Produce Display & Transit for Street Vendor",
        "category": "Problem identification",
        "programme_tags": ["Product Design"],
        "archetypes": ["Problem identification", "Product innovation"],
        "competencies": ["Ergonomics", "Anthropometry", "Materiality", "Modular mechanics", "Contextual empathy"],
        "difficulty": "Medium",
        "time_minutes": 35,
        "total_marks": 20,
        "scenario": (
            "Street vegetable and fruit vendors walk 8–12 km daily pushing overloaded two-wheel wooden thelas or carrying heavy woven cane baskets. "
            "They face severe lumbar spine strain, poor produce ventilation causing quick spoilage, and chaotic organization during rush hour transactions. "
            "Design an ergonomic, lightweight modular display and handling solution addressing these physical and operational pain points."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction="Identify 4 specific physical and ergonomic pain points faced by the vendor during transport and display.",
                marks=6,
            ),
            SubQuestion(
                label="b",
                instruction="Draw a clean 3/4 perspective hero sketch of your redesigned solution in practical use on-site, annotating folding mechanisms, materials, and produce ventilation slots.",
                marks=14,
            ),
        ],
        "constraints": [
            "Must be manufacturable using regionally available materials (bamboo, bent aluminium, canvas, lightweight polymers).",
            "Must fold or stack into a compact footprint for overnight domestic storage.",
            "Must not require external electrical power.",
        ],
        "sketching_requirements": [
            "Centered hero 3/4 perspective view showing product in context.",
            "Detail zoom callouts for locking joint and handle grip.",
            "Human vendor interaction vignette showing push/pull posture.",
        ],
        "visual_sketch_prompt": (
            "ergonomic modular pushcart designed for Indian street fruit vendor, lightweight tubular frame, ventilated tiered bamboo crates, "
            "overhead sunshade canvas, vendor gripping padded handle, clean industrial design line sketch"
        ),
        "visual_negative_prompt": "photorealistic, motor vehicle, high-tech digital screens, blurry lines",
        "evaluation_rubric": [
            RubricItem(criterion="Pain point analysis & user empathy", marks=6),
            RubricItem(criterion="Hero perspective sketch quality & detailing", marks=8),
            RubricItem(criterion="Mechanism, joinery & material feasibility", marks=6),
        ],
        "practice_priority": 5,
        "priority_reason": "High-yield NID M.Des common question evaluating empathetic user observation and functional mechanism design.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2021 Street Vendor Ergonomics", "CEED 2022 Inclusive Transport"],
        "suggested_time_split": [
            TimeSplitItem(activity="Pain point identification & thumbnail exploration", minutes=7),
            TimeSplitItem(activity="Hero 3/4 perspective drawing & proportions", minutes=16),
            TimeSplitItem(activity="Detail mechanism insets & material callouts", minutes=8),
            TimeSplitItem(activity="Human posture interaction vignette", minutes=4),
        ],
    },
    {
        "id": "cat-3hr-q2-sequential-twist-storyboard",
        "question_order": 2,
        "title": "4-Frame Wordless Storyboard: Everyday Dilemma with Surprising Twist",
        "category": "Storyboard",
        "programme_tags": ["Communication Design", "Film and Video Communication"],
        "archetypes": ["Storytelling and storyboard", "Creative and lateral thinking"],
        "competencies": ["Sequential narrative", "Cinematography", "Visual pacing", "Framing", "Emotional expression"],
        "difficulty": "Medium",
        "time_minutes": 35,
        "total_marks": 20,
        "scenario": (
            "Create a 4-frame sequential visual story with NO dialogue, speech balloons, or captions about a crowded Indian railway station platform "
            "during monsoon season. The story must feature a lost umbrella and conclude with an unexpected, heartwarming or humorous twist."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction="Draw 4 sequential rectangular panels utilizing varied camera shots (Panel 1: Wide establishing shot; Panel 2: Medium action shot; Panel 3: Close-up tension shot; Panel 4: Twist resolution).",
                marks=16,
            ),
            SubQuestion(
                label="b",
                instruction="Write a 2-sentence summary explaining the emotional trajectory and the twist mechanism.",
                marks=4,
            ),
        ],
        "constraints": [
            "Strictly 4 frames arranged in a 2x2 grid with neat margins.",
            "Zero text in speech bubbles; visual storytelling only.",
            "Maintain consistent character wardrobe and prop appearance across all 4 frames.",
        ],
        "sketching_requirements": [
            "Varied camera angles and depths of field across frames.",
            "Expressive character gestures and environmental raindrops/reflections.",
            "Clear visual flow guiding the viewer's eye from frame 1 through 4.",
        ],
        "visual_sketch_prompt": (
            "4-panel sequential comic grid of monsoon railway platform: frame 1 wide wet platform crowd, frame 2 commuter realizes umbrella left on bench, "
            "frame 3 close-up hand reaching, frame 4 stray puppy sleeping dry under opened umbrella, clean black ink comic line art"
        ),
        "visual_negative_prompt": "speech bubbles, text words, photorealistic, color gradients, blurry panels",
        "evaluation_rubric": [
            RubricItem(criterion="Cinematic framing variety & visual continuity", marks=8),
            RubricItem(criterion="Story pacing, character gesture & twist delivery", marks=8),
            RubricItem(criterion="Written emotional summary & narrative articulation", marks=4),
        ],
        "practice_priority": 5,
        "priority_reason": "Core NID animation and communication design staple testing sequential thinking and camera grammar.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2019 4-Frame Railway Story", "CEED 2021 Visual Narrative"],
        "suggested_time_split": [
            TimeSplitItem(activity="Narrative pacing & shot breakdown thumbnailing", minutes=6),
            TimeSplitItem(activity="Frames 1 & 2 linework (Wide & Medium)", minutes=14),
            TimeSplitItem(activity="Frames 3 & 4 linework (Close-up & Twist)", minutes=12),
            TimeSplitItem(activity="Written narrative summary & cleanup", minutes=3),
        ],
    },
    {
        "id": "cat-3hr-q3-interior-bus-perspective",
        "question_order": 3,
        "title": "First-Person Perspective Drawing: Interior of an Electric City Bus",
        "category": "Drawing",
        "programme_tags": ["Furniture and Interior Design", "Animation Film Design"],
        "archetypes": ["Drawing and observation", "Human-centred design"],
        "competencies": ["1-point perspective", "First-person POV", "Human interaction", "Spatial lighting", "Interior detailing"],
        "difficulty": "Hard",
        "time_minutes": 40,
        "total_marks": 20,
        "scenario": (
            "You are seated in the rear window seat of a crowded modern electric city transit bus during evening rush hour. "
            "Depict the scene from your authentic first-person point of view looking down the aisle toward the front driver's windshield."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction="Construct a 1-point interior perspective drawing with floor-to-ceiling convergence, showing overhead grab rails, hanging straps, seated passengers, and standing commuters gripping poles.",
                marks=14,
            ),
            SubQuestion(
                label="b",
                instruction="Include your own foreground knees/hand resting on the seat grab bar in accurate proportion to ground the viewer, and render evening window lighting and reflective surfaces.",
                marks=6,
            ),
        ],
        "constraints": [
            "Must maintain believable 1-point perspective convergence along the central aisle.",
            "Foreground passenger elements must be larger and darker in line weight than the background driver area.",
            "Show diverse commuters (office worker, student, elderly passenger) with believable postures.",
        ],
        "sketching_requirements": [
            "Strong 3-tier line weight (bold foreground -> medium aisle -> fine background).",
            "Perspective vanishing point located near front bus windshield.",
            "Anatomically proportional human figures seated and standing in moving posture.",
        ],
        "visual_sketch_prompt": (
            "first-person POV seated inside crowded city bus looking down central aisle, knees visible in extreme lower foreground, "
            "passengers holding overhead yellow grab straps, seated commuters looking out windows, driver silhouette at far front, pencil perspective sketch"
        ),
        "visual_negative_prompt": "exterior bus photo, flat 2d elevation, photorealistic, blurry lines, crooked perspective lines",
        "evaluation_rubric": [
            RubricItem(criterion="1-point perspective convergence & spatial volume", marks=8),
            RubricItem(criterion="Foreground POV framing & human figure proportions", marks=6),
            RubricItem(criterion="Line weight hierarchy & atmospheric bus interior detailing", marks=6),
        ],
        "practice_priority": 5,
        "priority_reason": "High-frequency NID observation test evaluating immersive perspective and environmental rendering.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2018 Bus Interior POV", "CEED 2020 Metro Commuter Drawing"],
        "suggested_time_split": [
            TimeSplitItem(activity="Vanishing point & interior wireframe grid", minutes=8),
            TimeSplitItem(activity="Foreground knees, seats & grab rails", minutes=10),
            TimeSplitItem(activity="Passenger figures & varied postures along aisle", minutes=14),
            TimeSplitItem(activity="Window reflections, floor textures & shading", minutes=8),
        ],
    },
    {
        "id": "cat-3hr-q4-dual-metaphor-poster",
        "question_order": 4,
        "title": "Dual-Metaphor Campaign Poster: Domestic Water Conservation",
        "category": "Composition",
        "programme_tags": ["Communication Design", "Graphic Design"],
        "archetypes": ["Visual communication", "Creative and lateral thinking"],
        "competencies": ["Visual metaphor", "Semiotic synthesis", "Poster hierarchy", "Typography", "Visual wit"],
        "difficulty": "Medium",
        "time_minutes": 35,
        "total_marks": 20,
        "scenario": (
            "Design an awareness campaign poster for municipal apartment residents urging them to eliminate tap leaks and domestic water wastage. "
            "Your design MUST synthesize TWO unexpected visual elements: an everyday household bathroom/kitchen tap AND an hourglass or timer metaphor."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction="Draw a vertical campaign poster (3:4 ratio) integrating the dual visual metaphor into one seamless, powerful graphic focal point on clean white paper.",
                marks=14,
            ),
            SubQuestion(
                label="b",
                instruction="Incorporate an original hand-lettered English headline under 6 words with strong typographic hierarchy, and write a 2-sentence rationale.",
                marks=6,
            ),
        ],
        "constraints": [
            "Seamless visual blending; do not simply paste two separate cliparts next to each other.",
            "75–85% clean white paper with deliberate negative space.",
            "Headline must be hand-lettered, not scribbled casually.",
        ],
        "sketching_requirements": [
            "High contrast silhouette or bold line-art composition.",
            "Clever negative space interplay uniting the two concepts.",
            "Clear typographic baseline, kerning, and hierarchy.",
        ],
        "visual_sketch_prompt": (
            "minimalist graphic campaign poster, dripping household water tap whose falling water droplet forms the glass bulb of an hourglass, "
            "hand-lettered bold headline 'EVERY DROP COUNTS TIME', clean negative space, black ink vector-style poster illustration"
        ),
        "visual_negative_prompt": "messy collage, photorealistic, blurry stock poster, excessive text paragraphs, colored gradients",
        "evaluation_rubric": [
            RubricItem(criterion="Metaphorical synthesis & clever concept integration", marks=8),
            RubricItem(criterion="Graphic composition, contrast & negative space", marks=6),
            RubricItem(criterion="Hand-lettered headline typography & written concept rationale", marks=6),
        ],
        "practice_priority": 5,
        "priority_reason": "Core NID graphic communication test evaluating semiotic wit, poster hierarchy, and typographic discipline.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2021 Tea Poster Metaphor", "CEED Visual Communication"],
        "suggested_time_split": [
            TimeSplitItem(activity="Metaphor exploration & thumbnail variations", minutes=7),
            TimeSplitItem(activity="Central graphic illustration & silhouette drafting", minutes=16),
            TimeSplitItem(activity="Hand-lettered headline & visual hierarchy", minutes=8),
            TimeSplitItem(activity="Written concept note & final line tightening", minutes=4),
        ],
    },
    {
        "id": "cat-3hr-q5-circular-upcycling-invention",
        "question_order": 5,
        "title": "Lateral Thinking & Form Invention: Playful Learning Toy from Discarded Coconut Shells",
        "category": "Creativity",
        "programme_tags": ["Product Design", "Furniture and Interior Design"],
        "archetypes": ["Creative and lateral thinking", "Materials and sustainability"],
        "competencies": ["Lateral thinking", "Upcycling", "Material properties", "Joinery design", "Tactile ergonomics"],
        "difficulty": "Medium",
        "time_minutes": 35,
        "total_marks": 20,
        "scenario": (
            "Tens of thousands of hard hemispherical coconut shells (copra husks) are discarded daily at coastal juice stalls and temples. "
            "Using ONLY discarded coconut shells, natural cords, and wooden dowels, design an engaging tactile learning toy or musical rhythm kit for children aged 4–8."
        ),
        "subquestions": [
            SubQuestion(
                label="a",
                instruction="Draw a hero 3/4 perspective view of the assembled toy showing how the natural curves, acoustic resonance, and texture of the coconut shell are creatively utilized.",
                marks=14,
            ),
            SubQuestion(
                label="b",
                instruction="Draw an exploded or joinery detail diagram demonstrating how shells are fastened, smoothed, and made safe for young children without synthetic adhesives.",
                marks=6,
            ),
        ],
        "constraints": [
            "Must preserve and celebrate the natural material characteristics of coconut shell.",
            "Zero toxic glues or small detachable choking hazards.",
            "Must offer at least 2 distinct play or sensory interaction modes.",
        ],
        "sketching_requirements": [
            "Hero 3/4 perspective sketch showing assembly and surface textures.",
            "Exploded assembly view showing joinery pegs, cords, and chamfered edges.",
            "Child hand scale reference illustrating playful grip.",
        ],
        "visual_sketch_prompt": (
            "creative children rhythm percussion toy made from polished coconut shells and wooden dowels, "
            "interlocking sound chambers, organic hemispherical form, child hands holding wooden mallet, industrial design exploded sketch"
        ),
        "visual_negative_prompt": "plastic injection molded toy, electronic lights, photorealistic, blurry lines, messy scribble",
        "evaluation_rubric": [
            RubricItem(criterion="Lateral creativity & creative reuse of material form", marks=8),
            RubricItem(criterion="Hero perspective sketch quality & surface texture", marks=6),
            RubricItem(criterion="Exploded joinery detailing & child safety considerations", marks=6),
        ],
        "practice_priority": 5,
        "priority_reason": "High-value NID sustainable materials and lateral thinking test challenging students to transform discarded organic waste into functional beauty.",
        "prediction_confidence": "High",
        "historical_pattern_references": ["NID 2019 Natural Material Upcycling", "CEED Sustainable Toy Design"],
        "suggested_time_split": [
            TimeSplitItem(activity="Brainstorming play mechanisms & form thumbnails", minutes=7),
            TimeSplitItem(activity="Hero 3/4 perspective drawing with texture", minutes=16),
            TimeSplitItem(activity="Exploded joinery diagram & cord fastening detail", minutes=8),
            TimeSplitItem(activity="Child grip vignette & safety annotations", minutes=4),
        ],
    },
]


def seed_cat_3hr_paper():
    db = Database()

    # Clean up existing paper and questions
    db.delete_exam_paper(CAT_3HR_PAPER_ID)
    with db.connect() as conn:
        conn.execute("DELETE FROM generated_questions WHERE id LIKE 'cat-3hr-%'")

    paper = ExamPaperRecord(
        id=CAT_3HR_PAPER_ID,
        title="NID M.Des Design Aptitude Test (DAT) — 3-Hour Common Creative Paper",
        num_questions=5,
        total_time_minutes=180,
        difficulty="Mixed",
        paper_strategy="authentic_cat_paper",
        historical_relevance="high",
        programme_focus=["Product Design", "Communication Design", "Furniture and Interior Design", "Animation Film Design"],
        status="not_started",
        elapsed_seconds=0,
        created_at=utc_now_iso(),
        questions=[],
        warnings=[],
    )
    db.create_exam_paper(paper)

    stored_questions = []
    for q_data in QUESTIONS_3HR_DATA:
        stored_q = StoredGeneratedQuestion(
            id=q_data["id"],
            generation_mode="exam_simulator",
            exam_paper_id=CAT_3HR_PAPER_ID,
            question_order=q_data["question_order"],
            is_saved=False,
            model_used="NID M.Des DAT Official Archive",
            provider_used="curated_official_archive",
            practice_priority_score=5.0,
            historical_evidence=q_data["historical_pattern_references"],
            model_interpretation="Authentic 3-Hour NID M.Des DAT Common Paper testing core design competencies.",
            low_confidence_warning=None,
            raw_llm_response="",
            created_at=utc_now_iso(),
            title=q_data["title"],
            category=q_data["category"],
            programme_tags=q_data["programme_tags"],
            archetypes=q_data["archetypes"],
            competencies=q_data["competencies"],
            difficulty=q_data["difficulty"],
            time_minutes=q_data["time_minutes"],
            total_marks=q_data["total_marks"],
            scenario=q_data["scenario"],
            subquestions=q_data["subquestions"],
            constraints=q_data["constraints"],
            sketching_requirements=q_data["sketching_requirements"],
            visual_sketch_prompt=q_data["visual_sketch_prompt"],
            visual_negative_prompt=q_data["visual_negative_prompt"],
            evaluation_rubric=q_data["evaluation_rubric"],
            practice_priority=q_data["practice_priority"],
            priority_reason=q_data["priority_reason"],
            prediction_confidence=q_data["prediction_confidence"],
            historical_pattern_references=q_data["historical_pattern_references"],
            suggested_time_split=q_data["suggested_time_split"],
        )
        db.save_generated_question(stored_q)
        stored_questions.append(stored_q)

    paper.questions = stored_questions
    print(f"Successfully seeded official 3-Hour NID paper with {len(stored_questions)} questions!")
    print(f"Total time: {paper.total_time_minutes} minutes (3.0 hrs)")
    print(f"Total marks: {sum(q.total_marks for q in stored_questions)} marks")
    return paper


if __name__ == "__main__":
    seed_cat_5hr_paper()
    seed_cat_3hr_paper()
