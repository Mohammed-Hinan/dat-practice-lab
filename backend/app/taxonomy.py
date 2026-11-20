"""Domain taxonomy, NID M.Des archetypes, preparation profiles, and recurring themes."""

from __future__ import annotations

from typing import Dict, List, TypedDict


CATEGORIES: List[str] = [
    "Composition",
    "Creativity",
    "Design aptitude",
    "Drawing",
    "Logos, Symbols & Signs",
    "Problem identification",
    "Product sketch",
    "Storyboard",
]

# Reference observation from https://dnerdstudio.com/draw?exam=nid&level=mdes
# Strictly website-specific tagging counts; NEVER used as official NID weightage.
DNERD_REFERENCE_METADATA = {
    "source_url": "https://dnerdstudio.com/draw?exam=nid&level=mdes",
    "total_prompts_observed": 235,
    "default_prompt_time_minutes": 30,
    "website_tag_counts": {
        "Design aptitude": 214,
        "Product sketch": 6,
        "Problem identification": 5,
        "Storyboard": 3,
        "Composition": 3,
        "Creativity": 2,
        "Drawing": 2,
    },
    "disclaimer": (
        "These counts reflect website-specific tagging on Dnerd Studio and do not represent "
        "official NID DAT Prelims examination weightage. Balanced practice prevents "
        "over-sampling 'Design aptitude' solely due to its larger website tag count."
    ),
}

