"""Reverse-Engineered NID / CEED / UCEED Visual Sketch Knowledge Base.

Distilled from:
- 80+ real NID, CEED, and UCEED student examination sheets studied directly on Pinterest
  across Scene Drawing, Problem Identification, Product Design, Logos/Symbols/Signs,
  Storyboards, and Perspective Drawing; AND
- 11 curated user reference sheets (Hand+Screw, Desk Mate, Masala Dosa 4-panel,
  2-panel Domestic Perspective, 5-grid Mango Pickle, Chef at Work, NID 2021 Tea Poster,
  Do-Not-Feed Sign, Ergonomic Toothbrush, Toilet Pictograms, Blind Bottle).

Each category recipe separates:
  1. Design-thinking visual grammar (what makes a top-scoring NID/CEED answer)
  2. Reverse-engineered Pinterest prompt exemplar (few-shot anchor for local Ollama LLM)
  3. DreamShaper XL Turbo verified 2D line-art lock + strict firewall negative rules
"""

from __future__ import annotations

from typing import Dict, List


PINTEREST_RESEARCH_PILLARS: List[str] = [
    "Extreme POV & Foreground Overlap (Scenes & Perspective): Top-scoring NID scenes rarely use flat eye-level front views — they use immersive 1st-person POV (autorickshaw back seat with knees in foreground), extreme-foreground prop framing (oversized soda cans/cups/basket rim), bird's-eye crow POV, or worm's-eye low-angle views with 3-tier line weight (dark bold foreground -> medium midground -> light hairline background).",
    "Functional Engineering Visibility (Product & Problem Identification): Real NID product sheets (SOAP HOLDER, BASKY, ROSHNI, BLIND BOTTLE, SATHI, WOODY) always show HOW the product works — open lids, drainage plates, living hinges, velcro straps, tactile grip bumps, bamboo joinery, or ergonomic handles in bold 3/4 view, never smooth closed mystery blobs.",
    "Pure Binary Contrast & Uniform Grids (Logos, Symbols & Signs): Wayfinding/signage sheets (MOHEIM SIGNS, Toilet Pictograms, No-Feeding Sign) use crisp flat 2D solid-black geometric silhouettes on pure white paper with identical stroke weight and zero 3D mockups; single logos synthesize two visual metaphors via clever negative space.",
    "Cinematic 4-Frame Shot Progression (Storyboards): Authentic NID storyboards (Masala Dosa, Vegetable Market, Basketball Pass, Lightbulb Smash) use neat 2x2 rectangular grids with clean white gutters, consistent character clothing/hair across frames, and deliberate shot progression (Wide Establishing -> Medium Action -> Close-Up Hands/Reaction -> Resolution).",
    "Unified Visual-Flow Metaphor (Composition & Creativity): Top NID posters and lateral-thinking sketches (NID 2021 Tea Poster, Ergonomic Toothbrush) connect familiar everyday objects into one sweeping contour composition on 75-85% clean white paper, optionally using ONE restrained flat pastel/warm accent color for focal hierarchy.",
    "Zero AI Photo / Gibberish-Text Slop: Local DreamShaper XL Turbo is strictly firewalled from photorealism triggers ('realistic', 'industrial design', 'examination sheet', 'annotations', '20 minutes', 'table') and locked into proven 2D black ink / coloring-book outline / flat-vector icon grammars.",
]


