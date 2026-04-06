#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:
    from datetime import UTC
except ImportError:
    from datetime import timezone

    UTC = timezone.utc


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "use",
    "when",
    "with",
    "within",
}

ACTION_WORDS = {
    "add",
    "build",
    "create",
    "debug",
    "draft",
    "edit",
    "find",
    "fix",
    "generate",
    "handle",
    "implement",
    "improve",
    "inspect",
    "investigate",
    "make",
    "refactor",
    "review",
    "route",
    "scaffold",
    "search",
    "summarize",
    "support",
    "test",
    "update",
    "verify",
    "write",
}

LOW_SIGNAL_TOKENS = STOPWORDS | ACTION_WORDS | {
    "agent",
    "agents",
    "app",
    "code",
    "feature",
    "file",
    "files",
    "issue",
    "issues",
    "problem",
    "problems",
    "project",
    "repo",
    "repository",
    "request",
    "screen",
    "task",
    "workflow",
}

DEFAULT_CATEGORY = "workflow"

CATEGORY_RULES: dict[str, dict[str, Any]] = {
    "ios": {
        "keywords": [
            "ios",
            "ipad",
            "iphone",
            "swift",
            "swiftui",
            "xcode",
            "cloudkit",
            "firebase",
            "ocr",
            "vision",
            "modelcontext",
            "swiftdata",
        ],
        "steps": [
            "Inspect the touched Swift, SwiftUI, and service files before changing behavior.",
            "Preserve the layer boundaries and platform rules already documented in CLAUDE.md.",
            "Implement the smallest safe change for the requested iOS workflow and keep state updates explicit.",
            "Run the narrowest relevant build or test command, or record the exact reason verification could not run.",
        ],
        "validation": [
            "Run the smallest relevant `xcodebuild` build or test for the touched code.",
            "Re-check `CLAUDE.md` rules if the change touches `Domain/`, `Presentation/`, or Firebase integration.",
            "Confirm UI-state and async behavior on the affected screen when presentation code changes.",
        ],
        "examples": [
            "Debug OCR extraction regressions in the iOS app without breaking the domain boundaries.",
            "Investigate CloudKit or Firebase-related app behavior and verify the affected workflow.",
        ],
    },
    "frontend": {
        "keywords": [
            "frontend",
            "react",
            "tsx",
            "tailwind",
            "vite",
            "css",
            "ui",
            "ux",
            "component",
            "page",
            "browser",
            "playwright",
            "vitest",
        ],
        "steps": [
            "Inspect the current page, component, and styling patterns before changing UI behavior.",
            "Keep the existing design language and interaction model consistent unless the task explicitly changes them.",
            "Implement the narrowest component, route, or styling changes needed for the request.",
            "Run the smallest relevant frontend test or build step and capture any remaining manual QA gap.",
        ],
        "validation": [
            "Run the relevant unit, integration, or build command for the touched frontend area.",
            "Check the affected UI states, loading paths, and empty states if the change is user-facing.",
            "Verify that class names, route wiring, and shared utilities still align after the edit.",
        ],
        "examples": [
            "Refine a React page or component while preserving the existing design system.",
            "Fix a frontend interaction regression and verify the result with targeted tests or build checks.",
        ],
    },
    "docs": {
        "keywords": [
            "doc",
            "docs",
            "documentation",
            "markdown",
            "readme",
            "policy",
            "spec",
            "srs",
            "draft",
            "summary",
            "writeup",
            "compliance",
            "privacy",
        ],
        "steps": [
            "Gather the smallest set of source artifacts needed to write the document accurately.",
            "Extract decisions, dates, and constraints directly from source material before drafting new text.",
            "Write the document in a structure that optimizes quick scanning and future reuse.",
            "Proofread headings, links, dates, and factual claims against the source files before finishing.",
        ],
        "validation": [
            "Re-check names, dates, and references against the source documents after drafting.",
            "Ensure headings and section ordering match the intended audience and file conventions.",
            "Remove unsupported claims and keep the output grounded in the cited project artifacts.",
        ],
        "examples": [
            "Draft a project summary, policy, or implementation note from current repository documents.",
            "Update Markdown documentation so it matches the latest code or planning state.",
        ],
    },
    "testing": {
        "keywords": [
            "test",
            "tests",
            "unittest",
            "integration",
            "regression",
            "qa",
            "assertion",
            "coverage",
            "verify",
            "verification",
            "failing",
            "failure",
        ],
        "steps": [
            "Identify the exact behavior that should fail or pass before changing the test surface.",
            "Locate the smallest existing test scope that already covers the affected workflow.",
            "Add or adjust targeted tests so they prove the intended behavior rather than implementation trivia.",
            "Run the relevant test command and summarize what still remains unverified.",
        ],
        "validation": [
            "Run the narrowest test target that exercises the changed behavior.",
            "Check that the new assertions would fail without the intended fix.",
            "Record any intentionally skipped test coverage with the reason and remaining risk.",
        ],
        "examples": [
            "Add or adjust targeted regression tests for a known failing workflow.",
            "Narrow down a failing test surface and leave behind stable coverage for the fix.",
        ],
    },
    "github": {
        "keywords": [
            "github",
            "pull request",
            "pr",
            "review",
            "reviewer",
            "comment",
            "issue",
            "actions",
            "workflow run",
            "checks",
            "ci",
        ],
        "steps": [
            "Resolve the exact repository, PR, issue, or branch context before acting.",
            "Inspect the smallest amount of review, diff, or CI context needed for the request.",
            "Apply the requested GitHub-side change or related code change without broadening scope.",
            "Re-check status, comments, or requested-change state so the outcome is explicit.",
        ],
        "validation": [
            "Verify the target PR, issue, or branch before writing comments or applying labels.",
            "Re-check unresolved review or CI state after making the requested change.",
            "Summarize what changed, what remains open, and what evidence supports the conclusion.",
        ],
        "examples": [
            "Address actionable pull request feedback and summarize what still remains.",
            "Inspect a GitHub PR or issue, handle the requested task, and verify the updated state.",
        ],
    },
    "backend": {
        "keywords": [
            "api",
            "backend",
            "server",
            "endpoint",
            "database",
            "db",
            "migration",
            "schema",
            "service",
            "auth",
            "query",
            "worker",
        ],
        "steps": [
            "Inspect the current contract, schema, and call sites before changing backend behavior.",
            "Keep API boundaries, data shape, and error handling explicit while implementing the change.",
            "Update the narrowest service or persistence layer needed for the request.",
            "Run the relevant tests or contract checks and record any follow-up risk.",
        ],
        "validation": [
            "Run the smallest relevant backend test or validation command for the touched code path.",
            "Check contract shape, migrations, and error handling if the request changes data flow.",
            "Verify dependent call sites still match the updated interface after the edit.",
        ],
        "examples": [
            "Implement or debug an API or database workflow while preserving contract compatibility.",
            "Investigate a backend service issue and verify the fix with targeted checks.",
        ],
    },
    "workflow": {
        "keywords": [
            "workflow",
            "automation",
            "agent",
            "reuse",
            "search",
            "route",
            "scaffold",
            "template",
            "orchestration",
        ],
        "steps": [
            "Clarify the repeatable workflow, its trigger conditions, and the intended reusable outcome.",
            "Search for existing local skills, scripts, references, or assets before creating new ones.",
            "Capture the reusable steps and the minimum metadata needed for future discovery.",
            "Validate that another agent could find and reuse the resulting workflow with minimal context.",
        ],
        "validation": [
            "Check that the workflow is discoverable by name, tags, or trigger phrases.",
            "Confirm the documented steps are short, procedural, and actually reusable.",
            "Refresh the skill registry after any change so future agents can resolve the skill immediately.",
        ],
        "examples": [
            "Create or refine a repeatable local workflow that other agents can search and reuse.",
            "Search for an existing reusable process before inventing a new one.",
        ],
    },
}

TITLE_CASE_OVERRIDES = {
    "api": "API",
    "ci": "CI",
    "claude": "Claude",
    "cloudkit": "CloudKit",
    "firebase": "Firebase",
    "github": "GitHub",
    "ios": "iOS",
    "ipad": "iPad",
    "iphone": "iPhone",
    "ocr": "OCR",
    "pr": "PR",
    "swiftui": "SwiftUI",
    "ui": "UI",
    "ux": "UX",
    "xcode": "Xcode",
}

