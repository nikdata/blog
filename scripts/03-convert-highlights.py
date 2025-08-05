#!/usr/bin/env python3
"""
Convert Bear highlight syntax to HTML markup for Quarto blog posts.

This script processes post directories in processed-staging/ and:
1. Converts Bear highlight syntax: ==🟢text== → <mark style="background-color: #90EE90">text</mark>
2. Supports all Bear highlight colors (green, red, blue, yellow, purple)
3. Removes [HASH] index references if found
4. Provides detailed console output on changes made

Usage:
    python scripts/03-convert-highlights.py
    
The script automatically processes post directories in processed-staging/ (in place)
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# Color mapping for Bear highlights
HIGHLIGHT_COLORS = {
    '🟢': '#90EE90',  # Light green
    '🔴': '#ffcccb',  # Light red  
    '🔵': '#add8e6',  # Light blue
    '🟡': '#ffffe0',  # Light yellow
    '🟣': '#dda0dd',  # Plum/light purple
}

# Alternative color names for reference
COLOR_NAMES = {
    '🟢': 'green',
    '🔴': 'red',
    '🔵': 'blue', 
    '🟡': 'yellow',
    '🟣': 'purple',
}


def find_bear_highlights(content: str) -> List[Tuple[str, str, str]]:
    """
    Find all Bear highlight patterns in content.
    
    Returns:
        List of tuples: (full_match, color_emoji, highlighted_text)
    """
    # Pattern to match Bear highlights: ==🟢text==
    pattern = r'==(🟢|🔴|🔵|🟡|🟣)([^=]+)=='
    
    matches = []
    for match in re.finditer(pattern, content):
        full_match = match.group(0)
        color_emoji = match.group(1)
        text = match.group(2)
        matches.append((full_match, color_emoji, text))
    
    return matches


def convert_highlight_to_html(color_emoji: str, text: str) -> str:
    """
    Convert a single Bear highlight to HTML markup.
    
    Args:
        color_emoji: The color emoji (🟢, 🔴, etc.)
        text: The highlighted text
        
    Returns:
        HTML mark element with appropriate background color
    """
    if color_emoji not in HIGHLIGHT_COLORS:
        # Fallback for unsupported colors
        return f'<mark>{text}</mark>'
    
    color_code = HIGHLIGHT_COLORS[color_emoji]
    return f'<mark style="background-color: {color_code}">{text}</mark>'


def remove_hash_references(content: str) -> Tuple[str, List[str]]:
    """
    Remove Bear's [HASH] index references while preserving whitespace.
    
    Bear sometimes adds references like: [HASH abc123] 
    
    Returns:
        Tuple of (cleaned_content, list_of_removed_references)
    """
    # Pattern to match [HASH ...] references
    pattern = r'\[HASH\s+[a-fA-F0-9]+\]'
    
    removed_refs = re.findall(pattern, content)
    
    # Remove hash references but preserve surrounding whitespace
    cleaned_content = re.sub(pattern, '', content)
    
    # Only clean up multiple consecutive spaces on the same line, not across lines
    # This preserves intentional line breaks and paragraph spacing
    lines = cleaned_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Only compress multiple spaces within a line, preserve empty lines
        if line.strip():  # Non-empty line
            cleaned_line = re.sub(r' +', ' ', line)  # Multiple spaces → single space
            cleaned_lines.append(cleaned_line)
        else:  # Empty line
            cleaned_lines.append(line)  # Keep as-is (preserves empty lines)
    
    cleaned_content = '\n'.join(cleaned_lines)
    
    return cleaned_content, removed_refs


def process_markdown_content(content: str) -> Tuple[str, Dict[str, int], List[str]]:
    """
    Process markdown content to convert Bear highlights and remove references.
    
    Returns:
        Tuple of (processed_content, conversion_stats, removed_references)
    """
    original_content = content
    
    # Step 1: Find all Bear highlights
    highlights = find_bear_highlights(content)
    
    # Track conversion statistics
    conversion_stats = {color: 0 for color in COLOR_NAMES.values()}
    
    # Step 2: Convert highlights to HTML
    processed_content = content
    for full_match, color_emoji, text in highlights:
        html_markup = convert_highlight_to_html(color_emoji, text)
        processed_content = processed_content.replace(full_match, html_markup, 1)  # Replace one at a time
        
        color_name = COLOR_NAMES.get(color_emoji, 'unknown')
        conversion_stats[color_name] += 1
    
    # Step 3: Remove hash references
    processed_content, removed_refs = remove_hash_references(processed_content)
    
    return processed_content, conversion_stats, removed_refs


def process_post_directory(post_dir: Path) -> bool:
    """
    Process a single post directory to convert Bear highlights.
    
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
            original_content = f.read()
        
        # Process content
        processed_content, stats, removed_refs = process_markdown_content(original_content)
        
        # Check if any changes were made
        if original_content == processed_content:
            print(f"    ✅ No Bear highlights found - file unchanged")
            return True
        
        # Report changes
        total_highlights = sum(stats.values())
        if total_highlights > 0:
            print(f"    🎨 Converted {total_highlights} Bear highlights:")
            for color, count in stats.items():
                if count > 0:
                    print(f"      - {color}: {count} highlight(s)")
        
        if removed_refs:
            print(f"    🧹 Removed {len(removed_refs)} hash references:")
            for ref in removed_refs[:3]:  # Show first 3 only
                print(f"      - {ref}")
            if len(removed_refs) > 3:
                print(f"      - ... and {len(removed_refs) - 3} more")
        
        # Write processed content back to file
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        print(f"    ✅ Successfully updated {post_dir.name}")
        return True
        
    except UnicodeDecodeError as e:
        print(f"    ❌ Encoding error reading {content_file.name}: {e}")
        return False
    except UnicodeEncodeError as e:
        print(f"    ❌ Encoding error writing {content_file.name}: {e}")
        return False
    except IOError as e:
        print(f"    ❌ File I/O error with {content_file.name}: {e}")
        return False
    except Exception as e:
        print(f"    ❌ Unexpected error processing {post_dir.name}: {e}")
        return False


