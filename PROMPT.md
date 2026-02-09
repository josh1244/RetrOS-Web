# RetrOS-Web Design Document

## Design Philosophy

RetrOS-Web should feel authentic to selected era while maintaining modern usability. Design decisions prioritize:
- **Nostalgia + Usability Balance**: Strict visual era cues with flexible layout constraints
- **Privacy-First**: Local-first architecture with transparent offline operation
- **Minimal Friction**: Approval workflow keeps users in flow without friction
- **Extensibility**: Era system designed for easy addition of new eras

---

## Visual Design System

### Era-Specific Design Languages

#### Classic 90s Web (1994-1997)
- **Color Palette**: Bold primary colors, bright complementary pairs, high contrast
- **Typography**: Georgia serif for headers, monospace fallbacks; small text (10-12px)
- **UI Elements**: 
  - Beveled borders (2-4px with light/dark shades)
  - Animated GIFs for accent elements
  - Comic Sans / casual fonts for friendly CTAs
  - Horizontal rules and dividers between content blocks
- **Layout**: Table-based layouts, full-width designs, minimal whitespace
- **Textures**: Animated backgrounds, tiled patterns, scan lines

#### Windows 95 / 98
- **Color Palette**: System palette 256 colors, gray-heavy UI, teal accents
- **Typography**: MS Sans Serif, system fonts at fixed sizes (11px default)
- **UI Elements**:
  - Beveled 3D buttons with sunken/raised states
  - Gray window frames with title bars
  - Dialog box styling (white content area, gray borders)
  - Status bar at bottom with inset text
  - Classic checkbox/radio button shapes
- **Layout**: Window metaphor, contained cards, minimal rounded corners
- **Textures**: Flat colors, occasional textured backgrounds

#### Windows XP / Vista
- **Color Palette**: Luna theme blues, Aero glass effects, silver accents
- **Typography**: Segoe UI, slightly larger sizing (12px)
- **UI Elements**:
  - Glossy buttons with gradients
  - Rounded corners (4-6px)
  - Glass morphism effects (semi-transparent overlays)
  - Sidebar navigation with icon + label
- **Layout**: More whitespace than 95/98, centered content areas
- **Textures**: Gradient backgrounds, subtle patterns, glass effects

#### Windows 7
- **Color Palette**: Clean blues, whites, light grays
- **Typography**: Segoe UI, balanced sizing
- **UI Elements**:
  - Flat-ish buttons with minimal beveling
  - Ribbon-like toolbars (optional)
  - Card-based layouts
  - Accent color accents for actions
- **Layout**: Grid-based, generous whitespace, modern spacing
- **Textures**: Minimal texturing, flat design approaching

---

## Component Architecture

### Core UI Components

#### Approval Popup / Banner
- **Location**: Top of viewport (persistent banner style) or modal overlay (first-visit)
- **Content**:
  - Preview thumbnail of styled page (small, showing color changes)
  - "Styling applied for [Era Name]" confirmation message
  - Three action buttons: Approve, Reject/Regenerate, Provide Feedback
  - Collapse/expand controls to show/hide feedback UI
- **States**:
  - **Default**: Showing preview + primary actions
  - **Feedback Open**: Expanded section with preset buttons + free-text input
  - **Processing**: Loading state during AI regeneration
  - **Approved**: Confirmation state before closing
- **Era-Specific Styling**: The banner itself should reflect the selected era's design

#### Era Selection Interface
- **Initial Setup Screen**:
  - Visual grid of era options (8 total: 90s, 95, 98, ME, 2000, XP, Vista, 7)
  - Each option shows:
    - Era name + date range
    - Small visual preview card showing characteristic colors/typography
    - Selection state indicator (radio button era-styled)
  - "Set as Default" CTA below grid
  - Quick reference: "Change anytime in settings"
- **Settings Menu Access**: Quick era switcher (dropdown or tabs)

#### Style Feedback UI
- **Preset Buttons**: 
  - "Too Modern" (suggest more retro)
  - "Too Simple" (suggest more detailed)
  - "Simplify Layout" (reduce complexity)
  - "Make It More Usable" (relax strict era adherence)
  - "Regenerate" (no feedback, just re-generate)
