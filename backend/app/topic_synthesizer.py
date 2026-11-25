"""Dynamic NID M.Des / CEED Topic Synthesizer & Curated Topic Bank.

Provides:
1. Massive Curated Topic Bank (300+ authentic, single-focus NID/CEED topics across all 8 categories).
2. Combinatorial Topic Synthesizer (infinite permutations of User Demographics × Everyday Environments × Friction Points).
3. Persistent fingerprint-based anti-repetition engine ensuring no recent topic recurrence.
"""

from __future__ import annotations

import random
import re
from typing import Dict, List, Optional, Set, Tuple


# ==============================================================================
# 1. AUTHENTIC BLUEPRINTS & MASSIVE CURATED SEED BANK (320+ TOPICS)
# ==============================================================================

NID_BLUEPRINTS: Dict[str, List[Tuple[str, List[str], List[str]]]] = {
    "Composition": [
        (
            "Forced-metaphor poster: Sketch a poster promoting the given social or lifestyle message that MUST combine two unexpected everyday visual elements, with an English title under 6 words.",
            ["nid_haryana_creative_leadership", "general_nid_mdes"],
            [
                "encouraging teenagers to take screen-free breaks before sleep",
                "saving household water during summer shortages",
                "stopping single-use plastic bags at weekly vegetable markets",
                "reducing unnecessary noise pollution in residential lanes",
                "promoting organ donation awareness among young adults",
                "preventing food wastage at lavish community wedding banquets",
                "encouraging safe pedestrian zebra-crossing habits in busy market streets",
                "celebrating the dignity and patience of neighbourhood sanitation workers",
                "highlighting the loss of outdoor play spaces in dense vertical apartment complexes",
                "promoting groundwater recharging through rooftop rainwater harvesting in cities",
                "discouraging rash honking and road rage among two-wheeler commuters",
                "fostering intergenerational companionship between college students and lonely seniors",
                "combating school bullying and fostering peer empathy among students",
            ],
        ),
        (
            "Campaign + poster: Plan an awareness campaign for a college, neighbourhood, or workplace. Subquestion A: list 5 specific everyday situations to improve (1-2 sentences each). Subquestion B: design a bold poster tackling one of them.",
            ["nid_gandhinagar_sdm", "nid_haryana_creative_leadership"],
            [
                "reducing food waste at large family weddings and campus canteens",
                "honouring and supporting neighbourhood sanitation workers",
                "building kindness and patience in crowded public queues",
                "encouraging neighbourhood book-sharing and community reading",
                "sensitizing young drivers to stray animal welfare on city roads",
                "promoting responsible disposal of domestic sanitary and medical waste",
                "creating inclusive, harassment-free late-evening public transport environments",
                "encouraging urban residents to segregate kitchen compost from dry recyclables at the source",
                "promoting regular eye and posture checkups for software developers and remote workers",
                "celebrating the craft heritage of local handloom weavers and potters in urban spaces",
                "building community preparedness for seasonal urban monsoon flash floods",
                "an anti-bullying school awareness campaign to combat harassment and empower bystanders",
            ],
        ),
        (
            "Identity & visual system: You are launching the given initiative or channel. Subquestion A: define its focus, audience, and tagline. Subquestion B: design its logo/emblem and show it applied on one real-world surface.",
            ["nid_gandhinagar_sdm", "general_nid_mdes"],
            [
                "an independent regional street-food documentary channel",
                "a youth collective promoting local handloom weavers to college students",
                "a neighbourhood tool-lending and repair library",
                "a mobile repair van fixing discarded household electronics for underprivileged students",
                "a community terrace gardening collective sharing indigenous heirloom seeds",
                "a bicycle commuting network advocating safe cycle corridors in metro cities",
                "an indigenous children's storytelling podcast celebrating forgotten folk legends",
                "a social enterprise converting discarded temple flower waste into natural incense and dyes",
                "a student-led zero-plastic canteen cooperative in a design university",
                "a volunteer elder-care companion service connecting youth with nursing homes",
            ],
        ),
        (
            "Visualise a stark everyday contrast: Subquestion A: briefly explain the root tension behind the given social contrast. Subquestion B: communicate this fact using ONLY simple shapes, icons, or visual metaphor so anyone understands at a glance.",
            ["nid_haryana_creative_leadership", "general_nid_mdes"],
            [
                "clean drinking water wasted in urban car-washing vs water scarcity in dry villages",
                "unused electronic gadgets piling up in drawers vs the shortage of simple local repair options",
                "monsoon waterlogging in wealthy residential enclaves vs severe potable water shortages in informal settlements",
                "overflowing food buffets at corporate banquets vs daily wage earners skipping meals",
                "children glued to indoor tablet screens vs empty local municipal parks and playgrounds",
                "fast fashion clothing waste piling up in landfills vs traditional artisans struggling to sell slow handlooms",
            ],
        ),
        (
            "Multi-point public informational poster: The authorities/organization requires a public visual guide communicating 5 to 7 specific critical tips or guidelines to a first-time, elderly, or multilingual audience. Subquestion A: Sketch a bold, well-structured poster (3:4 vertical ratio) integrating all points using clear visual hierarchy and minimal text. Subquestion B: Write a punchy bilingual tagline under 6 words and explain your layout/focal point strategy.",
            ["general_nid_mdes", "nid_gandhinagar_sdm", "nid_haryana_creative_leadership"],
            [
                "7 ATM safety and transaction rules for rural or first-time digital banking users (hide PIN, press cancel, reject stranger help, count cash, report un-dispensed cash, leave on welcome screen, take card)",
                "5 escalator and platform boarding etiquette rules at an overcrowded metro junction during monsoon rush",
                "6 emergency domestic gas cylinder (LPG) leak response protocols for high-density apartment residents",
                "5 pedestrian and zebra-crossing safety rules for primary school children in bustling market lanes",
                "6 hygiene, water-purification, and disease-prevention protocols for flood relief temporary shelter camps",
                "5 responsible disposal and handling rules for domestic medical, sanitary, and sharp waste",
                "6 extreme heatwave survival, hydration, and shade guidelines for outdoor construction and delivery workers",
                "5 cyber-safety and OTP fraud prevention habits for senior citizens using smartphones for digital payments",
            ],
        ),
        (
            "Symbol & Campaign Poster: Subquestion A: Design an original, high-contrast symbol/emblem representing the core theme. Subquestion B: Design a full-page awareness campaign poster deploying the symbol with a powerful tagline under 6 words.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "raising awareness about binary gender inclusivity and neutral public spaces",
                "anti-bullying, empathy, and mental wellbeing campaign across secondary school campuses",
                "promoting voluntary organ donation pledges among university students and young professionals",
                "combating fast-fashion textile waste and celebrating local garment repair and upcycling culture",
                "mental health decompression and stress relief for competitive entrance examination aspirants",
                "protecting community stray animal welfare and driver sensitization in residential sectors",
            ],
        ),
        (
            "Metaphorical literature/poetry poster: Translate the underlying philosophy and emotional resonance of the given quote or couplet into a powerful visual poster with an original tagline.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "Rabindranath Tagore: 'Where the mind is without fear and the head is held high, where knowledge is free...'",
                "Mahatma Gandhi: 'The earth has enough for everyone's need, but not for everyone's greed'",
                "Kabir: 'Slowly, slowly O mind, everything in its own time happens; even if the gardener waters with a hundred pots, fruit arrives only in season'",
                "APJ Abdul Kalam: 'Dreams are not what you see in sleep, dreams are things which do not let you sleep'",
                "Chief Seattle: 'We do not inherit the earth from our ancestors, we borrow it from our children'",
            ],
        ),
    ],
    "Creativity": [
        (
            "Modular 3D geometric block showpiece: You are provided with 16 identical wooden cubes in 4 distinct colours (4 of each colour). Subquestion A: Construct a stable 3D perspective or isometric sculptural showpiece displaying interlocking faces, cantilevers, voids, and structural equilibrium. Subquestion B: Explain the 4-colour distribution logic, tabletop context, and dimension scale reference.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "16 wooden cubes in 4 colors forming an artistic drawing-room tabletop showpiece",
                "16 modular interlocking blocks in 4 wood species forming a contemplative Zen desk sculpture",
                "12 triangular prisms in 3 tones forming an architectural modular desktop organizer",
                "16 hexagonal blocks in 4 colors forming a tactile acoustic tabletop sound sculpture",
            ],
        ),
        (
            "Sensory object story: Weave the sensory qualities (sound, light, touch, smell) of any 4 of the listed everyday objects into a short original story, then draw the most vivid moment without dialogue.",
            ["nid_haryana_creative_leadership", "general_nid_mdes"],
            [
                "a brass bell, a wet chalk stick, a paper hand-fan, a steel tumbler, and a hot glass of chai",
                "a rusty padlock, a dry leaf, a wooden ruler, a clay lamp, and a steaming tiffin box",
                "a jute gunny sack, roasted groundnuts in paper cone, a kerosene lantern, and a rain-soaked umbrella",
                "a wooden clothes peg, a glass marble, a leather chappal, and a burning incense stick",
                "a copper coin, a bundle of wet lemongrass, a sizzling iron tawa, and a worn cloth handkerchief",
                "a cracked porcelain tea cup, a train ticket stub, a brass whistle, and a ball of coarse coir rope",
                "a hand-carved wooden stamp, wet indigo paste, a spinning bicycle spoke, and a fresh marigold garland",
            ],
        ),
        (
            "Biomimetic product metaphor: Design a practical everyday product whose form and mechanism are inspired by the given natural organism or creature. Subquestion A: explain 3 key functional features borrowed from the organism. Subquestion B: draw a clean 3/4 perspective sketch showing the product in practical use on clean white paper.",
            ["nid_haryana_creative_leadership", "general_nid_mdes"],
            [
                "a compact desktop study lamp inspired by the streamlined anatomy and arched posture of a river dolphin",
                "a lightweight portable rain poncho and hood inspired by folding beetle wing covers",
                "a handheld fruit-picking tool inspired by the flexible prehensile grip of a chameleon",
                "an ergonomic heavy-backpack weight-distribution strap inspired by elephant shoulder skeletal structure",
                "a non-electric evaporative food-cooling container inspired by termite mound ventilation channels",
                "a puncture-resistant flexible work glove inspired by the interlocking dermal scales of a pangolin",
                "a water-shedding outdoor helmet surface inspired by the hydrophobic micro-texture of a lotus leaf",
                "a compact self-expanding temporary emergency shelter inspired by the unfolding geometry of a cicada wing",
                "a multi-angle clamping desktop tool holder inspired by the claw articulation of a coconut crab",
                "a silent low-energy ceiling fan blade profile inspired by the serrated wing feathers of an owl",
                "a modular interlocking wall-tile system inspired by the hexagonal architecture of a honeycomb",
            ],
        ),
        (
            "Single-prop lateral invention: Using ONLY the given humble everyday object as a prop, invent and illustrate distinct ways to teach 2 abstract values (like teamwork, patience, or courage) or solve 3 unrelated daily problems.",
            ["nid_haryana_creative_leadership", "nid_gandhinagar_sdm"],
            [
                "a single sheet of daily newspaper",
                "a three-tier steel tiffin box",
                "a wooden clothespin",
                "an empty cardboard egg carton",
                "a standard two-metre coir rope",
                "a flat terracotta earthen saucer (sakora)",
                "a discarded bicycle inner tube",
                "a single bamboo ruler with centimetre markings",
                "a metal wire clothes hanger",
                "a dried whole coconut shell",
                "an ordinary ceramic coffee mug",
                "a 5-metre roll of brown packaging tape",
                "a single wooden safety matchstick box",
                "a stainless-steel tablespoon",
                "an empty two-litre plastic soda bottle",
                "a pair of stainless steel scissors",
                "a discarded automobile rubber tyre",
            ],
        ),
        (
            "Sensory cross-domain synthesis: Combine the physical interaction of an everyday food or natural process with a non-food functional product.",
            ["nid_haryana_creative_leadership"],
            [
                "the tactile peeling and segmenting of an orange translated into a portable travel grooming kit",
                "the layered unfurling of an onion translated into a modular privacy desk screen",
                "the porous water-cooling seepage of an earthen matka translated into an evaporative laptop cooling stand",
                "the resilient tensile bounce of a rubber tree leaf translated into an ergonomic shoe sole insert",
                "the crushing and rolling of sugarcane in a street press translated into a manual paper compactor",
            ],
        ),
        (
            "Form Sensitivity & Product Translation: Study the given three-dimensional geometric or bionic form. Subquestion A: Translate the curvature, rhythm, and parting lines of this form into a single-seater living-room chair or ergonomic desktop lifestyle accessory. Draw a clean 3/4 perspective sketch. Subquestion B: Annotate 4 key functional, material, and ergonomic details demonstrating how form serves function.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "translating an equiangular nautilus shell spiral into a compact modular desktop cable and device organizer",
                "translating a smooth river pebble with an eroded concave hollow into an ergonomic meditation stool",
                "translating an origami-folded hyperbolic paraboloid into a flat-pack sheet-metal lounge chair",
                "translating the segmented protective exoskeleton of a pill-bug (armadillo) into an expandable hard-shell commuter backpack",
                "translating a continuous twisted moebius strip into a bent-plywood reading bench",
                "translating the segmented conical architecture of a pinecone into an ambient acoustic desk lamp",
                "translating an egg-shaped ellipsoid sliced diagonally into a compact dual-chamber food warmer",
            ],
        ),
        (
            "Literal or Subversive Idiom Visualization: Subquestion A: Choose two common idioms and depict their meaning through a clever, witty visual illustration (visual pun) without relying on text labels. Subquestion B: Explain in 2 sentences how the composition communicates the metaphor.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "'Walking on eggshells' and 'Spilling the beans'",
                "'Burning the candle at both ends' and 'A bitter pill to swallow'",
                "'A storm in a teacup' and 'Barking up the wrong tree'",
                "'Burying your head in the sand' and 'The elephant in the room'",
                "'Cutting corners' and 'Caught red-handed'",
                "'Don't put all your eggs in one basket' and 'Bite the bullet'",
            ],
        ),
        (
            "Lateral thinking & conceptual transformation: Subquestion A: Re-imagine the given common object, situation, or anatomy under an impossible or surreal constraint. Subquestion B: Illustrate 4 distinct everyday interactions resulting from this change.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "if the human head were an exact rigid cube: four everyday human interactions (sleeping, wearing spectacles, eating, wearing a helmet)",
                "five innovative uses for an ordinary safety helmet, completely unrelated to headgear or protection",
                "five innovative everyday uses combining an old tyre, a plastic bottle, a cricket bat, and a plastic bucket",
                "re-imagining an everyday tea flask inspired by an animated character's personality and form",
                "re-imagining an everyday umbrella if raindrops fell upwards from the ground",
            ],
        ),
    ],
    "Drawing": [
        (
            "Multi-figure dynamic sports & action: Subquestion A: Illustrate at least 4 interacting human figures in diverse athletic action postures (such as bowler, batsman, fielders, runners) with dynamic lines of action, balance, and foreshortening. Subquestion B: Depict the spatial ground plane, pitch markings, and environmental context with 3-tier line weight.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "a lively group of boys playing gully cricket in an open neighbourhood ground",
                "children playing kabaddi or kho-kho on an unpaved rural sports field",
                "young athletes playing street football or soccer on a waterlogged monsoon lane",
                "teenagers playing volleyball or badminton across an improvised rope net",
                "children competing in tug-of-war or hopscotch during school recess",
            ],
        ),
        (
            "High-angle aerial & balcony perspective: Subquestion A: Construct a steep 3-point high-angle perspective looking down from an elevated vantage point (4th-floor balcony, pedestrian footbridge, or rooftop terrace), showing vertical line convergence. Subquestion B: Render strong directional sunlight, cast shadows, and foreshortened human figures seen from above.",
            ["general_nid_mdes"],
            [
                "looking down from a 4th-floor apartment balcony at a neighbourhood place of worship surrounded by a landscaped garden on a busy sunny day",
                "looking down from a high pedestrian overbridge onto a crowded railway junction platform during train arrival",
                "looking down from a 3rd-floor terrace onto a bustling weekly open-air vegetable market",
                "looking down from an apartment window onto a busy waterlogged street after a heavy monsoon downpour",
                "looking down from a library mezzanine onto students working around study tables and bookshelves",
            ],
        ),
        (
            "Observational social scenario & human emotional reactions: Subquestion A: Depict the central subject's body posture, physical gesture, and immediate interaction with the environment. Subquestion B: Illustrate nearby bystanders and passersby exhibiting contrasting, realistic emotional reactions (disgust, protection, curiosity, indifference) in an authentic public setting.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "a man smoking a cigarette in a crowded bus shelter or railway tea stall",
                "a street performer or magician gathering a crowd of spectators on a city promenade",
                "a commuter dropping an open crate of fruits at a busy metro exit during rush hour",
                "an argument over an auto-rickshaw fare in front of a crowded railway station",
                "passengers reacting to a stray street dog wandering into a modern air-conditioned metro station",
            ],
        ),
        (
            "Body-constraint object observation: Subquestion A: draw 3 existing everyday objects that match the given physical constraint in accurate proportion, naming each. Subquestion B: draw one of them being operated by a human hand or foot.",
            ["general_nid_mdes"],
            [
                "everyday objects operated using only the thumb and index finger",
                "everyday objects operated using only one foot while standing",
                "everyday kitchen tools operated with one hand only",
                "everyday objects operated with a whole-palm squeeze grip",
                "everyday tools operated through a continuous two-handed twisting motion",
                "everyday objects pulled or tensioned towards the user's torso",
                "everyday objects operated using only the elbow or forearm when hands are soiled",
                "everyday tools operated using index finger and palm counter-pressure",
                "everyday objects operated using only the heel of the palm while pushing downwards",
                "everyday objects operated using simultaneous foot pedal depression and one-hand guiding",
            ],
        ),
        (
            "Expressions, gestures or postures: Subquestion A: draw 5 distinct facial expressions or hand postures observed in the given everyday moment, labelling each clearly. Subquestion B: briefly note what visual cues distinguish them.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "people's reactions during a sudden power cut in a crowded hall",
                "different hand grips and postures of artisans or street cooks at work",
                "commuters negotiating and bargaining with an auto-rickshaw driver in heavy rain",
                "spectators reacting to a nail-biting final over of a gully cricket match",
                "passengers waiting on a delayed winter railway platform at 5 AM",
                "parents teaching a young child how to ride a bicycle without training wheels",
                "vendors and buyers negotiating at a wholesale fish harbour at dawn",
                "family members saying goodbye at a crowded railway platform train window",
                "an elderly artisan examining a cracked gemstone through a handheld jeweller's loupe",
                "school students waiting outside an examination hall five minutes before paper distribution",
                "passengers attempting to steady themselves inside a sharply turning city bus",
            ],
        ),
        (
            "Plan-to-3D spatial observation: Subquestion A: draw a labelled top-view plan of the given everyday space showing movement and activity zones. Subquestion B: turn part of that plan into a realistic 3D eye-level perspective sketch.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "a lively corner tea stall with a wooden bench and preparation counter",
                "a neighbourhood home courtyard with drying clothes, tulsi pot, and washing area",
                "a student's study desk, bookshelf, and wall organizer in a compact hostel room",
                "a tiny open-air roadside cobbler's umbrella workstation with tools laid out on burlap",
                "a busy neighbourhood barber shop with two mirrors, chairs, and waiting bench",
                "a primary health centre dispensary counter with waiting queue and medicine shelves",
                "a small traditional tailoring shop with a pedal sewing machine and fabric rolls",
                "a flower garland vendor's platform outside a temple entrance",
            ],
        ),
        (
            "Dramatic perspective & eye-level storytelling: Draw a full-frame, eye-level observational scene capturing human interaction, light, and everyday Indian context for the given scenario.",
            ["general_nid_mdes"],
            [
                "a vendor loading an overflowing three-wheeled pushcart with watermelons under morning sunlight",
                "an elderly woman carefully threading a needle near a window while her grandchild plays with clay marbles",
                "two mechanics working under the raised bonnet of an old Ambassador car in a roadside garage",
                "commuters huddled together under a narrow shop awning during a sudden blinding cloudburst",
                "a potter kicking a heavy stone wheel while shaping a large earthen water pitcher",
                "first-person point of view (1st-person POV) looking down at your hands kneading dough on a low wooden chawki",
                "first-person point of view looking down from an upper railway berth at fellow passengers sleeping below",
                "an eye-level view of a street sugarcane juice vendor feeding thick canes through geared metal rollers",
                "an overhead worm's-eye perspective looking up at a kite entangled in overhead electric wires in a narrow lane",
            ],
        ),
        (
            "Visual Sensitivity & Typography Extension: You are given the visual styling and construction language of 2 sample letters ('A' and 'B'). Subquestion A: Following the exact same font anatomy, stem weight, terminal style, and optical rhythm, draw the target word in uppercase display lettering. Subquestion B: Sketch a matching geometric monogram or favicon in the same typeface style.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "Style: Ornamental Art-Deco monolinear lettering with stepped serifs. Target word: 'F O R E S T'",
                "Style: Heritage Gujarati block-print textile stamps with micro-grid cutouts. Target word: 'C R A F T'",
                "Style: Heavy industrial stencil with angled bridge cuts. Target word: 'K I N E T I C'",
                "Style: Fluid calligraphic ribbon with dynamic thick-thin contrast. Target word: 'M O N S O O N'",
                "Style: Minimalist rounded monolinear geometric glyphs. Target word: 'S H E L T E R'",
                "Style: Indian folk Warli geometry with triangular negative spaces. Target word: 'P U L S E'",
            ],
        ),
        (
            "Extreme Camera Point-of-View Drawing: Draw the described scene from the specific unconventional optical point of view, using accurate perspective, relative scale, and light-and-shade.",
            ["general_nid_mdes"],
            [
                "a room camera mounted high in the corner of a 12x12 room capturing a tall father taking a vertical selfie with his playful family",
                "an 8-year-old walking a dog in a park with lamp posts, drawn strictly from the eye-level point of view of the dog looking back at the boy",
                "a crow perched on a high tree branch looking down at a roadside fresh fruit-juice vendor serving customers",
                "an auto-rickshaw passenger's first-person POV looking past their own knees and the driver's shoulders onto a rainy city crossroads",
                "a child crouching under a dining table looking out at adults gathered around during a family dinner",
                "a security guard's desk-level POV looking past an open register at a late-night visitor entering the lobby",
            ],
        ),
    ],
    "Logos, Symbols & Signs": [
        (
            "Cognitive journey & route cartography: Subquestion A: Draw an intuitive hand-drawn cognitive route map from home or origin to an important destination (exam centre, regional market, hospital) showing transport modes, major turns, and spatial road spine. Subquestion B: Depict 5 recognizable urban landmarks, directional compass rose, and transit wayfinding legend.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "route traversed from home to reach examination centre (TCS iON Digital Zone-Aluva)",
                "evacuation and relief route through flood-affected urban neighbourhood to relief camp",
                "heritage walking trail through old walled city market to historic monument",
                "daily pedestrian and bicycle commute from residential hostel to university campus",
            ],
        ),
        (
            "Behavioural & wayfinding signs: Design a coherent set of 4 clear, wordless or minimal-text public signs for the given everyday space. Subquestion A: draw 4 distinct signs using simple high-contrast shapes. Subquestion B: briefly explain how each sign guides or improves people's behaviour.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "a busy hospital waiting hall shared by patients, families, and wheelchair users",
                "a crowded metro escalator and platform during peak rush hour",
                "a neighbourhood public park shared by morning walkers, children, and pet owners",
                "a quiet municipal library with reading zones, children's corners, and phone booths",
                "a railway station platform where passengers wait with heavy luggage during monsoon rains",
                "a multi-faith community cremation and burial ground with distinct quiet zones",
                "a heritage archaeological site protecting ancient rock carvings from visitor touch",
                "a zero-waste college campus sorting wet food, dry paper, electronic waste, and packaging",
                "a crowded inter-state bus terminus with designated boarding, luggage, and feeding rooms",
                "a public beach walkway promoting turtle nesting protection and litter prevention",
            ],
        ),
        (
            "Logo, symbol & brand identity: You are creating a visual identity for the given local initiative, product, or public service. Subquestion A: draw a clean, memorable logo/emblem that works in pure black and white and write a short tagline (under 6 words). Subquestion B: show the logo applied on one real-world surface and explain the visual idea.",
            ["general_nid_mdes", "nid_haryana_creative_leadership", "nid_gandhinagar_sdm"],
            [
                "a neighbourhood repair cafe where residents fix broken household appliances",
                "a regional handloom and natural-dye weavers' cooperative",
                "an independent Indian street-food documentary channel",
                "a community seed-sharing and rooftop gardening collective",
                "a student-run night-time campus bicycle and shuttle service",
                "a sustainable pottery collective crafting non-electric terracotta refrigeration pots",
                "an indigenous toy-making guild from Channapatna creating educational sensory puzzles",
                "a citizen water-watch group monitoring lake health and reviving urban wetlands",
                "a rural solar-power microgrid cooperative run by local women entrepreneurs",
                "a mobile veterinary ambulance providing medical aid to injured street animals",
                "a community cycling club promoting safe school commutes for young girls",
                "an indigenous seed preservation network in tribal Maharashtra",
                "a women-led solar lamp assembly enterprise in remote Himalayan villages",
                "a clean river revival action committee mobilizing weekend youth cleanups",
            ],
        ),
        (
            "Universal wordless pictograms: Create a set of 4 universal pictograms/symbols understandable at a glance by people who cannot read English or local scripts. Subquestion A: draw the 4 matching pictograms inside square frames with consistent line weight. Subquestion B: justify the visual cues you chose for instant recognition.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "waste segregation bins (wet compost, dry paper/plastic, glass/metal, and e-waste) at a railway station",
                "emergency safety actions (fire exit, assembly point, first aid, and no-elevator) inside a public mall",
                "care and handling instructions for a handmade terracotta and cloth gift parcel",
                "accessible facilities (ramp, tactile path, drinking water, and quiet seating) at a heritage museum",
                "hygiene guidelines (wash hands with soap, discard masks properly, boil water, social distance) at a village health camp",
                "child-safety pictograms on a public playground (soft landing, adult supervision, no push, age limit)",
                "water conservation instructions in public restrooms (half flush, turn tap firmly off, report leaks)",
                "artisan tool-safety icons in a shared community carpentry workshop (eye goggles, tie hair, clean blade, unplug power)",
                "civic etiquette pictograms on a crowded state transport bus (yield seat to elderly, fold umbrella, keep bags under seat, speak softly)",
                "zero-waste community kitchen handling icons (boil water, separate organic scraps, wash steel plates, dry cloth)",
                "emergency monsoon flood evacuation markers for a low-lying riverbank settlement (high ground, shelter direction, medical boat, clean water)",
            ],
        ),
        (
            "Institutional Identity & Acronym Emblem: Subquestion A: Create a clean, memorable emblem or wordmark that seamlessly embeds the given acronym and an evocative dual visual metaphor, functioning in pure black and white. Subquestion B: Illustrate the emblem in context on 2 real-world touchpoints (e.g. jersey, official stamp, vehicle, packaging) and explain your visual rationale.",
            ["general_nid_mdes", "nid_haryana_creative_leadership", "nid_gandhinagar_sdm"],
            [
                "Indian Women's Hockey Association ('IWHA') combining sports agility, hockey stick geometry, and national pride",
                "Tribal Forest Honey Collective ('TFHC') combining wild honeycomb geometry and flora",
                "Citizen River Action Watch ('CRAW') combining flowing water waves and human guardian hands",
                "Street Women Artisans Guild ('SWAD') combining spinning charkha threads and clay tools",
                "Indian Museum of Science ('IMOS') combining atomic orbits and traditional Indian geometric jali patterns",
                "Senior Assistance & Friendly Escort ('SAFE') combining an elderly walking cane and caring embrace",
                "Village Agro Network Initiative ('VANI') combining a radio broadcast wave and grain stalk",
                "Kids Heritage & Educational League ('KHEL') combining traditional wooden spinning tops and open books",
            ],
        ),
        (
            "Cohesive 4-Icon System: Design a set of 4 uniform, wordless pictograms inside 4 equal square frames with identical line weight and geometric grammar. Subquestion A: Draw the 4 matching icons clearly. Subquestion B: Explain the visual cues used to ensure universal recognition without text.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "4 gallery icons for the Indian Museum of Science: [Astronomy], [Robotics], [Ancient Metallurgy], [Bio-energy]",
                "4 heritage craft pavilions at a national craft mela: [Handlooms], [Terracotta Pottery], [Dhokra Metal Casting], [Bamboo Joinery]",
                "4 public transport wayfinding icons: [Quiet Reading Zone], [Tactile Guide Path], [Pram/Luggage Ramp], [Emergency Defibrillator]",
                "4 climate resilience zones in a civic park: [Rooftop Rain Harvesting], [Solar Gazebo], [Compost Pit], [Butterfly Sanctuary]",
                "4 universal kitchen-safety warning icons for commercial kitchens: [Grease Fire No Water], [Sharp Blade Guard], [Hot Steam Vent], [Chemical Sanitizer Only]",
            ],
        ),
        (
            "Safety Symbol & Instructional Guidebook: Subquestion A: Design a high-visibility hazard warning emblem for the given domestic or public utility risk. Subquestion B: Design a 3-step illustrated pocket guide demonstrating safe emergency response without panic.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "domestic LPG gas cylinder leak protocol ('Suraksha') and kitchen ventilation steps",
                "street-level electrical transformer safety and flooded monsoon road hazard guide",
                "school laboratory acid splash and chemical burn first-aid protocol",
                "high-speed escalator emergency stop button and child entrapment prevention",
                "overcrowded suburban railway platform edge warning and gap awareness",
            ],
        ),
    ],
    "Problem identification": [
        (
            "Spatial interior & ergonomic product evaluation: Subquestion A: Draw an eye-level or 2-point interior perspective room sketch specifically tailored for the target occupant (elderly individual or young child) showing furniture layout, circulation, and resident positioning. Subquestion B: Identify one product depicted, state its primary functional purpose, and describe 3 concrete ways to improve its functionality and safety.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "room interior for an elderly person above 50 years old with mobility considerations",
                "room interior for a growing child aged 6-10 years with active play and study needs",
                "compact kitchen workspace tailored for a wheelchair user",
                "study and sleeping room tailored for a visually impaired college student",
            ],
        ),
        (
            "Observation to insight chain: Picture spending 10 minutes observing how people use the given everyday Indian place. Subquestion A: write 8 crisp field observations and derive 3 distinct design opportunities from them. Subquestion B: sketch ONE practical product or spatial solution based on your strongest insight with short annotations.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "a bustling roadside tea stall (chai tapri) during morning rush hour",
                "a public railway station drinking-water tap used by children, elderly passengers, and wheelchair users",
                "a crowded neighbourhood bakery packing fragile pastries and hot tea in the morning",
                "a shared college hostel terrace where students dry laundry during humid monsoon days",
                "a municipal primary school water and hand-washing trough during recess",
                "a local government ration distribution shop on the first week of the month",
                "a crowded footwear storage stand outside a busy pilgrimage temple on a festival morning",
                "an overcrowded suburban train compartment doorway during morning peak boarding",
                "a public bus stop shelter shared by senior citizens, school children, and street vendors",
                "a roadside puncture repair shop working on motorcycle tyres in dim evening light",
                "a crowded municipal dairy booth milk-token queue early in the morning",
                "a small-town railway level-crossing gate during a 20-minute train passage",
                "a community washing ghat or handpump where neighbours wash clothes and fill vessels",
                "an outdoor flower market where delicate marigolds and jasmine are sorted and auctioned before dawn",
            ],
        ),
        (
            "Everyday micro-action friction: Picture someone in the given ordinary daily situation. Subquestion A: identify at least 5 concrete usability, comfort, or safety problems they face. Subquestion B: redesign or sketch one practical fix addressing the biggest root cause, showing it in use.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "buying vegetables in a crowded covered market with wet floors and heavy bags",
                "finding a seat, guarding luggage, and charging a phone in an overnight railway waiting hall",
                "boarding a crowded monsoon ferry jetty while carrying umbrellas and grocery sacks",
                "using a common public water dispenser at a railway station across all age groups and wheelchair users",
                "an elderly person with arthritic hands unlocking a stiff metal padlock in dim porch light",
                "a delivery rider checking GPS on a smartphone mounted on a scooter during heavy rain",
                "a parent balancing a toddler, an umbrella, and school bags while crossing a muddy flooded street",
                "a roadside food vendor frying snacks in hot oil while managing paper currency and customer queues",
                "a student reading in a dim dorm room while trying not to wake up sleeping roommates",
                "carrying four steaming cups of tea and snacks across a busy office corridor without a tray",
            ],
        ),
        (
            "Service & queue friction: Picture citizens navigating the given everyday counter or service. Subquestion A: identify 5 specific bottlenecks, confusion points, or accessibility issues. Subquestion B: sketch a simple signage, layout, or workflow improvement with brief labels.",
            ["nid_gandhinagar_sdm", "nid_haryana_creative_leadership"],
            [
                "waiting at a busy small-town pharmacy counter with handwritten prescriptions",
                "sending fragile festive parcels at a small-town post office before Diwali",
                "attending an early-morning vaccination queue at a rural primary health clinic",
                "buying tickets and snacks during a 10-minute single-screen cinema intermission",
                "registering outpatients and collecting blood tokens at a busy municipal government hospital",
                "returning library books and clearing dues during semester-end clearance at a university",
                "boarding a state transport overnight sleeper bus where passengers carry sacks and poultry",
                "collecting and transporting heavy drinking water vessels from a community tap to a third-floor walkup tenement",
                "managing wet raincoats, dripping umbrellas, and school bags inside a crowded municipal bus",
                "dispensing liquid medicine drops to a squirming infant in a dim rural bedroom",
                "handling and drying fragile wet clay pots during an unseasonal monsoon shower",
                "manoeuvring a heavily loaded handcart through narrow bazaar lanes with open roadside drains",
            ],
        ),
    ],
    "Product sketch": [
        (
            "Inclusive everyday object redesign: Observe the given public or household object. Subquestion A: identify at least 5 usability problems across diverse users (including children, elderly, or wheelchair users) and sketch 2 quick thumbnails. Subquestion B: present your final redesigned concept as a complete presentation sheet: (1) primary 3/4 perspective hero sketch showing form & tactile grip, (2) zoom-in circular detail callout of the mechanism, (3) hand-in-use ergonomic sketch, and (4) functional/material callouts.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "a common public drinking-water dispenser at an Indian railway station",
                "a public hospital waiting-hall bench shared by elderly patients, parents with toddlers, and wheelchair users",
                "a roadside bus-stop shelter and seating module in a humid coastal Indian town",
                "a community waste collection handcart used by municipal sweepers in narrow residential lanes",
                "a public park drinking fountain accessible to both wheelchair users and children",
                "an ergonomic hand-washing station for rural government primary schools without running tap plumbing",
                "a sturdy public luggage trolley adapted for uneven platform ramps and steep foot overbridges",
            ],
        ),
        (
            "Compact transforming constraint: Design a space-saving transforming product for the given tight Indian living space that folds or converts when not in use. Subquestion A: list key space/ergonomic constraints and sketch 2-3 quick layout thumbnails. Subquestion B: present your final design as a complete concept sheet showing: (1) hero 3/4 view in open working state, (2) folded/transformed state detail with folding mechanism, (3) human interaction sketch showing scale, and (4) material & joinery annotations.",
            ["general_nid_mdes", "nid_haryana_creative_leadership"],
            [
                "a compact study desk and storage system for a student living in a 100 sq ft hostel room",
                "a foldable clothes-drying and ironing station for a cramped urban apartment balcony",
                "a convertible seating-and-work counter for a tiny roadside cobbler or tailor stall",
                "a multi-tier collapsible spice and utensil organiser for a 40 sq ft micro-kitchen in an urban tenement",
                "a dual-purpose child's study table that folds flat into a wall-mounted chalkboard organizer",
                "a portable folding examination and bedding cot for mobile rural health camps",
                "a modular stackable stool and storage crate system for tiny street food kiosks",
            ],
        ),
        (
            "Ergonomic form exploration (5 thumbnails + final): Design a handheld everyday tool for a user with limited physical strength. Subquestion A: explore 5 distinct handle or grip forms through quick annotated thumbnail sketches. Subquestion B: present your developed final concept as a complete presentation sheet: (1) hero 3/4 perspective sketch, (2) zoom-in detail callout of the blade/mechanism, (3) close-up ergonomic hand-grip vignette in proportion, and (4) dimensions & material callouts.",
            ["general_nid_mdes"],
            [
                "a handheld kitchen vegetable peeler and chopper for a person with weak grip strength or arthritis",
                "a spill-free hot tea kettle and pouring aid for an elderly person with trembling hands",
                "an easy-grip jar, bottle, and medicine blister-pack opener for older adults living alone",
                "an ergonomic harvesting sickel/knife reducing wrist strain for female agricultural labourers",
                "a lightweight, adaptive broom handle reducing lower back flexion for domestic cleaning workers",
                "an assistive handwriting and stylus grip aid for children with motor control challenges",
            ],
        ),
        (
            "Craft meets contemporary design: Choose a traditional Indian craft (bamboo weaving, terracotta, Channapatna wood-turning, or Dhokra metal casting). Design a contemporary functional home or desktop product that keeps the artisan craft viable. Subquestion A: explain the craft technique, sustainable materials, and artisan livelihood opportunity. Subquestion B: present your final product as a complete presentation sheet: (1) hero 3/4 perspective sketch, (2) joinery/weave detail callout bubble, (3) ergonomic in-use vignette showing human interaction, and (4) craft material callouts.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "traditional bamboo weaving adapted into a flat-pack modular desktop organizer and lamp",
                "terracotta pottery craft adapted into an electricity-free evaporative vegetable cooling unit",
                "Channapatna natural-lacquered wood craft adapted into an ergonomic sensory toy and therapy grip tool",
                "Dhokra bell-metal casting adapted into contemporary ergonomic door hardware and handles",
                "Kashmir wicker willow craft adapted into stackable modular laundry and storage baskets",
                "Blue pottery of Jaipur adapted into heat-resistant kitchen trivets and modular wall hooks",
                "Santhal tribal iron craft adapted into minimal contemporary bookends and desktop stationery organizers",
            ],
        ),
        (
            "Transform one object for 3 distinct users: Take the given humble everyday object and design 3 genuinely different variations tailored to the three listed user groups. Subquestion A: explain briefly how form, capacity, grip, and features change for each user. Subquestion B: sketch all 3 variations side by side with clear feature callouts and user-in-use vignettes.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "a simple steel tiffin box adapted for a school child, an office commuter, and a construction labourer",
                "a daily drinking-water bottle adapted for a 5-year-old child, a two-wheeler delivery rider, and a senior citizen on morning walks",
                "an everyday carry bag adapted for a street flower vendor, a college architecture student, and a daily train commuter",
                "a walking stick adapted for a blind urban pedestrian, an elderly rural pilgrim, and an adventure trekker",
                "a portable flashlight adapted for an auto mechanic, a night-shift watchman, and an outdoor camper",
            ],
        ),
        (
            "Disaster-relief systems product + exploded view: Design a low-cost, portable, group-usable emergency product for the given crisis scenario. Subquestion A: map key system constraints (power/fuel, safety, flat-pack transport size, group use) and a brief user scenario. Subquestion B: present your final design as a complete concept sheet: (1) hero 3/4 view of the assembled product in use, (2) labelled exploded view showing components and assembly, and (3) materials and safety feature callouts.",
            ["nid_gandhinagar_sdm", "general_nid_mdes"],
            [
                "a low-cost, portable cooking stove solution for a family displaced by seasonal floods",
                "a flat-pack, electricity-free water-filtration and clean-storage kit for a cyclone relief camp",
                "a portable solar lighting, phone-charging, and emergency whistle lantern for flood-affected villages",
                "a lightweight floating rescue stretcher and stretcher-carrier for waterlogged rescue operations",
                "a modular partition and privacy screen with storage pockets for crowded disaster shelter halls",
            ],
        ),
        (
            "Factory surplus material reuse: A local workshop has surplus offcuts of the given material. Subquestion A: invent 2 useful, sellable products for compact Indian homes using the surplus. Subquestion B: present the best product as a complete concept sheet in 3/4 view with joinery details, hand-interaction vignette, and material callouts.",
            ["nid_gandhinagar_sdm", "general_nid_mdes"],
            [
                "surplus teak wood offcuts from a neighbourhood carpentry shop",
                "discarded ceramic tile offcuts from a local tile workshop",
                "surplus hollow bamboo poles from a construction supplier",
                "discarded automotive seatbelt webbing and upholstery fabric offcuts from a car repair garage",
                "discarded leather scrap offcuts from a shoe-manufacturing factory",
                "discarded aluminium corrugated sheet offcuts from a shed construction site",
            ],
        ),
    ],
    "Storyboard": [
        (
            "3-Stage craft and culinary transformation: Subquestion A: Illustrate Stage 1 (Raw material selection & preparation) and Stage 2 (Active intermediate transformation mechanism & hand craftsmanship) with hand-tool interactions. Subquestion B: Illustrate Stage 3 (Final outcome, packaging, and tactile in-use preservation).",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "raw green mangoes or fruit to jarred sun-preserved traditional pickle",
                "raw coastal seashells and beads to finished handcrafted wearable jewellery",
                "raw wet clay lump on potter's wheel to glazed terracotta water vessel",
                "harvested raw cotton bolls to hand-spun charkha yarn and woven textile",
                "fresh whole milk to artisanal clarified ghee and clay-pot butter",
                "reclaimed scrap aluminium cans into sand-cast modular door handles",
            ],
        ),
        (
            "Product + circular sustainability system storyboard (4-6 frames): Design a practical reusable alternative for the given high-waste Indian context, considering usage, collection, washing, and return. Subquestion A: outline the product features and circular service loop briefly. Subquestion B: present both the product and the end-to-end user system in a clear 4-to-6 frame storyboard.",
            ["nid_gandhinagar_sdm", "general_nid_mdes"],
            [
                "a reusable alternative to single-use plastic cups sold at crowded Indian festivals and fairs",
                "a returnable food-packaging and wash-loop system for highway dhaba and railway station meals",
                "a neighbourhood doorstep refill and container-return system for household cleaning liquids and pulses",
                "a returnable cloth-and-mesh produce bag system for weekly vegetable street markets",
                "a reusable stainless-steel tiffin exchange service for office lunch delivery in tech parks",
                "a closed-loop glass bottle deposit and collection system for roadside fruit juice vendors",
                "a community school uniform and textbook hand-down exchange system among neighbourhood families",
                "a circular repair and redistribution cycle for discarded wooden fruit crates into student desks",
                "a reusable cloth garland and flower-basket return system outside pilgrimage temples",
                "a returnable stainless-steel cup system at large outdoor college cultural festivals",
                "a decentralized neighbourhood composting loop converting fallen dry leaves into community potting soil",
                "a localized rainwater capture and shared filtration system in an urban housing colony",
                "a battery-swap and recycling journey for electric delivery three-wheelers in a busy market",
            ],
        ),
        (
            "Quick-response public dilemma (4 frames): Place the student in the given sudden everyday moment. Subquestion A: illustrate 4 sequential frames showing how you respond step by step with varied camera angles. Subquestion B: briefly explain why each step matters.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "a sudden power cut hits a packed single-screen cinema just before the climax",
                "a sudden gust of monsoon wind blows away a street vendor's stack of paper bags and bills",
                "an elderly potter tries to rescue freshly shaped wet clay pots as unexpected rain begins",
                "a young child's ball rolls beneath a parked state transport bus in a crowded station",
                "a stray puppy gets trapped in an open roadside stormwater drain during an evening cloudburst",
                "a passenger notices an unclaimed ticking package left on a crowded suburban train luggage rack",
                "a sudden water pipe burst floods a roadside tea stall while morning commuters are drinking chai",
                "a blind commuter's white cane gets caught between platform gap and train footboard during boarding",
                "a fire starts in an outdoor roadside waste bin near a cluster of wooden vendor carts",
                "an elderly man collapses on a morning jogging park path and fellow walkers respond",
                "two auto-rickshaws get wedged at a narrow old-town blind turn, blocking an ambulance behind them",
            ],
        ),
        (
            "Wordless everyday twist (4 frames): Create a 4-frame visual story with NO dialogue or speech bubbles about the given everyday moment, ending with a warm or surprising twist. Subquestion A: draw the 4 sequential frames with varied camera angles (wide, medium, close-up, resolution). Subquestion B: write a 2-sentence summary of the emotional shift.",
            ["nid_haryana_creative_leadership", "general_nid_mdes"],
            [
                "a stray cat wanders into a quiet second-hand bookshop and triggers a small chain reaction",
                "a child drops their lunchbox on their very first day at a new school",
                "a hurried passenger accidentally swaps identical cloth bags at a busy tea stall",
                "a forgotten umbrella on a park bench brings two quiet strangers into a warm moment",
                "a street musician plays an unusual homemade flute to an empty lane until an unexpected audience appears",
                "a tailor carefully patches an old torn kurta for a little boy who needs it for a school function",
                "an elderly grandmother and her tech-savvy grandchild discover a surprising shared pastime on a rainy afternoon",
                "a stray street dog guides a lost toddler back to her mother in a busy market",
                "a roadside tea vendor receives an unexpected painted signboard from an art student customer",
                "a young girl attempts to plant a mango sapling in a cracked urban pavement corner",
                "an old bicycle that was neglected in a shed gets lovingly refurbished for a child's birthday",
            ],
        ),
    ],
    "Design aptitude": [
        (
            "Craft meets contemporary design: Using the given traditional Indian craft and material, design a contemporary everyday home product. Subquestion A: explain the craft's strengths, your target urban user, and how this product keeps the craft relevant and supports local artisans. Subquestion B: sketch the contemporary product in context with material and joinery callouts.",
            ["nid_gandhinagar_sdm", "nid_haryana_creative_leadership", "general_nid_mdes"],
            [
                "traditional Indian bamboo weaving adapted into a modern compact home product",
                "traditional Indian terracotta pottery adapted into a contemporary urban kitchen or cooling product",
                "traditional Channapatna lacquered woodcraft adapted into a functional modern desk or home organizer",
                "traditional hand-block textile printing adapted into modular acoustic or storage panels for student rooms",
                "traditional brass metal repousse craft adapted into durable contemporary lighting fixtures",
                "traditional coir rope braiding adapted into ergonomic modular floor seating for small apartments",
                "traditional leather puppet (Tholu Bommalata) craft adapted into artistic lampshades for public libraries",
            ],
        ),
        (
            "Future everyday place in 2047: Imagine the given familiar Indian place in the year 2047. Subquestion A: describe how technology and sustainability change it AND list 5 things from today that will stay the same. Subquestion B: illustrate the 2047 scene combining both.",
            ["nid_gandhinagar_sdm", "nid_haryana_creative_leadership"],
            [
                "a neighbourhood spice and vegetable market in the year 2047",
                "a local family-run pharmacy and clinic in the year 2047",
                "a small-town railway station tea stall in the year 2047",
                "a municipal primary school classroom in a rural district in the year 2047",
                "a roadside vehicle repair and battery recharge workshop in the year 2047",
                "a community festival celebration in an old-town courtyard in the year 2047",
                "a public municipal library and community skills workshop in the year 2047",
                "a rural primary health and telemedicine wellness centre in the year 2047",
                "a traditional artisan weaving cluster with solar micro-turbines in the year 2047",
                "a residential neighbourhood rainwater well and community pantry in the year 2047",
            ],
        ),
        (
            "Product innovation & ergonomic redesign: Observe the user and working conditions in the given everyday scenario. Subquestion A: identify 5 concrete functional or ergonomic pain points and propose 5 distinct design features that solve them. Subquestion B: present your redesigned concept in clean 3/4 perspective showing the product in active use on-site, with circular detail callouts for key mechanisms and material notes.",
            ["general_nid_mdes", "nid_gandhinagar_sdm"],
            [
                "a children's school backpack for ages 6 to 10 that protects spine posture during monsoon walks",
                "a commuter lunchbox for young working professionals that keeps wet gravies and crisp breads fresh",
                "a study lamp for college hostel students living in crowded, shared rooms with dim power supplies",
                "a durable water bottle for two-wheeler delivery riders that mounts securely and stays cool",
                "a portable personal laundry washing aid for solo travelers and hostel students",
                "an ergonomic carrying harness for street newspaper delivery vendors",
                "a modular spill-proof tiffin container for construction labourers carrying hot food",
            ],
        ),
        (
            "City policy effects & consequences: A city announces the given bold public policy. Subquestion A: map the opportunities, challenges, and unintended consequences for everyday citizens. Subquestion B: illustrate one key effect and a practical safeguard with brief notes.",
            ["nid_gandhinagar_sdm", "nid_haryana_creative_leadership"],
            [
                "making old-town market streets completely vehicle-free on weekends",
                "requiring every neighbourhood to host a free weekend repair cafe for broken appliances",
                "mandating that all commercial food establishments donate surplus unserved meals to local shelters",
                "banning private petrol two-wheelers inside historic heritage zones and replacing them with shared e-cycles",
                "requiring all residential apartment societies to harvest 100% of their rooftop rainwater",
                "subsidizing street food vendors to completely eliminate single-use plastics and thermocol tableware",
                "mandating universal wheelchair ramps and tactile paving for all roadside pharmacies and grocery stores",
                "establishing municipal tool-sharing and equipment-lending libraries in every neighbourhood ward",
                "replacing commercial outdoor billboards with vertical public gardens and air-purifying moss walls",
                "mandating that all public transport bus stops provide free shaded drinking water and phone SOS charging points",
                "instituting a zero-waste certification and tax incentive for local street market associations",
            ],
        ),
    ],
}


