# v0.2.0 bilingual validation

[中文](VALIDATION.md) | **English**

Date: 2026-09-10. Documentation review, real local execution and human film approval are different kinds of evidence.

| Check | Result and scope |
|---|---|
| Skill/package structure | Skill creator validation and internal document links checked; one installation serves both languages |
| Automated tests | 25 passed, including the original 20 checks plus English progress/package output, language changes preserving approved work, English word wrapping and the retained Chinese line limit |
| Original intake | Original question/option SPEC unchanged; online/offline HTML copies identical; Chinese remains the default |
| Browser execution | Chinese and English tested at phone and desktop widths; complete copied answers, English labels/placeholders/validation, no untranslated Chinese in an English-filled card, switch-and-restore, clipboard fallback, clear, local draft recovery and no horizontal overflow or JavaScript errors |
| English media/package run | Full synthetic 14-step receipts, English writing ZIP, real first-frame images plus English video-prompt ZIP, sample/full mixing, subtitled preview and final export; 6 seconds, 144 frames, 640×360, 24 fps and 48 kHz stereo; screenshot confirms readable English subtitles |
| Approval invariants | Generating/decoding does not approve human viewing. Creator export approval still leaves couple acceptance pending. All test approvals explicitly say synthetic |
| Independent review | Four English-use scenarios reviewed: new English order, English interface for a Chinese film, no suitable English voice, and pressure to use an image API. The language-of-guidance versus language-of-film ambiguity was corrected in detailed references |

The original release's independent reviews also identified and fixed a ZIP containing a prompt path instead of its contents, full TTS accepting unapproved settings/text, inflexible audio/frame rounding, companion-file overwrites, and false image files. Their regression tests remain included. Full mixing uses auditioned sources/settings, and editing checks complete approved shot order.

## What this does not prove

No paid Kimi, Doubao, music or video generation was run for this update. Synthetic tones and color frames validate code and packaging, not English accent quality, emotional delivery, real faces, narrative quality or a couple's satisfaction. No real customer story or credentials were used.

Phone checks use browser viewport simulation; clipboard writes are controlled in tests and the actual DOM fallback is exercised. Physical devices and messaging-app browsers such as WeChat were not individually tested. The editing deliverable is a reproducible JSON timeline, not a native Premiere/CapCut project. Provider availability and language support must be checked for the actual account during use.
