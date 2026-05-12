"""
Utilities for Project 4 instructional-video generation prompts.

This file has no vendor dependency. The provider-specific scripts import it so
that prompts are consistent across OpenAI, Gemini/Veo, Runway, and Replicate.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class DiyStep:
    step_id: str
    domain: str
    step_description: str
    tool_names: str
    supplies_objects: str
    process_technique: str = ""
    safety_equipment: str = ""
    previous_step: str = ""
    next_step: str = ""
    reference_image_url: str = ""


def build_instructional_prompt(
    step: DiyStep,
    architecture: str = "structured",
    duration_seconds: int = 8,
) -> str:
    """Return a concise but explicit prompt for a single DIY micro-clip.

    architecture options:
    - direct: one plain-language instruction
    - structured: action-object-tool decomposition
    - metadata: uses Stesso-like metadata fields
    - reference: includes reference-image guidance when provided
    - sequential: includes previous/next step context for continuity
    - constraints: emphasizes negative constraints and safety
    """
    arch = architecture.strip().lower()
    base = (
        f"Realistic close-up instructional DIY video, {duration_seconds} seconds. "
        f"Step: {step.step_description}. "
        f"Show {step.tool_names} working on {step.supplies_objects}. "
        "Hands visible, stable camera, neutral workshop lighting, no text overlay."
    )

    if arch == "direct":
        return base

    if arch == "metadata":
        return (
            f"{base}\n"
            f"clipDescription: {step.step_description}\n"
            f"toolNames: {step.tool_names}\n"
            f"suppliesNames: {step.supplies_objects}\n"
            f"processTechnique: {step.process_technique or 'single visible manual action'}\n"
            f"safetyEquipment: {step.safety_equipment or 'normal homeowner safety precautions'}\n"
            "Show the start state, the tool-to-object contact point, the motion, and the finished state."
        )

    if arch == "reference":
        reference_line = (
            f"Use this reference image for generic tool/object shape: {step.reference_image_url}. "
            if step.reference_image_url
            else "Use a generic, brand-agnostic reference for the tool shape and scale. "
        )
        return (
            f"{base}\n"
            f"{reference_line}Keep the {step.tool_names} shape, scale, and contact point stable. "
            "Do not change the workpiece material or add extra tools."
        )

    if arch == "sequential":
        return (
            f"{base}\n"
            f"Previous step context, not shown as a separate action: {step.previous_step or 'the work area is already prepared'}.\n"
            f"Current step only: {step.step_description}.\n"
            f"Next step context, not shown as a separate action: {step.next_step or 'the result will be checked afterward'}.\n"
            "Keep the same workpiece, camera distance, and hand orientation throughout."
        )

    if arch == "constraints":
        return (
            f"{base}\n"
            "Constraints: no floating tools, no extra tools, no morphing hands, no reversed action, "
            "no impossible deformation, no dramatic camera move. Show the completed end state for one full second."
        )

    # Default: structured action-object-tool prompt.
    return (
        f"{base}\n"
        f"Action: {step.process_technique or step.step_description}.\n"
        f"Tool: {step.tool_names}, held naturally and correctly.\n"
        f"Object/material: {step.supplies_objects}.\n"
        "Required visual sequence: start state -> visible tool-to-object contact -> full motion -> finished state."
    )


def load_steps_csv(path: str | Path) -> list[DiyStep]:
    """Load a CSV with columns matching DiyStep field names.

    Required columns: step_id, domain, step_description, tool_names, supplies_objects.
    Optional columns: process_technique, safety_equipment, previous_step, next_step, reference_image_url.
    """
    required = {"step_id", "domain", "step_description", "tool_names", "supplies_objects"}
    rows: list[DiyStep] = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required CSV columns: {sorted(missing)}")
        for raw in reader:
            rows.append(DiyStep(**{field.name: raw.get(field.name, "") for field in DiyStep.__dataclass_fields__.values()}))
    return rows


def write_prompt_queue(
    steps: Iterable[DiyStep],
    out_path: str | Path,
    architecture: str = "structured",
    duration_seconds: int = 8,
) -> None:
    """Write step_id, architecture, and prompt to a CSV for batch review."""
    with Path(out_path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["step_id", "architecture", "prompt"])
        writer.writeheader()
        for step in steps:
            writer.writerow(
                {
                    "step_id": step.step_id,
                    "architecture": architecture,
                    "prompt": build_instructional_prompt(step, architecture, duration_seconds),
                }
            )