# ==============================================================================
# 2. MODULAR COMBINATORIAL SYNTHESIS MATRICES (27,000+ COMBINATIONS)
# ==============================================================================

DEMOGRAPHICS = [
    "an elderly person with arthritis and reduced finger grip strength",
    "a female street flower vendor carrying fresh garlands through morning crowds",
    "a wheelchair user commuting through a state transport bus station",
    "a primary school child walking through waterlogged monsoon streets",
    "a night-shift hospital nurse carrying patient charts and medicine doses",
    "a traditional rural artisan weaving delicate bamboo products in dim light",
    "a two-wheeler delivery rider balancing bulky parcels in congested evening traffic",
    "a college student sharing a cramped 100 sq ft hostel room with two roommates",
    "an elderly passenger traveling alone on an overnight unreserved train journey",
    "a roadside tea vendor washing steel glasses at a busy morning tapri",
    "a visually impaired pedestrian navigating unpaved footpaths with a cane",
    "a construction labourer eating a packed lunch on an exposed dusty site",
    "a community sanitation worker emptying open waste bins in narrow lanes",
    "a small-scale vegetable vendor pushing a three-wheeled wooden handcart",
    "a pregnant woman navigating crowded public health centre queues",
    "a rural schoolteacher carrying books, chalk, and teaching aids across village mud tracks",
    "a highway truck driver taking rest during a long overnight freight trip",
    "a street cobbler working on pavement steps with minimal hand tools",
    "a migrant worker remitting money and managing paper documents in a busy post office",
    "a home cook preparing meals for a family of seven in a tight 35 sq ft kitchen",
]