PROTECTED_SKILLS = {"project-skill-router", "omc-reference"}
ARCHIVE_DIRNAME = "_archived"
USAGE_FILENAME = "usage.json"
USAGE_HISTORY_LIMIT = 12
ACTIVE_RECENT_DAYS = 14
PRUNE_NEVER_REUSED_DAYS = 21
PRUNE_SINGLE_REUSE_DAYS = 45
PRUNE_LOW_REUSE_DAYS = 90
DEFAULT_MANAGEMENT_MODE = "patch"
REFRESH_STALE_DAYS = 45
REFRESH_LOW_SCORE_THRESHOLD = 10.0
REFRESH_SCORE_HISTORY_LIMIT = 8
REFRESH_TAG_LIMIT = 8
REFRESH_TRIGGER_LIMIT = 6
REFRESH_EXAMPLE_LIMIT = 6
SUBTASK_ROUTING_COMMAND = 'python3 .claude/tools/skill_agent.py auto "<sub-task>" --json'


@dataclass(slots=True)
class SkillRecord:
    name: str
    path: str
    description: str
    category: str
    tags: list[str]
    triggers: list[str]
    summary: str
    steps: list[str]
    related_skills: list[str]
    validation: list[str]
    examples: list[str]
    title: str
    management_mode: str


@dataclass(slots=True)
class SkillBlueprint:
    name: str
    title: str
    description: str
    category: str
    summary: str
    tags: list[str]
    triggers: list[str]
    steps: list[str]
    related_skills: list[str]
    validation: list[str]
    examples: list[str]
    source_task: str


@dataclass(slots=True)
class SkillRefreshPlan:
    name: str
    path: str
    status: str
    reason: str
    management_mode: str
    changes: dict[str, Any]
    recent_tasks: list[str]
    reuse_count: int
    avg_score: float | None
    updated_days: int


@dataclass(slots=True, frozen=True)
class CliArgument:
    flags: tuple[str, ...]
    kwargs: dict[str, Any]


@dataclass(slots=True, frozen=True)
class CliCommand:
    name: str
    help: str
    handler: Callable[[argparse.Namespace], int]
    arguments: tuple[CliArgument, ...] = ()
    configure: Callable[[argparse.ArgumentParser], None] | None = None


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search, rank, scaffold, and index repo-local Claude skills."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in build_command_specs():
        command_parser = subparsers.add_parser(command.name, help=command.help)
        add_shared_location_args(command_parser)
        if command.configure:
            command.configure(command_parser)
        add_cli_arguments(command_parser, command.arguments)
        command_parser.set_defaults(func=command.handler)

    return parser


def add_cli_arguments(
    parser: argparse.ArgumentParser,
    arguments: tuple[CliArgument, ...],
) -> None:
    for argument in arguments:
        parser.add_argument(*argument.flags, **argument.kwargs)


def add_shared_location_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Repository root. Defaults to auto-detecting from the current working directory.",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        help="Skills directory. Defaults to <repo-root>/.claude/skills.",
    )
    parser.add_argument(
        "--registry-path",
        type=Path,
        help="Registry path. Defaults to <skills-dir>/registry.json.",
    )


def add_create_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("name", help="Skill name. Will be normalized to hyphen-case.")
    parser.add_argument("--summary", required=True, help="What the skill does.")
    parser.add_argument(
        "--when",
        required=True,
        help="When the agent should use the skill.",
    )
    parser.add_argument(
        "--category",
        default=DEFAULT_CATEGORY,
        help=f"Skill category. Defaults to {DEFAULT_CATEGORY!r}.",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Tag to index for search. Repeat to add more.",
    )
    parser.add_argument(
        "--trigger",
        action="append",
        default=[],
        help="Trigger phrase that should lead an agent to this skill.",
    )
    parser.add_argument(
        "--step",
        action="append",
        default=[],
        help="Workflow step to include in the skill body. Repeat to add more.",
    )
    parser.add_argument(
        "--related",
        action="append",
        default=[],
        help="Related skill name. Repeat to add more.",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite an existing skill directory."
    )


