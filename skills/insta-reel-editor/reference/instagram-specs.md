# Instagram Reels: Specs & Platform Facts

*Last verified: October 2026. Platform rules change, so re-check items marked (secondary) before
promising them to a user. The Graph API Reel spec is the only machine-readable official spec.*

## Upload / delivery spec

| Item | Value | Source |
|------|-------|--------|
| Container | MP4 or MOV; **moov atom at the front; no edit lists** | Graph API Reel spec [1] |
| Video codec | H.264 or HEVC, progressive, **closed GOP**, 4:2:0 | [1] |
| Frame rate | **23–60 fps** (some guides say a 30 fps minimum; treat that as advice) | [1]; Hootsuite [16] |
| Resolution | **1080×1920 (9:16)** recommended; API max width 1920 px; aspect 0.01:1–10:1 accepted | [1] |
| 4K | in-app uploads accept it and downscale; playback caps at 1080p. Master at 1080×1920 | Hopper [13], Meta Eng [8] |
| Video bitrate | VBR, **max 25 Mbps** | [1] |
| Audio | **AAC, ≤ 48 kHz, mono/stereo, 128 kbps** | [1] |
| Duration | **3 s minimum**; 15 min max via API; in-app camera up to 20 min (Nov 2025) | [1], PetaPixel [5], Buffer [7] |
| File size | 300 MB via API (ads spec reportedly up to 4 GB) | [1] (secondary [57]) |
| Cover | JPEG, ≤ 8 MB, sRGB, 9:16 recommended; API `thumb_offset` in ms picks a frame | [1] |
| Colour | Export SDR BT.709. HDR is preserved only for iPhone-shot Dolby Vision (since Nov 2025) | Meta Eng [10] |

**This skill's master** (`finalize.py`): H.264 High@4.2, yuv420p, CRF 18, maxrate 20M, 2 s closed GOP,
source fps, BT.709 tags, AAC-LC 48 kHz stereo 128k, −14 LUFS / −1.5 dBTP, `+faststart`, no edit list.

## How Instagram processes uploads

- At upload it makes fast "basic" H.264 encodes; when a reel's projected watch time crosses a threshold,
  "advanced" VP9/AV1 encodes follow (≈ 7 resolutions × 5 CRFs) [8][9]. A reel looks soft at first and
  sharpens if it gets views. Instagram "biases to higher quality for creators who drive more views" (Mosseri, Oct 2024) [11].
- User setting: **Upload at highest quality** (Settings → Media quality) [12].
- Upload the highest-quality file you can: the Creators FAQ says to upload the highest resolution possible [2].

## Length & distribution

| Fact | Source |
|------|--------|
| Reels up to 3 min since Jan 2025 ("we still are focused on short form") | Mosseri [4] |
| Instagram recommends reels **≤ 3 min** to unconnected audiences (non-followers) | Creators FAQ [2] |
| Instagram's guide (Sep 2026): 3–15 s trends/one-liners; **15–60 s "sweet spot for tutorials"**; 60 s–3 min detailed how-tos | about.instagram.com [33] |
| 6M-reel study (H1 2026): 45–60 s highest engagement rate; > 180 s lowest | Socialinsider [37] (secondary) |

## Ranking signals (as stated by Instagram)

- Top three signals: **watch time, likes per reach, sends per reach**. Likes matter more for followers,
  sends more for non-followers (Mosseri, Jan 2025) [24].
- Reels ranking predicts reshare, watch-through, like and audio-page visits [3].
- **Deprioritized:** low-resolution or **watermarked** reels, **muted** reels, reels with **borders**,
  **majority-text** reels, and reposts [3].
- **Originality:** accounts that post unoriginal content 10+ times in 30 days lose recommendation
  eligibility (Apr 2024) [25]. Extended to photos and carousels in Apr 2026. "Watermarks, minor crops,
  or basic reposts are unlikely to qualify"; commentary, narration, graphics or remix are required [27].
- Your **own** logo is fine; other apps' logos (TikTok, CapCut) are not recommended (Mosseri, Oct 2024) [26].
- First 3 seconds: "Make sure the first 3 seconds of your reel are engaging" [2]. Insights show a
  **skip rate** (people who leave in the first 3 s) and a retention curve (Aug 2025) [32].
- Trial Reels (Dec 2024): shown to non-followers first, for professional accounts [28].
- Hashtags: capped at 5 per post (Dec 2025) [56] (secondary).
- Mosseri (Jan 2026): the most trustworthy content now "looks the least produced" [55].