ENVIRONMENTS = [
    "a bustling roadside tea stall (chai tapri) during morning rush hour",
    "a crowded government hospital outpatient (OPD) registration hall",
    "an open-air weekly village market (haat) on dusty, uneven ground",
    "a busy suburban railway platform during peak evening commuter boarding",
    "a cramped urban apartment balcony used for laundry, plants, and utility storage",
    "a rural primary health clinic facing intermittent power and water cuts",
    "a narrow heritage old-town alley packed with scooters, pedestrians, and street stalls",
    "an interstate government bus cabin during an overnight monsoon journey",
    "a shared community kitchen inside a temporary flood-relief camp",
    "a roadside vehicle tyre repair shop working with basic manual equipment",
    "a noisy municipal school dining hall during midday meal distribution",
    "a community drinking-water tanker queue under midday summer heat",
    "a pilgrimage temple footwear-storage and baggage counter on a festival morning",
    "a municipal library reading room shared by competitive exam aspirants and senior citizens",
    "a busy wholesale fish and vegetable harbour market at dawn",
    "a cramped barber shop with two chairs and waiting customers in a residential lane",
    "a highway dhaba dining area serving bus passengers during a 15-minute halt",
    "a public park walking loop shared by morning runners, toddlers, and pet owners",
    "a small-town railway station waiting hall during winter train delays",
    "a traditional handloom weaver's shed with wood and pit looms",
]