def validate_processed_content(content: str) -> List[str]:
    """
    Validate that highlight conversion was successful.
    
    Returns:
        List of validation warnings/errors
    """
    issues = []
    
    # Check for remaining Bear highlight syntax
    remaining_highlights = find_bear_highlights(content)
    if remaining_highlights:
        issues.append(f"Found {len(remaining_highlights)} unconverted Bear highlights")
    
    # Check for malformed HTML
    mark_pattern = r'<mark[^>]*>.*?</mark>'
    mark_matches = re.findall(mark_pattern, content, re.DOTALL)
    
    # Basic HTML validation
    for match in mark_matches:
        if not match.endswith('</mark>'):
            issues.append("Found malformed <mark> tag")
        if 'style=' in match and 'background-color:' not in match:
            issues.append("Found <mark> tag without background-color style")
    
    return issues


def main():
    """Main entry point."""
    staging_dir = Path("processed-staging")
    
    if not staging_dir.exists():
        print("❌ Error: processed-staging/ directory not found")
        print("Run the previous scripts in the pipeline first")
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
    
    print(f"🎨 Converting Bear highlights to HTML markup")
    print("=" * 60)
    print(f"📂 Found {len(post_dirs)} post directory(ies) to process")
    
    success_count = 0
    failed_posts = []
    total_highlights_converted = 0
    color_breakdown = {color: 0 for color in COLOR_NAMES.values()}
    
    # Process each post directory
    for post_dir in sorted(post_dirs):
        if process_post_directory(post_dir):
            success_count += 1
            
            # Count highlights for summary (re-read to get accurate count)
            try:
                content_file = post_dir / "index.qmd"
                if not content_file.exists():
                    content_file = post_dir / "index.md"
                    if not content_file.exists():
                        md_files = list(post_dir.glob("*.md")) + list(post_dir.glob("*.qmd"))
                        if md_files:
                            content_file = md_files[0]
                
                if content_file.exists():
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Count HTML mark tags as proxy for converted highlights
                    mark_count = len(re.findall(r'<mark[^>]*>.*?</mark>', content, re.DOTALL))
                    total_highlights_converted += mark_count
                    
                    # Try to estimate color breakdown by background-color values
                    for color_emoji, color_code in HIGHLIGHT_COLORS.items():
                        color_pattern = rf'<mark[^>]*background-color:\s*{re.escape(color_code)}[^>]*>'
                        color_matches = len(re.findall(color_pattern, content))
                        color_name = COLOR_NAMES[color_emoji]
                        color_breakdown[color_name] += color_matches
                        
            except:
                pass  # Skip counting if file can't be read
        else:
            failed_posts.append(post_dir.name)
    
    # Final summary
    print(f"\n📊 Conversion Summary")
    print("=" * 40)
    print(f"Posts processed: {len(post_dirs)}")
    print(f"✅ Successful: {success_count}")
    
    if failed_posts:
        print(f"❌ Failed: {len(failed_posts)}")
        print("Failed posts:")
        for post_name in failed_posts:
            print(f"    - {post_name}")
        print()
    
    print(f"🎨 Total highlights converted: {total_highlights_converted}")
    
    if total_highlights_converted > 0:
        print("Color breakdown:")
        for color, count in color_breakdown.items():
            if count > 0:
                print(f"    - {color}: {count}")
    
    if failed_posts:
        print("\n⚠️  Some posts failed processing. Check the errors above.")
        sys.exit(1)
    else:
        print("\n🎉 All posts processed successfully!")
        print("Bear highlights have been converted to HTML markup.")


if __name__ == "__main__":
    main()