## Sound

- Meta (Nov 2024): "Over 75% of Reels views on Instagram are sound on" [34]. Older "85% silent"
  figures are Facebook 2016 data [36]. Captions still help: 80% are more likely to finish a captioned
  video (Verizon/Publicis 2019) [35].
- No official LUFS target. **−14 LUFS / −1 dBTP** is the practitioner convention [45][46].
- Business accounts: Meta Sound Collection only; copyrighted audio can get reels muted, and muted reels
  aren't recommended [3][59].

## Crops of the 9:16 frame

| Surface | Visible region on 1080×1920 | Source |
|---------|----------------------------|--------|
| Reels viewer | full frame minus UI overlays (see safe-zones.md) | — |
| **Profile grid (3:4, since Jan 2025)** | centre 1080×1440, **y 240–1680** | Mosseri [4], Kapwing [20] |
| Home feed preview (4:5) | centre 1080×1350, y 285–1635 | (secondary) [22] |
| Legacy 1:1 | centre 1080×1080, y 420–1500 | geometry |

Grid thumbnails can be repositioned after posting (early 2026) [23].

## Meta's own editor (Edits app): what users compare you to

Launched Apr 2025: auto captions, word highlighting, green screen and cutouts, keyframes with easing,
templates, beat sync, auto-cut silences, teleprompter, volume ducking, "Loudness Match" (Jun 2026),
200+ SFX, 4K/HDR export, bilingual captions [50][51][52][60]. The Instagram app's "First Draft"
(Aug/Sep 2026) auto-trims pauses into a rough cut [54]. This skill should beat those on **editorial
judgement**: hook choice, retake removal, transcript-driven graphics, brand consistency and QA.

## Sources

[1] developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media ·
[2] creators.instagram.com/faq · [3] about.instagram.com/blog/announcements/instagram-ranking-explained ·
[4] threads.com/@mosseri/post/DE-efFqyStv; engadget.com (3-minute reels, Jan 2025) ·
[5] petapixel.com/2025/11/25/instagram-updates-camera-so-you-can-film-20-minute-reels ·
[7] buffer.com/resources/instagram-reels-length · [8] engineering.fb.com/2023/02/21/video-engineering/av1-codec-facebook-instagram-reels ·
[9] engineering.fb.com/2022/11/04/video-engineering/instagram-video-processing-encoding-reduction ·
[10] engineering.fb.com/2025/11/17/ios/enhancing-hdr-on-instagram-for-ios-with-dolby-vision ·
[11] tubefilter.com/2024/10/28/instagram-lowers-video-quality-creators-adam-mosseri ·
[12] jasminealley.com/upload-high-quality-instagram-reels · [13] hopperhq.com/blog/instagram-reel-size ·
[16] blog.hootsuite.com/instagram-reels · [20] kapwing.com/resources/instagrams-new-grid-layout-size-and-dimensions-2025 ·
[22] quso.ai/blog/instagram-thumbnail-size · [23] almcorp.com/blog/instagram-thumbnail-editing-profile-grid ·
[24] highstyle.ai/insights/instagram-reels-algorithm-2026 · [25] techcrunch.com/2024/04/30 (originality) ·
[26] socialmediatoday.com (own logo OK) · [27] engadget.com / petapixel.com/2026/04/30 (originality, photos) ·
[28] techcrunch.com/2024/12/10 (Trial Reels) · [32] socialmediatoday.com (retention insights, skip rate) ·
[33] about.instagram.com/blog/tips-and-tricks/how-to-make-instagram-reels · [34] developers.facebook.com/blog/post/2024/11/07 ·
[35] forbes.com (Verizon/Publicis 2019) · [36] digiday.com/media/silent-world-facebook-video ·
[37] socialinsider.io/blog/instagram-reels-length · [45] cutscore.io/blog/loudness-for-instagram-reels ·
[46] criticallisteninglab.com/en/learn/loudness/social-media · [50] techcrunch.com (Edits launch) ·
[51] en.wikipedia.org/wiki/Edits_(app) · [52] thereelstars.com (Edits audio upgrade) ·
[54] kapwing.com/resources/instagram-first-draft-tested · [55] tomsguide.com (least produced) ·
[56] techbuzz.ai (hashtag cap) · [57] postfa.st/sizes/instagram/reels · [59] foximusic.com (music copyright) ·
[60] primalvideo.com (Edits guide)
