#!/usr/bin/env python3
"""
Fix image paths and organize images for Quarto blog posts.

This script processes post directories in processed-staging/ and:
1. Ensures images are in standardized img/ subdirectory within each post
2. Updates markdown image references to use img/ paths
3. Converts Bear sizing syntax to Quarto format
4. Handles PDF links and embeds
5. Validates that all referenced images exist

Input/Output: processed-staging/ (in-place processing)
"""

import os
import re
import shutil
from pathlib import Path
import json

def convert_sizing_syntax(content):
    """Convert Bear sizing syntax to Quarto format."""
    changes = []
    
    # Pattern: {"width":123} or {"width": 123} -> {width=123}
    def replace_sizing(match):
        try:
            sizing_json = match.group(1)
            # Parse the JSON-like syntax
            sizing_data = json.loads(sizing_json)
            
            # Convert to Quarto format
            quarto_attrs = []
            for key, value in sizing_data.items():
                if key == "width":
                    quarto_attrs.append(f"width={value}")
                elif key == "height":
                    quarto_attrs.append(f"height={value}")
                else:
                    # Keep other attributes as-is
                    quarto_attrs.append(f"{key}={value}")
            
            quarto_syntax = "{" + ", ".join(quarto_attrs) + "}"
            changes.append(f"Converted sizing: {match.group(0)} → {quarto_syntax}")
            return quarto_syntax
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"      Warning: Could not parse sizing syntax '{match.group(1)}': {e}")
            return match.group(0)  # Return original if parsing fails
    
    # Find Bear sizing syntax patterns
    sizing_pattern = r'\{("width":\s*\d+(?:\s*,\s*"height":\s*\d+)?)\}'
    updated_content = re.sub(sizing_pattern, replace_sizing, content)
    
    return updated_content, changes

def extract_image_references(content):
    """Extract all image references from markdown content."""
    images = []
    
    # Pattern for markdown images: ![alt](path) or ![alt](path){sizing}
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)(?:\{[^}]*\})?'
    
    for match in re.finditer(image_pattern, content):
        alt_text = match.group(1)
        image_path = match.group(2)
        images.append({
            'alt': alt_text,
            'path': image_path,
            'full_match': match.group(0)
        })
    
    return images

def update_image_paths(content):
    """Update image paths to use standardized img/ directory."""
    changes = []
    
    def replace_image_path(match):
        alt_text = match.group(1)
        original_path = match.group(2)
        sizing_part = match.group(3) if match.lastindex >= 3 else ""
        
        # Extract just the filename from the path
        filename = Path(original_path).name
        
        # New path should always be img/filename
        new_path = f"img/{filename}"
        
        # Reconstruct the markdown image syntax
        new_syntax = f"![{alt_text}]({new_path}){sizing_part}"
        
        if original_path != new_path:
            changes.append(f"Updated path: {original_path} → {new_path}")
        
        return new_syntax
    
    # Pattern for markdown images with optional sizing
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)(\{[^}]*\})?'
    updated_content = re.sub(image_pattern, replace_image_path, content)
    
    return updated_content, changes

def handle_pdf_links(content):
    """Convert PDF links to embeds where appropriate."""
    changes = []
    
    # For now, just track PDF references - could be enhanced later
    pdf_pattern = r'\[([^\]]*)\]\(([^)]+\.pdf)\)'
    pdf_matches = re.findall(pdf_pattern, content)
    
    if pdf_matches:
        changes.append(f"Found {len(pdf_matches)} PDF reference(s) - manual review recommended")
    
    return content, changes

def organize_images_in_post(post_dir):
    """Ensure images are properly organized in the post's img/ directory."""
    changes = []
    
    # The img/ directory should already exist from script 01
    img_dir = post_dir / "img"
    
    if not img_dir.exists():
        # No images to organize
        return changes
    
    if not img_dir.is_dir():
        changes.append(f"Warning: img path exists but is not a directory")
        return changes
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.pdf'}
    
    # Check for any loose image files in the post directory root
    for item in post_dir.iterdir():
        if item.is_file() and item.suffix.lower() in image_extensions and item.name != "index.qmd" and item.name != "index.md":
            # Move loose image to img/ directory
            destination = img_dir / item.name
            
            # Handle filename conflicts
            counter = 1
            original_destination = destination
            while destination.exists():
                stem = original_destination.stem
                suffix = original_destination.suffix
                destination = img_dir / f"{stem}_{counter:02d}{suffix}"
                counter += 1
            
            shutil.move(str(item), str(destination))
            changes.append(f"Moved loose image: {item.name} → img/{destination.name}")
    
    # Check for subdirectories that might contain images (but shouldn't exist after script 01)
    for item in post_dir.iterdir():
        if item.is_dir() and item.name != "img":
            # Check if this directory contains images
            image_files = [f for f in item.rglob("*") if f.is_file() and f.suffix.lower() in image_extensions]
            
            if image_files:
                changes.append(f"Warning: Found images in unexpected directory {item.name}/")
                # Move them to img/
                for image_file in image_files:
                    destination = img_dir / image_file.name
                    
                    # Handle filename conflicts
                    counter = 1
                    original_destination = destination
                    while destination.exists():
                        stem = original_destination.stem
                        suffix = original_destination.suffix
                        destination = img_dir / f"{stem}_{counter:02d}{suffix}"
                        counter += 1
                    
                    shutil.move(str(image_file), str(destination))
                    changes.append(f"Moved image: {item.name}/{image_file.name} → img/{destination.name}")
                
                # Try to remove the now-empty directory
                try:
                    item.rmdir()
                    changes.append(f"Removed empty directory: {item.name}")
                except OSError as e:
                    changes.append(f"Warning: Could not remove directory {item.name}: {e}")
    
    return changes

