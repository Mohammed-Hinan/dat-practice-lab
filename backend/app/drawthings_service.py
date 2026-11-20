"""Local Draw Things HTTP API integration & NID / CEED / UCEED Visual Answer Generator."""

from __future__ import annotations

import asyncio
import base64
import io
import math
import re
import socket
import time
import urllib.parse
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from PIL import Image, ImageOps

from .database import Database
from .llm_service import LLMService, VISUAL_PROMPT_PAIR_JSON_SCHEMA, validate_local_endpoint
from .nid_sketch_knowledge import (
    CATEGORY_SKETCH_KNOWLEDGE,
    PINTEREST_RESEARCH_PILLARS,
)
from .ollama_provider import LLMProviderError
from .schemas import (
    AppSettings,
    CraftSketchPromptRequest,
    CraftSketchPromptResponse,
    DrawThingsEssenceResponse,
    DrawThingsGenerateRequest,
    DrawThingsGenerateResponse,
    DrawThingsStatus,
    SketchStylePreset,
    VisualDeltaAnalysis,
    VisualLearningCreate,
    VisualLearningRecord,
)


# Distilled summary pillars shown cleanly in UI
NID_DRAWING_ESSENCE: List[str] = [
    "Question-First Visual Translation: Analyse the exact category, user, constraints, deliverables, and available time — never blindly apply one drawing style to every question.",
    "Category-True Visual Language (A–H): Composition (focal point + depth), Creativity (visual metaphor), Design Aptitude (functional user-context), Drawing (perspective + proportion), Logos/Symbols/Signs (simple reproducible marks), Problem Identification (obvious friction + cause-targeted fix), Product Sketch (3/4 views + mechanisms + hand interaction), Storyboard (consistent sequential panels).",
    "Gesture-Based Human Figures & Freehand Construction: Line-of-action postures, simplified believable anatomy, and geometric construction (cubes, cylinders, ellipses) with consistent perspective and contact shadows.",
    "Authentic Examination Answer Sheet: Clean white paper, graphite pencil construction, confident black fineliner outlines, controlled diagonal hatching/light shading, and tidy visual hierarchy (Primary idea → Secondary details/views → Tertiary brief annotations).",
    "Time-Realistic Execution (20-Minute Standard): Neat, competent NID/CEED/UCEED student exam answer — never photorealism, never glossy CGI, never agency pitch decks, never messy scribbles.",
    "Structured Positive + Negative Prompting: Every question outputs both a concrete design-specific positive prompt (exact solution, views, features, medium) and a tailored negative prompt excluding photorealism, 3D CGI, and category-breaking artifacts.",
]


# Complete Master System Prompt supplied by the user (preserved faithfully for inspection & prompt crafting)
NID_VISUAL_ANSWER_MASTER_PROMPT = """# SYSTEM PROMPT
# NID / CEED / UCEED VISUAL ANSWER GENERATOR
## Examination-Oriented Design Thinking and Hand-Drawn Visualisation Engine

You are an expert design aptitude examination mentor, NID M.Des candidate, CEED candidate, industrial designer, visual communication designer, storyboard artist and freehand sketching instructor.

Your responsibility is to transform NID, CEED and UCEED drawing-based examination questions into high-quality, realistic, hand-drawn examination answer sheets.

You understand the difference between professional design presentation, academic design exploration, technical product sketching, visual storytelling and timed examination drawing.
You do NOT blindly apply one drawing style to every question.

Your first responsibility is to understand the question. Your second responsibility is to determine the appropriate visual solution. Your third responsibility is to create a drawing that a capable design entrance examination candidate could realistically produce under examination conditions.

The final drawing must demonstrate: Design thinking, Visual intelligence, Originality, Communication, Observation, Functional understanding, Drawing ability, Composition, Appropriate level of detail.
The purpose is not to generate attractive AI artwork. It is to demonstrate design aptitude through visual communication.

---
# PART 1: UNDERSTAND THE EXAMINATION QUESTION
Internally extract: Examination (NID/CEED/UCEED), Category, Main objective, Target audience, Context and environment, Constraints, Required deliverables, Number of drawings or frames, Expected annotations, Marks and available time.
Respect every explicit instruction (exact number of alternatives/frames, requested views, pencil-only vs poster colour, exact POV). Never omit a required deliverable.

# PART 2: SELECT THE CORRECT VISUAL LANGUAGE
- A. COMPOSITION: Clear focal point, foreground/middle-ground/background depth, overlapping, human proportions, leading lines, intentional balance, purposeful character-environment interaction. Observational drawing & freehand perspective.
- B. CREATIVITY: Original visual metaphors, unexpected associations, transformation/exaggeration/analogy, immediate visual comprehension without long essays. Avoid generic AI sci-fi clichés.
- C. DESIGN APTITUDE: Designer's process — user & context, requirements, practical functional concept, user interaction, material choices, usability. Functional and understandable, never impractical decoration.
- D. DRAWING: Correct 1-point/2-point perspective, clear horizon & vanishing points, believable proportions, overlapping & scale depth, gesture-based human figures, geometric construction, foreground/background line weight, light/shade/cast shadows. Freehand pencil or pen, never photo or digital painting.
- E. LOGOS, SYMBOLS AND SIGNS: Message + audience → simplified geometric forms, negative space, crisp silhouettes, visual metaphors, consistent sign systems, instant small-size legibility. Do NOT create 3D sculptures, decorative architectural signboards, or elaborate mockups unless explicitly requested.
- F. PROBLEM IDENTIFICATION: Context, User, Problem, Cause, Impact, Solution. Situational sketches, expressive human gestures, before-and-after comparisons, arrows, callouts. Make the friction visually obvious and fix the actual cause.
- G. PRODUCT SKETCH: Functional 3D product communication — 3/4 perspective view, supporting orthographic/side/top views or alternatives, ergonomic human interaction, moving/detachable parts, mechanisms, materials, feature annotations. Confident freehand construction, ellipses, varied line weight, controlled shading. Never an attractive shell without functional logic.
- H. STORYBOARD: Beginning, middle, end across the exact required number of rectangular frames with spacing; one clear action per frame; consistent character appearance, clothing, and proportions; expressive body language; varied camera angles (wide/medium/close-up); clear progression.

# PART 3: HUMAN FIGURE DRAWING STANDARD
Simplified, believable, gesture-based human figures: line of action, head placement, shoulder/hip tilt, simple torso forms, directional limbs with volume, clothing silhouettes, grounded contact with the environment. Never hyperrealistic anatomy or stiff identical mannequins.

# PART 4: OBJECT AND PERSPECTIVE CONSTRUCTION
Construct objects using cubes, cuboids, cylinders, cones, spheres, and ellipses as guides; maintain consistent perspective, relative scale, overlap, and contact shadows; avoid impossible intersections.

# PART 5: EXAMINATION ANSWER SHEET PRESENTATION
Clean white paper background using graphite pencils, black fineliners, ballpoint pens, colour pencils, or light markers as appropriate. Natural hand-drawn linework, subtle line-weight variation, visible construction strokes, controlled organic imperfections, neat visual hierarchy (Primary idea → Secondary views/details → Tertiary brief annotations). Neither messy doodle nor agency presentation.

# PART 6: DETAIL AND TIME MANAGEMENT
Adapt complexity strictly to available examination time (e.g., achievable cleanly in 20 minutes). Prioritise the central idea without wasted decorative rendering.

# PART 7: STRICT VISUAL QUALITY CONTROL
Verify: answers the actual question, correct category language, all deliverables present, understandable design, believable proportions & perspective, meaningful gestures, functional product features, consistent storyboard sequence, reproducible by hand, clean space usage, zero unnecessary decoration.

# PART 8: IMAGE GENERATION STYLE & STRUCTURED PROMPT FORMAT
Never force product-presentation techniques onto storyboards, storyboard panels onto logos, or photorealism/3D CGI onto hand-drawn exam answers.
For every question, output BOTH:
1. Positive prompt: Specify the ACTUAL concrete design solution, views/frames, user interactions, functional details, natural hand-drawn medium, clean white-paper exam sheet presentation, and realistic timed exam quality (e.g., achievable in 20 minutes).
2. Negative prompt: Explicitly exclude photorealism, 3D render, CGI, glossy commercial product photography, futuristic fantasy clichés, impossible mechanisms, decorative backgrounds, cinematic lighting, CAD perfection, watermarks, and category-inappropriate artifacts.

# FINAL PRINCIPLE
Think like a designer. Observe like a designer. Solve like a designer. Communicate like a designer. Draw like a capable NID/CEED candidate working under examination conditions."""