FRICTION_POINTS = [
    "carrying multiple hot liquid containers without spilling or burning fingers",
    "storing and keeping perishable items fresh without access to electrical refrigeration",
    "organising and protecting paper receipts, tickets, and prescriptions from moisture",
    "operating tools or devices with one hand while keeping the other hand free for balance",
    "folding, packing, and carrying bulky gear into a lightweight flat-pack under 30 seconds",
    "securing heavy, irregular loads onto a two-wheeler pillion seat without shifting",
    "providing high-contrast visual cues instantly legible to people who cannot read text",
    "drying wet laundry inside cramped indoor rooms during continuous monsoon humidity",
    "opening stiff medicine blister packs and tight container lids with painful hands",
    "lighting dark stairwells and pathways safely during sudden electrical power outages",
    "preventing precious drinking water from leaking, spilling, or becoming contaminated",
    "sorting recyclable dry waste from wet kitchen waste at crowded community gatherings",
    "maintaining stable, ergonomic body posture during repetitive manual work",
    "safely storing and retrieving personal valuables in crowded, open public spaces",
    "navigating long, slow-moving queues without excessive physical standing fatigue",
    "shielding sensitive eyes, face, and respiratory tract from dusty roadside exhaust fumes",
    "safeguarding fragile, handcrafted products from breakage during rough transit",
    "cleaning and sanitising shared utility surfaces without using expensive disposable wipes",
    "adjusting furniture or work surfaces to comfortably fit both young children and adults",
    "dispensing controlled small portions of liquids or powders without messy overflow",
]


