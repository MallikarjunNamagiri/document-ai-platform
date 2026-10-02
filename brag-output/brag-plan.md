# Brag Plan: Document AI

## What is this app?
A dark-ops chat console that answers questions about an uploaded document using hybrid RAG, cites page sources, and flashes a cache badge when it has already seen the question.

## The angle
This is not a landing page. It is a command console that pretends it already ingested the contract. The joke-that-isn’t-a-joke is the footer: **Enterprise RAG v2.0**. The video should feel like a quiet SOC demo — amber spark, green ready light, then a real Q&A that ends with page citations.

## Hook (first 2-3 seconds)
The amber ✦ and the words **Document AI**, then the sidebar status **● System Ready**. Hold. That green ready light is the visual identity.

## Key moments (the middle)
- Recreate the real chat: type `What does the contract say about termination?` into **Ask a question about the document...**, hit **Send**.
- Stream a short grounded answer under the **✦ DOCUMENT AI** label.
- Sources land: `Sources: Acme-MSA.pdf (p.12), Acme-MSA.pdf (p.18)`.
- A second, similar question returns instantly with the **⚡ Cache** pill.

## Outro / punchline
**Document AI.** Then smaller: **Answers with pages.** Tiny footer: **Enterprise RAG v2.0**.

## User flow worth showing
Ask about the document → streamed answer with the Document AI label → sources (page numbers) and, on a repeat, the Cache badge.

## Tone
- Preset: polished
- Creative direction: quiet ops-console product film
- Interpretation: fewer scenes, longer holds, mixed-case light type, no hype language, amber on near-black. Humor only from the product calling itself Enterprise RAG v2.0.

## Format: landscape — 1920x1080
## Duration: 20 seconds

## Visual identity (from the project)
- Background: `#080a0e`
- Accent: `#fbbf24` (amber-400 spark / labels), `#f59e0b` (amber-500 Send button)
- Status: `#4ade80` (green-400 System Ready / Cache)
- Text: `#ffffff` / `#f3f4f6` (gray-100)
- Muted: `#9ca3af` (gray-400), `#6b7280` (gray-500)
- Surfaces: `#1a1f28` (user bubble + input), `#11151b` (assistant bubble)
- Borders: `rgba(255,255,255,0.10)`
- Display font: Geist Sans (fallback: system-ui)
- Body font: Geist Sans; status/cache in Geist Mono
- Strongest visual element: left sidebar with ✦ Document AI, Document Engine, ● System Ready, and the amber Send button on the chat input

## Share copy (draft)
Ask the PDF. Document AI answers with page numbers — and if you asked it already, it just says ⚡ Cache.

## Audio direction
- Role: warm corporate bed with sparse professional accents
- Music: `happy-beats-business-moves-vol-11-by-ende-dot-app.mp3`
- Music treatment: start near 0, volume low-moderate (~0.22–0.28), short fade-in, fade under the outro logo
- Music cue guidance: preset at `.cursor/skills/brag/assets/music/cues/happy-beats-business-moves-vol-11-by-ende-dot-app.music-cues.md` (~114.84 BPM). Strong cues: 1.60s (hook lock), 5.80s / 6.34s (chat send / first token), 12.65s (sources), 17.91s (outro name). Beat-grid from ~8.96s for sequential source lines (every other beat so text stays readable).
- Audio-reactive treatment: subtle; amber spark glow and green ready-dot presence breathe with RMS/bass. No waveforms.
- SFX posture: sparse; motion-matched; professional restraint
- Audio-coupled moments: keyboard ticks while the question types; click on Send; soft card/bong when the assistant bubble arrives; a quieter tick for the Cache pill
- Restraint rule: no casino sounds, no stingers stacked on every beat, no narration

## Storyboard

### Scene 1 — Ready — 3.6s
Full-bleed recreation of the Document AI chrome: dark `#080a0e` canvas, left sidebar with amber ✦, **Document AI**, **DOCUMENT ENGINE**, then **● System Ready** in green mono. Main pane empty except a faint input bar. Hook line over the empty chat, mixed case, light weight: **The document is already in.**
Sequential/interaction: yes — ✦ then name, then System Ready (hold each label ≥0.8s after settle).
Audio intent: bed eases in; one soft interface tick when Ready appears.
Audio-coupled idea: Ready-dot glow; optional beat lock on 1.60s for the Ready line.
Music: warm bed
Transition mood: soft slide → Scene 2

### Scene 2 — Ask — 6.4s
Same UI, now in use. Cursor/caret in the input. Placeholder **Ask a question about the document...** is replaced as the question types: `What does the contract say about termination?` Then the amber **Send** button depresses. User bubble appears on the right (`#1a1f28`). Assistant bubble opens on the left with **✦ DOCUMENT AI** and streamed answer text (fictional stand-in, not real customer data): `Termination requires 30 days’ written notice, except for material breach.`
Sequential/interaction: yes — type → Send click → user bubble → streaming tokens.
Audio intent: keyboard ticks during type; click on Send; soft card when the assistant bubble lands.
Audio-coupled idea: Send / first token near 5.80s strong cue.
Music: continues under
Transition mood: soft crossfade → Scene 3

### Scene 3 — Pages, then cache — 6.0s
Assistant bubble grows a sources footer: **Sources: Acme-MSA.pdf (p.12), Acme-MSA.pdf (p.18)** — two source fragments appear one by one, then hold together. A second user bubble: `And the notice period?` Instant assistant reply, same answer, with the green **⚡ Cache** pill top-right of the DOCUMENT AI header.
Sequential/interaction: yes — source line 1, source line 2 (every other beat, then full hold ≥1.2s), then Cache pill.
Audio intent: two quiet arrival ticks for sources; a slightly brighter but still small tick for Cache.
Audio-coupled idea: sources near 12.65s; Cache as the payoff of this scene, not rushed.
Music: continues
Transition mood: slow crossfade → Scene 4

### Scene 4 — Name — 4.0s
Chat recedes slightly. Center: **Document AI**. Under it: **Answers with pages.** Bottom-right, small gray: **Enterprise RAG v2.0**. Amber ✦ holds.
Sequential/interaction: none
Audio intent: music fades; let the last tick ring if it exists.
Audio-coupled idea: name lock near 17.91s if it does not fight the hold.
Music: fade under logo
Transition mood: hold to black

**Total: 20.0s**

**Music mood for this video:** warm professional / slightly upbeat business bed
**Audio summary:** Quiet bed in, keyboard and a send click for the ask, two source ticks, a cache tick, fade under the name.