# Category-level reverse-engineered knowledge powering both Question Generation and Draw Things rendering
CATEGORY_SKETCH_KNOWLEDGE: Dict[str, Dict[str, object]] = {
    "Drawing": {
        "pinterest_references": [
            "Autorickshaw back-seat moving POV (knees in foreground, driver ahead, city road outside)",
            "Crow's-eye bird's-eye view looking past branch onto a Fresh Juice cart",
            "Supermarket counter with huge soda cans in extreme foreground and shopkeeper behind",
            "Head chef at stove with foreground back-view helper chef (10.5/13 marks)",
            "Close-up human hand pinching a tiny metal screw in accurate proportion",
        ],
        "camera_angles": [
            "first-person POV with foreground knees/hands framing the midground action",
            "extreme foreground prop overlap (large everyday object in lower foreground, people behind)",
            "1-point eye-level interior perspective with floor/ceiling lines converging to horizon",
            "bird's-eye high-angle view looking steeply down onto an everyday Indian scene",
            "close-up human hand holding or operating a small everyday tool in accurate scale",
        ],
        "visual_rules": (
            "Choose a strong NID camera angle (1st-person POV, extreme foreground prop overlap, bird's-eye, "
            "or close-up human hand scale). Show clear 3-tier depth (bold foreground -> midground action -> "
            "light background everyday Indian props), gesture-based human postures, and parallel diagonal hatching."
        ),
        "reverse_engineered_example": (
            "first-person back-seat POV inside a moving Indian autorickshaw, passenger knees in lower foreground, "
            "driver in khaki shirt seen from behind gripping handlebars, crowded street bus and shops through front windshield"
        ),
        "default_style_preset": "observational_pencil",
    },
    "Product sketch": {
        "pinterest_references": [
            "BLIND BOTTLE (hand-drawn concept sheet: 3/4 hero bottle in center with tactile bumps, exploded cap with silicone straw, flip-lid zoom bubble, and hand-in-use drinking vignette)",
            "DESK MATE (hand-drawn concept sheet: 3/4 organizer with mug on heating plate, zoom callout of control buttons, top view heating coil, hand pressing button)",
            "SOAP HOLDER (3/4 wall-mounted dish with exploded sliding drainage plate and zigzag ventilation ridges)",
            "BASKY & Sketchy Packy (convertible shopping/sketch organizer showing shoulder strap in-use silhouette and folding joints)",
            "ROSHNI (collapsible solar emergency lantern showing accordion ribs compressing from tall cylinder to flat puck)",
            "BED BUDDY (multifunctional bedside table with pull-out tray, warm dimmable light, and feature specification column)",
            "SATHI (wearable wrist medication reminder with forearm/fingertip adjustment vignette)",
            "Ergonomic Toothbrush for Elderly (wide contoured grip & angled bristles with close-up hand power-grip)",
        ],
        "camera_angles": [
            "multi-element concept sheet: centered hero 3/4 perspective view showing form & surface textures, circular zoom-in detail callout bubble showing internal mechanism on upper corner, ergonomic vignette of human hand gripping the product on lower corner",
            "bold 3/4 perspective view with exploded cap/lid showing internal straw, filter, or sliding drainage tray",
            "3/4 perspective view showing interlocking joinery, hinge mechanism, and tactile grip affordance",
        ],
        "visual_rules": (
            "Compose an authentic NID/CEED multi-element concept presentation sheet: (1) Centered hero 3/4 perspective sketch showing form, parting lines, and tactile textures; (2) Zoom-in circular detail callout bubble or exploded view showing internal mechanism/assembly; (3) Ergonomic in-use vignette showing human hand grip or user interaction to prove scale; (4) Graphite pencil linework and diagonal parallel hatching on clean white paper with generous negative space. Never a floating single object or photorealistic render."
        ),
        "reverse_engineered_example": (
            "concept sketch presentation sheet: centered hero 3/4 perspective drawing of an ergonomic water bottle with tactile silicone grip bumps, circular zoom-in detail callout bubble on upper corner showing flip-top lid mechanism, small ergonomic vignette of human hand gripping the bottle on lower corner, graphite pencil line art on clean white paper"
        ),
        "default_style_preset": "product_sketch",
    },
    "Problem identification": {
        "pinterest_references": [
            "Crowded Indian vegetable market / railway waiting hall / supermarket aisle friction scenes",
            "SOAP HOLDER & BLIND BOTTLE & SATHI (targeted ergonomic fix addressing a specific user struggle)",
            "Mother multitasking in kitchen while child throws food (2-panel domestic chaos)",
        ],
        "camera_angles": [
            "eye-level 1-point perspective scene making the human struggle immediately visible through body posture",
            "high-angle crowd/queue perspective showing bottleneck, luggage, umbrellas, and confused commuters",
            "3/4 perspective view of a practical low-cost product/spatial fix solving the exact friction point",
        ],
        "visual_rules": (
            "Depending on the prompt, depict EITHER: (a) an immersive Indian situational scene where body posture, "
            "crowding, wet floors, or awkward luggage make the exact everyday problem visually unmistakable; OR "
            "(b) a clear 3/4 view of the practical product/layout fix with visible functional details."
        ),
        "reverse_engineered_example": (
            "eye-level 1-point perspective of a crowded wet Indian vegetable market lane, commuter struggling to balance "
            "heavy cloth grocery bags and an open umbrella while stepping past overflowing wicker vegetable baskets"
        ),
        "default_style_preset": "observational_pencil",
    },
    "Storyboard": {
        "pinterest_references": [
            "4-panel Masala Dosa making (low-angle over tawa -> ladle swirl -> folding filling -> banana leaf serve)",
            "4-panel Indian Vegetable Market (wide stall -> weighing produce -> washing greens -> smiling vendor)",
            "5-grid Raw Mango Pickle process (hands washing -> traditional cutter -> adding spices -> mixing -> sun-drying jars)",
            "3-panel Basketball pass & 4-panel Lightbulb smash (varied wide/medium/close-up dynamic shots)",
        ],
        "camera_angles": [
            "4-panel sequence progressing from Wide Establishing Shot -> Medium Action -> Close-Up Hands/Reaction -> Resolution",
        ],
        "visual_rules": (
            "Describe a crisp 4-step sequential narrative for ONE consistent Indian character across 4 neat square panels: "
            "Frame 1 establishing wide shot, Frame 2 medium problem/action shot, Frame 3 dramatic close-up of hands or facial "
            "reaction, Frame 4 warm or clever resolution. Zero speech bubbles or text boxes."
        ),
        "reverse_engineered_example": (
            "Panel 1 wide shot of a quiet Indian bookshop as a stray cat sneaks past shelves, Panel 2 medium shot of cat "
            "leaping onto stacked books, Panel 3 close-up of falling book revealing a lost envelope, Panel 4 shopkeeper smiling holding the cat"
        ),
        "default_style_preset": "storyboard_frame",
    },
    "Logos, Symbols & Signs": {
        "pinterest_references": [
            "Do-Not-Feed Birds/Squirrels circular prohibition sign (flat silhouette hand + crumbs + bird + squirrel)",
            "MOHEIM SIGNS & Japanese Toilet Pictogram Collection (uniform flat black minimalist icon grid)",
            "Negative-Space Pencil-Lifter & S+Brain / Book+Eye conceptual black-and-white logos",
            "Compass-circle geometric animal emblem with pure clean minimal curves",
        ],
        "camera_angles": [
            "centered flat 2D emblem combining two iconic silhouettes via negative space (for single logo prompts)",
            "neat 2x2 grid of four uniform square flat-black minimalist icons with identical line weight (for 4-sign/pictogram prompts)",
        ],
        "visual_rules": (
            "Keep forms ultra-simple, bold, flat 2D solid-black silhouettes on pure white background. "
            "If the question asks for a single LOGO/EMBLEM, merge two recognizable visual metaphors cleanly via negative space. "
            "If the question asks for 4 SIGNS or PICTOGRAMS, describe a neat 2x2 grid of four matching flat black geometric icons. "
            "NEVER depict 3D mockups, outdoor wall signboards, or text letters."
        ),
        "reverse_engineered_example": (
            "neat 2x2 grid of four minimalist flat black wayfinding pictogram icons inside rounded square frames: "
            "wheelchair ramp, drinking water tap with cup, quiet reading person, and first-aid cross"
        ),
        "default_style_preset": "logo_symbol",
    },
    "Composition": {
        "pinterest_references": [
            "NID 2021 'How to make a cup of tea' single-page flowing poster (tilted vessel -> spoons -> strainer -> mug)",
            "Bold visual-metaphor awareness posters combining two unexpected everyday objects with generous white space",
        ],
        "camera_angles": [
            "unified vertical flowing composition connecting everyday objects from top to bottom",
            "bold central visual metaphor fusing two contrasting objects on uncluttered white negative space",
        ],
        "visual_rules": (
            "Build ONE bold, unified graphic poster visual metaphor combining the prompt's two unexpected everyday elements "
            "with clear top-to-bottom visual flow, strong figure-ground contrast, generous clean white negative space, and "
            "optional subtle single pastel accent tint. Zero printed text or slogans inside the image."
        ),
        "reverse_engineered_example": (
            "bold graphic visual metaphor of a glowing smartphone screen morphing into a crescent moon and folded paper pillow "
            "above a sleeping teenager, flowing curved lines, generous clean white negative space"
        ),
        "default_style_preset": "poster_metaphor",
    },
    "Creativity": {
        "pinterest_references": [
            "Unexpected hybrid character/creature in a funny everyday Indian moment",
            "Single-prop lateral invention (newspaper, steel tiffin box, wooden clothespin transformed cleverly)",
            "Ergonomic Toothbrush / Creative Ideation sketch with clean black ink outlines and one warm accent",
        ],
        "camera_angles": [
            "expressive dynamic 3/4 character/object frame showing clever visual transformation in action",
        ],
        "visual_rules": (
            "Visually fuse familiar everyday objects into ONE immediately readable, playful, surprising transformation "
            "or hybrid character caught in a relatable everyday moment — clever and concrete, never generic sci-fi."
        ),
        "reverse_engineered_example": (
            "playful whimsical creature combining a migrating bird's wings, a vintage sewing machine body with threaded spool, "
            "and a sleepy postman's leather satchel perched on a rain-soaked letterbox"
        ),
        "default_style_preset": "poster_metaphor",
    },
    "Design aptitude": {
        "pinterest_references": [
            "Future 2047 Indian street market / railway tea stall blending subtle eco-tech with timeless human rituals",
            "City policy spatial transformation (pedestrianized market street, neighbourhood repair cafe)",
            "Stark everyday visual contrast using simple iconic visual comparison",
        ],
        "camera_angles": [
            "2-point eye-level street perspective blending everyday Indian life with a clear practical design intervention",
            "split visual contrast showing two side-by-side simple scenes communicating a social tension at a glance",
        ],
        "visual_rules": (
            "Illustrate the core design-thinking insight in ONE unmistakable Indian everyday scene or clean split visual "
            "comparison — grounded human activity, practical eco-materials or civic layout improvements, clear spatial depth."
        ),
        "reverse_engineered_example": (
            "2-point street perspective of a bustling vehicle-free Indian old-town spice market in 2047, vendors under "
            "curved solar bamboo canopies weighing spices in steel scales while pedestrians stroll on shaded stone lanes"
        ),
        "default_style_preset": "observational_pencil",
    },
}