CATEGORY_DEFINITIONS: Dict[str, Dict[str, object]] = {
    "Composition": {
        "description": (
            "Visual arrangement, spatial hierarchy, figure-ground balance, poster/graphic layout, "
            "framing, contrast, rhythm, and visual metaphor within a defined frame."
        ),
        "typical_formats": [
            "Design a poster, emblem, signage system, or editorial cover within a specified frame.",
            "Arrange given geometric/organic shapes or everyday objects into a meaningful composition conveying a specific emotion or social message.",
            "Create a visual metaphor communicating a complex social, cultural, or ecological issue with minimal or zero text.",
        ],
        "expected_balance": "Heavy visual/sketching with brief conceptual rationale.",
        "default_archetypes": ["Visual communication", "Creative and lateral thinking"],
    },
    "Creativity": {
        "description": (
            "Divergent ideation, lateral association, unexpected combinations, metaphor generation, "
            "word-to-visual transformation, and unconventional concept framing."
        ),
        "typical_formats": [
            "Generate multiple distinct, non-obvious uses or transformations of a mundane object under strict constraints.",
            "Combine two unrelated objects, roles, or situations to invent a plausible concept or visual narrative.",
            "Interpret an abstract phrase, proverb, or constraint visually and conceptually in multiple ways.",
        ],
        "expected_balance": "Mixed quick ideation thumbnails and concise conceptual explanations.",
        "default_archetypes": ["Creative and lateral thinking", "Visual communication"],
    },
    "Design aptitude": {
        "description": (
            "Holistic design thinking combining observation, empathy, reasoning, systems awareness, "
            "material logic, practical intervention, and visual communication in real-world Indian and global contexts."
        ),
        "typical_formats": [
            "Analyse an everyday public, domestic, or occupational situation and propose a realistic intervention.",
            "Examine a material's properties or local craft technique and apply it to solve a contemporary user need.",
            "Design a service touchpoint, kiosk, educational aid, or inclusive experience for a specific user group.",
            "Imagine a grounded near-future scenario (e.g., 15 years ahead) and illustrate how a daily activity adapts.",
        ],
        "expected_balance": "Balanced structured written reasoning and annotated explanatory diagrams/sketches (occasionally text-heavy analytical framing).",
        "default_archetypes": [
            "Human-centred design",
            "Materials and sustainability",
            "Future and systems thinking",
            "Interaction and service design",
        ],
    },
    "Drawing": {
        "description": (
            "Observational accuracy, proportion, perspective (1/2/3-point), human posture and gestures, "
            "object geometry, light/shadow, cutaway/exploded views, and step-by-step physical process illustration."
        ),
        "typical_formats": [
            "Draw a familiar everyday object or tool in accurate proportion and illustrate a human hand or user interacting with it.",
            "Illustrate a specific real-world scene from an unusual viewpoint (ant's-eye, bird's-eye, or through an opening) maintaining perspective and scale.",
            "Show the physical transformation of an object or an everyday multi-step process through clear observational drawings.",
        ],
        "expected_balance": "Primarily observational sketching with minimal labels.",
        "default_archetypes": ["Drawing and observation"],
    },
    "Logos, Symbols & Signs": {
        "description": (
            "Visual identity marks, brand logos, public wayfinding signage, behavioural signs, "
            "wordless pictograms, and universal symbols communicating instant meaning across language barriers."
        ),
        "typical_formats": [
            "Design a clear set of 4 to 5 behavioural or wayfinding signs for an everyday public space and explain how each guides user action.",
            "Design a memorable logo, emblem, and tagline for a local initiative, craft collective, or public service and show one real-world application.",
            "Create a set of universal wordless symbols/icons understandable at a glance by multilingual or low-literacy users.",
        ],
        "expected_balance": "Crisp, high-contrast iconic graphic marks/signs with brief functional rationale.",
        "default_archetypes": ["Visual communication", "Human-centred design"],
    },
    "Problem identification": {
        "description": (
            "Critical observation of everyday environments, identifying latent usability/safety/systemic pain points, "
            "understanding multiple stakeholders, prioritising one core problem, and proposing a feasible intervention."
        ),
        "typical_formats": [
            "Given a realistic everyday scenario (e.g., railway station waiting hall, monsoon street vendor, hospital OPD queue), identify 5 distinct problems across stakeholders, prioritise one, and propose an intervention.",
            "Audit an existing everyday object or public system for accessibility, ergonomic, or environmental failures and redesign a targeted part.",
        ],
        "expected_balance": "Structured analytical breakdown (numbered observations, prioritisation logic) paired with an annotated intervention sketch.",
        "default_archetypes": ["Problem identification", "Human-centred design", "Future and systems thinking"],
    },
    "Product sketch": {
        "description": (
            "Functional product ideation, form exploration, ergonomics, joinery/mechanism clarity, "
            "material specification, orthographic/3D perspective sketching, and callout annotations."
        ),
        "typical_formats": [
            "Redesign or invent a tangible product for a specific user and environment under explicit material, portability, or cost constraints.",
            "Illustrate the product in perspective with callouts explaining mechanism, interaction, ergonomics, and key dimensions/materials.",
        ],
        "expected_balance": "Annotated perspective product sketch, detail callouts, usage vignette, and concise functional notes.",
        "default_archetypes": ["Product innovation", "Human-centred design", "Materials and sustainability"],
    },
    "Storyboard": {
        "description": (
            "Sequential visual storytelling across a fixed number of frames showing character emotion, "
            "pacing, camera angles, transitions, conflict/resolution, or step-by-step user/service journeys."
        ),
        "typical_formats": [
            "Create a 4 to 6 frame storyboard depicting a narrative twist, emotional arc, or interaction between unusual characters/objects without dialogue (or with strict word limits).",
            "Illustrate a step-by-step user journey showing how a person discovers, uses, and finishes interacting with a service or product.",
        ],
        "expected_balance": "Sequential framed panels with clear visual continuity, framing variety, and brief captions only if permitted.",
        "default_archetypes": ["Storytelling and storyboard", "Interaction and service design"],
    },
}

PROGRAMME_TAGS: List[str] = [
    "Product Design",
    "Furniture & Interior Design",
    "Ceramic & Glass Design",
    "Toy & Game Design",
    "Transportation & Automobile Design",
    "Universal Design",
    "Graphic Design",
    "Animation Film Design",
    "Film & Video Communication",
    "Photography Design",
    "Exhibition Design",
    "Textile Design",
    "Apparel Design",
    "Lifestyle Accessory Design",
    "Interaction Design",
    "Information Design",
    "New Media Design",
    "Digital Game Design",
    "Strategic Design Management",
    "Design for Retail Experience",
]


class ArchetypeSpec(TypedDict):
    code: str
    name: str
    description: str
    prompt_patterns: List[str]
    primary_categories: List[str]