def validate_image_references(content, post_dir):
    """Validate that all referenced images exist."""
    errors = []
    warnings = []
    
    images = extract_image_references(content)
    img_dir = post_dir / "img"
    
    for image in images:
        image_path = post_dir / image['path']
        
        if not image_path.exists():
            errors.append(f"Missing image: {image['path']}")
        elif not image_path.is_file():
            errors.append(f"Image path exists but is not a file: {image['path']}")
        elif image_path.stat().st_size == 0:
            warnings.append(f"Empty image file: {image['path']}")
    
    # Check for orphaned images (images in img/ that aren't referenced)
    if img_dir.exists():
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
        existing_images = set()
        for img_file in img_dir.iterdir():
            if img_file.is_file() and img_file.suffix.lower() in image_extensions:
                existing_images.add(img_file.name)
        
        referenced_images = set()
        for image in images:
            if image['path'].startswith('img/'):
                referenced_images.add(image['path'][4:])  # Remove 'img/' prefix
            else:
                referenced_images.add(Path(image['path']).name)
        
        orphaned = existing_images - referenced_images
        if orphaned:
            warnings.append(f"Orphaned images (not referenced): {', '.join(sorted(orphaned))}")
    
    return errors, warnings

def process_post_directory(post_dir):
    """Process a single post directory."""
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
    
    # Read the file
    try:
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError as e:
        print(f"    ❌ Error: Could not read {content_file}: {e}")
        return False
    
    original_content = content
    all_changes = []
    
    # 1. Organize images first (should already be done by script 01, but double-check)
    print("    🗂️  Organizing images...")
    image_changes = organize_images_in_post(post_dir)
    all_changes.extend(image_changes)
    
    # 2. Convert sizing syntax
    print("    📏 Converting sizing syntax...")
    content, sizing_changes = convert_sizing_syntax(content)
    all_changes.extend(sizing_changes)
    
    # 3. Update image paths
    print("    🔗 Updating image paths...")
    content, path_changes = update_image_paths(content)
    all_changes.extend(path_changes)
    
    # 4. Handle PDF links
    print("    📄 Checking PDF links...")
    content, pdf_changes = handle_pdf_links(content)
    all_changes.extend(pdf_changes)
    
    # 5. Validate image references
    print("    ✅ Validating image references...")
    errors, warnings = validate_image_references(content, post_dir)
    
    if errors:
        print(f"    ❌ Validation errors:")
        for error in errors:
            print(f"      - {error}")
        return False
    
    if warnings:
        print(f"    ⚠️  Warnings:")
        for warning in warnings:
            print(f"      - {warning}")
    
    # Write the updated content if there were changes
    if content != original_content:
        try:
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"    ✅ Updated {content_file.name}")
        except Exception as e:
            print(f"    ❌ Error writing {content_file}: {e}")
            return False
    else:
        print(f"    ℹ️  No content changes needed")
    
    # Report all changes
    if all_changes:
        print(f"    📋 Changes made:")
        for change in all_changes:
            print(f"      - {change}")
    else:
        print(f"    ✨ No changes needed")
    
    return True

def main():
    """Main function to process all post directories in processed-staging."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    staging_dir = repo_root / "processed-staging"
    
    if not staging_dir.exists():
        print(f"❌ Error: {staging_dir} does not exist.")
        print("Make sure to run the previous scripts first.")
        return
    
    print("🖼️  Fixing image paths and organizing images")
    print("=" * 55)
    print(f"📂 Processing directory: {staging_dir}")
    
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
        return
    
    print(f"📁 Found {len(post_dirs)} post directory(ies)")
    
    success_count = 0
    error_count = 0
    
    # Process each post directory
    for post_dir in sorted(post_dirs):
        try:
            if process_post_directory(post_dir):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"❌ Unexpected error processing {post_dir.name}: {e}")
            error_count += 1
    
    # Summary
    print(f"\n📊 Processing Summary")
    print("=" * 30)
    print(f"✅ Successfully processed: {success_count}")
    print(f"❌ Errors: {error_count}")
    
    if error_count > 0:
        print(f"\n⚠️  Some posts had errors. Please review and fix before proceeding.")
        return
    
    print(f"\n🎉 Image path processing complete!")
    print(f"📋 Next step: python scripts/05-validate-content.py")

if __name__ == "__main__":
    main()