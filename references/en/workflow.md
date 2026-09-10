# Workflow and approvals

[中文](../workflow.md) | **English**

These are English-language instructions, not a requirement to make an English film. The approved brief and `PROJECT_STATE.json.content_language` determine narration language, writing length units, voice language and subtitles. For Chinese films, retain natural Chinese narration, its character-based planning and a Chinese-capable voice; do not translate approved content when the interface changes.

Start every production reply with the current step out of 14, phase, status, and remaining steps. The assistant runs the process; the creator supplies materials and judgment. Checks and rework stay within the current step.

| Step | Assistant work | What the creator does | Evidence to register |
|---|---|---|---|
| 1 | Send the original questionnaire in English; organize FACTS.md, specifications and photo mapping | Forward the card, return filled text and photos, resolve material gaps | Confirmed usable brief, including events that did not happen or must be omitted |
| 2 | Build a complete case-specific writing ZIP and copyable text; strongly recommend Kimi K3; review its returned draft | Copy the prompt into Kimi, return the entire draft, read and revise it | Creator-approved SCRIPT.txt, separate from review notes |
| 3 | Provide the exact full script and concise verification points | Forward to the couple; report their approval of the named version or return edits | Explicit couple approval, not only the creator's preference |
| 4 | Check voice configuration only now; audition 3–5 available voices supporting the film language on one excerpt | Listen and choose voice, delivery and pace | Audition files and VOICE_SELECTION.json |
| 5 | Generate the complete approved narration with selected settings; check text, pronunciation and duration | Listen to the whole narration | Approved voice file, script, settings and real VO_TIMING.json |
| 6 | Design SHOT_PLAN.json and a readable storyboard using real narration timing | Approve every shot, reference identity, period and style | Storyboard and reference versions |
| 7 | Select about three difficult or tone-setting shots, with reference instructions and full prompts | Generate manually in an external GPT conversation and return original files | Approved pilot images after identity, style and motion-readiness checks |
| 8 | Provide remaining prompts; inspect the full set, including pilots | Generate the remaining images with references; return each original by shot ID | Complete selected image set and consistency approval |
| 9 | Inspect actual first frames, write action prompts, package each image and prompt | Generate videos, watch them, return by shot ID; redo individual failures | Actual video review of key action, faces, hands, objects and adjacent cuts |
| 10 | Map BGM to the narration's emotional timeline; supply about three real samples | Choose a style, returning manually generated audio when needed | Selected sample and reason |
| 11 | Arrange music across the story; generate/receive music sources and mix representative excerpts | Listen to openings, turns and ending moments with narration | Approved music source, settings and .mix.json files |
| 12 | Create the entire mix with approved sources and retain both stems | Listen end to end, including transitions and ending | Full-length audio approval |
| 13 | Assemble the complete subtitled preview here; perform technical checks | Watch the full film, approve or identify shot IDs/timestamps to fix | Creator preview approval |
| 14 | Export final film, SRT, editable timing plan and checks | Creator verifies the export, then obtains couple acceptance | Separate producer and couple approvals, in that order |

## Practical branches

- No computer: open the same card on a phone. If clipboard permission fails, select and copy the displayed full text. Voice/chat collection is fine after organizing and verifying answers. The couple does not install the skill.
- No matching life event: “other / no such event / don't remember / don't include it” are valid. Use supported material without filling a narrative gap with fiction. If there is not enough to write, stay at step 1 and ask only for the concrete missing fact.
- Recommended model unavailable: explain the account's actual choices and let the creator select an alternative writing, speech or music capability. Preserve the same quality checks and gates. Images remain manual in external GPT.
- Full narration too long: consider natural pace and pauses first. If text must change, return to steps 2/3 for approval; do not quietly delete sentences or speed up the entire track to fit an old storyboard.
- Multiple speakers: confirm who says each line, audition each speaker, then assemble one approved master narration. Do not invent direct quotes.
- Screenshots or a cloud-file listing: these are not the original media. Request actual readable image, audio or video files before declaring them received and reviewed.
- No listening/viewing capability: disclose it and ask the creator to check specific points; record human inspection rather than claiming perception from decoding.
- Revision: save a new version and reopen affected steps. One replaced image normally affects that image, its video, the preview and final export. Changed narration timing also affects storyboard timing, edit points, music and subtitles. Preserve unrelated work.
- Pressure to skip ahead: explain which current decision determines later materials. Do not bypass couple script approval, pilots or listening/viewing gates.
- Language switch: translate guidance and package labels, not approved scripts or names. If the film itself must change language, prepare new text and revisit affected approvals.

PROJECT_STATE.json stores files, hashes, roles, timestamps, actual reply evidence and revision history. The creator can relay the couple's confirmation; the couple needs no login. The script checks order and versions but cannot prove that a reported human reply is truthful. Always explain the precise missing item and the next useful action.