ARCHETYPES: List[ArchetypeSpec] = [
    {
        "code": "A",
        "name": "Problem identification",
        "description": (
            "Present a realistic situation. Ask the student to identify problems, understand "
            "stakeholders, prioritise issues and propose solutions."
        ),
        "prompt_patterns": [
            "Identify five distinct problems in a specific everyday setting, select the most critical one with justification, and propose a practical solution.",
            "Map pain points experienced by two contrasting stakeholders in the same environment and propose a balanced intervention.",
        ],
        "primary_categories": ["Problem identification", "Design aptitude"],
    },
    {
        "code": "B",
        "name": "Product innovation",
        "description": (
            "Ask the student to invent, modify, combine, redesign or improve a product with "
            "specific functional and material constraints."
        ),
        "prompt_patterns": [
            "Redesign an everyday tool or domestic product using a constrained set of materials or without electricity.",
            "Combine the functionality of two familiar objects to solve a specific situational constraint and illustrate its mechanism.",
        ],
        "primary_categories": ["Product sketch", "Design aptitude", "Creativity"],
    },
    {
        "code": "C",
        "name": "Human-centred design",
        "description": (
            "Create design challenges involving elderly people, children, people with disabilities, "
            "commuters, workers, students and other user groups."
        ),
        "prompt_patterns": [
            "Design an inclusive aid, spatial adaptation, or routine workflow for a user group facing sensory, mobility, or literacy barriers.",
            "Observe a specific occupational routine (e.g., street vendor, delivery worker, rural health worker) and reduce physical strain or friction.",
        ],
        "primary_categories": ["Design aptitude", "Problem identification", "Product sketch"],
    },
    {
        "code": "D",
        "name": "Visual communication",
        "description": (
            "Generate tasks involving posters, symbols, signs, graphics, campaigns, infographics, "
            "branding and visual metaphors."
        ),
        "prompt_patterns": [
            "Design a wordless or minimal-text public awareness poster or wayfinding symbol system using clear visual metaphors.",
            "Translate a multi-step civic process or public safety instruction into a visual infographic understandable across language barriers.",
        ],
        "primary_categories": ["Composition", "Design aptitude", "Creativity"],
    },
    {
        "code": "E",
        "name": "Storytelling and storyboard",
        "description": (
            "Generate visual narrative tasks with a specific number of frames, characters, "
            "scenarios, emotions and sequential actions."
        ),
        "prompt_patterns": [
            "Tell a complete visual story in 5 frames featuring an unexpected encounter or perspective shift without using speech bubbles.",
            "Create a 6-panel sequential narrative where an everyday object plays the central role in resolving a small human dilemma.",
        ],
        "primary_categories": ["Storyboard", "Creativity", "Composition"],
    },
    {
        "code": "F",
        "name": "Drawing and observation",
        "description": (
            "Generate object drawing, perspective, proportion, transformation, object manipulation, "
            "human activities and everyday process illustration tasks."
        ),
        "prompt_patterns": [
            "Draw an everyday object in accurate proportion, then illustrate a specific human interaction or mechanical state of that object.",
            "Sketch a rich everyday scene from a specified non-standard eye level, capturing scale, depth, and natural human postures.",
        ],
        "primary_categories": ["Drawing", "Product sketch", "Composition"],
    },
    {
        "code": "G",
        "name": "Materials and sustainability",
        "description": (
            "Generate tasks involving material properties, local crafts, environmental challenges, "
            "reuse, circularity and sustainable design."
        ),
        "prompt_patterns": [
            "Explain 3 physical properties of a traditional/discarded material and leverage those properties to create a durable everyday utility.",
            "Design a circular reuse or repair intervention that extends the lifecycle of a commonly discarded packaging or household waste stream.",
        ],
        "primary_categories": ["Design aptitude", "Product sketch", "Problem identification"],
    },
    {
        "code": "H",
        "name": "Future and systems thinking",
        "description": (
            "Generate hypothetical scenarios involving future products, services, technologies, "
            "communities, transportation, education and public infrastructure."
        ),
        "prompt_patterns": [
            "Imagine a realistic urban or rural scenario in 2040 shaped by climate or demographic change, and illustrate a system/artifact that helps communities adapt.",
            "Analyse second-order consequences of an emerging technology in public spaces and propose a thoughtful design intervention.",
        ],
        "primary_categories": ["Design aptitude", "Problem identification", "Storyboard"],
    },
    {
        "code": "I",
        "name": "Interaction and service design",
        "description": (
            "Generate tasks involving interfaces, kiosks, apps, interactive products, service "
            "journeys and step-by-step user experiences."
        ),
        "prompt_patterns": [
            "Design a low-friction physical-digital service touchpoint (e.g., public transit kiosk, ration/clinic check-in) for first-time or low-literacy users.",
            "Map a 4-step user experience journey resolving bottlenecks in a crowded civic service, illustrating key screens or physical touchpoints.",
        ],
        "primary_categories": ["Design aptitude", "Storyboard", "Problem identification"],
    },
    {
        "code": "J",
        "name": "Creative and lateral thinking",
        "description": (
            "Generate tasks involving unusual object combinations, visual associations, word "
            "interpretation, storytelling constraints and unconventional ideas."
        ),
        "prompt_patterns": [
            "Take three unrelated everyday items and generate distinct, visually explained concepts combining them into functional or playful solutions.",
            "Reimagine an ordinary rule, ritual, or object if one physical law or social habit were reversed.",
        ],
        "primary_categories": ["Creativity", "Composition", "Storyboard"],
    },
]