- **Free-Text Input**:
  - Optional textarea for detailed guidance
  - Placeholder: "e.g., make the colors brighter, add more borders..."
  - Character limit: 200 characters (brief guidance)
- **Submit Button**: "Regenerate & Apply" or similar

#### Hybrid Cache Status Indicator
- **Subtle indicator** in extension popup showing:
  - "Using cached style from [date]"
  - "Generated fresh for this visit"
  - "Offline mode - using cached style"
- **Optional**: Small animation showing cache hit vs. generation

---

## User Experience Flows

### Flow 1: First Visit Setup
1. User installs RetrOS-Web extension
2. Extension popup triggers setup screen showing era selection grid
3. User selects desired era (visual preview of each)
4. Clicks "Set as Default"
5. Extension ready, can be used immediately

### Flow 2: First Visit to New Site
1. User navigates to site with RetrOS-Web active
2. Proxy fetches page, checks hybrid cache
3. Cache miss → AI generates style in background
4. Style injected + approval banner appears at top
5. User sees styled page with preset feedback options
6. User approves (style cached) or provides feedback (regenerates)
7. On subsequent visits: style applied instantly from cache

### Flow 3: Manual Regeneration
1. User clicks "Reject" or feedback button in approval banner
2. Popup expands to show preset feedback buttons + free-text input
3. User selects preset (or types feedback) and clicks "Regenerate"
4. Processing state shown (brief spinner/message)
5. New AI style generated and applied
6. User can approve or provide more feedback
7. No limit on regeneration attempts

### Flow 4: Era Switching
1. User opens settings (extension icon → settings)
2. Era selector shown (simplified vs. initial setup)
3. User selects new era
4. Extension applies era change globally
5. Current site immediately re-generates style (or shows cache if available)
6. Subsequent visits to sites apply new era

### Flow 5: Offline Mode
1. No internet connection available
2. Hybrid cache checked for site + era
3. If cached: style applied automatically (indicator shows "cached style")
4. If not cached: fallback to basic era-inspired styling or notification
5. On reconnect: background generation for uncached sites

---

## Interaction Patterns & Micro-UX

### Feedback Submission Flow
- User hovers over preset button → tooltip shows what this feedback influences
- Click preset → visual feedback (button highlight/press state)
- Free-text input (if used) → character counter appears below input
- Submit → brief loading state (500-1000ms) → success confirmation → apply new style
- Option to accept immediately or request another generation

### Cache Hit Indication
- Subtle badge in extension popup: "🔄 Cached" vs. "✨ Generated"
- Hover state: Shows timestamp of when style was cached
- Rare but important: If site redesign detected, cache invalidated automatically

### Era Visual Feedback
- When era selected: Quick visual "preview" of that era's colors flashes briefly
- When style applied: Smooth 200-300ms fade/transition between old and new styles
- Approval banner uses era-appropriate animation (e.g., GIF-like jitter for 90s)

### Error States
- **Generation failed**: "Couldn't generate style - using fallback. Try again?"
- **Offline cache miss**: "Style not cached for offline use. Go online to generate."
- **API/Proxy error**: Graceful degradation to basic styling + error message

---

## Data & State Management

### Client-Side State (Extension)
```
activeEra: string (selected era name)
currentSite: {
  domain: string
  cacheKey: string
  cacheStatus: "hit" | "miss" | "pending" | "failed"
  approvalStatus: "pending" | "approved" | "rejected"
}
settings: {
  era: string
  autoApprove: boolean (optional future)
  feedbackHistoryLength: number
}
```

### Cache Storage Structure
```
~/.retroweb/styles/
  ├── 90s/
  │   ├── github.com-approved.css
  │   ├── github.com-metadata.json
  │   └── ...
  ├── windows95/
  ├── windows98/
  └── ...
```

### Metadata File Format
```json
{
  "domain": "github.com",
  "era": "windows95",
  "cacheKey": "layout-fingerprint-hash",
  "generatedAt": "2026-02-08T10:30:00Z",
  "approvalStatus": "approved",
  "feedbackGiven": ["too-modern"],
  "regenerationCount": 0
}
```

---

## Visual Hierarchy & Layout

### Extension Popup
- **Header**: RetrOS-Web logo + era name (era-styled)
- **Status Section**: Current site, cache status, approval status
- **Action Zone**: 
  - Approve / Reject buttons (if pending)
  - Feedback zone (if open)
  - Settings link (gear icon, bottom right)
