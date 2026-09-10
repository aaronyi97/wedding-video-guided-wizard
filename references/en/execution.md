# Execution reference

[中文](../execution.md) | **English**

These are English-language instructions, not a requirement to make an English film. The approved brief and `PROJECT_STATE.json.content_language` determine narration language, writing length units, voice language and subtitles. For Chinese films, retain natural Chinese narration, its character-based planning and a Chinese-capable voice; do not translate approved content when the interface changes.

The assistant runs these commands; the creator supplies the current human decision. PROJECT below means the actual absolute order directory: replace it before execution. Work from the skill root. Python 3.9+ is required for helpers. Keep customer files outside the public skill and follow the host's storage rules. Surface tool failures with an English explanation and the next concrete action.

## Language, state and versions

```bash
python3 scripts/wizard.py init PROJECT --lang en
python3 scripts/wizard.py summary PROJECT
python3 scripts/wizard.py prepare PROJECT --step 1 --files FACTS.md
python3 scripts/wizard.py approve PROJECT --step 1 --by producer --evidence 'The actual creator reply approving this version'
python3 scripts/wizard.py validate PROJECT
```

`--lang en` sets English guidance/package labels and defaults the film language to English. Use `--content-language zh` at initialization for an English-speaking creator making a Chinese film. Chinese remains the default when flags are omitted. To switch an existing order's interface only, run `python3 scripts/wizard.py language PROJECT --lang en`; this preserves film language, files, step and approvals. Existing v0.1.0 state without language fields is treated as Chinese. Changing the actual script language is a content revision requiring renewed approvals.

`prepare` registers actual current files. Run `approve` only after receiving the applicable reply. Step 3 uses role `couple`; step 14 requires `producer` and then `couple`; other steps use `producer`. Progress advances automatically. Never copy the example evidence as if it were a real reply or hand-edit state to skip gates.

Register all selected deliverables and the manifests that explain them. Especially: step 3 SCRIPT.txt, step 5 full narration, step 6 SHOT_PLAN.json, steps 7/8 selected original images, step 9 selected videos, step 11 samples and `.mix.json`, and step 12 full mixed master. Technical QC and human feedback remain separate records.

For a revision, preserve earlier files and reopen affected steps:

```bash
python3 scripts/wizard.py reopen PROJECT --step 8 --affected 9 13 14 --reason 'Replace S04 image and redo that shot plus film exports'
```

This reopens 8, 9, 13 and 14, preserving unrelated approvals. Omitting `--affected` reopens every subsequent step. After reconfirming, progress skips still-approved steps. If a file changes or disappears, reopen and record the reason rather than replacing an old hash to hide the change.

## Writing and video ZIPs

```bash
python3 scripts/wizard.py writing-pack PROJECT --prompt WRITING_PROMPT.txt --out writing-v1.zip
python3 scripts/wizard.py video-pack PROJECT --manifest VIDEO_PACK.json --out video-v1.zip
```

Step 2's writing ZIP contains `00-README.txt`, `01-Copy-to-Kimi-K3.txt`, and a hash manifest for an English interface. Also provide the independent full text for convenient copying. The assistant embeds all case facts, style, length and output instructions; placeholder detection cannot replace editorial review.

Step 6's registered SHOT_PLAN.json has `{"shots":[{"id":"S01"},{"id":"S02"}]}` plus the timing, fact sources, reference and action fields described in the visual guide. Step 9 uses:

```json
{"plan":"SHOT_PLAN.json","shots":[
  {"id":"S01","image":"images/S01-v2.png","prompt":"prompts/S01-video.txt"},
  {"id":"S02","image":"images/S02-v1.png","prompt":"prompts/S02-video.txt"}
]}
```

Shot IDs must match the approved storyboard; images must be approved in steps 7/8 and actually decodable with Pillow. `prompt` is the path of a UTF-8 file containing the full video prompt. The ZIP copies its contents, not the path. Each English shot folder includes `first-frame.png` (or original format) and `video-prompt.txt`, with root instructions and SHA256 manifest. The video prompt must match the actual first frame. On return, check shot ID and version before approving videos.

## Optional configuration

```bash
python3 scripts/media.py doctor
```

This reports configuration presence without exposing keys. It does not prove permission, credit, English voice capability or authorization to spend. Kimi: `MOONSHOT_API_KEY`, optional `MOONSHOT_MODEL` (default `kimi-k3`) and `MOONSHOT_BASE_URL` (official addresses only). Doubao: `DOUBAO_API_KEY`, or `DOUBAO_APP_ID` plus `DOUBAO_ACCESS_KEY`; optional `DOUBAO_RESOURCE_ID` defaults to `seed-tts-2.0`. Use values from the actual account rather than trying invented identifiers.