ARCHETYPE_NAMES: List[str] = [a["name"] for a in ARCHETYPES]


class PreparationProfileSpec(TypedDict):
    id: str
    name: str
    campus: str
    is_user_defined: bool
    note: str
    emphasis_areas: List[str]
    favoured_archetypes: List[str]
    favoured_programmes: List[str]
    category_boosts: Dict[str, float]
    theme_boosts: Dict[str, float]


PREPARATION_PROFILES: Dict[str, PreparationProfileSpec] = {
    "nid_gandhinagar_sdm": {
        "id": "nid_gandhinagar_sdm",
        "name": "NID Gandhinagar — Strategic Design Management",
        "campus": "NID Gandhinagar",
        "is_user_defined": False,
        "note": (
            "Emphasises problem framing, systems thinking, stakeholder alignment, services, "
            "sustainability, and strategic visual communication while maintaining all 7 categories."
        ),
        "emphasis_areas": [
            "Problem identification and framing",
            "Systems thinking",
            "Stakeholder understanding",
            "Social and environmental challenges",
            "Strategic design decisions",
            "Service and experience design",
            "Innovation and future scenarios",
            "Sustainability and circularity",
            "Visual communication",
            "Connecting design decisions to real-world outcomes",
        ],
        "favoured_archetypes": [
            "Problem identification",
            "Future and systems thinking",
            "Interaction and service design",
            "Materials and sustainability",
            "Human-centred design",
            "Visual communication",
        ],
        "favoured_programmes": [
            "Strategic Design Management",
            "Design for Retail Experience",
            "Information Design",
            "Interaction Design",
            "Universal Design",
            "Product Design",
        ],
        "category_boosts": {
            "Problem identification": 1.35,
            "Design aptitude": 1.25,
            "Storyboard": 1.05,
            "Composition": 1.05,
            "Product sketch": 1.0,
            "Creativity": 0.95,
            "Drawing": 0.85,
        },
        "theme_boosts": {
            "public_infrastructure": 1.35,
            "sustainability_materials": 1.35,
            "interaction_service": 1.35,
            "future_design": 1.3,
            "accessibility_inclusive": 1.2,
            "social_awareness": 1.2,
            "transportation_mobility": 1.15,
            "product_innovation": 1.1,
            "elderly_children": 1.1,
            "storytelling_narratives": 1.0,
        },
    },
    "nid_haryana_creative_leadership": {
        "id": "nid_haryana_creative_leadership",
        "name": "NID Haryana — Creative Leadership",
        "campus": "NID Haryana",
        "is_user_defined": True,
        "note": (
            "User-defined preparation profile (not a programme label from the Dnerd Studio "
            "filter list; does not assume official NID Haryana evaluation criteria). "
            "Emphasises divergent thinking, cross-disciplinary imagination, storytelling, "
            "cultural awareness, and original concept articulation."
        ),
        "emphasis_areas": [
            "Divergent thinking",
            "Creative problem-solving",
            "Cross-disciplinary imagination",
            "Visual storytelling",
            "Cultural and social awareness",
            "Innovation",
            "Future-oriented thinking",
            "Communication and expression",
            "Understanding different perspectives",
            "Developing and explaining original concepts",
        ],
        "favoured_archetypes": [
            "Creative and lateral thinking",
            "Storytelling and storyboard",
            "Future and systems thinking",
            "Visual communication",
            "Human-centred design",
            "Problem identification",
        ],
        "favoured_programmes": [
            "Strategic Design Management",
            "New Media Design",
            "Exhibition Design",
            "Film & Video Communication",
            "Graphic Design",
            "Interaction Design",
        ],
        "category_boosts": {
            "Creativity": 1.35,
            "Storyboard": 1.25,
            "Composition": 1.2,
            "Design aptitude": 1.15,
            "Problem identification": 1.15,
            "Product sketch": 0.95,
            "Drawing": 0.9,
        },
        "theme_boosts": {
            "storytelling_narratives": 1.35,
            "future_design": 1.35,
            "social_awareness": 1.3,
            "interaction_service": 1.2,
            "sustainability_materials": 1.15,
            "public_infrastructure": 1.15,
            "product_innovation": 1.15,
            "accessibility_inclusive": 1.1,
            "elderly_children": 1.05,
            "transportation_mobility": 1.05,
        },
    },
    "general_nid_mdes": {
        "id": "general_nid_mdes",
        "name": "General NID M.Des preparation",
        "campus": "All NID Campuses",
        "is_user_defined": False,
        "note": (
            "Broad, balanced NID M.Des DAT Prelims readiness across observation, sketching, "
            "problem-solving, visual communication, storytelling, and creative aptitude."
        ),
        "emphasis_areas": [
            "Observational drawing and spatial clarity",
            "Practical problem identification",
            "Product form and functional sketching",
            "Visual storytelling and composition",
            "Empathy and everyday Indian context awareness",
            "Divergent ideation under exam time constraints",
        ],
        "favoured_archetypes": ARCHETYPE_NAMES,
        "favoured_programmes": PROGRAMME_TAGS,
        "category_boosts": {cat: 1.0 for cat in CATEGORIES},
        "theme_boosts": {
            "accessibility_inclusive": 1.0,
            "elderly_children": 1.0,
            "public_infrastructure": 1.0,
            "sustainability_materials": 1.0,
            "product_innovation": 1.0,
            "transportation_mobility": 1.0,
            "social_awareness": 1.0,
            "future_design": 1.0,
            "storytelling_narratives": 1.0,
            "interaction_service": 1.0,
        },
    },
}