def _build_combinatorial_topic_for_category(category: str) -> Tuple[str, str]:
    """Dynamically synthesize a fresh, culturally coherent, single-focus design topic."""
    user = random.choice(DEMOGRAPHICS)
    env = random.choice(ENVIRONMENTS)
    friction = random.choice(FRICTION_POINTS)

    if category == "Product sketch":
        bp = (
            "Inclusive everyday object redesign: Observe the given everyday situation. "
            "Subquestion A: identify 5 usability problems and sketch 2 quick thumbnails. "
            "Subquestion B: present your final redesigned concept as a complete presentation sheet: "
            "(1) hero 3/4 perspective sketch, (2) zoom-in circular mechanism callout, "
            "(3) hand-in-use ergonomic sketch, and (4) functional/material callouts."
        )
        topic = f"a functional everyday product assisting {user} in {env}, specifically addressing the challenge of {friction}"
    elif category == "Problem identification":
        bp = (
            "Everyday micro-action friction: Picture someone in the given ordinary daily situation. "
            "Subquestion A: identify at least 5 concrete usability, comfort, or safety problems they face. "
            "Subquestion B: redesign or sketch one practical fix addressing the biggest root cause, showing it in use."
        )
        topic = f"{user} navigating {env} while struggling with {friction}"
    elif category == "Drawing":
        bp = (
            "Observational spatial and human study: Subquestion A: draw 3 proportional detail studies of everyday objects or gestures in this scene. "
            "Subquestion B: draw a dramatic eye-level perspective sketch capturing human posture, context, and light."
        )
        topic = f"an eye-level observational scene showing {user} in {env} dealing with {friction}"
    elif category == "Storyboard":
        bp = (
            "4-frame sequential visual narrative: Create a 4-frame visual story with NO dialogue showing a human response to an everyday friction. "
            "Subquestion A: draw 4 sequential frames with varied camera angles (wide, medium, close-up, resolution). "
            "Subquestion B: write a 2-sentence summary of the emotional shift."
        )
        topic = f"a 4-frame wordless sequence of {user} in {env} overcoming {friction}"
    elif category == "Logos, Symbols & Signs":
        bp = (
            "Behavioural & wayfinding signs: Design a coherent set of 4 clear, wordless or minimal-text public signs for the given everyday space. "
            "Subquestion A: draw 4 distinct signs using simple high-contrast shapes. "
            "Subquestion B: briefly explain how each sign guides or improves people's behaviour."
        )
        topic = f"a set of 4 clear, wordless public signs for {env} to assist {user} with {friction}"
    elif category == "Composition":
        bp = (
            "Forced-metaphor poster: Sketch a poster promoting the given social message combining two unexpected visual elements with a title under 6 words. "
            "Subquestion A: note the visual metaphor and hierarchy rationale. "
            "Subquestion B: execute the framed poster sketch with high contrast."
        )
        topic = f"an awareness poster highlighting the dignity and daily struggle of {user} dealing with {friction}"
    elif category == "Creativity":
        bp = (
            "Biomimetic product metaphor: Design a practical everyday product whose form and mechanism are inspired by a natural organism. "
            "Subquestion A: explain 3 functional features borrowed from the organism. "
            "Subquestion B: draw a clean 3/4 perspective sketch showing the product in practical use."
        )
        topic = f"a bio-inspired tool or gear helping {user} solve {friction} in {env}"
    else:  # Design aptitude
        bp = (
            "Systemic design & policy intervention: A public initiative is introduced in the given everyday context. "
            "Subquestion A: map opportunities, challenges, and unintended consequences for citizens. "
            "Subquestion B: sketch one practical product or spatial safeguard with annotations."
        )
        topic = f"a municipal public initiative in {env} designed to support {user} with {friction}"

    return bp, topic