```bash
python3 scripts/media.py kimi PROJECT --prompt WRITING_PROMPT.txt --out SCRIPT-draft.txt --authorized
python3 scripts/media.py tts PROJECT --text VO_EXCERPT.txt --instructions VO_DIRECTION.txt --voice VERIFIED_ENGLISH_VOICE_ID --out voice-option-1.mp3 --authorized
python3 scripts/media.py probe PROJECT/voice-option-1.mp3
```

Replace the example voice ID with a real, verified English-capable voice. `--authorized` records permission already given for this task; it does not create permission. Never put real keys in commands, chat, ZIPs or GitHub. Auditions run in step 4; full narration in step 5. Raw provider timestamps are saved as `.timing.json` and must be checked before becoming VO_TIMING.json.

After the step 4 selection, generate and register VOICE_SELECTION.json with `voice`, integer `rate`, `instructions` path, actual `instructions_sha256`, step 3 `source_script` path and its actual `source_script_sha256`. Register the selection alongside audition files, then approve from the actual choice reply. Step 5 reads this file by default (`--selection` can override the path) and rejects unapproved text, voice, direction or pace.

No generic guessed video/music API is bundled. Use verified available tools/documentation for a chosen provider, or hand off prompts and receive media back. Images must always be generated manually in external GPT.

## Local mixing and editing

The local path needs FFmpeg, ffprobe, Pillow and an appropriate subtitle font. Prefer host-bundled dependencies; install only missing components and continue in the same conversation. Set `FFMPEG_BIN`, `FFPROBE_BIN` or `WEDDING_FONT` when needed. Pillow can be installed with `python3 -m pip install Pillow` in the selected environment. English has Latin-font fallbacks and does not require installing a Chinese font; Chinese subtitles need a Chinese-capable font. Quote paths that contain spaces.

```bash
python3 scripts/media.py mix PROJECT --voice audio/voice-final.wav --music audio/music-arranged.wav --start 12 --length 15 --gain 0.16 --out audio/mix-sample-1.wav
python3 scripts/media.py mix PROJECT --voice audio/voice-final.wav --music audio/music-arranged.wav --gain 0.16 --out audio/mix-full.wav
python3 scripts/media.py assemble PROJECT --plan EDIT_PLAN.json --out film-preview-v1.mp4
```

Adjust example intervals and gain to the actual project. Narration must match step 5. Step 12 reuses sources and gain approved in step 11 and must cover the full narration. Arrange music extensions/edits before approving excerpts; preserve stems.

EDIT_PLAN.json is the editable, reproducible timing plan, kept with original sources. It is not a native Premiere or CapCut project. Example:

```json
{
  "storyboard":"SHOT_PLAN.json","subtitle_language":"en",
  "audio":"audio/mix-full.wav","width":1920,"height":1080,"fps":24,
  "shots":[
    {"id":"S01","file":"videos/S01-v1.mp4","in":0,"out":4,"start":0,"end":4},
    {"id":"S02","file":"videos/S02-v2.mp4","in":1,"out":5,"start":4,"end":8}
  ],
  "cues":[{"start":0.3,"end":3.7,"text":"The first approved narration line."},
          {"start":4.2,"end":7.7,"text":"The second approved narration line."}]
}
```

Generate actual timings from approved audio and observed video action. Use every approved storyboard shot exactly once in order; changing narrative order or omitting a shot requires revisiting storyboard approval. Source ranges must fit available video, and cuts align to frames. Round the final visual endpoint to the nearest frame within half a frame, preserving the full audio duration.

English subtitles wrap by words and measured width, at most two lines; Chinese retains 18 characters per line and two lines. If a cue is too long, split it at a semantic time boundary rather than changing approved words or shrinking text until unreadable. Preserve names and punctuation; review synchronization against actual speech. Set `subtitle_language` explicitly when it differs from the project's film-language default.

Assembly supports straight cuts, moderate speed adjustments, aspect-preserving padding, burned-in subtitles and a single approved mixed soundtrack. It runs only at steps 13/14 and checks approved video/audio hashes. It outputs MP4, SRT and technical QC, without auto-approving human viewing or final delivery. Existing outputs and companion files are not overwritten. Deliver the actual plan, source mapping and usage notes with the final film.
