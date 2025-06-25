"""Update project name throughout the template."""

import argparse
import re
import sys
from pathlib import Path


def validate_project_name(name: str) -> bool:
    """Validate that the project name follows Python package naming conventions."""
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        return False

    # Check it's not a Python keyword or builtin
    import builtins
    import keyword

    if keyword.iskeyword(name):
        return False

    return not hasattr(builtins, name)


def get_files_to_update() -> list[Path]:
    """Get list of files that need project name updates."""
    files = [
        "pyproject.toml",
        "README.md",
    ]

    # Add optional files if they exist
    optional_files = [
        ".github/workflows/ci.yml",
    ]

    all_files = files + optional_files
    return [Path(f) for f in all_files if Path(f).exists()]


def get_replacements(old_name: str, new_name: str) -> list[tuple[str, str]]:
    """Get list of string replacements to make."""
    # Handle both underscore and hyphen versions
    old_hyphen = old_name.replace("_", "-")
    new_hyphen = new_name.replace("_", "-")

    return [
        # Exact matches
        (old_name, new_name),
        (old_hyphen, new_hyphen),
        # In quotes
        (f'"{old_name}"', f'"{new_name}"'),
        (f'"{old_hyphen}"', f'"{new_hyphen}"'),
        (f"'{old_name}'", f"'{new_name}'"),
        (f"'{old_hyphen}'", f"'{new_hyphen}'"),
        # Import statements
        (f"from {old_name}", f"from {new_name}"),
        (f"import {old_name}", f"import {new_name}"),
        # Markdown code blocks
        (f"`{old_name}`", f"`{new_name}`"),
        (f"`{old_hyphen}`", f"`{new_hyphen}`"),
    ]


def update_file_contents(file_path: Path, replacements: list[tuple[str, str]]) -> bool:
    """Update file contents with replacements."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        for old, new in replacements:
            content = content.replace(old, new)

        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return True

        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}", file=sys.stderr)
        return False


def rename_directory(old_name: str, new_name: str) -> bool:
    """Rename the package directory."""
    old_dir = Path(f"src/{old_name}")
    new_dir = Path(f"src/{new_name}")

    if old_dir.exists() and not new_dir.exists():
        try:
            old_dir.rename(new_dir)
            print(f"✓ Renamed directory: {old_dir} → {new_dir}")
            return True
        except Exception as e:
            print(f"Error renaming directory: {e}", file=sys.stderr)
            return False

    return False


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Update project name throughout the template"
    )
    parser.add_argument(
        "new_name",
        help="New project name (lowercase, underscores allowed)",
    )
    parser.add_argument(
        "--old-name",
        default="project_name",
        help="Old project name to replace (default: project_name)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )

    args = parser.parse_args()

    # Validate new name
    if not validate_project_name(args.new_name):
        print(f"Error: '{args.new_name}' is not a valid Python package name.")
        print("Package names must:")
        print("  - Start with a lowercase letter")
        print("  - Contain only lowercase letters, numbers, and underscores")
        print("  - Not be a Python keyword or builtin")
        sys.exit(1)

    if args.new_name == args.old_name:
        print("New name is the same as old name. Nothing to do.")
        sys.exit(0)

    print(f"Updating project name: {args.old_name} → {args.new_name}")

    # Get replacements
    replacements = get_replacements(args.old_name, args.new_name)

    # Update files
    files = get_files_to_update()
    updated_count = 0

    for file_path in files:
        if args.dry_run:
            content = file_path.read_text(encoding="utf-8")
            would_change = any(old in content for old, _ in replacements)
            if would_change:
                print(f"Would update: {file_path}")
        elif update_file_contents(file_path, replacements):
            print(f"✓ Updated: {file_path}")
            updated_count += 1

    # Rename directory
    if args.dry_run:
        old_dir = Path(f"src/{args.old_name}")
        if old_dir.exists():
            print(f"Would rename: {old_dir} → src/{args.new_name}")
    elif rename_directory(args.old_name, args.new_name):
        updated_count += 1

    # Summary
    if args.dry_run:
        print("\nDry run complete. No files were modified.")
    else:
        print(f"\n✨ Updated {updated_count} items successfully!")

        # Additional instructions
        print("\nDon't forget to:")
        print("  1. Update author information in pyproject.toml")
        print("  2. Update the project description in README.md")
        print("  3. Review and update CLAUDE.md if needed")


if __name__ == "__main__":
    main()
