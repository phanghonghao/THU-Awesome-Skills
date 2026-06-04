# Category Rules

This file defines the category-level extraction and rendering rules used by `scripts/paper_to_onepage_html.py`.

The intended pipeline is:

1. Read PDF with PyMuPDF (`pdf-reader` style)
2. Recover metadata from arXiv or first-page PDF text
3. Classify the paper into a category
4. Apply category-specific extraction rules
5. Render a one-page HTML summary

## Design Principle

Do not treat all papers as generic "method + results + metrics" documents.

Different research categories need different:

- extraction targets
- preferred sections
- evaluation signals
- risk interpretation
- one-page card labels

## Categories

### 1. Locomotion

Typical examples:

- BeyondMimic
- humanoid control papers
- motion tracking / motion imitation papers

Classification signals:

- Title contains `BeyondMimic`
- Text contains terms such as:
  - `humanoid`
  - `locomotion`
  - `motion tracking`
  - `guided diffusion`
  - `cartwheels`
  - `spin-kicks`

Primary extraction targets:

- motion source / demonstration source
- tracking objective
- controller or policy structure
- reward or regularization terms
- robustness outside nominal trajectories
- skill composition evidence
- sim-to-real / deployment signal

Preferred sections / keywords:

- `method`, `methods`, `approach`
- `results`, `experiments`, `evaluation`
- `discussion`, `limitations`
- fallback keywords:
  - `motion tracking`
  - `policy`
  - `reward`
  - `controller`
  - `human-like`
  - `walking`
  - `running`
  - `skills`
  - `compose`

One-page card labels:

- `Motion Control Summary`
- `Control / Training Highlights`
- `Locomotion Results`
- `Deployment / Generalization Risks`
- `Locomotion Reading Lens`

### 2. World Model

Typical examples:

- DreamDojo
- robot world model papers

Classification signals:

- Title contains `DreamDojo`
- Title contains `robot world model`
- Text contains:
  - `world model`
  - `latent action`
  - `continuous latent actions`
  - `world model pretraining`

Primary extraction targets:

- data scale
- action representation
- pretraining setup
- post-training / adaptation setup
- control interface
- transfer/generalization setup
- data coverage limits

Preferred sections / keywords:

- `method`, `methods`, `approach`
- `results`, `experiments`, `evaluation`
- fallback keywords:
  - `latent action`
  - `pretrain`
  - `continuous actions`
  - `video prediction`
  - `transfer`
  - `generalization`
  - `dexterous`
  - `post-training`

One-page card labels:

- `World Model Summary`
- `Representation / Training Highlights`
- `Data / Transfer Signals`
- `Coverage / Control Risks`
- `World Model Reading Lens`

Structured metrics preference:

- `Data Scale`
- `Control Rate`

### 3. World Action Model

Typical examples:

- DreamZero
- WAM papers

Classification signals:

- Title contains `DreamZero`
- Title contains `World Action Models are Zero-shot Policies`
- Text contains:
  - `world action model`
  - `world action models`
  - `zero-shot policies`

Primary extraction targets:

- joint video + action modeling
- policy interpretation
- zero-shot transfer
- few-shot adaptation
- cross-embodiment transfer
- closed-loop inference
- real-time deployment

Preferred sections / keywords:

- `method`, `methods`, `approach`
- `results`, `experiments`, `evaluation`
- fallback keywords:
  - `jointly predicting video and action`
  - `cross-embodiment`
  - `post-training`
  - `zero-shot`
  - `few-shot`
  - `unseen tasks`
  - `unseen environments`
  - `closed-loop`

One-page card labels:

- `World Action Model Summary`
- `Action Modeling Highlights`
- `Zero-shot / Transfer Results`
- `Transfer / Embodiment Risks`
- `WAM Reading Lens`

Structured metrics preference:

- `Data Scale`
- `Control Rate`

### 4. Vision Action Model

Typical examples:

- VAM / VLA-like policy papers where perception-action coupling is primary

Classification signals:

- Text contains:
  - `vision action model`
  - `vision-language-action`
  - `vla`
  - `vision encoder`

Primary extraction targets:

- visual input stack
- encoder / backbone
- action head
- conditioning inputs
- inference latency
- real-world success rate
- perception failure modes

Preferred sections / keywords:

- `vision encoder`
- `policy head`
- `action tokens`
- `real-world`
- `latency`
- `success rate`
- `manipulation`
- `occlusion`

One-page card labels:

- `Vision Action Model Summary`
- `Perception / Action Highlights`
- `Execution Results`
- `Perception / Latency Risks`
- `VAM Reading Lens`

### 5. Multimodal Interpretation

Typical examples:

- MIMIC
- VLM interpretation / inversion papers

Classification signals:

- Title contains `MIMIC:`
- Text contains:
  - `multimodal inversion`
  - `vlm`
  - `model interpretation`
  - `conceptualization`

Primary extraction targets:

- inversion mechanism
- feature alignment
- regularization design
- qualitative vs quantitative interpretation evidence
- semantic realism limits

Preferred sections / keywords:

- `inversion`
- `feature alignment`
- `regularizers`
- `semantic realism`
- `visual quality`
- `semantic metrics`

One-page card labels:

- `Interpretation Summary`
- `Inversion Highlights`
- `Interpretability Results`
- `Interpretation Risks`
- `Interpretation Reading Lens`

### 6. General

Fallback category when no category-specific rule matches.

Fallback card labels:

- `Core Summary`
- `Method Highlights`
- `Benchmarks & Results`
- `Limitations & Risks`
- `Reading Lens`

## Extraction Rules

### Metadata

Priority order:

1. arXiv metadata fetched from inferred arXiv id
2. first-page PDF title
3. first-page PDF author block
4. first-page abstract block
5. fallback to filename

### Section Extraction

Use heading-aware extraction first:

- `find_heading_block(...)`

Fallback to keyword-window extraction:

- `find_section(...)`

Fallback to sentence bulletization:

- `bulletize(...)`

### Metrics

Generic metrics extraction is only a fallback.

When category-specific structured metrics are available, prefer them:

- `Data Scale`
- `Control Rate`

Known limitation:

- regex metrics extraction may still capture irrelevant numeric artifacts in some PDFs

## Rendering Rules

All one-page outputs share the same outer HTML layout, but the card labels and extraction sources change by category.

The four main content zones are:

1. summary
2. method / representation / control highlights
3. results / transfer / execution signals
4. risks + reading lens

## Current Limitations

- classification is still heuristic, not model-based
- metrics extraction is not fully trustworthy for all categories
- some PDFs have noisy first-page text ordering
- method extraction can still degrade when the paper uses unusual section titles

## Recommended Next Extensions

1. Add per-category metric extractors instead of generic regex fallback
2. Add per-category section alias dictionaries
3. Add optional per-paper override config
4. Add a small validation report showing:
   - inferred category
   - arXiv id
   - metadata source
   - which extraction fallbacks were used