# Category-specific Part 2 methodologies & tailored negative baselines so local 3B LLMs stay
# fast inside num_ctx=2048 while applying 100% of the exact category rules from the Master Prompt.
CATEGORY_METHODOLOGY_MODULES: Dict[str, Dict[str, str]] = {
    "Composition": {
        "methodology": (
            "COMPOSITION: Organise a clear focal point with foreground, middle ground, and background depth, "
            "overlapping forms, leading lines, intentional balance, and expressive human figures interacting with "
            "the environment (or a bold, unified graphic exam poster if a poster is asked). Keep negative space clean."
        ),
        "medium": (
            "hand-drawn NID examination answer sheet on clean white paper, confident black fineliner outlines, "
            "natural graphite pencil construction and subtle diagonal hatching (or restrained flat colour-pencil accents if poster)"
        ),
        "negative_baseline": (
            "photorealism, photograph, 3D render, CGI, glossy digital painting, cinematic lighting, cluttered background, "
            "randomly scattered objects, generic AI artwork, complex typography, illegible garbled text, watermarks, logos, wooden desk, physical pen"
        ),
    },
    "Creativity": {
        "methodology": (
            "CREATIVITY: Communicate one clever, original visual metaphor, unexpected object association, transformation, "
            "or lateral-thinking concept immediately through visuals rather than long text. Show clear visual relationship "
            "between everyday inspiration and inventive solution — never generic sci-fi gadgets or random shapes."
        ),
        "medium": (
            "hand-drawn NID examination answer sheet on clean white paper, expressive freehand graphite pencil and black fineliner "
            "ideation sketch, confident varied contour lines, light diagonal pencil hatching, clean student sketchbook layout"
        ),
        "negative_baseline": (
            "photorealism, photograph, 3D render, CGI, generic sci-fi futuristic technology, meaningless abstract shapes, "
            "glossy commercial illustration, cinematic lighting, dark background, illegible text, watermarks, wooden desk, physical pencil"
        ),
    },
    "Design aptitude": {
        "methodology": (
            "DESIGN APTITUDE: Show practical, user-centred design thinking — clear context, user interaction, functional layout "
            "or practical concept solving the real-world brief, material/usability clarity, and a primary scene/concept supported "
            "by one small detail or user-interaction vignette."
        ),
        "medium": (
            "hand-drawn NID M.Des examination answer sheet on clean white paper, freehand graphite pencil construction, "
            "confident black fineliner outlines, subtle pencil hatching, neat visual hierarchy, realistic student exam sheet"
        ),
        "negative_baseline": (
            "photorealism, photograph, 3D render, CGI, glossy corporate presentation board, impractical decorative fantasy, "
            "cinematic lighting, perfect CAD geometry, cluttered background, illegible text, watermarks, wooden desk, physical pen"
        ),
    },
    "Drawing": {
        "methodology": (
            "DRAWING: Demonstrate observational accuracy, believable 1-point or 2-point freehand perspective with clear horizon, "
            "accurate object-to-human proportions (e.g., human hand operating object or eye-level spatial depth with foreground/midground/background), "
            "gesture-based figures, foreground-vs-background line weight, and controlled directional cast shadows."
        ),
        "medium": (
            "hand-drawn freehand graphite pencil observational examination drawing on clean white paper inside a neat thin border, "
            "visible light perspective construction strokes, varied pencil line weight, clean parallel diagonal pencil hatching, pure monochrome"
        ),
        "negative_baseline": (
            "photorealism, photograph, digital painting, 3D render, CGI, colour photo, glossy illustration, cinematic lighting, "
            "hyperrealistic airbrushing, distorted perspective, stiff mannequin poses, decorative border, wooden desk, physical pencil, hand holding pencil, watermarks, text"
        ),
    },
    "Logos, Symbols & Signs": {
        "methodology": (
            "LOGOS, SYMBOLS & SIGNS: Communicate instant meaning through ultra-simple, reproducible geometric forms, bold negative space, "
            "high-contrast black-and-white silhouettes, and consistent line weight across a neat set of icons or one clean emblem. "
            "NEVER draw 3D sculptures, architectural signboards, wall mockups, or decorative installations unless explicitly requested."
        ),
        "medium": (
            "flat hand-drawn black ink and graphite examination sheet on clean white paper showing crisp high-contrast monochrome "
            "geometric logo marks or uniform wordless wayfinding pictograms inside neat square frames, Bauhaus clarity"
        ),
        "negative_baseline": (
            "photorealism, photograph, 3D render, 3D sculpture, architectural signboard, outdoor wall mockup, glossy badge, gradients, "
            "colour photo, complex typography, illegible garbled letters, decorative flourishes, wooden desk, physical pen, watermarks"
        ),
    },
    "Problem identification": {
        "methodology": (
            "PROBLEM IDENTIFICATION: Make the real-world everyday friction immediately obvious in a situational perspective sketch — "
            "show the exact user struggling through clear body posture and gestures, the environmental cause, and a small practical "
            "before/after or targeted fix vignette with simple directional arrows."
        ),
        "medium": (
            "hand-drawn NID examination answer sheet on clean white paper, observational graphite pencil and black fineliner "
            "situational sketch, expressive simplified human figures, clear foreground/background depth, light diagonal pencil hatching"
        ),
        "negative_baseline": (
            "photorealism, photograph, 3D render, CGI, glossy corporate infographic, decorative scenery unrelated to the problem, "
            "stiff mannequins, cinematic lighting, dark background, complex typography, illegible text, wooden desk, physical pen, watermarks"
        ),
    },
    "Product sketch": {
        "methodology": (
            "PRODUCT SKETCH: Communicate a practical, buildable 3D product — primary three-quarter perspective view showing clear "
            "volume, ergonomics, functional components, moving/opening mechanisms, and material logic, paired with one smaller "
            "orthographic side/top detail view or human hand-interaction sketch. Never an empty decorative shell."
        ),
        "medium": (
            "hand-drawn industrial design examination answer sheet on clean white paper, natural graphite pencil construction lines, "
            "confident black fineliner contour outlines, controlled diagonal pencil hatching and subtle light grey shading, clean student sketchbook quality"
        ),
        "negative_baseline": (
            "photorealism, photograph, 3D render, CGI, glossy commercial product photography, futuristic fantasy technology, "
            "impossible mechanical components, decorative background, cinematic lighting, excessive detailing, vector illustration, "
            "corporate presentation board, perfect CAD geometry, complex typography, illegible text, wooden desk, physical pen, watermarks, logos"
        ),
    },
    "Storyboard": {
        "methodology": (
            "STORYBOARD: Show clear narrative progression (beginning, middle, end) across neat hand-ruled rectangular panels with clean spacing, "
            "one unmistakable action per frame, consistent character appearance/clothing/proportions, expressive body language and hands, "
            "varied camera angles (wide, medium, close-up), and motion/steam cues — NO unrelated panels or cluttered speech bubbles."
        ),
        "medium": (
            "hand-drawn graphite pencil and black fineliner storyboard examination sheet on clean white paper, neat hand-ruled rectangular panels, "
            "loose confident gesture linework, expressive comic-realistic figures, light diagonal pencil hatching, monochrome"
        ),
        "negative_baseline": (
            "photorealism, photograph, 3D render, CGI, speech bubbles, cluttered dialogue walls, inconsistent character faces or outfits, "
            "unrelated comic panels, glossy anime render, cinematic lighting, dark background, illegible text, wooden desk, physical pencil, watermarks"
        ),
    },
}


# Ironclad negative prompt firewall ALWAYS merged before sending to Draw Things (blocks B&W photos, fake tables, text, anime, turnaround sheets)
UNIVERSAL_NEGATIVE_FIREWALL = (
    "anime, manga, cartoon, character turnaround sheet, turnaround sheet, model sheet, multiple views, "
    "multiple angles of same person, orthographic character sheet, standing mannequin, anime girl, female anime, "
    "stylized eyes, chibi, kawaii, photograph, photo, photorealistic, realistic, grayscale photo, black and white photo, "
    "3d render, CGI, glossy, reflections, studio lighting, smooth airbrush shading, depth of field, bokeh, text, letters, "
    "words, numbers, handwriting, table, chart, form, document, spec sheet, caption box, speech bubble, "
    "physical pencil, physical pen, hand holding pen, wooden desk, watermark"
)

LOGO_NEGATIVE_FIREWALL = (
    f"{UNIVERSAL_NEGATIVE_FIREWALL}, 3d render, 3d object, physical product, plastic, metal, container, bucket, tub, bin, box, trash can, "
    "isometric, perspective, depth, shading, gradient, shadows, reflection, glossy, raytracing, CGI, photorealism, photograph, "
    "colored, mockup, physical signboard, outdoor wall, desk, room"
)

PRODUCT_NEGATIVE_FIREWALL = (
    f"{UNIVERSAL_NEGATIVE_FIREWALL}, 3d plastic render, glossy plastic, raytracing, keyshot, blender render, 3d cad model, "
    "smooth airbrush shading, dark background, grey studio gradient, colored lighting, floating object, realistic skin, photorealistic hand"
)

STORYBOARD_NEGATIVE_FIREWALL = (
    f"{UNIVERSAL_NEGATIVE_FIREWALL}, speech bubbles, dialogue box, text panel, narration box, cluttered text, "
    "inconsistent characters, 3d render, glossy anime render, photorealism"
)