- **Typography**: Era-appropriate sizing and spacing
- **Colors**: Inherit from active era design language

### Settings Panel
- **Tabs**: Era Selection | Cache Management | About
- **Era Selection Tab**:
  - Grid of 8 era options (similar to setup)
  - Current selection highlighted
  - Visual preview for each
- **Cache Management**:
  - "Clear all styles" button
  - "Clear cache for this site" option
  - Total cache size display
- **About**: Extension version, links to README, GitHub

---

## Accessibility Considerations

### Keyboard Navigation
- Tab through all interactive elements (buttons, inputs, era options)
- Enter/Space to activate buttons
- Arrow keys to navigate era grid
- Escape to close modals/banners

### Screen Reader Support
- All buttons have descriptive aria-labels
- Approval banner announces itself on appearance
- Form inputs properly associated with labels
- Image previews have alt text describing era styling

### Color Contrast
- Approval banner uses sufficient contrast regardless of era styling
- Error messages use both color + icon/text for distinction
- Feedback preset buttons have clear visual states

### Responsiveness
- Approval banner adapts to small viewports (mobile browser)
- Extension popup sized appropriately for small screens
- Settings panel mobile-friendly

---

## Performance Considerations

### AI Generation
- Debounce feedback input (500ms) to avoid rapid regenerations
- Show processing state immediately (psychological feedback)
- Target generation time: < 3 seconds for most sites
- Fallback: If generation takes > 10s, show "still processing..." message

### Caching Strategy
- Check cache before API call (instant feedback)
- Lazy-load curated packs from GitHub (background on startup)
- Cache cleanup: Archive styles older than 6 months
- Total cache size limit: 50MB (auto-prune oldest if exceeded)

### Network Optimization
- Only send page structure digest to AI (not full DOM)
- Compress cached styles (gzip)
- Batch feedback data before sending to backend

---

## Extension UI Layout

### Popup Window (Compact View)
```
┌─────────────────────────────────┐
│ 🖥️ RetrOS-Web [⚙️]             │  ← Header with settings
├─────────────────────────────────┤
│ Status: github.com              │
│ Era: Windows 95                 │
│ Cache: 🔄 (regenerated 2h ago)  │
├─────────────────────────────────┤
│ [✓ Approve] [✕ Reject] [💬 ...]│  ← Action buttons
├─────────────────────────────────┤
│ Feedback (optional):            │
│ ☐ Too Modern  ☐ Too Simple     │
│ ☐ Simplify    ☐ More Usable    │
│ [Feedback text input...]        │
│ [🔄 Regenerate]                 │
└─────────────────────────────────┘
```

### Approval Banner (On-Page)
- Positioned at top, below browser chrome
- Era-styled appearance (respects selected era design)
- Collapsible/closeable with X button
- Contains status + action buttons + optional feedback section
- Smooth fade-in animation

---

## Future Design Enhancements

### Phase 2: Advanced Features
- Per-site era override UI (site-specific settings)
- Style editor for power users (customize generated CSS)
- Community style ratings (upvote/downvote cache)
- Preview mode (see style before approval)

### Phase 3: Distro Integration
- System-wide retro mode indicator
- Integration with OS-level era selection
- Distro-specific branding in extension UI

### Phase 4: Mobile Expansion
- Mobile Firefox support (responsive approval UI)
- Tablet-optimized settings layout

---

## Design Tokens & Constants

### Spacing Scale
- `xs`: 4px
- `sm`: 8px
- `md`: 16px
- `lg`: 24px
- `xl`: 32px

### Typography Scale
- Display: 24px
- Heading: 18px
- Body: 14px
- Small: 12px
- Tiny: 10px

### Animation Timings
- Quick interactions: 150ms
- Page transitions: 300ms
- Loading states: 500-1000ms

### Z-Index Hierarchy
- Extension popup: 100000
- Approval banner: 99999
- Tooltips: 99998
- Default content: 0

---

## Handoff to Implementation

These design specs establish:
1. ✅ Visual language for each era
2. ✅ Component structure and interaction patterns
3. ✅ User workflows and UX flows
4. ✅ Data models and storage strategy
5. ✅ Accessibility and performance guidelines

Ready for engineering implementation phase.
