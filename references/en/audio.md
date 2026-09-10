# Narration and music

[中文](../audio.md) | **English**

These are English-language instructions, not a requirement to make an English film. The approved brief and `PROJECT_STATE.json.content_language` determine narration language, writing length units, voice language and subtitles. For Chinese films, retain natural Chinese narration, its character-based planning and a Chinese-capable voice; do not translate approved content when the interface changes.

## Voice: steps 4–5

Doubao speech synthesis is recommended. Check local configuration when reaching this step, and skip setup reminders if it is already usable. If missing, guide the creator to enable the relevant speech resource and store credentials in local environment variables or the host's secret manager. Do not ask for keys in chat. Configuration is not proof of account permission or balance.

For English narration, verify that the actual speaker/resource supports English and the desired accent. A Chinese voice identifier or a configured key does not establish this. If the account has no suitable English voice, explain the gap and let the creator choose an available English-capable service or provide externally generated narration; keep the same auditions, full-track review and approval gates. Do not silently change provider or fabricate speaker IDs.

Choose one short passage from the approved script that includes narrative and an emotional shift. Use exactly that text for 3–5 voice auditions. Record text, delivery instructions, speaker ID and pace. Prefer natural storytelling and intentional pauses over a presenter voice or slowing everything down. Check names and pronunciations without translating names.

After the creator chooses, save VOICE_SELECTION.json. Generate the entire pure SCRIPT.txt in step 5 with those settings, checking it against step 3. Do not send headings, review notes or shot numbers to TTS. If splitting a long script, use semantic boundaries and consistent settings, then assemble a complete narration. Verify returned timing against the actual audio; otherwise use available alignment tools or human marking. Never estimate final timestamps from character or word counts.

Check missing/repeated/extra words, pronunciation, delivery, breathing and true duration. The creator listens to the entire track before storyboarding. A different voice requires a new audition. Pronunciation instructions must preserve meaning; a changed spoken script needs appropriate renewed approval. The built-in TTS adapter deliberately rejects a full script or selected settings that no longer match approved hashes.

## BGM: steps 10–12

Recommend Suno V5.5 when the selected service actually offers it. Use an already configured and authorized music API, or provide complete prompts for external generation and receive the audio back. A Suno product version does not imply a public API: verify provider documentation, fields, authentication, version and extension capabilities. The package does not bundle a guessed third-party music endpoint. User-supplied music follows the same review process.

Map the full narration into opening, development, emotional turns and ending, noting actual time ranges, intensity, density and silence. Offer about three genuinely different styles suited to this story, not three fixed presets for every couple. Default to instrumental music that leaves room for speech, with no intrusive lead melody or abrupt drums. Use lyrics only when specifically requested.

Each external prompt must include this story's emotional course, musical style, instrumentation, sense of pace, target duration, development, speech space, natural ending and instrumental requirement. Timings are creative guidance, not a guarantee that a generator obeys exact seconds. Listen to returned music before deciding on cuts, extensions or regeneration.

Step 10 requires real audible samples, not three written style names. Step 11 produces or receives music covering the intended film, then mixes representative excerpts with the approved narration. Review the turning points and whether music masks speech. Music material may be generated now; do not present a full-length mix as complete before excerpt approval.

Only at step 12 deliver the full mix. Preserve narration, music sources and arrangement/gain settings. Lower music under speech, allow pauses to breathe and end naturally. Automatic ducking prevents masking; it does not create the story's emotional development. Do not disguise an undersized track with an obvious loop or silent padding.

`media.py mix` performs local sidechain mixing. Register the excerpt's `.mix.json` in step 11; the full mix must reuse those approved sources and gain. Significant musical or balance changes require another sample review. Listen end to end for edits, clipping, sudden changes and intelligibility. WAV is recommended for the master; video export uses AAC.

## Optional official adapters

- [Kimi documentation](https://platform.kimi.ai/docs/overview): official Chat Completions; verify models available to the account.
- [Doubao HTTP streaming synthesis](https://www.volcengine.com/docs/6561/1598757) and [voice list](https://www.volcengine.com/docs/6561/1257544): select a verified speaker/resource and supported delivery controls.

Automated checks cover request boundaries and response parsing, not paid end-to-end validation of every account, English accent, speaker or provider. Diagnose an uncertain request before retrying a paid call.