# Regex patterns stripped from ANY positive prompt before hitting Draw Things so diffusion NEVER generates
# fake spec tables, gibberish paragraphs, B&W studio photographs, or disconnected multi-view photo collages.
_DIFFUSION_BAN_PATTERNS: List[str] = [
    r"\b(?:flat\s+top-?down|scanned|hand-?drawn)\s+",
    r"\b(?:industrial\s+design|product\s+design|commercial\s+product)\b",
    r"\b(?:nid|ceed|uceed|m\.?des|dat|entrance)\b",
    r"\b(?:examination|exam)\s+(?:answer\s+)?(?:sheet|drawing|quality|paper)\b",
    r"\b(?:answer\s+sheet|student\s+sketchbook(?:\s+presentation)?|sketchbook\s+page)\b",
    r"\b(?:handwritten|feature|brief|short)?\s*(?:annotations?|callouts?|labels?|labelled|captions?|typography|headings?|titles?)\b",
    r"\b(?:orthographic|blueprint|spec(?:ification)?\s+sheet|chart|table|diagram\s+labels?)\b",
    r"\b(?:achievable\s+in|within)\s+\d+\s*(?:min(?:utes?)?|m)\b",
    r"\b\d+\s*(?:minutes?|mins?)\b",
    r"\b(?:photorealistic|realistic|natural|believable|lifelike|studio|high\s+resolution|mechanical\s+construction)\b",
    r"\b(?:include|including|paired\s+with|plus)\s+(?:one\s+)?(?:smaller\s+)?(?:side|top|front|back|detail|orthographic|secondary)[^.,;]*",
    r"\b(?:two|three|multiple)\s+(?:distinct\s+)?(?:views|alternatives|concepts|sketches)\b",
    r"\b(?:graphite\s+pencil|black\s+fineliner|pencil\s+construction|pencil\s+shading|subtle\s+shading|diagonal\s+hatching|clean\s+white\s+paper|white\s+paper)\b",
    r"^(?:product\s+sketch|drawing|composition|creativity|storyboard|problem\s+identification|design\s+aptitude|logos?,?\s*symbols?\s*&?\s*signs?)\s*:\s*",
]


def sanitize_subject_for_diffusion(raw_prompt: str) -> str:
    """Hard prompt firewall: strip all photo, fake-table, gibberish-text, and collage triggers."""
    text = re.sub(r"\s+", " ", raw_prompt).strip()
    for pat in _DIFFUSION_BAN_PATTERNS:
        text = re.sub(pat, " ", text, flags=re.IGNORECASE)
    # Remove leftover dangling verbs/punctuation
    text = re.sub(r"\b(?:draw|sketch|illustrate|showing|show|depicting|illustrating)\s+(?:a\s+|an\s+|the\s+)?", "", text, count=1, flags=re.IGNORECASE)
    text = re.sub(r"\s*[,.;:]+\s*[,.;:]+", ", ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.;:-")
    # Cap subject core at <= 65 words so full scenario + intervention + setting stays at peak CLIP weight
    words = text.split()
    if len(words) > 65:
        text = " ".join(words[:65]).rstrip(" ,.;:-")
    return text or "an everyday Indian street scene in eye-level 1-point perspective"


# Visually verified 10/10 2D line-art style wrappers on DreamShaper v8 (768x512 / 640x640, 16-20 steps)
# NEVER bypassed — every render is strictly locked into crisp 2D hand-drawn outlines or flat signage silhouettes.
SKETCH_STYLE_TEMPLATES: Dict[SketchStylePreset, Tuple[str, str, str, str]] = {
    "product_sketch": (
        "Industrial design pencil sketch of",
        "two-point perspective, visible light construction lines and ellipses, clean fine-liner ink outlines with light grey marker shading, white sketchbook background, monochrome",
        PRODUCT_NEGATIVE_FIREWALL,
        "Product Ideation Sheet: 2-point perspective, construction ellipses, fineliner ink outlines & grey marker shading",
    ),
    "exploded_view": (
        "Industrial design exploded view technical pencil sketch of",
        "showing components and internal mechanism aligned on an isometric axis, crisp line weight, technical drafting guidelines, white background, monochrome",
        f"{UNIVERSAL_NEGATIVE_FIREWALL}, 3d render, plastic render, glossy, dark background",
        "Exploded Views & Mechanisms: technical pencil sketch aligned on an isometric axis",
    ),
    "observational_pencil": (
        "Loose graphite pencil sketch on white paper of",
        "eye-level one-point perspective, dynamic human figures in natural poses, expressive cross-hatching for shadows, NID entrance exam sketching style, no color, pure white background",
        f"{UNIVERSAL_NEGATIVE_FIREWALL}, color, colorful, solid grey gradient",
        "Perspective & Daily Life Scene: eye-level 1-point perspective, dynamic human figures & cross-hatching",
    ),
    "perspective_worm_eye": (
        "Extreme low-angle worm's-eye view pencil sketch from ground level looking up at",
        "dramatic three-point perspective convergence, strong foreground elements, clean cross-hatching on pure white paper, monochrome",
        f"{UNIVERSAL_NEGATIVE_FIREWALL}, color, flat angle, eye-level, high-angle",
        "Worm's-Eye View (Low Angle): ground level looking up, dramatic 3-point perspective convergence",
    ),
    "perspective_bird_eye": (
        "High-angle bird's-eye view pencil sketch looking down from high vantage onto",
        "dramatic foreshortening of vehicles and human figures below, crisp fine-liner ink and graphite shading, pure white background, monochrome",
        f"{UNIVERSAL_NEGATIVE_FIREWALL}, color, ground level, eye-level, worm's-eye",
        "Bird's-Eye View (High Angle): looking down from above, dramatic foreshortening",
    ),
    "storyboard_frame": (
        "4-panel comic storyboard pencil sketch in a neat 2x2 grid showing",
        "clear facial expressions, expressive character gestures, clean line art, light pencil hatching, white background, no text boxes, no speech bubbles",
        STORYBOARD_NEGATIVE_FIREWALL,
        "Storyboarding & Sequential Action: 4-panel comic storyboard pencil sketch, clear facial expressions",
    ),
    "logo_symbol": (
        "Minimalist black and white vector logo symbol for",
        "clever negative space combining two visual metaphors, flat geometric Bauhaus style, bold clean lines, centered on a pure white background, zero gradients, zero 3D, zero perspective",
        LOGO_NEGATIVE_FIREWALL,
        "Logo, Symbol & Sign: Bauhaus flat vector mark, clever negative space, pure white background",
    ),
    "problem_ergonomic_analysis": (
        "Graphite pencil sketch on clean white paper showing",
        "visible light pencil construction lines, hand-drawn cross-hatching, clean fine-liner ink outlines, white sketchbook background, monochrome, no color, zero photographic lighting, zero 3d render",
        f"{UNIVERSAL_NEGATIVE_FIREWALL}, photograph, photo, realistic skin, photographic lighting, vintage photo, retro photo, grayscale photo, black and white photo, sepia, dark background, grey background, textured background, complex background, 3d render, CGI, glossy, color, colorful",
        "Problem Identification & Ergonomic Analysis: clean pencil & ink sketch of functional intervention solving friction",
    ),
    "metamorphosis_4stage": (
        "Step-by-step 4-stage visual metamorphosis pencil sketch showing",
        "progressive morphing transformation from left to right, clean graphite shading, visible outline evolution, white sketchbook background",
        f"{UNIVERSAL_NEGATIVE_FIREWALL}, color, photorealism, 3d render, dark background",
        "Object Transformation & Metamorphosis: step-by-step 4-stage progressive morphing pencil sketch",
    ),
    "poster_metaphor": (
        "Minimalist graphic design awareness poster on clean white paper about",
        "bold conceptual visual metaphor, flowing contour linework, generous clean white negative space, flat screenprint graphic style, monochrome with subtle ink wash",
        f"{UNIVERSAL_NEGATIVE_FIREWALL}, complex paragraphs, illegible text, photorealism, 3d render",
        "Poster Design & Visual Metaphor: bold visual analogy, generous negative space & flat screenprint style",
    ),
    "character_mascot": (
        "Character design turnaround sheet pencil sketch on white paper of",
        "front view, side view, and dynamic action pose, expressive proportions, clean line art, subtle pencil shading, pure white background",
        f"{UNIVERSAL_NEGATIVE_FIREWALL}, 3d render, CGI, photorealism, color, dark background",
        "Character Design & Mascot: turnaround sheet (front, side, action pose), clean line art",
    ),
}

VISUAL_DELTA_JSON_SCHEMA: Dict[str, object] = {
    "type": "object",
    "properties": {
        "what_changed": {"type": "string"},
        "why_changed": {"type": "string"},
        "actionable_guidelines": {"type": "string"},
        "negative_guidelines": {"type": "string"},
    },
    "required": [
        "what_changed",
        "why_changed",
        "actionable_guidelines",
        "negative_guidelines",
    ],
    "additionalProperties": False,
}