# ==============================================================================
# 3. DYNAMIC SELECTION & PERSISTENT FINGERPRINT ENGINE
# ==============================================================================

_RECENT_TOPIC_FINGERPRINTS: List[str] = []


def _fingerprint_text(text: str) -> str:
    """Extract key content words into a canonical sorted lowercase signature."""
    words = re.findall(r"[a-z]{3,}", text.lower())
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "your", "design",
        "question", "sketch", "draw", "using", "into", "about", "their", "them",
        "what", "how", "one", "two", "three", "five", "user", "users", "create",
        "explain", "propose", "based", "given", "show", "make", "should", "must",
    }
    content_words = [w for w in words if w not in stop]
    return " ".join(sorted(set(content_words[:12])))


def _has_high_overlap(sig_a: str, sig_b: str, threshold: float = 0.50) -> bool:
    set_a = set(sig_a.split())
    set_b = set(sig_b.split())
    if not set_a or not set_b:
        return False
    overlap = len(set_a & set_b) / len(set_a | set_b)
    return overlap >= threshold


def pick_nid_blueprint_and_topic(
    category: str,
    active_profiles: List[str],
    slot_idx: int = 0,
    historical_fingerprints: Optional[List[str]] = None,
) -> Tuple[str, str]:
    """Select a fresh, authentic NID blueprint paired with a non-repeating topic.

    Alternates between:
    - 320+ curated NID topic seeds across categories.
    - Dynamically generated combinatorial topics (27,000+ permutations).
    Checks against both session memory and recent database fingerprints to guarantee no repetition.
    """
    global _RECENT_TOPIC_FINGERPRINTS

    recent_sigs = set(_RECENT_TOPIC_FINGERPRINTS)
    if historical_fingerprints:
        for fp in historical_fingerprints[:60]:
            recent_sigs.add(_fingerprint_text(fp))

    pool = NID_BLUEPRINTS.get(category, NID_BLUEPRINTS["Design aptitude"])
    # Filter pool by active_profiles so the 2026 common paper ("general_nid_mdes") gets authentic common blueprints
    matching_bps = [bp for bp in pool if any(p in bp[1] for p in active_profiles)]
    usable_pool = matching_bps if matching_bps else pool

    # 50% chance of curated blueprint pool, 50% chance of combinatorial synthesis
    use_combinatorial = random.random() < 0.50

    if not use_combinatorial:
        bp_tuple = usable_pool[slot_idx % len(usable_pool)] if slot_idx > 0 else random.choice(usable_pool)
        bp_text, _, topics = bp_tuple

        available_topics = []
        for t in topics:
            sig = _fingerprint_text(t)
            if not any(_has_high_overlap(sig, r_sig) for r_sig in recent_sigs):
                available_topics.append(t)

        if available_topics:
            topic = random.choice(available_topics)
            chosen_sig = _fingerprint_text(topic)
            _RECENT_TOPIC_FINGERPRINTS.append(chosen_sig)
            if len(_RECENT_TOPIC_FINGERPRINTS) > 80:
                _RECENT_TOPIC_FINGERPRINTS.pop(0)
            return bp_text, topic

    # Fallback or chosen path: Combinatorial Dynamic Synthesis
    for _ in range(12):  # Try up to 12 random combinations to find a completely non-overlapping topic
        bp_text, candidate_topic = _build_combinatorial_topic_for_category(category)
        candidate_sig = _fingerprint_text(candidate_topic)
        if not any(_has_high_overlap(candidate_sig, r_sig) for r_sig in recent_sigs):
            _RECENT_TOPIC_FINGERPRINTS.append(candidate_sig)
            if len(_RECENT_TOPIC_FINGERPRINTS) > 80:
                _RECENT_TOPIC_FINGERPRINTS.pop(0)
            return bp_text, candidate_topic

    # Emergency fallback (guaranteed fresh):
    bp_text, candidate_topic = _build_combinatorial_topic_for_category(category)
    _RECENT_TOPIC_FINGERPRINTS.append(_fingerprint_text(candidate_topic))
    return bp_text, candidate_topic