def resolve_smart_style_preset(category: str, prompt_text: str) -> str:
    """Choose the best verified 2D style preset based on BOTH category AND prompt content (Pinterest insights)."""
    low = prompt_text.lower()
    if any(k in low for k in ("worm", "ant's-eye", "ants eye", "ground level looking up", "low angle", "low-angle")):
        return "perspective_worm_eye"
    if any(k in low for k in ("bird's-eye", "birds eye", "balcony looking down", "high angle", "high-angle", "aerial")):
        return "perspective_bird_eye"
    if any(k in low for k in ("exploded view", "exploded", "internal mechanism", "spring, ink cartridge", "components aligned")):
        return "exploded_view"
    if any(k in low for k in ("metamorphosis", "transforming into", "4-stage", "gradually transforming")):
        return "metamorphosis_4stage"
    if any(k in low for k in ("mascot", "character design", "turnaround", "creature")):
        return "character_mascot"
    if any(k in low for k in ("ergonomic analysis", "pain points", "struggling with", "ergonomic")):
        return "problem_ergonomic_analysis"

    if category == "Logos, Symbols & Signs":
        return "logo_symbol"
    if category == "Storyboard":
        return "storyboard_frame"
    if category == "Product sketch":
        return "product_sketch"
    if category == "Composition":
        return "poster_metaphor"
    if category == "Creativity":
        return "metamorphosis_4stage"
    if category == "Problem identification":
        return "problem_ergonomic_analysis"
    if category in ("Drawing", "Design aptitude"):
        return "observational_pencil"
    return "product_sketch"


