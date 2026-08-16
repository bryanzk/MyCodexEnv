---
name: podcast-episode-prep
description: Prepare a podcast episode from source video or audio through organized local assets, verified episode audio, evidence-based title and show notes, square cover art, and a reviewed unpublished Spotify for Creators draft. Use when asked to extract episode audio, assemble an intro and main recording, organize episode media, draft episode copy from an event page or notes, adapt event artwork for Spotify, upload an episode, or prepare a podcast draft without publishing it.
---

# Podcast Episode Prep

Prepare one episode end to end while keeping local editing, draft creation, and publication as separate states.

## Establish the episode contract

Before changing files or a creator account, identify:

- episode number and working title;
- source video or audio;
- episode workspace or existing asset folder;
- intro, outro, music, and cover sources;
- factual sources for the copy;
- target podcast/show and the immediately previous episode;
- requested terminal state: local assets, exported audio, unpublished draft, scheduled episode, or published episode.

Reuse the user's existing folder and naming pattern. Do not impose a new directory tree for a one-off episode. Confirm the target episode in every external write so an existing episode is not overwritten.

## Prepare local audio

1. Inspect the source and record its path, format, duration, and size.
2. Extract audio with a native export when available; use an installed media tool only when automation or format control is useful.
3. Save the extracted file in the episode workspace with a source-derived name.
4. Verify the output exists and inspect its codec, sample rate, channels, and duration.
5. Spot-check playback near the beginning, middle, and end. Treat metadata checks as necessary but not sufficient.

When assembling an episode:

1. Duplicate a prior editing project before reusing it.
2. Remove prior-episode media from the duplicate.
3. Place the verified intro first, then the main recording and any explicitly requested outro or music.
4. Preview the opening transition, at least one middle section, and the ending.
5. Export a new final audio file and verify that export independently.

Do not describe an edit as finalized merely because a timeline exists or plays in the editor.

## Organize assets

Keep the episode workspace lightweight. Preserve source files and distinguish them from derivatives:

- source media;
- extracted audio;
- reusable intro or outro;
- final episode audio;
- cover source;
- final square cover.

Do not rename or move user files unless requested. Report exact artifact paths so the next step can consume the verified files.

## Draft episode copy

Use the supplied event page, notes, transcript, or other authoritative source. Separate confirmed facts from interpretation and never invent guest details, claims, links, dates, or locations.

Prepare:

- one episode title;
- a concise opening summary;
- three to five concrete discussion points;
- guest or speaker context when verified;
- source or registration links the user wants retained;
- an optional closing call to action.

Match the language and voice of adjacent episodes when available, but do not copy stale facts from the previous episode. Present the copy for review before an irreversible publish action.

## Prepare cover art

Prefer adapting the designated event or brand image over creating unrelated artwork.

1. Confirm the cover source belongs to the target episode.
2. Create a square composition suitable for Spotify.
3. Preserve recognizable branding and essential title text.
4. Keep important text and faces away from crop edges.
5. Inspect the final image at full size and thumbnail size.
6. Record the final asset path and whether it has been applied to the draft.

Generating a cover, applying it to a draft, and verifying it on the review page are three separate states.

## Prepare the Spotify draft

Treat creator-account changes as external writes.

1. Confirm the correct show and choose the new-episode flow.
2. Upload only the independently verified final audio.
3. Fill the title and description from the reviewed copy.
4. Apply the verified square cover when requested.
5. Advance to the review step.
6. Read back the audio identity or duration, title, description, cover, and publish controls.
7. Stop with an unpublished draft unless the user explicitly authorizes scheduling or publishing in the current request.

Never infer publish permission from permission to upload, draft copy, or replace a cover. Do not modify the previous episode while preparing the new one.

## Report state

Report only states supported by fresh checks:

- `source_verified`
- `audio_extracted`
- `edit_assembled`
- `final_audio_exported`
- `copy_drafted`
- `cover_generated`
- `cover_applied`
- `spotify_draft_created`
- `review_readback_verified`
- `scheduled`
- `published`

Include exact artifact paths, the target episode, what was read back, and the remaining action. For any completion claim, include `command`, `exit_code`, `key_output`, and `timestamp` when a command-based check exists; otherwise name the UI or source-system readback and its observed time.