class ThemeSpec(TypedDict):
    id: str
    label: str
    description: str
    keywords: List[str]
    related_categories: List[str]
    related_archetypes: List[str]


RECURRING_THEMES: List[ThemeSpec] = [
    {
        "id": "accessibility_inclusive",
        "label": "Accessibility & Inclusive Design",
        "description": "Designing for physical, sensory, cognitive, linguistic, or socioeconomic inclusion.",
        "keywords": [
            "accessibility", "accessible", "inclusive", "disability", "disabled", "blind",
            "visually impaired", "wheelchair", "deaf", "hearing", "braille", "tactile",
            "low-literacy", "illiterate", "universal design", "assistive", "barrier-free",
        ],
        "related_categories": ["Design aptitude", "Problem identification", "Product sketch"],
        "related_archetypes": ["Human-centred design", "Problem identification"],
    },
    {
        "id": "elderly_children",
        "label": "Elderly Users & Children",
        "description": "Age-specific ergonomics, safety, play, companionship, learning, and dignity.",
        "keywords": [
            "elderly", "senior citizen", "old age", "aged", "grandparent", "child", "children",
            "kid", "kids", "toddler", "school", "toy", "play", "classroom", "pediatric",
            "student", "adolescent", "aging",
        ],
        "related_categories": ["Product sketch", "Design aptitude", "Storyboard"],
        "related_archetypes": ["Human-centred design", "Product innovation"],
    },
    {
        "id": "public_infrastructure",
        "label": "Public Infrastructure & Everyday Problems",
        "description": "Civic spaces, queues, markets, hospitals, campuses, street vending, sanitation, and monsoon resilience.",
        "keywords": [
            "public", "infrastructure", "station", "hospital", "queue", "street", "vendor",
            "market", "park", "toilet", "sanitation", "civic", "municipality", "monsoon",
            "water", "garbage", "waiting", "crowd", "community", "village", "rural", "urban",
            "hostel", "canteen", "library",
        ],
        "related_categories": ["Problem identification", "Design aptitude", "Drawing"],
        "related_archetypes": ["Problem identification", "Future and systems thinking"],
    },
    {
        "id": "sustainability_materials",
        "label": "Sustainability & Materials",
        "description": "Material properties, local crafts, waste reduction, reuse, repairability, and ecological impact.",
        "keywords": [
            "sustainable", "sustainability", "material", "bamboo", "clay", "terracotta",
            "jute", "plastic", "recycle", "reuse", "circular", "waste", "eco", "biodegradable",
            "craft", "artisan", "upcycle", "packaging", "climate", "solar", "repair", "zero waste",
        ],
        "related_categories": ["Design aptitude", "Product sketch", "Problem identification"],
        "related_archetypes": ["Materials and sustainability", "Product innovation"],
    },
    {
        "id": "product_innovation",
        "label": "Product Innovation & Redesign",
        "description": "Functional improvements, ergonomics, portability, multi-use artifacts, and constrained mechanisms.",
        "keywords": [
            "product", "redesign", "device", "tool", "gadget", "furniture", "chair", "bag",
            "bottle", "kitchen", "utensil", "appliance", "mechanism", "foldable", "portable",
            "ergonomic", "modular", "combine", "modify", "invent", "lamp", "desk",
        ],
        "related_categories": ["Product sketch", "Design aptitude", "Creativity"],
        "related_archetypes": ["Product innovation", "Human-centred design"],
    },
    {
        "id": "transportation_mobility",
        "label": "Transportation & Mobility",
        "description": "Commuting, last-mile transit, trains, buses, bicycles, pedestrian safety, and luggage/cargo handling.",
        "keywords": [
            "transport", "transportation", "mobility", "commute", "commuter", "bus", "train",
            "railway", "metro", "auto", "rickshaw", "bicycle", "bike", "scooter", "traffic",
            "pedestrian", "helmet", "luggage", "delivery", "vehicle", "parking", "road",
        ],
        "related_categories": ["Problem identification", "Product sketch", "Design aptitude"],
        "related_archetypes": ["Problem identification", "Future and systems thinking", "Product innovation"],
    },
    {
        "id": "social_awareness",
        "label": "Social Awareness & Communication",
        "description": "Posters, visual metaphors, civic campaigns, signage, health literacy, and cultural expression.",
        "keywords": [
            "poster", "campaign", "awareness", "signage", "symbol", "icon", "metaphor",
            "graphic", "infographic", "mental health", "hygiene", "safety", "conservation",
            "culture", "heritage", "gender", "social", "communicate", "message", "logo",
            "wayfinding", "banner",
        ],
        "related_categories": ["Composition", "Creativity", "Design aptitude"],
        "related_archetypes": ["Visual communication", "Creative and lateral thinking"],
    },
    {
        "id": "future_design",
        "label": "Future-Oriented & Systems Design",
        "description": "Speculative yet grounded 2035–2050 scenarios across cities, work, learning, climate, and AI.",
        "keywords": [
            "future", "2030", "2040", "2050", "tomorrow", "speculative", "ai", "robot",
            "smart city", "autonomous", "drone", "space", "climate change", "hyper",
            "emerging", "system", "ecosystem", "next generation", "post-", "imagine a world",
        ],
        "related_categories": ["Design aptitude", "Creativity", "Storyboard"],
        "related_archetypes": ["Future and systems thinking", "Creative and lateral thinking"],
    },
    {
        "id": "storytelling_narratives",
        "label": "Storytelling & Visual Narratives",
        "description": "Sequential frames, character arcs, perspective shifts, wordless narratives, and visual humour.",
        "keywords": [
            "storyboard", "story", "frame", "frames", "panel", "panels", "sequence",
            "narrative", "character", "comic", "scene", "dialogue", "emotion", "journey",
            "twist", "film", "animation", "beginning", "climax", "ending",
        ],
        "related_categories": ["Storyboard", "Creativity", "Composition"],
        "related_archetypes": ["Storytelling and storyboard", "Creative and lateral thinking"],
    },
    {
        "id": "interaction_service",
        "label": "Interaction & Service Experiences",
        "description": "Kiosks, mobile apps, onboarding flows, physical-digital touchpoints, and service blueprints.",
        "keywords": [
            "interaction", "interactive", "interface", "app", "kiosk", "screen", "service",
            "experience", "onboarding", "booking", "check-in", "payment", "digital",
            "touchpoint", "user journey", "atm", "vending", "dashboard", "ux", "ui",
        ],
        "related_categories": ["Design aptitude", "Storyboard", "Problem identification"],
        "related_archetypes": ["Interaction and service design", "Human-centred design"],
    },
]

STANDARD_COMPETENCIES: List[str] = [
    "Observation",
    "Empathy",
    "Problem framing",
    "Divergent thinking",
    "Systems thinking",
    "Visual communication",
    "Proportion & perspective",
    "Ergonomic reasoning",
    "Material intelligence",
    "Sequential storytelling",
    "Stakeholder analysis",
    "Sustainability reasoning",
    "Constraint navigation",
    "Service & interaction logic",
]