EXACT_EXAM_TRIGGER_TEMPLATES: Dict[str, Dict[str, str]] = {
    "product_ideation": {
        "title": "Product Ideation Sheet",
        "style_preset": "product_sketch",
        "template": "Industrial design pencil sketch of {subject}, two-point perspective, visible light construction lines and ellipses, clean fine-liner ink outlines with light grey marker shading, white sketchbook background, monochrome.",
    },
    "exploded_view_mechanism": {
        "title": "Exploded Views & Mechanisms",
        "style_preset": "exploded_view",
        "template": "Industrial design exploded view technical pencil sketch of {subject}, showing internal parts and mechanism aligned on an isometric axis, crisp line weight, white background.",
    },
    "perspective_daily_life": {
        "title": "Perspective & Daily Life Scene",
        "style_preset": "observational_pencil",
        "template": "Loose graphite pencil sketch on white paper of {subject}, eye-level one-point perspective, dynamic human figures in natural poses, expressive cross-hatching for shadows, NID entrance exam sketching style, no color.",
    },
    "perspective_worm_eye": {
        "title": "Ant's-Eye / Worm's-Eye View (Low Angle)",
        "style_preset": "perspective_worm_eye",
        "template": "Extreme low-angle worm's-eye view pencil sketch from ground level looking up at {subject}, dramatic three-point perspective convergence, strong foreground elements, clean cross-hatching on white paper.",
    },
    "perspective_bird_eye": {
        "title": "Bird's-Eye View (High Angle)",
        "style_preset": "perspective_bird_eye",
        "template": "High-angle bird's-eye view pencil sketch looking down from high vantage onto {subject}, dramatic foreshortening, crisp fine-liner ink and graphite shading, white background.",
    },
    "perspective_eye_level_2point": {
        "title": "Eye-Level Two-Point Perspective",
        "style_preset": "observational_pencil",
        "template": "Eye-level two-point perspective pencil drawing standing at the corner of {subject}, clear horizon line and vanishing points, depth recession, natural human proportions, monochrome.",
    },
    "storyboard_sequential": {
        "title": "Storyboarding / Sequential Action",
        "style_preset": "storyboard_frame",
        "template": "4-panel comic storyboard pencil sketch showing {subject}, clear facial expressions, clean line art, white background.",
    },
    "logo_symbol_sign": {
        "title": "Logo, Symbol & Sign",
        "style_preset": "logo_symbol",
        "template": "Minimalist black and white vector logo symbol for {subject}, clever negative space combining {visual_elements}, flat geometric Bauhaus style, bold clean lines, centered on a pure white background, no gradients, no 3D.",
    },
    "problem_ergonomic_analysis": {
        "title": "Problem Identification & Ergonomic Analysis",
        "style_preset": "problem_ergonomic_analysis",
        "template": "Industrial design problem analysis sketch sheet on white paper showing {subject}, clear graphite pencil line art, highlighted focus areas for ergonomic pain points, clean line weight, no background clutter.",
    },
    "object_metamorphosis": {
        "title": "Object Transformation & Metamorphosis",
        "style_preset": "metamorphosis_4stage",
        "template": "Step-by-step 4-stage visual metamorphosis pencil sketch showing {subject}, progressive morphing evolution, clean graphite shading, white sketchbook background.",
    },
    "poster_visual_communication": {
        "title": "Poster Design & Visual Communication",
        "style_preset": "poster_metaphor",
        "template": "Minimalist graphic design awareness poster on white paper about {subject}, bold visual metaphor of {visual_elements}, clean layout, flat screenprint style.",
    },
    "character_design_mascot": {
        "title": "Character Design & Mascots",
        "style_preset": "character_mascot",
        "template": "Character design turnaround sheet pencil sketch on white paper of {subject}, front view, side view, and dynamic action pose, clean line art.",
    },
}