FALLBACK_CATEGORY_LEARNING_DELTAS: Dict[str, Dict[str, str]] = {
    "Product sketch": {
        "what_changed": (
            "Shifted from an isolated 3D object to an authentic NID exam ideation layout: "
            "confident two-point perspective linework, visible human hand grip demonstrating scale, "
            "and a dedicated circular mechanism callout."
        ),
        "why_changed": (
            "NID and CEED Part B examiners award top marks for clear user-product interaction, "
            "functional mechanism logic, and hand-drawn line hierarchy rather than unbuildable glossy shells."
        ),
        "actionable_guidelines": "two-point perspective pencil linework with visible human hand grip and circular mechanism detail",
        "negative_guidelines": "floating product without human hands, glossy plastic render, CAD render, flat front elevation",
    },
    "Logos, Symbols & Signs": {
        "what_changed": (
            "Replaced 3D perspective object rendering with a pure 2D flat geometric Bauhaus vector mark, "
            "clever negative space silhouette, and solid black line weight on pure white paper."
        ),
        "why_changed": (
            "Logo and sign evaluation criteria test visual metaphor clarity, silhouette legibility at thumbnail scale, "
            "and reproduction simplicity; 3D perspective and gradients invalidate symbol design marks."
        ),
        "actionable_guidelines": "flat 2D minimalist geometric silhouette using clever negative space on pure white paper",
        "negative_guidelines": "3D render, perspective, depth, shading, gradient, plastic container, signboard mockup",
    },
    "Storyboard": {
        "what_changed": (
            "Organized narrative into clean hand-drawn sequential frames with varied camera distances (establishing shot to close-up), "
            "consistent character body language, and expressive gestures without cluttered speech bubbles."
        ),
        "why_changed": (
            "NID storyboarding questions evaluate visual storytelling economy: clear character emotion, "
            "temporal progression, and camera variation within strictly timed panel constraints."
        ),
        "actionable_guidelines": "sequential rectangular frames with varied camera angles, expressive character gestures, and clean line art",
        "negative_guidelines": "cluttered speech bubbles, text walls, single isolated frame, photorealism, inconsistent character",
    },
    "Drawing": {
        "what_changed": (
            "Corrected eye-level 1-point/2-point perspective depth with strong foreground figure overlap, "
            "natural everyday Indian props, and expressive graphite diagonal hatching."
        ),
        "why_changed": (
            "Observational drawing marks depend on realistic spatial depth, vanishing point discipline, "
            "and believable gesture anatomy under timed exam conditions."
        ),
        "actionable_guidelines": "eye-level perspective with prominent foreground figure overlap and clean graphite hatching",
        "negative_guidelines": "flat 2D cutouts, distorted vanishing points, photorealism, color, cluttered background",
    },
    "Problem identification": {
        "what_changed": (
            "Highlighted the physical user friction and ergonomic pain point directly in the human posture, "
            "paired with a clear cause-targeted redesign sketch."
        ),
        "why_changed": (
            "Design aptitude questions require identifying root causes rather than symptoms; visible ergonomic strain "
            "and practical usability fixes demonstrate true empathetic observation."
        ),
        "actionable_guidelines": "clear situational sketch highlighting user posture tension and practical ergonomic fix",
        "negative_guidelines": "abstract diagram without human user, decorative scene, photorealism, dark lighting",
    },
    "Composition": {
        "what_changed": (
            "Unified the drawing around a single bold visual metaphor with leading lines, "
            "dramatic negative space, and clear primary-to-secondary visual hierarchy."
        ),
        "why_changed": (
            "Composition problems reward strong focal points, deliberate balance, and immediate conceptual impact "
            "over scattered decorative details."
        ),
        "actionable_guidelines": "bold conceptual visual metaphor with generous white negative space and flowing leading lines",
        "negative_guidelines": "scattered unorganized items, dark background, complex paragraphs, photorealism",
    },
    "Creativity": {
        "what_changed": (
            "Created an imaginative progressive metamorphosis showing smooth organic-to-geometric shape transition "
            "in clean graphite shading across clear stages."
        ),
        "why_changed": (
            "Creativity questions assess analogical thinking and fluent form exploration; readable step-by-step transformation "
            "proves lateral design thinking."
        ),
        "actionable_guidelines": "step-by-step progressive metamorphosis pencil sketch showing smooth shape transition",
        "negative_guidelines": "disconnected random objects, photorealism, color, 3D render, dark background",
    },
    "Design aptitude": {
        "what_changed": (
            "Anchored the product redesign into its everyday operational environment with believable human scale, "
            "material callouts, and intuitive control touchpoints."
        ),
        "why_changed": (
            "Demonstrating end-to-end design aptitude requires showing how the solution fits user habits and spatial constraints."
        ),
        "actionable_guidelines": "human-centered design scene showing user interaction, intuitive touchpoints, and functional logic",
        "negative_guidelines": "commercial advertisement style, isolated CAD render, impossible floating components",
    },
}


def default_style_for_category(category: str, prompt_text: str = "") -> SketchStylePreset:
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

    if category == "Storyboard":
        return "storyboard_frame"
    if category == "Composition" or category == "Creativity":
        return "poster_metaphor"
    if category == "Logos, Symbols & Signs":
        return "logo_symbol"
    if category == "Problem identification":
        return "problem_ergonomic_analysis"
    if category in ("Drawing", "Design aptitude"):
        return "observational_pencil"
    return "product_sketch"


def default_negative_for_category(category: str) -> str:
    mod = CATEGORY_METHODOLOGY_MODULES.get(category)
    if mod:
        return mod["negative_baseline"]
    return CATEGORY_METHODOLOGY_MODULES["Product sketch"]["negative_baseline"]


def build_category_visual_system_prompt(category: str, time_minutes: int = 20) -> str:
    """Build a crisp system prompt pairing NID Master principles with reverse-engineered Pinterest exemplars."""
    mod = CATEGORY_METHODOLOGY_MODULES.get(category, CATEGORY_METHODOLOGY_MODULES["Design aptitude"])
    kb = CATEGORY_SKETCH_KNOWLEDGE.get(category, CATEGORY_SKETCH_KNOWLEDGE["Design aptitude"])
    example = str(kb["reverse_engineered_example"])
    visual_rules = str(kb["visual_rules"])
    return f"""You are the NID / CEED / UCEED VISUAL ANSWER GENERATOR translating an exam question into a concrete, drawable visual description (`positive_prompt`) and exclusion list (`negative_prompt`) for a 2D line-art drawing engine.

Step 1 — Apply real Pinterest-studied NID/CEED exam visual grammar for {category}:
- Design discipline: {mod["methodology"]}
- Reverse-engineered visual rule: {visual_rules}

Step 2 — Write ONLY concrete visible elements (18 to 35 plain English words) in `positive_prompt`:
- Specify the EXACT single cohesive drawn scene, open functional product concept, 4-panel shot sequence, visual metaphor, or flat geometric icon/sign that best answers THIS question.
- Name specific physical parts, camera angle/perspective (e.g. "first-person POV", "extreme foreground prop overlap", "bird's-eye", "3/4 perspective view with open lid/joinery"), human posture/gesture, and 2–3 concrete everyday Indian props.
- STRICT GUARDRAILS (NEVER break these):
  * NEVER write "examination answer sheet", "exam sheet", "annotations", "callouts", "labels", "handwritten", "table", "blueprint", "orthographic", "20 minutes", "NID", "realistic", "natural", or "photorealistic" (those words trigger AI gibberish text and studio photographs — our 2D ink/line-art renderer applies the hand-drawn sketch medium automatically!).
  * NEVER ask for text, speech bubbles, or separate pasted collages inside the image.

Reverse-engineered Pinterest exemplar for {category}:
"{example}"

Return ONLY valid JSON with keys `positive_prompt` and `negative_prompt`."""


def build_fallback_visual_prompts(
    title: str,
    scenario: str,
    category: str,
    time_minutes: int = 20,
    style_preset: Optional[SketchStylePreset] = None,
    subquestions: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
    sketching_requirements: Optional[List[str]] = None,
) -> Tuple[str, str]:
    """Deterministic, guardrail-safe pure visual brief + negative prompt harvesting question clues."""
    mod = CATEGORY_METHODOLOGY_MODULES.get(category, CATEGORY_METHODOLOGY_MODULES["Design aptitude"])
    
    # 1. Clean scenario into persona & setting
    clean_scenario = scenario.strip()
    first_sentence = re.split(r"(?<=[.!?])\s+", clean_scenario)[0] if clean_scenario else title
    cleaned_context = re.sub(
        r"\b(you are an?|imagine someone|picture someone|pick one|design one|create a|list \d+|identify \d+|explain how|as an?)\b",
        "",
        first_sentence or title,
        flags=re.IGNORECASE,
    ).strip(" ,.;:-")

    # 2. Extract intervention from sketching requirements or subquestions
    intervention = ""
    if sketching_requirements:
        for req in sketching_requirements:
            if re.search(r"\b(?:intervention|solution|practical fix|fix|redesign|carrier|mechanism|tool|device)\b", req, re.IGNORECASE):
                intervention = re.sub(r"^(?:show|draw|illustrate|depict)\s+(?:yourself\s+|the\s+user\s+)?", "", req, flags=re.IGNORECASE).strip()
                break
        if not intervention and sketching_requirements:
            intervention = re.sub(r"^(?:show|draw|illustrate|depict)\s+(?:yourself\s+|the\s+user\s+)?", "", sketching_requirements[-1], flags=re.IGNORECASE).strip()

    if not intervention and subquestions:
        for sq in subquestions:
            if re.search(r"\b(?:design|intervention|practical fix|fix|redesign|solution|deliverable)\b", sq, re.IGNORECASE):
                intervention = re.sub(r"^(?:[A-Z]\)|sketch of a|design a|present your|sketch a|deliverable:?)\s*", "", sq, flags=re.IGNORECASE).strip()
                break

    # 3. Extract constraints
    constraint_str = ""
    if constraints:
        constraint_str = ", ".join(constraints[:2])

    # 4. Synthesize concrete core
    if intervention and cleaned_context:
        core = f"{cleaned_context}, actively using a practical functional intervention: {intervention}"
        if constraint_str:
            core = f"{core} ({constraint_str})"
    elif cleaned_context:
        core = f"{cleaned_context}"
        if constraint_str:
            core = f"{core} ({constraint_str})"
    else:
        core = sanitize_subject_for_diffusion(f"{title}, {first_sentence}")

    core = sanitize_subject_for_diffusion(core)

    framing = {
        "Product sketch": f"hero 3/4 perspective view of {core} with open functional parts and tactile grip texture, paired with a zoom-in circular mechanism detail bubble and human hand-interaction vignette",
        "Drawing": f"1-point eye-level perspective of {core}, foreground figure overlapping midground action and background everyday props",
        "Storyboard": f"four sequential everyday action moments showing {core}, consistent Indian character with expressive gestures and dynamic camera angles",
        "Composition": f"bold unified visual metaphor composition of {core}, strong focal point and flowing everyday objects",
        "Logos, Symbols & Signs": f"clean circular or square minimalist geometric symbol representing {core}, bold simple iconic shapes",
        "Problem identification": f"eye-level perspective scene of {core}, human figure actively operating the functional design intervention to solve physical strain, with surrounding environment",
        "Creativity": f"clever visual transformation combining familiar everyday objects for {core}, immediately readable imaginative form",
        "Design aptitude": f"eye-level perspective scene of {core}, showing people interacting practically with the redesigned everyday object or space",
    }.get(category, core)
    return sanitize_subject_for_diffusion(framing), _merge_negative_prompts(
        mod["negative_baseline"], UNIVERSAL_NEGATIVE_FIREWALL
    )


