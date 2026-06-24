import json

from action_semantics.indexed_videos import flatten_indexed_videos, prepare_indexed_videos
from action_semantics.models import ClipRecord
from action_semantics.text import clip_text_segments


def test_flatten_indexed_videos_preserves_real_clip_fields(tmp_path):
    source_path = tmp_path / "indexed-videos.jsonl"
    source_path.write_text(
        json.dumps(
            {
                "video_id": 42,
                "youtube_id": "abc123",
                "url": "https://example.test/watch?v=abc123",
                "title": "Repair a chair",
                "category": {"name": "Furniture & Decor"},
                "clips": [
                    {
                        "name": "Tighten the loose chair leg",
                        "description": "Use a screwdriver to tighten the leg screw.",
                        "goal": "Stop the chair from wobbling.",
                        "tools": "Screwdriver, clamp",
                        "supplies": "Wood glue",
                        "start": 3.0,
                        "end": 21.5,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    clips, profile = flatten_indexed_videos(source_path)

    assert clips[0]["clip_id"] == "indexed-video-42-clip-000"
    assert clips[0]["title"] == "Tighten the loose chair leg"
    assert clips[0]["gemini_metadata"]["clip"]["tools"] == ["Screwdriver", "clamp"]
    assert clips[0]["gemini_metadata"]["clip"]["supplies"] == ["Wood glue"]
    assert profile["video_count"] == 1
    assert profile["clip_count"] == 1
    assert profile["month1_month2_ready"] is True
    assert profile["month3_ready"] is False
    assert len(profile["month3_blockers"]) == 3


def test_prepare_indexed_videos_writes_flat_export_and_profile(tmp_path):
    source_path = tmp_path / "indexed-videos.jsonl"
    source_path.write_text(
        '{"video_id": 1, "clips": [{"name": "Clean a pipe"}]}\n', encoding="utf-8"
    )

    paths = prepare_indexed_videos(source_path, tmp_path / "prepared")

    assert paths["clips"].exists()
    assert paths["profile"].exists()
    assert json.loads(paths["clips"].read_text(encoding="utf-8").strip())["clip_id"] == (
        "indexed-video-1-clip-000"
    )


def test_indexed_video_inventory_metadata_is_not_parsed_as_action_text():
    clip = ClipRecord(
        clip_id="indexed-video-1-clip-000",
        title="Tighten the hinge",
        gemini_metadata={
            "source_video": {"category": "Cleaning", "title": "How to use a drill"},
            "clip": {"tools": ["Scrubbing brush"], "supplies": ["Baking soda"]},
        },
    )

    segments = clip_text_segments(clip)

    assert [(segment.source_field, segment.text) for segment in segments] == [
        ("title", "Tighten the hinge")
    ]