def cmd_list(args: argparse.Namespace) -> int:
    records, _, _ = load_records_from_args(args)
    if args.json:
        print(json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2))
        return 0

    for record in records:
        print(f"{record.name}\t{record.category}\t{record.path}")
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    records, skills_dir, registry_path = load_records_from_args(args)
    write_registry(records, registry_path)
    relative_registry = safe_relative_path(registry_path, skills_dir.parent)
    print(f"Refreshed {len(records)} skills into {relative_registry}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    records, _, _ = load_records_from_args(args)
    matches = search_records(records, args.query, limit=args.top)
    if args.json:
        payload = [
            {"score": score, "reason": reason, **asdict(record)}
            for score, reason, record in matches
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not matches:
        print("No matching skills found.")
        return 0

    for score, reason, record in matches:
        print(f"[{score:.1f}] {record.name} ({record.category})")
        print(f"  path: {record.path}")
        print(f"  reason: {reason}")
        print(f"  summary: {record.summary}")
    return 0


def cmd_suggest(args: argparse.Namespace) -> int:
    records, _, _ = load_records_from_args(args)
    matches = search_records(records, args.task, limit=args.top)
    if args.json:
        payload = {
            "task": args.task,
            "matches": [
                {"score": score, "reason": reason, **asdict(record)}
                for score, reason, record in matches
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Task: {args.task}")
    if not matches:
        print("No reusable skill found. Consider creating a new one.")
        return 0

    for index, (score, reason, record) in enumerate(matches, start=1):
        print(f"{index}. {record.name} [{score:.1f}]")
        print(f"   path: {record.path}")
        print(f"   reason: {reason}")
        print(f"   use: {record.description}")
    best_score = matches[0][0]
    if best_score < 4.0:
        print("Recommendation: no strong match; scaffold a new reusable skill.")
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    records, _, _ = load_records_from_args(args)
    matches = search_records(records, args.task, limit=1)
    if not matches:
        print("")
        return 1
    score, _, record = matches[0]
    if score < args.min_score:
        print("")
        return 1
    print(record.path)
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    existing_records, skills_dir, registry_path = load_records_from_args(args)
    blueprint = build_manual_blueprint(
        raw_name=args.name,
        summary=args.summary,
        when=args.when,
        category=args.category,
        tags=args.tag,
        triggers=args.trigger,
        steps=args.step,
        related_skills=args.related,
        existing_records=existing_records,
    )
    record = create_skill(skills_dir=skills_dir, blueprint=blueprint, force=args.force)
    records = discover_skills(skills_dir)
    write_registry(records, registry_path)
    record_skill_event(
        usage_path=resolve_usage_path(skills_dir),
        record=record,
        action="manual-create",
        task=blueprint.source_task,
    )
    print(f"Created {record.name} at {record.path}")
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    existing_records, skills_dir, registry_path = load_records_from_args(args)
    blueprint = build_bootstrap_blueprint(
        task=args.task,
        raw_name=args.name,
        category=args.category,
        extra_tags=args.tag,
        existing_records=existing_records,
    )

    if args.dry_run:
        emit_blueprint_preview(blueprint, as_json=args.json)
        return 0

    record = create_skill(skills_dir=skills_dir, blueprint=blueprint, force=args.force)
    records = discover_skills(skills_dir)
    write_registry(records, registry_path)
    record_skill_event(
        usage_path=resolve_usage_path(skills_dir),
        record=record,
        action="manual-bootstrap",
        task=blueprint.source_task,
    )
    if args.json:
        payload = blueprint_payload(blueprint)
        payload["path"] = record.path
        payload["created"] = True
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"Bootstrapped {record.name} at {record.path}")
    return 0


def cmd_auto(args: argparse.Namespace) -> int:
    records, skills_dir, registry_path = load_records_from_args(args)
    matches = search_records(records, args.task, limit=3)
    preferred_match = choose_auto_match(matches, args.task)
    usage_path = resolve_usage_path(skills_dir)

    if preferred_match and preferred_match[0] >= args.min_score:
        score, reason, record = preferred_match
        record_skill_event(
            usage_path=usage_path,
            record=record,
            action="auto-reuse",
            task=args.task,
            score=score,
        )
        skill_update = None
        if not args.skip_update:
            skill_update = maybe_auto_update_skill(
                record=record,
                skills_dir=skills_dir,
                registry_path=registry_path,
                usage_path=usage_path,
                task=args.task,
            )
        payload = {
            "action": "reuse",
            "task": clean_text(args.task),
            "match": match_payload(score, reason, record),
        }
        if skill_update:
            payload["skill_update"] = skill_update
        emit_auto_result(payload, as_json=args.json)
        return 0

    blueprint = build_bootstrap_blueprint(
        task=args.task,
        raw_name=None,
        category=args.category,
        extra_tags=args.tag,
        existing_records=records,
    )

    if args.dry_run:
        payload = {
            "action": "preview-create",
            "task": clean_text(args.task),
            "min_score": args.min_score,
            "best_match": match_payload(*preferred_match) if preferred_match else None,
            "blueprint": blueprint_payload(blueprint),
        }
        emit_auto_result(payload, as_json=args.json)
        return 0

    record = create_skill(skills_dir=skills_dir, blueprint=blueprint, force=args.force)
    updated_records = discover_skills(skills_dir)
    write_registry(updated_records, registry_path)
    record_skill_event(
        usage_path=usage_path,
        record=record,
        action="auto-created",
        task=blueprint.source_task,
    )
    payload = {
        "action": "created",
        "task": clean_text(args.task),
        "min_score": args.min_score,
        "best_match": match_payload(*preferred_match) if preferred_match else None,
        "created_skill": asdict(record),
        "blueprint": blueprint_payload(blueprint),
    }
    emit_auto_result(payload, as_json=args.json)
    return 0


def cmd_usage(args: argparse.Namespace) -> int:
    records, skills_dir, _ = load_records_from_args(args)
    summaries = build_skill_usage_summaries(records, resolve_usage_path(skills_dir))
    if args.status != "all":
        summaries = [item for item in summaries if item["status"] == args.status]

    if args.json:
        print(json.dumps(summaries, ensure_ascii=False, indent=2))
        return 0

    if not summaries:
        print("No skill usage data available.")
        return 0

    for item in summaries:
        print(
            f"[{item['status']}] {item['name']} "
            f"reuse={item['reuse_count']} create={item['create_count']} "
            f"last={item['last_activity_days']}d age={item['age_days']}d"
        )
        print(f"  path: {item['path']}")
        print(f"  reason: {item['reason']}")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    records, skills_dir, _ = load_records_from_args(args)
    plans = build_skill_refresh_plans(records, resolve_usage_path(skills_dir))
    if args.status != "all":
        plans = [plan for plan in plans if plan.status == args.status]

    payload = [refresh_plan_payload(plan) for plan in plans]
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not payload:
        print("No skill refresh candidates.")
        return 0

    for item in payload:
        print(f"[{item['status']}] {item['name']} ({item['management_mode']})")
        print(f"  path: {item['path']}")
        print(f"  reason: {item['reason']}")
        if item["updated_fields"]:
            print(f"  fields: {', '.join(item['updated_fields'])}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    records, skills_dir, registry_path = load_records_from_args(args)
    usage_path = resolve_usage_path(skills_dir)
    plans = build_skill_refresh_plans(records, usage_path)
    if args.name:
        normalized_name = normalize_name(args.name)
        plans = [plan for plan in plans if plan.name == normalized_name]
        if not plans:
            raise SystemExit(f"No skill named {normalized_name} was found.")
    else:
        plans = [plan for plan in plans if plan.status == "candidate"]

    payload = [refresh_plan_payload(plan) for plan in plans]
    if not args.apply:
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if not payload:
            print("No skill refresh candidates.")
            return 0
        for item in payload:
            print(f"[{item['status']}] {item['name']} ({item['management_mode']})")
            print(f"  path: {item['path']}")
            print(f"  reason: {item['reason']}")
            if item["updated_fields"]:
                print(f"  fields: {', '.join(item['updated_fields'])}")
        print("Next: rerun with `--apply` to persist these metadata updates.")
        return 0

    if not plans:
        if args.json:
            print(json.dumps([], ensure_ascii=False, indent=2))
        else:
            print("No skill refresh candidates.")
        return 0

    records_by_name = {record.name: record for record in records}
    updated: list[dict[str, Any]] = []
    for plan in plans:
        if plan.status != "candidate":
            continue
        record = records_by_name.get(plan.name)
        if not record:
            continue
        updated.append(
            apply_skill_update_plan(
                record=record,
                plan=plan,
                usage_path=usage_path,
                task=plan.recent_tasks[0] if plan.recent_tasks else f"refresh {plan.name}",
                action="manual-update",
            )
        )

    updated_records = discover_skills(skills_dir)
    write_registry(updated_records, registry_path)

    if args.json:
        print(json.dumps(updated, ensure_ascii=False, indent=2))
        return 0

    if not updated:
        print("No skill refresh candidates.")
        return 0

    for item in updated:
        print(f"[updated] {item['name']} ({item['management_mode']})")
        print(f"  path: {item['path']}")
        print(f"  fields: {', '.join(item['updated_fields'])}")
        print(f"  reason: {item['reason']}")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    records, skills_dir, registry_path = load_records_from_args(args)
    usage_path = resolve_usage_path(skills_dir)
    summaries = build_skill_usage_summaries(records, usage_path)
    candidates = [item for item in summaries if item["status"] == "candidate"]

    if args.json and not args.apply:
        print(json.dumps(candidates, ensure_ascii=False, indent=2))
        return 0

    if not candidates:
        if args.json:
            print(json.dumps([], ensure_ascii=False, indent=2))
        else:
            print("No prune candidates.")
        return 0

    if not args.apply:
        for item in candidates:
            print(f"[candidate] {item['name']}")
            print(f"  path: {item['path']}")
            print(f"  reason: {item['reason']}")
        print("Next: rerun with `--apply` to archive these skills.")
        return 0

    archived = archive_skill_candidates(candidates, skills_dir, usage_path)
    updated_records = discover_skills(skills_dir)
    write_registry(updated_records, registry_path)

    if args.json:
        print(json.dumps(archived, ensure_ascii=False, indent=2))
        return 0

    for item in archived:
        print(f"[archived] {item['name']}")
        print(f"  from: {item['from_path']}")
        print(f"  to: {item['archived_path']}")
        print(f"  reason: {item['reason']}")
    return 0


def build_command_specs() -> list[CliCommand]:
    return [
        CliCommand(
            name="list",
            help="List discovered skills.",
            handler=cmd_list,
            arguments=(cli_argument("--json", action="store_true", help="Emit JSON."),),
        ),
        CliCommand(
            name="refresh",
            help="Scan skills and rebuild the registry file.",
            handler=cmd_refresh,
        ),
        CliCommand(
            name="search",
            help="Search skills by task, trigger, category, or tags.",
            handler=cmd_search,
            arguments=(
                cli_argument("query", help="Search query."),
                cli_argument("--top", type=int, default=5, help="Result limit."),
                cli_argument("--json", action="store_true", help="Emit JSON."),
            ),
        ),
        CliCommand(
            name="suggest",
            help="Recommend the best skill matches for a task.",
            handler=cmd_suggest,
            arguments=(
                cli_argument("task", help="Natural-language task description."),
                cli_argument("--top", type=int, default=3, help="Result limit."),
                cli_argument("--json", action="store_true", help="Emit JSON."),
            ),
        ),
        CliCommand(
            name="resolve",
            help="Return the best-matching skill path for a task.",
            handler=cmd_resolve,
            arguments=(
                cli_argument("task", help="Natural-language task description."),
                cli_argument(
                    "--min-score",
                    type=float,
                    default=4.0,
                    help="Minimum score required to treat the match as reusable.",
                ),
            ),
        ),
        CliCommand(
            name="create",
            help="Create a new skill with structured metadata.",
            handler=cmd_create,
            configure=add_create_arguments,
        ),
        CliCommand(
            name="bootstrap",
            help="Create a richer new skill from a task statement using inferred metadata.",
            handler=cmd_bootstrap,
            arguments=(
                cli_argument("task", help="Task statement used to scaffold a skill."),
                cli_argument(
                    "--name",
                    help="Explicit skill name. When omitted, derive one from the task.",
                ),
                cli_argument(
                    "--category",
                    default="auto",
                    help="Skill category. Defaults to auto inference from the task.",
                ),
                cli_argument(
                    "--tag",
                    action="append",
                    default=[],
                    help="Extra tag. Repeat to add more.",
                ),
                cli_argument(
                    "--dry-run",
                    action="store_true",
                    help="Preview the generated skill without writing files.",
                ),
                cli_argument(
                    "--json",
                    action="store_true",
                    help="Emit the generated skill preview as JSON.",
                ),
                cli_argument(
                    "--force",
                    action="store_true",
                    help="Overwrite an existing skill directory.",
                ),
            ),
        ),
        CliCommand(
            name="auto",
            help="Resolve the best local skill for a task, or create one automatically when missing.",
            handler=cmd_auto,
            arguments=(
                cli_argument("task", help="Task statement to resolve against local skills."),
                cli_argument(
                    "--min-score",
                    type=float,
                    default=8.0,
                    help="Minimum score required to reuse an existing skill.",
                ),
                cli_argument(
                    "--category",
                    default="auto",
                    help="Category hint when a new skill must be generated.",
                ),
                cli_argument(
                    "--tag",
                    action="append",
                    default=[],
                    help="Extra tag to include if a new skill is generated.",
                ),
                cli_argument(
                    "--dry-run",
                    action="store_true",
                    help="Do not write files when no reusable skill exists; return a creation preview instead.",
                ),
                cli_argument(
                    "--skip-update",
                    action="store_true",
                    help="Skip automatic metadata refresh after reusing an existing skill.",
                ),
                cli_argument("--json", action="store_true", help="Emit JSON."),
                cli_argument(
                    "--force",
                    action="store_true",
                    help="Overwrite an existing generated skill if needed.",
                ),
            ),
        ),
        CliCommand(
            name="usage",
            help="Show skill reuse frequency, freshness, and cleanup candidates.",
            handler=cmd_usage,
            arguments=(
                cli_argument("--json", action="store_true", help="Emit JSON."),
                cli_argument(
                    "--status",
                    default="all",
                    choices=["all", "active", "stale", "candidate", "protected"],
                    help="Filter by computed usage status.",
                ),
            ),
        ),
        CliCommand(
            name="review",
            help="Review existing skills for safe metadata refresh candidates.",
            handler=cmd_review,
            arguments=(
                cli_argument("--json", action="store_true", help="Emit JSON."),
                cli_argument(
                    "--status",
                    default="candidate",
                    choices=["all", "candidate", "healthy", "protected", "locked"],
                    help="Filter by computed refresh status.",
                ),
            ),
        ),
        CliCommand(
            name="update",
            help="Preview or apply safe metadata refreshes for existing skills.",
            handler=cmd_update,
            arguments=(
                cli_argument(
                    "name",
                    nargs="?",
                    help="Specific skill name. When omitted, operate on all refresh candidates.",
                ),
                cli_argument("--json", action="store_true", help="Emit JSON."),
                cli_argument(
                    "--apply",
                    action="store_true",
                    help="Apply the planned metadata updates instead of only previewing them.",
                ),
            ),
        ),
        CliCommand(
            name="prune",
            help="Archive low-value skills that have seen little or no reuse.",
            handler=cmd_prune,
            arguments=(
                cli_argument("--json", action="store_true", help="Emit JSON."),
                cli_argument(
                    "--apply",
                    action="store_true",
                    help="Archive the current candidates instead of only previewing them.",
                ),
            ),
        ),
    ]


def cli_argument(*flags: str, **kwargs: Any) -> CliArgument:
    return CliArgument(flags=tuple(flags), kwargs=kwargs)


def load_records_from_args(
    args: argparse.Namespace,
) -> tuple[list[SkillRecord], Path, Path]:
    repo_root = resolve_repo_root(args.repo_root)
    skills_dir = (args.skills_dir or repo_root / ".claude" / "skills").resolve()
    registry_path = (args.registry_path or skills_dir / "registry.json").resolve()
    records = discover_skills(skills_dir)
    return records, skills_dir, registry_path


def resolve_repo_root(explicit_root: Path | None) -> Path:
    if explicit_root:
        return explicit_root.resolve()

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".claude").exists():
            return candidate
    return current


def discover_skills(skills_dir: Path) -> list[SkillRecord]:
    records: list[SkillRecord] = []
    if not skills_dir.exists():
        return records

    for skill_file in sorted(skills_dir.rglob("SKILL.md")):
        if ARCHIVE_DIRNAME in skill_file.parts:
            continue
        record = parse_skill(skill_file)
        if record:
            records.append(record)
    return sorted(records, key=lambda item: (item.category, item.name))


def parse_skill(skill_file: Path) -> SkillRecord | None:
    text = skill_file.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    name = normalize_name(str(frontmatter.get("name") or skill_file.parent.name))
    description = clean_text(str(frontmatter.get("description") or ""))
    title = extract_title(body) or name.replace("-", " ").title()

    companion_metadata = load_companion_metadata(skill_file.parent / "skill.json")
    summary = clean_text(str(companion_metadata.get("summary") or description or title))
    category = normalize_category(
        str(companion_metadata.get("category") or DEFAULT_CATEGORY),
        summary,
    )
    tags = unique_strings(companion_metadata.get("tags", []))
    triggers = unique_strings(companion_metadata.get("triggers", []))
    steps = unique_strings(companion_metadata.get("steps", []))
    related_skills = unique_strings(companion_metadata.get("related_skills", []))
    validation = unique_strings(companion_metadata.get("validation", []))
    examples = unique_strings(companion_metadata.get("examples", []))
    management_mode = normalize_management_mode(
        companion_metadata.get("management_mode", DEFAULT_MANAGEMENT_MODE)
    )

    if not description:
        description = summary

    return SkillRecord(
        name=name,
        path=str(skill_file.parent),
        description=description,
        category=category,
        tags=tags,
        triggers=triggers,
        summary=summary,
        steps=steps,
        related_skills=related_skills,
        validation=validation,
        examples=examples,
        title=title,
        management_mode=management_mode,
    )


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return {}, text

    frontmatter: dict[str, Any] = {}
    for line in lines[1:closing_index]:
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        frontmatter[key.strip()] = parse_scalar(raw_value.strip())

    body = "\n".join(lines[closing_index + 1 :]).lstrip()
    return frontmatter, body


def parse_scalar(raw_value: str) -> Any:
    if raw_value in {"true", "false"}:
        return raw_value == "true"
    if raw_value.startswith(("'", '"')) and raw_value.endswith(("'", '"')):
        return raw_value[1:-1]
    return raw_value


def load_companion_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def normalize_management_mode(value: Any) -> str:
    if not isinstance(value, str):
        return DEFAULT_MANAGEMENT_MODE
    normalized = clean_text(value).lower()
    if normalized in {"locked", "managed", "patch"}:
        return normalized
    return DEFAULT_MANAGEMENT_MODE


def extract_title(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def unique_strings(values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    if not isinstance(values, list):
        return result
    for value in values:
        if not isinstance(value, str):
            continue
        item = clean_text(value)
        if not item or item in seen:
            continue
        result.append(item)
        seen.add(item)
    return result


def search_records(
    records: list[SkillRecord],
    query: str,
    *,
    limit: int,
) -> list[tuple[float, str, SkillRecord]]:
    query_text = clean_text(query).lower()
    query_tokens = tokenize(query_text)
    if not query_tokens:
        return []

    matches: list[tuple[float, str, SkillRecord]] = []
    for record in records:
        score, reasons = score_record(record, query_text, query_tokens)
        if score <= 0:
            continue
        matches.append((score, ", ".join(reasons[:3]), record))

    matches.sort(key=lambda item: (-item[0], item[2].name))
    return matches[:limit]


def score_record(
    record: SkillRecord,
    query_text: str,
    query_tokens: set[str],
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    name_tokens = tokenize(record.name.replace("-", " "))
    category_tokens = tokenize(record.category.replace("-", " "))
    title_tokens = tokenize(record.title)
    description_tokens = tokenize(record.description)
    summary_tokens = tokenize(record.summary)
    tag_tokens = {token for tag in record.tags for token in tokenize(tag)}
    trigger_tokens = {token for phrase in record.triggers for token in tokenize(phrase)}
    step_tokens = {token for step in record.steps for token in tokenize(step)}
    related_tokens = {token for name in record.related_skills for token in tokenize(name)}
    validation_tokens = {
        token for check in record.validation for token in tokenize(check)
    }
    example_tokens = {token for example in record.examples for token in tokenize(example)}

    if query_text in record.name:
        score += 6.0
        reasons.append("full skill-name match")
    if query_text in record.description.lower():
        score += 5.0
        reasons.append("description phrase match")
    if query_text in record.summary.lower():
        score += 4.5
        reasons.append("summary phrase match")

    intersections = [
        ("name", name_tokens, 4.0),
        ("category", category_tokens, 3.0),
        ("title", title_tokens, 2.5),
        ("tags", tag_tokens, 2.5),
        ("triggers", trigger_tokens, 2.5),
        ("description", description_tokens, 1.75),
        ("summary", summary_tokens, 1.75),
        ("steps", step_tokens, 1.0),
        ("validation", validation_tokens, 1.0),
        ("examples", example_tokens, 1.0),
        ("related", related_tokens, 1.0),
    ]

    for label, tokens, weight in intersections:
        overlap = query_tokens & tokens
        if not overlap:
            continue
        score += weight * len(overlap)
        reasons.append(f"{label} overlap: {', '.join(sorted(overlap)[:3])}")

    if record.category in query_text:
        score += 1.5
        reasons.append("category phrase match")

    return score, reasons


def tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,}", text.lower())
    return {token for token in tokens if token not in STOPWORDS}


def ordered_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,}", text.lower())
    ordered: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in seen or token in STOPWORDS:
            continue
        ordered.append(token)
        seen.add(token)
    return ordered


def build_manual_blueprint(
    *,
    raw_name: str,
    summary: str,
    when: str,
    category: str,
    tags: list[str],
    triggers: list[str],
    steps: list[str],
    related_skills: list[str],
    existing_records: list[SkillRecord],
) -> SkillBlueprint:
    normalized_summary = sentence_case(summary)
    source_task = clean_text(f"{summary} {when}")
    normalized_category = normalize_category(category, source_task)
    focus = derive_focus_phrase(source_task)
    inferred_tags = infer_tags(source_task, normalized_category, tags)
    inferred_triggers = unique_strings(triggers) or infer_trigger_phrases(
        source_task, normalized_category
    )
    inferred_steps = ensure_nested_skill_routing_step(
        unique_strings(steps) or infer_steps(normalized_category, normalized_summary)
    )
    inferred_validation = infer_validation(normalized_category)
    inferred_examples = infer_examples(
        normalized_category, normalized_summary, focus, inferred_triggers
    )
    inferred_related = (
        unique_strings(related_skills)
        or suggest_related_skills(
            existing_records, source_task, exclude_name=normalize_name(raw_name)
        )
    )

    description = ensure_sentence(
        f"{normalized_summary.rstrip('.')} . Use when {clean_text(when).rstrip('.')}"
    ).replace(" .", ".")
    name = normalize_name(raw_name)
    return SkillBlueprint(
        name=name,
        title=build_title(name),
        description=description,
        category=normalized_category,
        summary=normalized_summary,
        tags=inferred_tags,
        triggers=inferred_triggers,
        steps=inferred_steps,
        related_skills=inferred_related,
        validation=inferred_validation,
        examples=inferred_examples,
        source_task=source_task,
    )


def build_bootstrap_blueprint(
    *,
    task: str,
    raw_name: str | None,
    category: str,
    extra_tags: list[str],
    existing_records: list[SkillRecord],
) -> SkillBlueprint:
    source_task = clean_text(task)
    normalized_category = normalize_category(category, source_task)
    name = normalize_name(raw_name or derive_name_from_task(source_task))
    summary = derive_summary_from_task(source_task)
    when = build_when_clause(source_task)
    focus = derive_focus_phrase(source_task)
    inferred_triggers = infer_trigger_phrases(source_task, normalized_category)
    inferred_steps = ensure_nested_skill_routing_step(
        infer_steps(normalized_category, source_task)
    )
    inferred_validation = infer_validation(normalized_category)
    inferred_examples = infer_examples(
        normalized_category, summary, focus, inferred_triggers
    )
    inferred_related = suggest_related_skills(
        existing_records, source_task, exclude_name=name
    )
    description = ensure_sentence(f"{summary.rstrip('.')} . Use when {when}").replace(" .", ".")

    return SkillBlueprint(
        name=name,
        title=build_title(name),
        description=description,
        category=normalized_category,
        summary=summary,
        tags=infer_tags(source_task, normalized_category, extra_tags),
        triggers=inferred_triggers,
        steps=inferred_steps,
        related_skills=inferred_related,
        validation=inferred_validation,
        examples=inferred_examples,
        source_task=source_task,
    )


def normalize_category(category: str, task_text: str) -> str:
    normalized = normalize_name(category)
    if not normalized or normalized == "auto":
        return infer_category(task_text)
    return normalized


def infer_category(task_text: str) -> str:
    lowered = task_text.lower()
    tokens = tokenize(task_text)
    best_category = DEFAULT_CATEGORY
    best_score = 0

    for category, rule in CATEGORY_RULES.items():
        score = 0
        for keyword in rule["keywords"]:
            normalized_keyword = keyword.lower()
            if " " in normalized_keyword and normalized_keyword in lowered:
                score += 3
                continue
            keyword_tokens = tokenize(normalized_keyword)
            overlap = tokens & keyword_tokens
            if overlap:
                score += len(overlap)
        if score > best_score:
            best_category = category
            best_score = score

    return best_category


def infer_tags(task_text: str, category: str, extra_tags: list[str]) -> list[str]:
    tags: list[str] = []
    tags.append(category)
    for token in ordered_tokens(task_text):
        if token in LOW_SIGNAL_TOKENS:
            continue
        tags.append(token)
        if len(tags) >= 5:
            break
    tags.extend(extra_tags)
    return unique_strings(tags)


def infer_trigger_phrases(task_text: str, category: str) -> list[str]:
    cleaned = clean_text(task_text).rstrip(".")
    focus = derive_focus_phrase(cleaned)
    action = detect_action_word(cleaned)
    triggers = [cleaned]

    if focus and focus != cleaned:
        triggers.append(focus)

    if action and focus:
        if action in {"debug", "fix", "investigate", "inspect"}:
            triggers.append(f"{focus} issue")
            triggers.append(f"{focus} regression")
        elif action in {"create", "build", "implement", "draft", "write", "add"}:
            triggers.append(f"{action} {focus}")
            triggers.append(f"{focus} workflow")
        else:
            triggers.append(f"{focus} workflow")

    if category != DEFAULT_CATEGORY and focus and category not in focus.split():
        triggers.append(f"{category} {focus}")

    return unique_strings(triggers[:5])


def infer_steps(category: str, task_text: str) -> list[str]:
    focus = derive_focus_phrase(task_text) or clean_text(task_text)
    steps = [build_task_intake_step(focus)]
    steps.extend(CATEGORY_RULES.get(category, CATEGORY_RULES[DEFAULT_CATEGORY])["steps"])
    return unique_strings(steps)


def ensure_nested_skill_routing_step(steps: list[str]) -> list[str]:
    return unique_strings([*steps, build_nested_skill_routing_step()])


def build_nested_skill_routing_step() -> str:
    return (
        f"If any workflow step expands into a repeatable, non-trivial subtask, run "
        f"`{SUBTASK_ROUTING_COMMAND}`, follow the reused or generated sub-skill, and then "
        "return to the current workflow."
    )


def infer_validation(category: str) -> list[str]:
    return unique_strings(CATEGORY_RULES.get(category, CATEGORY_RULES[DEFAULT_CATEGORY])["validation"])


def infer_examples(
    category: str,
    summary: str,
    focus: str,
    triggers: list[str],
) -> list[str]:
    examples = [ensure_sentence(summary)]
    examples.extend(CATEGORY_RULES.get(category, CATEGORY_RULES[DEFAULT_CATEGORY])["examples"])
    if focus:
        examples.append(
            ensure_sentence(f"Handle repeat work around {focus} with a reusable playbook")
        )
    if triggers:
        examples.append(ensure_sentence(f"Use this skill when asked to {triggers[0]}"))
    return unique_strings(examples[:4])


def build_task_intake_step(focus: str) -> str:
    if focus:
        return f"Clarify the desired outcome, failure mode, and constraints for {focus} before editing anything."
    return "Clarify the desired outcome, failure mode, and constraints before editing anything."


def build_when_clause(task_text: str) -> str:
    cleaned = clean_text(task_text).rstrip(".")
    return (
        f"the user asks to {cleaned}, when that workflow is failing, "
        "or when similar work is likely to recur"
    )


def derive_summary_from_task(task_text: str) -> str:
    cleaned = sentence_case(task_text.rstrip("."))
    if cleaned.lower().startswith("to "):
        cleaned = f"Handle {cleaned[3:]}"
    return ensure_sentence(cleaned)


def derive_focus_phrase(task_text: str) -> str:
    tokens = [token for token in ordered_tokens(task_text) if token not in LOW_SIGNAL_TOKENS]
    if len(tokens) < 2:
        tokens = [token for token in ordered_tokens(task_text) if token not in STOPWORDS][:3]
    return " ".join(tokens[:4]).strip()


def detect_action_word(task_text: str) -> str:
    for token in ordered_tokens(task_text):
        if token in ACTION_WORDS:
            return token
    return ""


def suggest_related_skills(
    records: list[SkillRecord],
    query: str,
    *,
    exclude_name: str,
    limit: int = 3,
    min_score: float = 4.0,
) -> list[str]:
    matches = search_records(records, query, limit=max(limit * 2, 6))
    related: list[str] = []
    for score, _, record in matches:
        if score < min_score or record.name == exclude_name:
            continue
        related.append(record.name)
        if len(related) >= limit:
            break
    return unique_strings(related)


def create_skill(
    *,
    skills_dir: Path,
    blueprint: SkillBlueprint,
    force: bool,
) -> SkillRecord:
    if not blueprint.name:
        raise SystemExit("Skill name cannot be empty after normalization.")

    skill_dir = skills_dir / blueprint.name
    if skill_dir.exists() and not force:
        raise SystemExit(f"{skill_dir} already exists. Use --force to overwrite it.")
    skill_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "category": blueprint.category,
        "summary": blueprint.summary,
        "tags": blueprint.tags,
        "triggers": blueprint.triggers,
        "steps": blueprint.steps,
        "related_skills": blueprint.related_skills,
        "validation": blueprint.validation,
        "examples": blueprint.examples,
        "source_task": blueprint.source_task,
        "management_mode": DEFAULT_MANAGEMENT_MODE,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    skill_md = build_skill_markdown(blueprint)
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (skill_dir / "skill.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return SkillRecord(
        name=blueprint.name,
        path=str(skill_dir),
        description=blueprint.description,
        category=blueprint.category,
        tags=blueprint.tags,
        triggers=blueprint.triggers,
        summary=blueprint.summary,
        steps=blueprint.steps,
        related_skills=blueprint.related_skills,
        validation=blueprint.validation,
        examples=blueprint.examples,
        title=blueprint.title,
        management_mode=DEFAULT_MANAGEMENT_MODE,
    )


def build_skill_markdown(blueprint: SkillBlueprint) -> str:
    lines = [
        "---",
        f"name: {blueprint.name}",
        f"description: {blueprint.description}",
        "---",
        "",
        f"# {blueprint.title}",
        "",
        "## Goal",
        "",
        ensure_sentence(blueprint.summary),
        "",
        "## Workflow",
        "",
    ]

    for index, step in enumerate(blueprint.steps, start=1):
        lines.append(f"{index}. {ensure_sentence(step)}")

    if blueprint.validation:
        lines.extend(["", "## Validation", ""])
        for item in blueprint.validation:
            lines.append(f"- {ensure_sentence(item)}")

    if blueprint.examples:
        lines.extend(["", "## Example Requests", ""])
        for example in blueprint.examples:
            lines.append(f"- {ensure_sentence(example)}")

    if blueprint.triggers:
        lines.extend(["", "## Trigger Phrases", ""])
        for trigger in blueprint.triggers:
            lines.append(f"- {ensure_sentence(trigger)}")

    lines.extend(["", "## Reuse Notes", ""])
    lines.append(f"- Category: `{blueprint.category}`")
    if blueprint.tags:
        lines.append(f"- Tags: {', '.join(f'`{tag}`' for tag in blueprint.tags)}")
    lines.append(
        "- Start future task routing with `python3 .claude/tools/skill_agent.py auto \"<task>\" --json`."
    )
    lines.append(
        f"- When a workflow step turns into its own reusable subtask, reroute it through "
        f"`{SUBTASK_ROUTING_COMMAND}` before inventing an ad-hoc mini-flow."
    )
    lines.append(
        "- Search for this skill with `python3 .claude/tools/skill_agent.py search \"<task>\"`."
    )
    lines.append(
        "- Review reuse health with `python3 .claude/tools/skill_agent.py usage`, inspect refresh candidates with `python3 .claude/tools/skill_agent.py review`, and archive stale skills with `python3 .claude/tools/skill_agent.py prune --apply`."
    )
    lines.append(
        "- Preview a generated skill with `python3 .claude/tools/skill_agent.py bootstrap \"<task>\" --dry-run --json`."
    )
    if blueprint.related_skills:
        lines.append(
            f"- Related skills: {', '.join(f'`{name}`' for name in blueprint.related_skills)}"
        )

    return "\n".join(lines) + "\n"


def emit_blueprint_preview(blueprint: SkillBlueprint, *, as_json: bool) -> None:
    payload = blueprint_payload(blueprint)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"Name: {blueprint.name}")
    print(f"Category: {blueprint.category}")
    print(f"Tags: {', '.join(blueprint.tags) or '(none)'}")
    print(f"Related: {', '.join(blueprint.related_skills) or '(none)'}")
    print("")
    print(payload["markdown"])


def blueprint_payload(blueprint: SkillBlueprint) -> dict[str, Any]:
    payload = asdict(blueprint)
    payload["markdown"] = build_skill_markdown(blueprint)
    return payload


def match_payload(score: float, reason: str, record: SkillRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["score"] = score
    payload["reason"] = reason
    return payload


def choose_auto_match(
    matches: list[tuple[float, str, SkillRecord]],
    task: str,
) -> tuple[float, str, SkillRecord] | None:
    for match in matches:
        if should_skip_auto_reuse(match[2], task):
            continue
        return match
    return None


def should_skip_auto_reuse(record: SkillRecord, task: str) -> bool:
    if record.name != "project-skill-router":
        return False
    return not is_skill_management_task(task)


def is_skill_management_task(task: str) -> bool:
    tokens = tokenize(task)
    return bool(
        tokens
        & {
            "automation",
            "bootstrap",
            "local",
            "registry",
            "reuse",
            "router",
            "scaffold",
            "skill",
            "skills",
        }
    )


def emit_auto_result(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    action = payload["action"]
    print(f"Action: {action}")
    print(f"Task: {payload['task']}")

    if payload.get("match"):
        match = payload["match"]
        print(f"Skill: {match['name']}")
        print(f"Path: {match['path']}")
        print(f"Reason: {match['reason']}")
        if payload.get("skill_update"):
            update = payload["skill_update"]
            print(
                "Updated fields: "
                + ", ".join(update["updated_fields"])
            )
        print("Next: open the skill and follow its workflow.")
        return

    if payload.get("created_skill"):
        created = payload["created_skill"]
        print(f"Skill: {created['name']}")
        print(f"Path: {created['path']}")
        print("Reason: no existing skill cleared the reuse threshold, so a new skill was generated.")
        print("Next: open the generated SKILL.md and use it immediately.")
        return

    if payload.get("blueprint"):
        blueprint = payload["blueprint"]
        print(f"Skill: {blueprint['name']}")
        print(f"Category: {blueprint['category']}")
        print("Reason: no reusable skill cleared the threshold; previewing a generated skill instead.")
        print("Next: rerun without --dry-run to persist the generated skill.")


def resolve_usage_path(skills_dir: Path) -> Path:
    return skills_dir / USAGE_FILENAME


def load_usage_store(usage_path: Path) -> dict[str, Any]:
    if not usage_path.exists():
        return {"skills": {}}
    try:
        payload = json.loads(usage_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"skills": {}}
    if not isinstance(payload, dict):
        return {"skills": {}}
    skills = payload.get("skills")
    if not isinstance(skills, dict):
        payload["skills"] = {}
    return payload


def write_usage_store(usage_path: Path, payload: dict[str, Any]) -> None:
    usage_path.parent.mkdir(parents=True, exist_ok=True)
    payload["updated_at"] = utc_now()
    usage_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def record_skill_event(
    *,
    usage_path: Path,
    record: SkillRecord,
    action: str,
    task: str,
    score: float | None = None,
) -> None:
    now = utc_now()
    payload = load_usage_store(usage_path)
    skills = payload.setdefault("skills", {})
    entry = skills.setdefault(record.name, {})

    entry["name"] = record.name
    entry["category"] = record.category
    entry["path"] = record.path
    entry["first_seen_at"] = str(entry.get("first_seen_at") or now)
    entry["last_activity_at"] = now
    entry["last_action"] = action
    entry["last_task"] = clean_text(task)
    entry["reuse_count"] = int(entry.get("reuse_count", 0))
    entry["create_count"] = int(entry.get("create_count", 0))
    entry["auto_hits"] = int(entry.get("auto_hits", 0))
    entry["update_count"] = int(entry.get("update_count", 0))

    if action in {"auto-reuse", "auto-created"}:
        entry["auto_hits"] += 1
    if "reuse" in action:
        entry["reuse_count"] += 1
        entry["last_reused_at"] = now
    if "create" in action or "bootstrap" in action:
        entry["create_count"] += 1
        entry["last_created_at"] = now
    if "update" in action:
        entry["update_count"] += 1
        entry["last_updated_at"] = now
    if score is not None:
        entry["last_score"] = round(score, 2)
        score_history = entry.get("score_history", [])
        if not isinstance(score_history, list):
            score_history = []
        score_history.append({"at": now, "score": round(score, 2)})
        entry["score_history"] = score_history[-REFRESH_SCORE_HISTORY_LIMIT:]

    history = entry.get("history", [])
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "at": now,
            "action": action,
            "task": clean_text(task),
        }
    )
    entry["history"] = history[-USAGE_HISTORY_LIMIT:]

    write_usage_store(usage_path, payload)


def maybe_auto_update_skill(
    *,
    record: SkillRecord,
    skills_dir: Path,
    registry_path: Path,
    usage_path: Path,
    task: str,
) -> dict[str, Any] | None:
    usage_store = load_usage_store(usage_path)
    entry = usage_store.get("skills", {}).get(record.name, {})
    plan = build_skill_refresh_plan(record, entry)
    if plan.status != "candidate":
        return None

    updated = apply_skill_update_plan(
        record=record,
        plan=plan,
        usage_path=usage_path,
        task=task,
        action="auto-update",
    )
    updated_records = discover_skills(skills_dir)
    write_registry(updated_records, registry_path)
    return updated


def build_skill_refresh_plans(
    records: list[SkillRecord],
    usage_path: Path,
) -> list[SkillRefreshPlan]:
    usage_store = load_usage_store(usage_path)
    skills = usage_store.get("skills", {})
    plans = [build_skill_refresh_plan(record, skills.get(record.name, {})) for record in records]
    plans.sort(
        key=lambda plan: (
            refresh_status_rank(plan.status),
            plan.updated_days * -1,
            plan.name,
        )
    )
    return plans


def build_skill_refresh_plan(
    record: SkillRecord,
    entry: dict[str, Any],
) -> SkillRefreshPlan:
    metadata = load_companion_metadata(Path(record.path) / "skill.json")
    management_mode = normalize_management_mode(
        metadata.get("management_mode", record.management_mode)
    )
    recent_tasks = recent_reuse_tasks(entry)
    reuse_count = int(entry.get("reuse_count", 0))
    avg_score = average_recent_score(entry)
    updated_at = (
        parse_datetime(metadata.get("updated_at"))
        or parse_datetime(metadata.get("created_at"))
        or filesystem_timestamp(Path(record.path) / "skill.json")
        or filesystem_timestamp(Path(record.path) / "SKILL.md")
        or datetime.now(UTC)
    )
    updated_days = max((datetime.now(UTC) - updated_at).days, 0)

    if record.name in PROTECTED_SKILLS:
        return SkillRefreshPlan(
            name=record.name,
            path=record.path,
            status="protected",
            reason="Core routing or reference skill.",
            management_mode=management_mode,
            changes={},
            recent_tasks=recent_tasks,
            reuse_count=reuse_count,
            avg_score=avg_score,
            updated_days=updated_days,
        )

    if management_mode == "locked":
        return SkillRefreshPlan(
            name=record.name,
            path=record.path,
            status="locked",
            reason="Locked skills require explicit manual edits.",
            management_mode=management_mode,
            changes={},
            recent_tasks=recent_tasks,
            reuse_count=reuse_count,
            avg_score=avg_score,
            updated_days=updated_days,
        )

    reasons: list[str] = []
    if reuse_count >= 1 and len(record.triggers) < 2 and recent_tasks:
        reasons.append("Trigger coverage is too thin for a reused skill.")
    if reuse_count >= 1 and len(record.examples) < 2 and recent_tasks:
        reasons.append("Example requests are too thin for a reused skill.")
    if reuse_count >= 2 and avg_score is not None and avg_score < REFRESH_LOW_SCORE_THRESHOLD:
        reasons.append("Recent reuse scores are low enough that metadata should be tightened.")
    if reuse_count >= 2 and updated_days >= REFRESH_STALE_DAYS and recent_tasks:
        reasons.append(f"Metadata has not been refreshed for {REFRESH_STALE_DAYS}+ days.")

    known_tokens = known_record_tokens(record)
    novel_tokens = [
        token
        for token in ordered_tokens(" ".join(recent_tasks))
        if token not in known_tokens and token not in LOW_SIGNAL_TOKENS
    ]
    if reuse_count >= 2 and len(novel_tokens) >= 2:
        reasons.append("Recent reuse requests contain new terms not represented in the skill metadata.")

    changes = build_refresh_metadata_changes(
        record=record,
        metadata=metadata,
        recent_tasks=recent_tasks,
        management_mode=management_mode,
    )
    actionable_fields = [
        field for field in changes if field not in {"updated_at", "management_mode"}
    ]
    if not reasons or not actionable_fields:
        return SkillRefreshPlan(
            name=record.name,
            path=record.path,
            status="healthy",
            reason="No safe metadata refresh is needed right now.",
            management_mode=management_mode,
            changes={},
            recent_tasks=recent_tasks,
            reuse_count=reuse_count,
            avg_score=avg_score,
            updated_days=updated_days,
        )

    return SkillRefreshPlan(
        name=record.name,
        path=record.path,
        status="candidate",
        reason=" ".join(reasons[:3]),
        management_mode=management_mode,
        changes=changes,
        recent_tasks=recent_tasks,
        reuse_count=reuse_count,
        avg_score=avg_score,
        updated_days=updated_days,
    )


def recent_reuse_tasks(entry: dict[str, Any], *, limit: int = 4) -> list[str]:
    history = entry.get("history", [])
    if not isinstance(history, list):
        history = []
    tasks: list[str] = []
    seen: set[str] = set()
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        action = str(item.get("action") or "")
        task = clean_text(str(item.get("task") or ""))
        if "reuse" not in action or not task or task in seen:
            continue
        tasks.append(task)
        seen.add(task)
        if len(tasks) >= limit:
            break
    fallback = clean_text(str(entry.get("last_task") or ""))
    if fallback and fallback not in seen and len(tasks) < limit:
        tasks.append(fallback)
    return tasks


def average_recent_score(entry: dict[str, Any], *, limit: int = 5) -> float | None:
    score_history = entry.get("score_history", [])
    if not isinstance(score_history, list):
        score_history = []
    values: list[float] = []
    for item in score_history[-limit:]:
        if not isinstance(item, dict):
            continue
        score = item.get("score")
        if isinstance(score, (int, float)):
            values.append(float(score))
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def known_record_tokens(record: SkillRecord) -> set[str]:
    token_fields = [
        record.name.replace("-", " "),
        record.category,
        record.description,
        record.summary,
        " ".join(record.tags),
        " ".join(record.triggers),
        " ".join(record.examples),
    ]
    tokens: set[str] = set()
    for field in token_fields:
        tokens |= tokenize(field)
    return tokens


def build_refresh_metadata_changes(
    *,
    record: SkillRecord,
    metadata: dict[str, Any],
    recent_tasks: list[str],
    management_mode: str,
) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    existing_tags = unique_strings(metadata.get("tags", record.tags))
    existing_triggers = unique_strings(metadata.get("triggers", record.triggers))
    existing_examples = unique_strings(metadata.get("examples", record.examples))

    joined_tasks = " ".join(recent_tasks)
    merged_tags = merge_limited_strings(
        existing_tags,
        infer_tags(joined_tasks, record.category, []),
        limit=REFRESH_TAG_LIMIT,
    )
    merged_triggers = merge_limited_strings(
        existing_triggers,
        [
            trigger
            for task in recent_tasks
            for trigger in infer_trigger_phrases(task, record.category)
        ],
        limit=REFRESH_TRIGGER_LIMIT,
    )
    merged_examples = merge_limited_strings(
        existing_examples,
        [ensure_sentence(sentence_case(task)) for task in recent_tasks],
        limit=REFRESH_EXAMPLE_LIMIT,
    )

    if merged_tags != existing_tags:
        changes["tags"] = merged_tags
    if merged_triggers != existing_triggers:
        changes["triggers"] = merged_triggers
    if merged_examples != existing_examples:
        changes["examples"] = merged_examples
    if normalize_management_mode(metadata.get("management_mode")) != management_mode:
        changes["management_mode"] = management_mode
    if changes:
        changes["updated_at"] = utc_now()
    return changes


def merge_limited_strings(existing: list[str], additions: list[str], *, limit: int) -> list[str]:
    merged = list(existing)
    seen = set(existing)
    for item in additions:
        cleaned = clean_text(item)
        if not cleaned or cleaned in seen:
            continue
        merged.append(cleaned)
        seen.add(cleaned)
        if len(merged) >= limit:
            break
    return merged


def refresh_status_rank(status: str) -> int:
    order = {
        "candidate": 0,
        "healthy": 1,
        "locked": 2,
        "protected": 3,
    }
    return order.get(status, 99)


def refresh_plan_payload(plan: SkillRefreshPlan) -> dict[str, Any]:
    return {
        "name": plan.name,
        "path": plan.path,
        "status": plan.status,
        "reason": plan.reason,
        "management_mode": plan.management_mode,
        "updated_fields": sorted(plan.changes.keys()),
        "recent_tasks": plan.recent_tasks,
        "reuse_count": plan.reuse_count,
        "avg_score": plan.avg_score,
        "updated_days": plan.updated_days,
    }


def apply_skill_update_plan(
    *,
    record: SkillRecord,
    plan: SkillRefreshPlan,
    usage_path: Path,
    task: str,
    action: str,
) -> dict[str, Any]:
    skill_dir = Path(record.path)
    metadata_path = skill_dir / "skill.json"
    metadata = load_companion_metadata(metadata_path)
    metadata.update(plan.changes)
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if plan.management_mode == "managed":
        blueprint = build_blueprint_from_record(record, metadata)
        (skill_dir / "SKILL.md").write_text(
            build_skill_markdown(blueprint),
            encoding="utf-8",
        )

    updated_record = parse_skill(skill_dir / "SKILL.md") or record
    record_skill_event(
        usage_path=usage_path,
        record=updated_record,
        action=action,
        task=task,
    )
    return {
        "name": updated_record.name,
        "path": updated_record.path,
        "management_mode": plan.management_mode,
        "updated_fields": sorted(plan.changes.keys()),
        "reason": plan.reason,
    }


def build_blueprint_from_record(
    record: SkillRecord,
    metadata: dict[str, Any],
) -> SkillBlueprint:
    return SkillBlueprint(
        name=record.name,
        title=record.title,
        description=record.description,
        category=normalize_category(str(metadata.get("category") or record.category), record.summary),
        summary=clean_text(str(metadata.get("summary") or record.summary)),
        tags=unique_strings(metadata.get("tags", record.tags)),
        triggers=unique_strings(metadata.get("triggers", record.triggers)),
        steps=ensure_nested_skill_routing_step(
            unique_strings(metadata.get("steps", record.steps))
        ),
        related_skills=unique_strings(metadata.get("related_skills", record.related_skills)),
        validation=unique_strings(metadata.get("validation", record.validation)),
        examples=unique_strings(metadata.get("examples", record.examples)),
        source_task=clean_text(str(metadata.get("source_task") or "")),
    )


def build_skill_usage_summaries(
    records: list[SkillRecord],
    usage_path: Path,
) -> list[dict[str, Any]]:
    usage_store = load_usage_store(usage_path)
    skills = usage_store.get("skills", {})
    summaries = []

    for record in records:
        entry = skills.get(record.name, {})
        summaries.append(summarize_skill_usage(record, entry))

    summaries.sort(
        key=lambda item: (
            usage_status_rank(item["status"]),
            -item["reuse_count"],
            -item["age_days"],
            item["name"],
        )
    )
    return summaries


def summarize_skill_usage(record: SkillRecord, entry: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(UTC)
    created_at = (
        parse_datetime(entry.get("first_seen_at"))
        or parse_datetime(load_skill_metadata_timestamp(record, "created_at"))
        or parse_datetime(load_skill_metadata_timestamp(record, "updated_at"))
        or filesystem_timestamp(Path(record.path) / "SKILL.md")
        or now
    )
    last_activity = (
        parse_datetime(entry.get("last_activity_at"))
        or parse_datetime(entry.get("last_reused_at"))
        or parse_datetime(entry.get("last_created_at"))
        or created_at
    )

    reuse_count = int(entry.get("reuse_count", 0))
    create_count = int(entry.get("create_count", 0))
    age_days = max((now - created_at).days, 0)
    last_activity_days = max((now - last_activity).days, 0)
    status, reason = classify_skill_usage(
        record.name,
        reuse_count=reuse_count,
        create_count=create_count,
        age_days=age_days,
        last_activity_days=last_activity_days,
    )

    return {
        "name": record.name,
        "path": record.path,
        "category": record.category,
        "management_mode": record.management_mode,
        "reuse_count": reuse_count,
        "create_count": create_count,
        "auto_hits": int(entry.get("auto_hits", 0)),
        "update_count": int(entry.get("update_count", 0)),
        "age_days": age_days,
        "last_activity_days": last_activity_days,
        "status": status,
        "reason": reason,
        "last_task": entry.get("last_task"),
        "last_action": entry.get("last_action"),
        "first_seen_at": format_datetime(created_at),
        "last_activity_at": format_datetime(last_activity),
    }


def classify_skill_usage(
    skill_name: str,
    *,
    reuse_count: int,
    create_count: int,
    age_days: int,
    last_activity_days: int,
) -> tuple[str, str]:
    if skill_name in PROTECTED_SKILLS:
        return "protected", "Core routing or reference skill."
    if reuse_count == 0 and create_count == 0 and age_days >= PRUNE_NEVER_REUSED_DAYS:
        return "candidate", f"Never used and older than {PRUNE_NEVER_REUSED_DAYS} days."
    if reuse_count == 0 and create_count >= 1 and last_activity_days >= PRUNE_NEVER_REUSED_DAYS:
        return "candidate", f"Created but never reused after {PRUNE_NEVER_REUSED_DAYS} days."
    if reuse_count <= 1 and last_activity_days >= PRUNE_SINGLE_REUSE_DAYS:
        return "candidate", f"Reused once or less and idle for {PRUNE_SINGLE_REUSE_DAYS}+ days."
    if reuse_count <= 2 and last_activity_days >= PRUNE_LOW_REUSE_DAYS:
        return "candidate", f"Low reuse and idle for {PRUNE_LOW_REUSE_DAYS}+ days."
    if reuse_count >= 3 or last_activity_days <= ACTIVE_RECENT_DAYS:
        return "active", "Recently active or reused often enough to keep."
    return "stale", "Low recent activity, but not yet old enough to archive."


def usage_status_rank(status: str) -> int:
    order = {
        "candidate": 0,
        "stale": 1,
        "active": 2,
        "protected": 3,
    }
    return order.get(status, 99)


def archive_skill_candidates(
    candidates: list[dict[str, Any]],
    skills_dir: Path,
    usage_path: Path,
) -> list[dict[str, Any]]:
    archive_dir = skills_dir / ARCHIVE_DIRNAME
    archive_dir.mkdir(parents=True, exist_ok=True)
    payload = load_usage_store(usage_path)
    skills = payload.setdefault("skills", {})
    archived: list[dict[str, Any]] = []

    for item in candidates:
        source = Path(item["path"])
        destination = unique_archive_path(archive_dir, item["name"])
        shutil.move(str(source), str(destination))
        entry = skills.setdefault(item["name"], {})
        entry["archived_at"] = utc_now()
        entry["archived_path"] = str(destination)
        entry["archive_reason"] = item["reason"]
        archived.append(
            {
                "name": item["name"],
                "from_path": str(source),
                "archived_path": str(destination),
                "reason": item["reason"],
            }
        )

    write_usage_store(usage_path, payload)
    return archived


def unique_archive_path(archive_dir: Path, name: str) -> Path:
    candidate = archive_dir / name
    if not candidate.exists():
        return candidate
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return archive_dir / f"{name}-{timestamp}"


def load_skill_metadata_timestamp(record: SkillRecord, key: str) -> str:
    metadata = load_companion_metadata(Path(record.path) / "skill.json")
    value = metadata.get(key)
    return str(value) if isinstance(value, str) else ""


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def filesystem_timestamp(path: Path) -> datetime | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, UTC)


def format_datetime(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def write_registry(records: list[SkillRecord], registry_path: Path) -> None:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": utc_now(),
        "skills": [asdict(record) for record in records],
    }
    registry_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_name(raw_name: str) -> str:
    lowered = raw_name.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized[:63]


def build_title(name: str) -> str:
    parts = [part for part in name.split("-") if part]
    rendered = [TITLE_CASE_OVERRIDES.get(part, part.capitalize()) for part in parts]
    return " ".join(rendered)


def derive_name_from_task(task: str) -> str:
    preferred = [token for token in ordered_tokens(task) if token not in LOW_SIGNAL_TOKENS]
    if len(preferred) < 2:
        preferred = [token for token in ordered_tokens(task) if token not in STOPWORDS]
    normalized = normalize_name("-".join(preferred[:5]))
    if normalized:
        return normalized
    return "new-skill"


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sentence_case(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    return text[0].upper() + text[1:]


def ensure_sentence(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if text[-1] not in ".!?":
        return f"{text}."
    return text


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def safe_relative_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1)
