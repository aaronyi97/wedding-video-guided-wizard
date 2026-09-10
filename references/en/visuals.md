# Storyboards, external images and image-to-video

[中文](../visuals.md) | **English**

## Step 6: storyboard

For each shot record ID, fact source, corresponding narration, final timeline range, period, location, identities and references, style, first frame, core action, end frame, transition and return checks. Use real approved narration timing including pauses; generated source duration is not the same as the used edit duration.

One narrative purpose per shot. Incidental motion is fine, but reduce repeated handoffs, complex rotations and choreography with many people. Split a difficult event into simpler framing without rewriting what happened. Style follows the couple's card: distinguish recognizable real people in a stylized environment from fully animated characters. Translate references into lighting, color, material and depth, not a dependency on another private skill. Do not impose one culture, campus setting or fixed visual style on every order.

Identity comes from the couple's actual photos. Explicitly map each person to references; request clear individual photos when a group image is ambiguous. Confirm age period, clothing and important props. Every shot showing a real person needs their corresponding reference.

## Steps 7–8: manual generation in external GPT only

Do not generate or edit images in Codex, call an image API, or click Generate automatically in the external app. This includes repairs and character masters. For each shot provide the references and upload order, a complete prompt, aspect ratio, return filename and checks. GPT Image 2 or the user's available GPT image capability is the suggested manual route; an available API does not authorize switching routes.

Select about three pilots based on this order's risk and tone-setting value: double identity, period changes, important emotion, hands or objects. Do not prescribe three fixed story events. If the whole film has fewer shots, use the actual number. Explain what each pilot tests and wait for approval before releasing remaining image prompts.

Image prompts describe one stable instant: scene, light, actual positions, objects already held, expression, composition, space for later movement and continuity requirements. Use explicit mapping such as “Reference image 1 shows…” rather than trying to reconstruct identity from facial adjectives. Avoid awkward half-turned starting poses without universally banning a turn.

Inspect returned originals for likeness, the same two identities, correct period/style, hands and objects, unwanted lettering/people, motion space and adjacent continuity. Recheck the entire set including pilots. Register chosen file versions and hashes; replacements need review.

## Step 9: prompts grounded in the selected first frame

Inspect the actual image before describing starting state → core action → ending state. Do not ask a person who has already looked up to rewind and look up again, or restart an approach after they are already close. If the first frame conflicts with the story, propose a local image/storyboard revision and confirm it first.

Each prompt contains its source image, duration/aspect ratio, coherent action and rhythm, one principal camera movement, and identity/clothing/prop/scene continuity. Usually one continuous shot, no dialogue and no music unless the brief specifically requires them. Do not redescribe the face or simultaneously require someone to walk closer and keep their position fixed.

Always provide the actual per-shot ZIP, whether video generation uses an authorized API or manual handoff: each folder contains `first-frame.png` (or the original format) and `video-prompt.txt`; the root includes instructions and file hashes. Use `wizard.py video-pack`; never ship only paths. Verify that the chosen model has a genuine first-frame input rather than assuming any reference slot locks the opening frame.

Manual directions: upload this shot's first frame, paste its video prompt, set duration/aspect ratio, generate, watch and return the original video by shot ID. Trying the hardest shot first can reduce waste within the same numbered step. Configured and authorized video tools may run in the current conversation; image generation remains manual.

Review the full motion and neighboring edit points: does the key event happen, are faces/hands/props stable, are there unexpected cuts or voices, and does an action reverse across shots? Fix individual failures or record a specifically accepted exception with its location and the creator's decision. Decoding and still-image approval do not replace video review.
