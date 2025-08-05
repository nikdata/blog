#!/usr/bin/env python3
"""
Standardize YAML frontmatter for Quarto blog posts.

This script processes post directories in processed-staging/ and:
1. Extracts or validates title from YAML or markdown headings
2. Standardizes author, date, categories format
3. Handles short-path generation and conflicts
4. Fixes common YAML syntax issues
5. Sets appropriate defaults for Quarto fields
6. Fixes duplicate heading markers (# # Hello -> # Hello)

Usage:
    python scripts/02-standardize-frontmatter.py
    
The script automatically processes post directories in processed-staging/ (in place)
"""

import os
import re
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


def extract_frontmatter_and_content(markdown_content: str) -> Tuple[Optional[Dict], str]:
    """
    Extract YAML frontmatter and remaining content from markdown.
    
    Returns:
        Tuple of (frontmatter_dict, remaining_content)
    """
    # Check for YAML frontmatter
    if not markdown_content.startswith('---'):
        return None, markdown_content
    
    # Find the closing ---
    lines = markdown_content.split('\n')
    yaml_end = None
    
    for i, line in enumerate(lines[1:], 1):  # Start from line 1 (skip first ---)
        if line.strip() == '---':
            yaml_end = i
            break
    
    if yaml_end is None:
        return None, markdown_content
    
    # Extract YAML content
    yaml_content = '\n'.join(lines[1:yaml_end])
    remaining_content = '\n'.join(lines[yaml_end + 1:])
    
    # Parse YAML
    try:
        frontmatter = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError as e:
        print(f"    Warning: YAML parsing error: {e}")
        # Try to fix common issues
        frontmatter = attempt_yaml_fix(yaml_content)
    
    return frontmatter, remaining_content


def attempt_yaml_fix(yaml_content: str) -> Dict:
    """
    Attempt to fix common YAML syntax issues.
    """
    lines = yaml_content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        # Check if line has a key-value pair
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Fix common issues
            if value and not (value.startswith('"') or value.startswith("'") or 
                             value.startswith('[') or value.startswith('{') or 
                             value.lower() in ['true', 'false'] or value.isdigit()):
                # Add quotes if value contains special characters
                if any(char in value for char in ['-', ':', '[', ']', '{', '}', '&', '*', '#', '|', '>', '%']):
                    value = f'"{value}"'
            
            fixed_lines.append(f"{key}: {value}")
        else:
            fixed_lines.append(line)
    
    try:
        return yaml.safe_load('\n'.join(fixed_lines)) or {}
    except yaml.YAMLError:
        print("    Warning: Could not fix YAML syntax, using empty frontmatter")
        return {}


def fix_duplicate_headings(content: str) -> Tuple[str, List[str]]:
    """
    Fix duplicate heading markers like '# # Hello World' -> '# Hello World'.
    
    Returns:
        Tuple of (fixed_content, list_of_changes)
    """
    changes = []
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        original_line = line
        
        # Look for patterns like "# # text", "## ## text", etc.
        # Use a simple approach: find lines that start with # patterns
        stripped = line.strip()
        
        if stripped.startswith('#'):
            # Count leading hashes
            hash_count = 0
            for char in stripped:
                if char == '#':
                    hash_count += 1
                else:
                    break
            
            # Check if after the initial hashes and whitespace, we have the same number of hashes again
            remaining = stripped[hash_count:].strip()
            if remaining.startswith('#' * hash_count):
                # Found duplicate pattern like "# # text" or "## ## text"
                # Extract the text after the second set of hashes
                text_part = remaining[hash_count:].strip()
                
                if text_part:  # Make sure there's actual text
                    # Preserve original indentation
                    indent = len(line) - len(line.lstrip())
                    fixed_line = ' ' * indent + '#' * hash_count + ' ' + text_part
                    
                    fixed_lines.append(fixed_line)
                    changes.append(f"Fixed duplicate heading: '{original_line.strip()}' → '{fixed_line.strip()}'")
                    continue
        
        # If no duplicate pattern found, keep the line as-is
        fixed_lines.append(original_line)
    
    return '\n'.join(fixed_lines), changes