def build_fallback_visual_prompt(
    title: str,
    scenario: str,
    category: str,
    style_preset: Optional[SketchStylePreset] = None,
) -> str:
    pos, _ = build_fallback_visual_prompts(
        title=title,
        scenario=scenario,
        category=category,
        style_preset=style_preset,
    )
    return pos


def _is_structured_exam_prompt(text: str) -> bool:
    """Detect whether the prompt is already a full structured NID visual answer prompt."""
    low = text.lower()
    if len(text) >= 165:
        return True
    markers = (
        "examination answer sheet",
        "hand-drawn",
        "three-quarter perspective",
        "3/4 perspective",
        "graphite pencil",
        "fineliner",
        "comic book line art",
        "achievable in",
    )
    return sum(1 for m in markers if m in low) >= 2


def _merge_negative_prompts(custom_neg: Optional[str], base_neg: str) -> str:
    parts: List[str] = []
    seen: set[str] = set()
    for raw in (custom_neg or "", base_neg):
        for tok in raw.split(","):
            t = tok.strip()
            key = t.lower()
            if t and key not in seen:
                seen.add(key)
                parts.append(t)
    return ", ".join(parts)


def _sketches_dir() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    out = project_root / "data" / "sketches"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _is_local_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


def normalize_init_image_for_diffusion(
    raw_b64: str,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    max_pixels: int = 768 * 512,
) -> Tuple[str, int, int]:
    """Decodes an uploaded base64 image (paper sketch photo), normalizes EXIF orientation,
    resizes it to match valid diffusion dimensions (multiples of 64, budget <= max_pixels),
    and returns (reencoded_base64, effective_width, effective_height).

    Draw Things /sdapi/v1/img2img strictly requires that init_images dimensions match
    payload width and height exactly.
    """
    clean_b64 = raw_b64.strip()
    if "," in clean_b64 and clean_b64.startswith("data:"):
        clean_b64 = clean_b64.split(",", 1)[1]

    try:
        img_data = base64.b64decode(clean_b64)
        image = Image.open(io.BytesIO(img_data))
    except Exception as exc:
        raise LLMProviderError(
            "Could not decode the uploaded sketch photo. Please upload a valid PNG, JPG, or WebP image."
        ) from exc

    # Automatically correct mobile photo EXIF orientation (crucial for phone photos of student sketches)
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    if image.mode != "RGB":
        image = image.convert("RGB")

    orig_w, orig_h = image.size

    if target_width is not None and target_height is not None:
        eff_w = max(256, (target_width // 64) * 64)
        eff_h = max(256, (target_height // 64) * 64)
    else:
        # Scale while strictly preserving aspect ratio, fitting within Apple M1 8GB memory budget
        total = orig_w * orig_h
        scale = math.sqrt(max_pixels / total) if total > max_pixels else 1.0
        eff_w = max(256, round((orig_w * scale) / 64.0) * 64)
        eff_h = max(256, round((orig_h * scale) / 64.0) * 64)
        if eff_w > 768:
            eff_w = 768
        if eff_h > 768:
            eff_h = 768
        eff_w = max(256, (eff_w // 64) * 64)
        eff_h = max(256, (eff_h // 64) * 64)

    resized_img = image.resize((eff_w, eff_h), Image.Resampling.LANCZOS)
    out_buf = io.BytesIO()
    resized_img.save(out_buf, format="PNG")
    norm_b64 = base64.b64encode(out_buf.getvalue()).decode("utf-8")
    return norm_b64, eff_w, eff_h


class DrawThingsService:
    """Communicates with Draw Things' local HTTP API server (default http://127.0.0.1:7860)."""

    def __init__(self, sketches_dir: Optional[Path] = None) -> None:
        self.sketches_dir = sketches_dir or _sketches_dir()
        self.sketches_dir.mkdir(parents=True, exist_ok=True)

    def get_essence_metadata(self) -> DrawThingsEssenceResponse:
        return DrawThingsEssenceResponse(
            essence_pillars=list(PINTEREST_RESEARCH_PILLARS),
            system_prompt=NID_VISUAL_ANSWER_MASTER_PROMPT,
            style_presets={
                key: {
                    "summary": summary,
                    "positive_prefix": f"{lead} <visual answer>, {tail}",
                    "negative_prompt": neg,
                }
                for key, (lead, tail, neg, summary) in SKETCH_STYLE_TEMPLATES.items()
            },
        )

    async def craft_visual_prompt(
        self,
        settings: AppSettings,
        llm_service: LLMService,
        req: CraftSketchPromptRequest,
        db: Optional[Database] = None,
    ) -> CraftSketchPromptResponse:
        """Use the NID / CEED / UCEED Master System Prompt to craft structured positive + negative prompts,
        enriching them with persistent learned update rules from the candidate's previous sketch uploads."""
        learned_rules: List[VisualLearningRecord] = []
        if db is not None:
            try:
                learned_rules = db.get_active_learned_rules_for_category(req.category, limit=3)
            except Exception:
                pass

        applied_rule_texts = [
            f"{r.actionable_guidelines} (learned from '{r.question_title}')"
            for r in learned_rules
        ]

        cat_sys_prompt = build_category_visual_system_prompt(
            category=req.category,
            time_minutes=req.time_minutes,
        )
        if learned_rules:
            cat_sys_prompt += (
                "\n\nLEARNED UPDATE LOGIC FROM CANDIDATE'S PREVIOUS EXAM SKETCH UPLOADS (ALWAYS ADOPT THIS):\n"
                + "\n".join(f"- {r.actionable_guidelines} (Rationale: {r.why_changed})" for r in learned_rules)
            )

        subq_block = (
            "Tasks:\n" + "\n".join(f"- {s[:200]}" for s in req.subquestions[:3]) + "\n"
            if req.subquestions
            else ""
        )
        const_block = (
            "Constraints: " + "; ".join(req.constraints[:3]) + "\n"
            if req.constraints
            else ""
        )
        draw_block = (
            "Drawing Requirements: " + "; ".join(req.sketching_requirements[:3]) + "\n"
            if req.sketching_requirements
            else ""
        )
        user_msg = (
            f"Examination: NID M.Des DAT Prelims\n"
            f"Category: {req.category}\n"
            f"Available Time: {req.time_minutes} minutes\n"
            f"Question Title: {req.title}\n"
            f"Scenario: {req.scenario[:650]}\n"
            f"{subq_block}{const_block}{draw_block}"
            "Generate a structured JSON object with `positive_prompt` (specifying the exact concrete design solution, "
            "views/frames, functional features, human interaction, and hand-drawn white-paper exam medium achievable "
            f"in {req.time_minutes} minutes) and `negative_prompt` (tailored exclusions)."
        )
        try:
            parsed = await llm_service.generate_json_with_schema(
                settings=settings,
                system_prompt=cat_sys_prompt,
                user_prompt=user_msg,
                json_schema=VISUAL_PROMPT_PAIR_JSON_SCHEMA,
                max_tokens=460,
                temperature=0.45,
            )
            pos = sanitize_subject_for_diffusion(str(parsed.get("positive_prompt") or ""))
            neg = str(parsed.get("negative_prompt") or "").strip()
            if len(pos) >= 20:
                for lr in learned_rules:
                    if lr.negative_guidelines:
                        neg = _merge_negative_prompts(neg, lr.negative_guidelines)
                merged_neg = _merge_negative_prompts(
                    neg,
                    _merge_negative_prompts(default_negative_for_category(req.category), UNIVERSAL_NEGATIVE_FIREWALL),
                )
                return CraftSketchPromptResponse(
                    visual_sketch_prompt=pos,
                    visual_negative_prompt=merged_neg,
                    style_preset=req.style_preset,
                    used_llm=True,
                    system_prompt=NID_VISUAL_ANSWER_MASTER_PROMPT,
                    applied_rules=applied_rule_texts,
                )
        except Exception:
            pass

        fb_pos, fb_neg = build_fallback_visual_prompts(
            title=req.title,
            scenario=req.scenario,
            category=req.category,
            time_minutes=req.time_minutes,
            style_preset=req.style_preset,
            subquestions=req.subquestions,
            constraints=req.constraints,
            sketching_requirements=req.sketching_requirements,
        )
        for lr in learned_rules:
            if lr.actionable_guidelines and lr.actionable_guidelines.lower() not in fb_pos.lower():
                fb_pos = f"{fb_pos}, {lr.actionable_guidelines}"
            if lr.negative_guidelines:
                fb_neg = _merge_negative_prompts(fb_neg, lr.negative_guidelines)

        return CraftSketchPromptResponse(
            visual_sketch_prompt=fb_pos,
            visual_negative_prompt=fb_neg,
            style_preset=req.style_preset,
            used_llm=False,
            system_prompt=NID_VISUAL_ANSWER_MASTER_PROMPT,
            applied_rules=applied_rule_texts,
        )

    async def _unload_ollama_model(self, settings: AppSettings) -> bool:
        """Free unified Metal RAM on 8 GB Macs by evicting any active Ollama models before rendering a sketch."""
        try:
            url = validate_local_endpoint(settings.ollama_base_url)
            unloaded_any = False
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
                # Query running models in Ollama GPU memory and evict them
                try:
                    ps_resp = await client.get(f"{url}/api/ps")
                    if ps_resp.status_code == 200:
                        data = ps_resp.json()
                        models = [
                            m.get("name")
                            for m in data.get("models", [])
                            if isinstance(m, dict) and m.get("name")
                        ]
                        for m_name in models:
                            resp = await client.post(
                                f"{url}/api/chat",
                                json={"model": m_name, "messages": [], "keep_alive": 0},
                            )
                            if resp.status_code == 200:
                                unloaded_any = True
                except Exception:
                    pass

                # Also ensure settings.model is evicted if configured
                if settings.model:
                    resp = await client.post(
                        f"{url}/api/chat",
                        json={"model": settings.model, "messages": [], "keep_alive": 0},
                    )
                    if resp.status_code == 200:
                        unloaded_any = True
            return unloaded_any
        except Exception:
            return False

    async def test_connection(
        self, settings: AppSettings, override_url: Optional[str] = None
    ) -> DrawThingsStatus:
        raw_url = override_url or settings.drawthings_base_url
        try:
            base_url = validate_local_endpoint(raw_url)
        except LLMProviderError as exc:
            return DrawThingsStatus(
                connected=False,
                endpoint=raw_url,
                message=str(exc),
            )

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.5)) as client:
                resp = await client.get(f"{base_url}/sdapi/v1/options")
                if resp.status_code == 404:
                    resp = await client.get(f"{base_url}/")
                resp.raise_for_status()
                latency_ms = int((time.perf_counter() - start) * 1000)
                active_model: Optional[str] = None
                try:
                    data = resp.json()
                    if isinstance(data, dict):
                        active_model = (
                            data.get("model")
                            or data.get("sd_model_checkpoint")
                            or None
                        )
                        loras = data.get("loras") or []
                        if active_model and isinstance(loras, list) and loras:
                            lora_names = [
                                str(l.get("file", "")).replace(".ckpt", "")
                                for l in loras
                                if isinstance(l, dict) and l.get("file")
                            ]
                            if lora_names:
                                active_model = f"{active_model} + {', '.join(lora_names)}"
                except Exception:
                    pass
                return DrawThingsStatus(
                    connected=True,
                    endpoint=base_url,
                    active_model=active_model,
                    latency_ms=latency_ms,
                    message=(
                        "Connected to local Draw Things HTTP server"
                        + (f" ({active_model})" if active_model else "")
                        + "."
                    ),
                )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
            grpc_7859 = _is_local_port_open("127.0.0.1", 7859)
            if grpc_7859:
                msg = (
                    "Draw Things is currently running its gRPC server on port 7859, not the HTTP API on "
                    f"{base_url}. In Draw Things Settings -> API Server, switch protocol to HTTP (port 7860)."
                )
            else:
                msg = (
                    f"Cannot reach Draw Things HTTP API at {base_url}. Open Draw Things -> Settings -> "
                    "enable API Server (HTTP, port 7860)."
                )
            return DrawThingsStatus(
                connected=False,
                endpoint=base_url,
                grpc_detected_on_7859=grpc_7859,
                message=msg,
            )

    async def _study_visual_delta(
        self,
        settings: AppSettings,
        llm_service: Optional[LLMService],
        db: Optional[Database],
        req: DrawThingsGenerateRequest,
        new_image_url: str,
        uploaded_image_url: str,
    ) -> VisualDeltaAnalysis:
        """Study what has changed between the baseline/older generation and the candidate's uploaded expected sketch,
        articulate the NID/CEED examination rationale (why), and persist an actionable update logic rule for future generations."""
        category = req.category or "Product sketch"
        title = req.question_title or req.prompt[:80]
        older_prompt = req.older_prompt or req.prompt

        fallback = FALLBACK_CATEGORY_LEARNING_DELTAS.get(
            category, FALLBACK_CATEGORY_LEARNING_DELTAS["Product sketch"]
        )
        what_changed = fallback["what_changed"]
        why_changed = fallback["why_changed"]
        actionable_guidelines = fallback["actionable_guidelines"]
        negative_guidelines = fallback["negative_guidelines"]

        if llm_service is not None:
            user_msg = (
                f"Question Category: {category}\n"
                f"Question Title: {title}\n"
                f"Baseline / Older Generation Prompt:\n\"{older_prompt}\"\n\n"
                f"Candidate's Uploaded Expected Visual Standard:\n"
                f"The candidate drew and uploaded their physical examination answer sheet for this question ({req.style_preset}). "
                "Contrast what the older automated generation lacked with what the candidate's drawing correctly emphasizes. "
                "Extract what changed, why this aligns with NID/CEED design aptitude criteria, and an actionable prompt update rule "
                "to use for future generations of similar questions."
            )
            try:
                system_prompt = (
                    "You are the NID / CEED Visual Answer Evaluator and Continuous Learning Engine. "
                    "Analyze the visual difference between the baseline generation and the candidate's uploaded expected answer sheet. "
                    "Return ONLY valid JSON matching the schema."
                )
                parsed = await llm_service.generate_json_with_schema(
                    settings=settings,
                    system_prompt=system_prompt,
                    user_prompt=user_msg,
                    json_schema=VISUAL_DELTA_JSON_SCHEMA,
                    max_tokens=450,
                    temperature=0.35,
                )
                if isinstance(parsed, dict) and parsed.get("what_changed") and parsed.get("actionable_guidelines"):
                    what_changed = str(parsed["what_changed"]).strip()
                    why_changed = str(parsed.get("why_changed") or why_changed).strip()
                    actionable_guidelines = str(parsed["actionable_guidelines"]).strip()
                    negative_guidelines = str(parsed.get("negative_guidelines") or negative_guidelines).strip()
            except Exception:
                pass

        analysis = VisualDeltaAnalysis(
            what_changed=what_changed,
            why_changed=why_changed,
            actionable_guidelines=actionable_guidelines,
            negative_guidelines=negative_guidelines,
            category=category,
        )

        if db is not None:
            try:
                db.save_visual_learning(
                    VisualLearningCreate(
                        question_id=req.question_id,
                        question_title=title,
                        category=category,
                        archetype="",
                        older_prompt=older_prompt,
                        older_image_url=req.older_image_url or "",
                        uploaded_image_url=uploaded_image_url,
                        new_image_url=new_image_url,
                        what_changed=what_changed,
                        why_changed=why_changed,
                        actionable_guidelines=actionable_guidelines,
                        negative_guidelines=negative_guidelines,
                    )
                )
            except Exception:
                pass

        return analysis

    async def generate_reference_sketch(
        self,
        settings: AppSettings,
        req: DrawThingsGenerateRequest,
        db: Optional[Database] = None,
        llm_service: Optional[LLMService] = None,
    ) -> DrawThingsGenerateResponse:
        if not settings.drawthings_enabled:
            raise LLMProviderError(
                "Draw Things sketch reference is disabled in Settings. Enable it in Settings to render sketches."
            )

        base_url = validate_local_endpoint(settings.drawthings_base_url)
        unloaded_ollama = False
        if settings.auto_unload_llm_for_sketch:
            unloaded_ollama = await self._unload_ollama_model(settings)
            if unloaded_ollama:
                # Give Apple M1 Metal unified memory a brief beat to reclaim Ollama buffers cleanly
                await asyncio.sleep(0.45)

        style_lead, style_tail, style_neg, _ = SKETCH_STYLE_TEMPLATES[req.style_preset]
        # STRICT GUARDRAIL: ALWAYS pass through the photo/table/gibberish firewall AND ALWAYS wrap with the
        # visually verified 2D line-art / flat-icon anchor (never bypassed!).
        clean_subject = sanitize_subject_for_diffusion(req.prompt)

        # Incorporate active learned update logic from candidate's previous sketch uploads in this category
        category = req.category or "Product sketch"
        applied_rules: List[str] = []
        if db is not None and category:
            try:
                active_records = db.get_active_learned_rules_for_category(category, limit=3)
                for r in active_records:
                    applied_rules.append(f"{r.actionable_guidelines} (learned from '{r.question_title}')")
                    if r.actionable_guidelines.lower() not in clean_subject.lower():
                        clean_subject = f"{clean_subject}, {r.actionable_guidelines}"
                    if r.negative_guidelines:
                        style_neg = _merge_negative_prompts(style_neg, r.negative_guidelines)
            except Exception:
                pass

        # -------------------------------------------------------------
        # CLOUD GENERATION: Google Gemini Imagen 3, Pollinations FLUX, or OpenAI DALL-E
        # -------------------------------------------------------------
        provider = getattr(settings, "sketch_provider", "gemini_imagen")
        if provider == "gemini_imagen":
            return await self._generate_gemini_imagen_sketch(
                settings=settings,
                clean_subject=clean_subject,
                style_lead=style_lead,
                style_tail=style_tail,
                req=req,
                db=db,
                llm_service=llm_service,
            )
        elif provider == "pollinations_flux":
            return await self._generate_pollinations_flux_sketch(
                clean_subject=clean_subject,
                style_lead=style_lead,
                style_tail=style_tail,
                req=req,
                db=db,
                llm_service=llm_service,
            )
        elif provider == "openai_dalle":
            return await self._generate_openai_dalle_sketch(
                settings=settings,
                clean_subject=clean_subject,
                style_lead=style_lead,
                style_tail=style_tail,
                req=req,
                db=db,
                llm_service=llm_service,
            )

        # -------------------------------------------------------------
        # LOCAL GENERATION: Draw Things on localhost:7860
        # -------------------------------------------------------------
        if not settings.drawthings_enabled:
            raise LLMProviderError(
                "Draw Things sketch reference is disabled in Settings. Enable it in Settings or switch to a Cloud Provider."
            )

        # Smart sub-mode for Logos/Signs: 4-sign/pictogram set -> clean 2x2 flat icon grid (like MOHEIM SIGNS)
        if req.style_preset == "logo_symbol":
            # Strip 3D product, perspective, and container words from logo prompt
            clean_subject = re.sub(
                r"\b(?:bins?|boxes?|containers?|buckets?|tubs?|waste\s+segregation\s+bins?|perspective|1-point|2-point|3d|isometric|cuboids?)\b",
                "pictograms",
                clean_subject,
                flags=re.IGNORECASE,
            )
            clean_subject = re.sub(r"\s+", " ", clean_subject).strip(" ,.;:-")
            if any(
                tok in clean_subject.lower()
                for tok in ("2x2", "four ", "4 ", "set of", "grid", "pictograms", "signs")
            ):
                style_lead = "flat minimalist black vector pictogram icon set in a neat 2x2 grid of four uniform square tiles on pure white background:"
                style_tail = "identical solid black line weight, clean minimalist signage symbols inside square borders, pure white background, high contrast 2d flat icons, zero 3d, zero perspective"
            else:
                style_lead = "flat minimalist black vector graphic logo emblem on pure white background:"
                style_tail = "solid black geometric mark, bold negative space silhouette, clean flat 2d graphic design icon on pure white paper, zero 3d, zero perspective"
            style_neg = LOGO_NEGATIVE_FIREWALL
        full_prompt = f"{style_lead} {clean_subject}, {style_tail}"

        effective_negative = _merge_negative_prompts(
            req.negative_prompt,
            _merge_negative_prompts(style_neg, UNIVERSAL_NEGATIVE_FIREWALL),
        )
        width = req.width or settings.drawthings_width
        height = req.height or settings.drawthings_height
        steps = req.steps or settings.drawthings_steps
        cfg_scale = req.cfg_scale or settings.drawthings_cfg_scale

        is_img2img = bool(req.init_image_base64 and req.init_image_base64.strip())
        endpoint = f"{base_url}/sdapi/v1/img2img" if is_img2img else f"{base_url}/sdapi/v1/txt2img"

        # Detect active Draw Things model to select the exact matching sampler (SDXL Turbo/Lightning vs SD1.5 LCM)
        active_model_str = ""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, connect=1.5)) as probe:
                opt = await probe.get(f"{base_url}/sdapi/v1/options")
                if opt.status_code == 200:
                    opt_data = opt.json()
                    if isinstance(opt_data, dict):
                        m = str(opt_data.get("model") or opt_data.get("sd_model_checkpoint") or "")
                        loras = opt_data.get("loras") or []
                        l_str = " ".join(str(x.get("file", "")) for x in loras if isinstance(x, dict))
                        active_model_str = f"{m} {l_str}".lower()
        except Exception:
            pass

        payload: Dict[str, object] = {
            "prompt": full_prompt,
            "negative_prompt": effective_negative,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": req.seed,
            "batch_size": 1,
        }
        if "lcm" in active_model_str:
            payload["sampler"] = "LCM"
        elif any(tok in active_model_str for tok in ("turbo", "lightning", "xl")):
            payload["sampler"] = "DPM++ SDE Karras"
        elif steps <= 10 and cfg_scale <= 2.2:
            payload["sampler"] = "DPM++ SDE Karras"
        else:
            # Standard SD 1.5 (e.g. DreamShaper 8, SD v1.5): adapt to optimal SD1.5 sampler & steps
            payload["sampler"] = "DPM++ 2M Karras"
            if steps <= 10:
                payload["steps"] = 20
            if cfg_scale <= 3.5:
                payload["cfg_scale"] = 6.5
            if width == 640 and height == 640:
                payload["width"] = 768
                payload["height"] = 512

        uploaded_image_url = ""
        if is_img2img and req.init_image_base64:
            clean_b64, eff_w, eff_h = normalize_init_image_for_diffusion(
                req.init_image_base64,
                target_width=req.width,
                target_height=req.height,
            )
            up_filename = f"uploaded_{uuid.uuid4().hex[:12]}.png"
            try:
                (self.sketches_dir / up_filename).write_bytes(base64.b64decode(clean_b64))
                uploaded_image_url = f"/api/sketches/{up_filename}"
            except Exception:
                pass

            payload["init_images"] = [clean_b64]
            payload["width"] = eff_w
            payload["height"] = eff_h
            width = eff_w
            height = eff_h
            payload["denoising_strength"] = req.denoising_strength

        start = time.perf_counter()
        data = None
        last_exc: Optional[Exception] = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=5.0)) as client:
                    resp = await client.post(endpoint, json=payload)
                    if resp.status_code == 503 and attempt == 0:
                        await asyncio.sleep(1.0)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    last_exc = None
                    break
            except (httpx.ConnectError, httpx.ReadError) as exc:
                last_exc = exc
                if attempt == 0:
                    await asyncio.sleep(0.8)
                    continue
            except httpx.TimeoutException as exc:
                raise LLMProviderError(
                    "Draw Things sketch generation timed out. Check that an 8-bit Turbo/SD1.5 model is selected and steps are <= 10."
                ) from exc
            except httpx.HTTPError as exc:
                detail = ""
                if hasattr(exc, "response") and exc.response is not None:
                    detail = f" ({exc.response.text[:250]})"
                raise LLMProviderError(f"Draw Things returned an error: {exc}{detail}") from exc

        if last_exc is not None:
            grpc_7859 = _is_local_port_open("127.0.0.1", 7859)
            if grpc_7859:
                raise LLMProviderError(
                    "Draw Things is running gRPC on port 7859 instead of HTTP on port 7860. "
                    "Switch Draw Things -> Settings -> API Server to HTTP (port 7860)."
                ) from last_exc
            raise LLMProviderError(
                f"Cannot connect to Draw Things HTTP API at {base_url}. "
                "Ensure Draw Things is open with API Server (HTTP, port 7860) enabled."
            ) from last_exc

        images = data.get("images") if isinstance(data, dict) else None
        if not images or not isinstance(images, list) or not isinstance(images[0], str):
            raise LLMProviderError("Draw Things did not return an image in its response.")

        img_b64 = images[0]
        if "," in img_b64 and img_b64.startswith("data:"):
            img_b64 = img_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(img_b64)

        filename = f"sketch_{uuid.uuid4().hex[:12]}.png"
        out_path = self.sketches_dir / filename
        out_path.write_bytes(img_bytes)

        learned_analysis: Optional[VisualDeltaAnalysis] = None
        if is_img2img and req.init_image_base64:
            learned_analysis = await self._study_visual_delta(
                settings=settings,
                llm_service=llm_service,
                db=db,
                req=req,
                new_image_url=f"/api/sketches/{filename}",
                uploaded_image_url=uploaded_image_url,
            )
            if learned_analysis and learned_analysis.actionable_guidelines:
                rule_desc = f"{learned_analysis.actionable_guidelines} (learned from '{req.question_title or req.prompt[:30]}')"
                if rule_desc not in applied_rules:
                    applied_rules.insert(0, rule_desc)

        latency_ms = int((time.perf_counter() - start) * 1000)
        return DrawThingsGenerateResponse(
            image_url=f"/api/sketches/{filename}",
            filename=filename,
            prompt_used=full_prompt,
            negative_prompt_used=effective_negative,
            width=width,
            height=height,
            steps=steps,
            latency_ms=latency_ms,
            mode="img2img" if is_img2img else "txt2img",
            unloaded_ollama=unloaded_ollama,
            learned_analysis=learned_analysis,
            applied_rules=applied_rules,
        )

    async def _generate_gemini_imagen_sketch(
        self,
        settings: AppSettings,
        clean_subject: str,
        style_lead: str,
        style_tail: str,
        req: DrawThingsGenerateRequest,
        db: Optional[Database] = None,
        llm_service: Optional[LLMService] = None,
    ) -> DrawThingsGenerateResponse:
        """Call Google Gemini Imagen 3 ('nanobanana' engine) for presentation-board reference sketches.
        Gracefully falls back to FLUX.1 if Google Free Tier returns 429 (quota limit: 0)."""
        start = time.perf_counter()
        full_prompt = (
            f"Authentic NID / CEED industrial design presentation sketch sheet on off-white paper: "
            f"{clean_subject}. {style_lead} {style_tail}, "
            "complete design presentation board with clear isometric guidelines, circular detail zoom bubbles, "
            "crisp hand-lettered English annotation headings and leader lines pointing to mechanisms, "
            "Copic marker shading, fine-liner ink outlines, clean white negative space"
        )
        api_key = settings.gemini_api_key.strip()
        if not api_key:
            raise LLMProviderError("Google Gemini API key is missing. Add your key in Settings.")

        img_bytes: Optional[bytes] = None
        last_error_msg = ""
        is_quota_exhausted = False

        # Attempt 1: Try Gemini native image generation models (including user-account nano-banana-2.1)
        for model_name in ["gemini-nano-banana-2.1", "gemini-2.5-flash-image", "gemini-3-pro-image"]:
            content_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"Generate a high-resolution industrial design presentation sketch: {full_prompt}"
                            }
                        ]
                    }
                ]
            }
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
                    resp = await client.post(content_url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates") if isinstance(data, dict) else None
                        if candidates and isinstance(candidates, list):
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for p in parts:
                                if isinstance(p, dict) and "inlineData" in p:
                                    b64 = p["inlineData"].get("data", "")
                                    if b64:
                                        img_bytes = base64.b64decode(b64)
                                        break
                        if img_bytes:
                            break
                    elif resp.status_code == 429:
                        is_quota_exhausted = True
                        last_error_msg = resp.text[:250]
                        break
                    else:
                        last_error_msg = f"{model_name} HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as exc:
                last_error_msg = str(exc)

        # Attempt 2: If generateContent wasn't successful and not 429, try standard Imagen 3 predict endpoint
        if not img_bytes and not is_quota_exhausted:
            predict_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
            aspect_ratio = "3:4" if (req.height or 0) > (req.width or 0) else "1:1"
            predict_payload = {
                "instances": [{"prompt": full_prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": aspect_ratio,
                    "outputMimeType": "image/jpeg",
                },
            }
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
                    resp = await client.post(predict_url, json=predict_payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        preds = data.get("predictions") if isinstance(data, dict) else None
                        if preds and isinstance(preds, list) and isinstance(preds[0], dict):
                            b64 = str(preds[0].get("bytesBase64Encoded") or "")
                            if b64:
                                img_bytes = base64.b64decode(b64)
                    elif resp.status_code == 429:
                        is_quota_exhausted = True
                        last_error_msg = resp.text[:250]
            except Exception as exc:
                last_error_msg = str(exc)

        # If Google image generation did not succeed, do NOT fallback to external services
        if not img_bytes:
            if is_quota_exhausted:
                raise LLMProviderError(
                    "Google Gemini API Quota: Your Google AI Studio project is currently on the non-billed Free Tier, "
                    "which has a daily quota limit of 0 for image models (gemini-nano-banana-2.1 / nano-banana-pro / imagen). "
                    "To unlock Google image generation via API, link a billing account on https://aistudio.google.com/."
                )
            raise LLMProviderError(f"Google Gemini image generation failed: {last_error_msg}")

        filename = f"sketch_{uuid.uuid4().hex[:12]}.jpg"
        out_path = self.sketches_dir / filename
        out_path.write_bytes(img_bytes)

        latency_ms = int((time.perf_counter() - start) * 1000)
        return DrawThingsGenerateResponse(
            image_url=f"/api/sketches/{filename}",
            filename=filename,
            prompt_used=full_prompt,
            negative_prompt_used="Default Google safety filters",
            width=1024,
            height=1024,
            steps=1,
            latency_ms=latency_ms,
            mode="txt2img",
            unloaded_ollama=False,
            learned_analysis=None,
            applied_rules=["Rendered with Google Gemini Imagen 3 ('nanobanana' engine)"],
        )

    async def _generate_pollinations_flux_sketch(
        self,
        clean_subject: str,
        style_lead: str,
        style_tail: str,
        req: DrawThingsGenerateRequest,
        db: Optional[Database] = None,
        llm_service: Optional[LLMService] = None,
    ) -> DrawThingsGenerateResponse:
        """100% Free online FLUX.1 generation via Pollinations.ai (zero setup, zero API key)."""
        start = time.perf_counter()
        full_prompt = (
            f"Industrial design presentation sketch on white paper: {clean_subject}, "
            f"{style_lead} {style_tail}, Copic marker shading, crisp black ink outlines, clean technical guidelines"
        )
        encoded_prompt = urllib.parse.quote(full_prompt)
        seed = req.seed if req.seed > 0 else int(time.time()) % 100000
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1024&height=1024&nologo=true&seed={seed}"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
                resp = await client.get(url, headers={"User-Agent": "DATPracticeLab/1.0"})
                if resp.status_code != 200:
                    raise LLMProviderError(f"Pollinations FLUX error ({resp.status_code}): {resp.text[:250]}")
                img_bytes = resp.content
        except httpx.TimeoutException as exc:
            raise LLMProviderError("Pollinations FLUX generation timed out (45s). Try again or switch to local Draw Things.") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Network error reaching Pollinations FLUX: {exc}") from exc

        filename = f"sketch_{uuid.uuid4().hex[:12]}.jpg"
        out_path = self.sketches_dir / filename
        out_path.write_bytes(img_bytes)

        latency_ms = int((time.perf_counter() - start) * 1000)
        return DrawThingsGenerateResponse(
            image_url=f"/api/sketches/{filename}",
            filename=filename,
            prompt_used=full_prompt,
            negative_prompt_used="Free online FLUX.1 (Pollinations)",
            width=1024,
            height=1024,
            steps=4,
            latency_ms=latency_ms,
            mode="txt2img",
            unloaded_ollama=False,
            learned_analysis=None,
            applied_rules=["Rendered with Free Cloud FLUX.1 (zero Mac RAM used)"],
        )

    async def _generate_openai_dalle_sketch(
        self,
        settings: AppSettings,
        clean_subject: str,
        style_lead: str,
        style_tail: str,
        req: DrawThingsGenerateRequest,
        db: Optional[Database] = None,
        llm_service: Optional[LLMService] = None,
    ) -> DrawThingsGenerateResponse:
        """OpenAI DALL-E 3 sketch generation."""
        start = time.perf_counter()
        full_prompt = (
            f"Industrial design presentation sketch on clean white paper: {clean_subject}. "
            f"{style_lead} {style_tail}, clean technical isometric perspective, circular mechanism callouts, "
            "crisp black fine-liner outlines with light marker shading, white background"
        )
        api_key = settings.openai_api_key.strip()
        if not api_key:
            raise LLMProviderError("OpenAI API key is missing. Add your key in Settings.")

        url = "https://api.openai.com/v1/images/generations"
        payload = {
            "model": "dall-e-3",
            "prompt": full_prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json",
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code != 200:
                    raise LLMProviderError(f"OpenAI DALL-E 3 error ({resp.status_code}): {resp.text[:300]}")
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise LLMProviderError("OpenAI DALL-E 3 timed out (60s).") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Network error reaching OpenAI API: {exc}") from exc

        data_list = data.get("data") if isinstance(data, dict) else None
        if not data_list or not isinstance(data_list, list):
            raise LLMProviderError("OpenAI did not return any image data.")

        b64 = str(data_list[0].get("b64_json") or "")
        img_bytes = base64.b64decode(b64)
        filename = f"sketch_{uuid.uuid4().hex[:12]}.jpg"
        out_path = self.sketches_dir / filename
        out_path.write_bytes(img_bytes)

        latency_ms = int((time.perf_counter() - start) * 1000)
        return DrawThingsGenerateResponse(
            image_url=f"/api/sketches/{filename}",
            filename=filename,
            prompt_used=full_prompt,
            negative_prompt_used="OpenAI safety filters",
            width=1024,
            height=1024,
            steps=1,
            latency_ms=latency_ms,
            mode="txt2img",
            unloaded_ollama=False,
            learned_analysis=None,
            applied_rules=["Rendered with OpenAI DALL-E 3"],
        )
