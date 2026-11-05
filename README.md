# System Design — Field Guide

An offline Android reader and practice app for a senior-level system design curriculum.

Built with Kotlin and Jetpack Compose. Everything is bundled in the APK: **25 chapters,
309 sections, 283 self-check questions and 80 multiple-choice questions** — no network needed.

## Install

Download `system-design-1.0.0.apk` from [Releases](../../releases/latest) and sideload it:

```bash
adb install system-design-1.0.0.apk
```

Or open the APK on the device and allow installation from your browser/file manager.

Requires Android 8.0 (API 26) or newer. The APK is signed with a local debug key, intended for
personal sideloading — not a Play Store build.

## What's inside

| | |
|---|---|
| **25 chapters** in 6 parts, from foundations to staff-level practice |
| **309 sections** with tables, code blocks, callouts and quotes rendered natively |
| **283 self-check questions** with reveal-on-tap answers |
| **80 exam-style MCQs** across 16 topics, with explanations |
| **Spaced repetition** — missed questions return on a 1, 3, 6, 12… day schedule |
| **Progress** — chapter completion, streak, per-topic accuracy, bookmarks |
| **Search** across every chapter and section |
| **Offline-first** — zero network permissions |

The curriculum covers: foundations and back-of-envelope estimation, scaling and load balancing,
databases, sharding, replication, consistency, caching, queues, distributed primitives, API design,
rate limiting, CDNs, search, storage and media, observability and SLOs, reliability and
multi-region, microservices, data structures at scale, a design playbook, seven worked designs,
a senior-level playbook, an interview playbook and a glossary.

## Build

```bash
export ANDROID_HOME=$HOME/Library/Android/sdk
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
./gradlew assembleRelease
```

The APK lands in `app/build/outputs/apk/release/app-release.apk`.

Release builds are signed with the local debug keystore so the APK is directly installable.
Replace the signing config in `app/build.gradle.kts` with your own keystore before publishing
an update that must be installable over this build.

## Content pipeline

The app does not parse Markdown at runtime. A build-time script converts the curriculum into
typed JSON so the reader can render real tables, code and collapsed answers:

```
curriculum markdown
      │  tools/build_content.py
      ▼
app/src/main/assets/content/
  index.json        parts, chapters, reading times
  ch-00.json …      sections → typed blocks
  questions.json    80 MCQs + 283 self-checks
```

Regenerate after editing content:

```bash
python3 tools/build_content.py \
  --src ../system-design-curriculum \
  --out app/src/main/assets/content
```

Block types: `paragraph`, `heading`, `list`, `table`, `code`, `quote`, `divider`.

## Architecture

```
dev.thalium.systemdesign
├── MainActivity.kt
├── MainViewModel.kt          navigation + search
├── data/
│   ├── Models.kt
│   ├── ContentRepository.kt  asset JSON → Kotlin models (cached)
│   └── ProgressRepository.kt SharedPreferences + StateFlow, streak & SRS
└── ui/
    ├── App.kt                Scaffold, bottom navigation, screen header
    ├── LibraryScreen.kt      parts, chapters, streak
    ├── ChapterScreen.kt      reader, section bookmarks, self-check
    ├── Quiz.kt               shared question card
    ├── PracticeScreen.kt     topic picker + session
    ├── ReviewScreen.kt       spaced repetition queue
    ├── SearchScreen.kt
    ├── StatsScreen.kt
    ├── Blocks.kt             native block renderer + inline markdown
    └── theme/Theme.kt        calm editorial palette and type scale
```

- **No database.** Content is immutable and bundled; progress is a small JSON blob in
  `SharedPreferences`.
- **No DI framework.** A single `AndroidViewModel` owns the two repositories.
- **No navigation library.** A small back stack in `MainViewModel`; the activity handles
  configuration changes itself.
- **SRS** is a lightweight SM-2 variant: correct → interval doubles (3 → 6 → 12 … capped at 45
  days), incorrect → 1 day.

## Content

The curriculum lives in `../system-design-curriculum` in the authoring workspace. It is included
here as compiled JSON under `app/src/main/assets/content`.

## License

Code: MIT. Curriculum text: © the author.