def extract_title_from_content(content: str) -> Tuple[Optional[str], str]:
    """
    Extract title from first H1 or H2 heading and remove it from content.
    Note: This function assumes duplicate headings have already been fixed.
    
    Returns:
        Tuple of (extracted_title, remaining_content)
    """
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check for H1 or H2
        if line.startswith('# ') or line.startswith('## '):
            # Extract title (remove # and ##)
            title = line.lstrip('#').strip()
            
            if title:
                # Remove this line from content
                remaining_lines = lines[:i] + lines[i+1:]
                remaining_content = '\n'.join(remaining_lines).strip()
                return title, remaining_content
    
    return None, content


def sanitize_filename(text: str) -> str:
    """
    Convert text to a valid filename/slug.
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces with dashes
    text = text.replace(' ', '-')
    
    # Remove invalid characters
    text = re.sub(r'[<>:"|?*\\/]', '', text)
    
    # Remove multiple consecutive dashes
    text = re.sub(r'-+', '-', text)
    
    # Remove leading/trailing dashes
    text = text.strip('-')
    
    return text or "untitled"


def parse_date(date_input: Any) -> str:
    """
    Parse various date formats into YYYY-MM-DD format.
    """
    if isinstance(date_input, datetime):
        return date_input.strftime('%Y-%m-%d')
    
    if not isinstance(date_input, str):
        date_input = str(date_input)
    
    # Common date patterns
    patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2025-08-04
        r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2025/08/04
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 08/04/2025
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 08-04-2025
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_input)
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:  # Year first
                year, month, day = groups
            else:  # Year last
                month, day, year = groups
            
            try:
                # Validate date
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
    
    # Try parsing common text formats
    try:
        from dateutil.parser import parse as date_parse
        parsed_date = date_parse(date_input)
        return parsed_date.strftime('%Y-%m-%d')
    except:
        pass
    
    # Fallback to current date
    print(f"    Warning: Could not parse date '{date_input}', using current date")
    return datetime.now().strftime('%Y-%m-%d')


def check_short_path_conflict(short_path: str, current_post_dir: Path) -> str:
    """
    Check for short-path conflicts and resolve them.
    """
    # Extract date prefix from current directory name
    dir_name = current_post_dir.name
    if '_' in dir_name:
        date_prefix = dir_name.split('_')[0]
    else:
        date_prefix = datetime.now().strftime('%Y%m%d')
    
    expected_dir = f"{date_prefix}_{short_path}"
    
    # Check if current directory already matches expected name
    if current_post_dir.name == expected_dir:
        return short_path  # No conflict with self
    
    # Check existing posts directory for conflicts
    posts_dir = Path("posts")
    if posts_dir.exists():
        for existing_dir in posts_dir.iterdir():
            if existing_dir.is_dir() and existing_dir.name.endswith(f"_{short_path}"):
                # Found conflict, add suffix
                counter = 1
                while True:
                    new_short_path = f"{short_path}-{counter:02d}"
                    
                    # Check if this conflicts
                    conflict_found = False
                    for check_dir in posts_dir.iterdir():
                        if check_dir.is_dir() and check_dir.name.endswith(f"_{new_short_path}"):
                            conflict_found = True
                            break
                    
                    if not conflict_found:
                        print(f"    Warning: short-path '{short_path}' conflicts with existing post, using '{new_short_path}'")
                        return new_short_path
                    
                    counter += 1
                    if counter > 99:
                        raise ValueError(f"Too many conflicts for short-path: {short_path}")
    
    return short_path


def standardize_frontmatter(frontmatter: Dict, content: str, post_dir: Path) -> Tuple[Dict, str]:
    """
    Standardize frontmatter according to Quarto requirements.
    """
    # Start with cleaned frontmatter
    clean_frontmatter = {}
    changes_made = []
    kept_as_is = []
    
    # ALWAYS fix duplicate headings first, regardless of title source
    print("    Fixing duplicate headings...")
    fixed_content, heading_changes = fix_duplicate_headings(content)
    if heading_changes:
        for change in heading_changes:
            print(f"      - {change}")
    
    # 1. Handle title
    yaml_title = frontmatter.get('title') or frontmatter.get('titel')  # Handle typo
    if yaml_title:
        clean_frontmatter['title'] = str(yaml_title).strip()
        kept_as_is.append(f"title: '{clean_frontmatter['title']}'")
        final_content = fixed_content  # Use the content with fixed headings
    else:
        # Extract from content
        extracted_title, remaining_content = extract_title_from_content(fixed_content)
        if not extracted_title:
            raise ValueError(f"No title found in YAML or content for {post_dir.name}")
        
        clean_frontmatter['title'] = extracted_title
        changes_made.append(f"title: extracted from content: '{extracted_title}'")
        final_content = remaining_content
    
    # 2. Set author (always Nikhil Agarwal)
    original_author = frontmatter.get('author')
    clean_frontmatter['author'] = "Nikhil Agarwal"
    if original_author and original_author != "Nikhil Agarwal":
        changes_made.append(f"author: changed from '{original_author}' to 'Nikhil Agarwal'")
    elif original_author:
        kept_as_is.append("author: 'Nikhil Agarwal'")
    else:
        changes_made.append("author: added 'Nikhil Agarwal'")
    
    # 3. Handle date
    date_value = frontmatter.get('date')
    if date_value:
        original_date = str(date_value)
        clean_frontmatter['date'] = parse_date(date_value)
        if original_date != clean_frontmatter['date']:
            changes_made.append(f"date: standardized from '{original_date}' to '{clean_frontmatter['date']}'")
        else:
            kept_as_is.append(f"date: '{clean_frontmatter['date']}'")
    else:
        clean_frontmatter['date'] = datetime.now().strftime('%Y-%m-%d')
        changes_made.append(f"date: added current date '{clean_frontmatter['date']}'")
    
    # 4. Handle description
    description = frontmatter.get('description')
    if description:
        clean_frontmatter['description'] = str(description).strip()
        kept_as_is.append(f"description: '{clean_frontmatter['description']}'")
    else:
        clean_frontmatter['description'] = '""'
        changes_made.append("description: added empty field (please fill in)")
    
    # 5. Handle short-path
    short_path = frontmatter.get('short-path')
    if not short_path or len(str(short_path).strip()) == 0:
        # Generate from title
        short_path = sanitize_filename(clean_frontmatter['title'])
        changes_made.append(f"short-path: generated from title: '{short_path}'")
    else:
        original_short_path = str(short_path)
        short_path = sanitize_filename(str(short_path))
        if original_short_path != short_path:
            changes_made.append(f"short-path: sanitized from '{original_short_path}' to '{short_path}'")
        else:
            kept_as_is.append(f"short-path: '{short_path}'")
    
    # Check for conflicts
    final_short_path = check_short_path_conflict(short_path, post_dir)
    if final_short_path != short_path:
        changes_made.append(f"short-path: conflict resolved, changed to '{final_short_path}'")
    
    clean_frontmatter['short-path'] = final_short_path
    
    # 6. Handle categories
    categories = frontmatter.get('categories', [])
    if isinstance(categories, str):
        # Single category as string
        clean_frontmatter['categories'] = [categories.strip()]
        changes_made.append(f"categories: converted string to list: [{categories.strip()}]")
    elif isinstance(categories, list):
        # List of categories
        if len(categories) > 1:
            changes_made.append(f"categories: multiple categories found, using first only: '{categories[0]}'")
        
        if categories:
            clean_frontmatter['categories'] = [str(categories[0]).strip()]
        else:
            clean_frontmatter['categories'] = []
            kept_as_is.append("categories: empty list")
    else:
        clean_frontmatter['categories'] = []
        changes_made.append("categories: added empty list")
    
    # 7. Set defaults for Quarto fields
    original_draft = frontmatter.get('draft')
    clean_frontmatter['draft'] = frontmatter.get('draft', False)
    
    # Handle boolean conversion
    if isinstance(clean_frontmatter['draft'], str):
        old_value = clean_frontmatter['draft']
        clean_frontmatter['draft'] = clean_frontmatter['draft'].lower() in ['true', 'yes', '1']
        changes_made.append(f"draft: converted '{old_value}' to boolean {str(clean_frontmatter['draft']).lower()}")
    elif original_draft is not None:
        kept_as_is.append(f"draft: {str(clean_frontmatter['draft']).lower()}")
    else:
        changes_made.append("draft: added default false")
    
    # TOC handling
    original_toc = frontmatter.get('toc')
    toc = frontmatter.get('toc', False)
    if isinstance(toc, str):
        old_value = toc
        toc = toc.lower() in ['true', 'yes', '1']
        changes_made.append(f"toc: converted '{old_value}' to boolean {str(toc).lower()}")
    elif original_toc is not None:
        kept_as_is.append(f"toc: {str(toc).lower()}")
    else:
        changes_made.append("toc: added default false")
    
    clean_frontmatter['toc'] = toc
    
    if toc and 'toc-depth' not in frontmatter:
        clean_frontmatter['toc-depth'] = 3
        changes_made.append("toc-depth: added default 3 (since toc is true)")
    elif 'toc-depth' in frontmatter:
        try:
            original_depth = frontmatter['toc-depth']
            clean_frontmatter['toc-depth'] = int(frontmatter['toc-depth'])
            if str(original_depth) != str(clean_frontmatter['toc-depth']):
                changes_made.append(f"toc-depth: converted '{original_depth}' to {clean_frontmatter['toc-depth']}")
            else:
                kept_as_is.append(f"toc-depth: {clean_frontmatter['toc-depth']}")
        except (ValueError, TypeError):
            clean_frontmatter['toc-depth'] = 3
            changes_made.append(f"toc-depth: invalid value, set to default 3")
    
    # Code line numbers
    original_cln = frontmatter.get('code-line-numbers')
    code_line_numbers = frontmatter.get('code-line-numbers', False)
    if isinstance(code_line_numbers, str):
        old_value = code_line_numbers
        code_line_numbers = code_line_numbers.lower() in ['true', 'yes', '1']
        changes_made.append(f"code-line-numbers: converted '{old_value}' to boolean {str(code_line_numbers).lower()}")
    elif original_cln is not None:
        kept_as_is.append(f"code-line-numbers: {str(code_line_numbers).lower()}")
    else:
        changes_made.append("code-line-numbers: added default false")
    
    clean_frontmatter['code-line-numbers'] = code_line_numbers
    
    # 8. Preserve other known Quarto fields
    quarto_fields = [
        'subtitle', 'image', 'image-alt', 'lang', 'bibliography',
        'citation', 'google-scholar', 'filters', 'lightbox', 'fig-cap-location'
    ]
    
    for field in quarto_fields:
        if field in frontmatter:
            clean_frontmatter[field] = frontmatter[field]
            kept_as_is.append(f"{field}: preserved")
    
    # Print changes for this file
    if changes_made:
        print(f"    Changes made:")
        for change in changes_made:
            print(f"      - {change}")
    
    if kept_as_is:
        print(f"    Kept as-is:")
        for item in kept_as_is:
            print(f"      - {item}")
    
    return clean_frontmatter, final_content


def format_yaml_frontmatter(frontmatter: Dict) -> str:
    """
    Format frontmatter as clean YAML.
    """
    # Custom ordering for readability
    ordered_fields = [
        'title', 'author', 'date', 'description', 'short-path', 'draft', 
        'toc', 'toc-depth', 'code-line-numbers', 'categories'
    ]
    
    lines = ['---']
    
    # Add ordered fields first
    for field in ordered_fields:
        if field in frontmatter:
            value = frontmatter[field]
            
            # Special formatting for categories
            if field == 'categories':
                if isinstance(value, list):
                    if value:
                        lines.append(f'{field}:')
                        for cat in value:
                            lines.append(f'  - {cat}')
                    else:
                        lines.append(f'{field}: []')
                else:
                    lines.append(f'{field}: [{value}]')
            # Special formatting for dates (always quoted)
            elif field == 'date':
                lines.append(f'{field}: "{value}"')
            # Special formatting for booleans (lowercase)
            elif isinstance(value, bool):
                lines.append(f'{field}: {str(value).lower()}')
            else:
                # Quote strings that might need it
                if isinstance(value, str) and (':' in value or value.lower() in ['true', 'false']):
                    lines.append(f'{field}: "{value}"')
                else:
                    lines.append(f'{field}: {value}')
    
    # Add any remaining fields
    for field, value in frontmatter.items():
        if field not in ordered_fields:
            # Handle booleans in remaining fields too
            if isinstance(value, bool):
                lines.append(f'{field}: {str(value).lower()}')
            else:
                lines.append(f'{field}: {value}')
    
    lines.append('---')
    lines.append('')  # Empty line after frontmatter
    
    return '\n'.join(lines)


def process_post_directory(post_dir: Path) -> bool:
    """
    Process a single post directory, updating its frontmatter.
    
    Returns:
        True if post was processed successfully, False otherwise
    """
    print(f"\n📝 Processing: {post_dir.name}")
    
    # Find the content file (index.qmd or index.md)
    content_file = post_dir / "index.qmd"
    if not content_file.exists():
        content_file = post_dir / "index.md"
        if not content_file.exists():
            # Look for any .md or .qmd file
            md_files = list(post_dir.glob("*.md")) + list(post_dir.glob("*.qmd"))
            if md_files:
                content_file = md_files[0]
                print(f"    Warning: Using {content_file.name} instead of index.qmd")
            else:
                print(f"    ❌ Error: No markdown file found in {post_dir.name}")
                return False
    
    try:
        # Read file
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter and content
        frontmatter, markdown_content = extract_frontmatter_and_content(content)
        
        if frontmatter is None:
            frontmatter = {}
        
        # Standardize frontmatter
        clean_frontmatter, final_content = standardize_frontmatter(frontmatter, markdown_content, post_dir)
        
        # Warning for empty description
        if clean_frontmatter.get('description') == '""':
            print(f"    ⚠️  WARNING: Description is empty - please add a description for SEO/preview purposes")
        
        # Format output
        yaml_section = format_yaml_frontmatter(clean_frontmatter)
        final_markdown = yaml_section + final_content
        
        # Write back to file
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(final_markdown)
        
        print(f"    ✅ Updated frontmatter for {post_dir.name}")
        return True
        
    except Exception as e:
        print(f"    ❌ Error processing {post_dir.name}: {e}")
        return False


def main():
    """Main entry point."""
    staging_dir = Path("processed-staging")
    
    if not staging_dir.exists():
        print("❌ Error: processed-staging/ directory not found")
        print("Run 01-sanitize-filenames.py first")
        sys.exit(1)
    
    # Find all post directories (directories containing markdown files)
    post_dirs = []
    for item in staging_dir.iterdir():
        if item.is_dir():
            # Check if directory contains markdown files
            md_files = list(item.glob("*.md")) + list(item.glob("*.qmd"))
            if md_files:
                post_dirs.append(item)
    
    if not post_dirs:
        print("ℹ️  No post directories found in processed-staging/")
        sys.exit(0)
    
    print(f"🔧 Standardizing YAML frontmatter")
    print("=" * 50)
    print(f"📂 Found {len(post_dirs)} post directory(ies) to process")
    
    success_count = 0
    failed_posts = []
    
    for post_dir in sorted(post_dirs):
        if process_post_directory(post_dir):
            success_count += 1
        else:
            failed_posts.append(post_dir.name)
    
    print(f"\n📊 Processing Summary")
    print("=" * 30)
    print(f"✅ Success: {success_count} posts")
    
    if failed_posts:
        print(f"❌ Failed: {len(failed_posts)} posts")
        for post_name in failed_posts:
            print(f"    - {post_name}")
        sys.exit(1)
    else:
        print("🎉 All posts processed successfully!")


if __name__ == "__main__":
    main()