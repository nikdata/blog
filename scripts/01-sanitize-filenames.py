#!/usr/bin/env python3
"""
Sanitize filenames in Bear exports for Quarto blog processing.
Enhanced version that handles both Bear export format AND loose image files.

This script:
1. Copies files from ingest-external-md/ to processed-staging/
2. Creates date-prefixed post directories (YYYYMMDD_post-name/)
3. Renames markdown files to index.qmd
4. Handles Bear export image directories (matching folder names)
5. Handles loose image files (creates img/ directory and moves them)
6. Updates image references in markdown files
7. Handles edge cases like duplicate names and encoding issues
8. Ignores README.md files in the input directory

Usage:
    python scripts/01-sanitize-filenames.py
    
The script automatically processes ingest-external-md/ → processed-staging/
"""

import os
import re
import sys
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime


def sanitize_filename(filename: str, is_directory: bool = False) -> str:
    """
    Sanitize a filename by removing invalid characters and normalizing format.
    
    Args:
        filename: Original filename (with or without extension)
        is_directory: Whether this is a directory name
        
    Returns:
        Sanitized filename
    """
    # Handle file extension separately
    if not is_directory and '.' in filename:
        name, ext = filename.rsplit('.', 1)
        ext = f".{ext.lower()}"
    else:
        name = filename
        ext = ""
    
    # Replace spaces with dashes
    name = name.replace(' ', '-')
    
    # Remove invalid filesystem characters
    invalid_chars = r'[<>:"|?*\\/]'
    name = re.sub(invalid_chars, '', name)
    
    # Remove multiple consecutive dashes
    name = re.sub(r'-+', '-', name)
    
    # Remove leading/trailing dashes
    name = name.strip('-')
    
    # Convert to lowercase
    name = name.lower()
    
    # Ensure name isn't empty
    if not name:
        name = "untitled"
    
    return name + ext


def extract_date_from_yaml(markdown_content: str) -> Optional[str]:
    """
    Extract date from YAML frontmatter if present.
    
    Args:
        markdown_content: Full markdown content with potential YAML frontmatter
        
    Returns:
        Date string in YYYYMMDD format, or None if not found or invalid
    """
    # Check if content starts with YAML frontmatter
    if not markdown_content.strip().startswith('---'):
        return None
    
    try:
        # Find the closing ---
        lines = markdown_content.split('\n')
        yaml_end = None
        
        for i, line in enumerate(lines[1:], 1):  # Start from line 1 (skip first ---)
            if line.strip() == '---':
                yaml_end = i
                break
        
        if yaml_end is None:
            return None
        
        # Extract YAML content
        yaml_content = '\n'.join(lines[1:yaml_end])
        
        # Parse YAML
        try:
            frontmatter = yaml.safe_load(yaml_content)
            if not frontmatter or 'date' not in frontmatter:
                return None
            
            date_value = frontmatter['date']
            
            # Handle different date formats
            if isinstance(date_value, datetime):
                return date_value.strftime('%Y%m%d')
            
            # Convert string dates to YYYYMMDD format
            date_str = str(date_value).strip().strip('"').strip("'")
            
            # Try to parse various date formats
            date_patterns = [
                r'^(\d{4})-(\d{1,2})-(\d{1,2})$',  # 2025-08-13
                r'^(\d{4})/(\d{1,2})/(\d{1,2})$',  # 2025/08/13
                r'^(\d{1,2})/(\d{1,2})/(\d{4})$',  # 08/13/2025
                r'^(\d{1,2})-(\d{1,2})-(\d{4})$',  # 08-13-2025
            ]
            
            for pattern in date_patterns:
                match = re.match(pattern, date_str)
                if match:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # Year first
                        year, month, day = groups
                    else:  # Year last
                        month, day, year = groups
                    
                    try:
                        # Validate and format date
                        date_obj = datetime(int(year), int(month), int(day))
                        return date_obj.strftime('%Y%m%d')
                    except ValueError:
                        continue
            
            # If no pattern matched, try dateutil parser as fallback
            try:
                from dateutil.parser import parse as date_parse
                parsed_date = date_parse(date_str)
                return parsed_date.strftime('%Y%m%d')
            except:
                pass
                
        except yaml.YAMLError:
            pass
            
    except Exception:
        pass
    
    return None


def get_date_prefix(markdown_content: str = None) -> str:
    """
    Get date prefix for post directory naming.
    
    Args:
        markdown_content: Optional markdown content to extract date from
        
    Returns:
        Date in YYYYMMDD format
    """
    # Try to extract date from YAML frontmatter first
    if markdown_content:
        yaml_date = extract_date_from_yaml(markdown_content)
        if yaml_date:
            return yaml_date
    
    # Fallback to current date
    return datetime.now().strftime("%Y%m%d")


def create_post_directory_name(markdown_filename: str, markdown_content: str = None) -> str:
    """
    Create a post directory name from markdown filename.
    
    Args:
        markdown_filename: Original filename like "My Blog Post.md"
        markdown_content: Optional markdown content to extract date from
        
    Returns:
        Directory name like "20250813_my-blog-post" (using YAML date if available)
    """
    # Remove extension
    name_without_ext = Path(markdown_filename).stem
    
    # Sanitize the name
    sanitized_name = sanitize_filename(name_without_ext, is_directory=True)
    
    # Get date prefix (from YAML if available, otherwise current date)
    date_prefix = get_date_prefix(markdown_content)
    
    return f"{date_prefix}_{sanitized_name}"


def find_markdown_files(directory: Path) -> List[Path]:
    """Find all markdown files in directory, excluding README.md."""
    all_md_files = list(directory.glob("*.md"))
    
    # Filter out README.md files (case-insensitive)
    filtered_files = []
    for md_file in all_md_files:
        if md_file.name.lower() != 'readme.md':
            filtered_files.append(md_file)
        else:
            print(f"  📄 Ignoring: {md_file.name}")
    
    return filtered_files


def find_image_directories(directory: Path, markdown_files: List[Path]) -> List[Path]:
    """
    Find directories that match markdown filenames (Bear export pattern).
    
    Bear exports create directories with same name as markdown file (without .md)
    """
    image_dirs = []
    
    for md_file in markdown_files:
        # Get filename without extension
        md_stem = md_file.stem
        potential_dir = directory / md_stem
        
        if potential_dir.is_dir():
            image_dirs.append(potential_dir)
    
    return image_dirs


def find_loose_images(directory: Path, markdown_files: List[Path], image_directories: List[Path]) -> List[Path]:
    """
    Find loose image files that aren't in directories and aren't markdown files.
    
    Args:
        directory: The input directory to scan
        markdown_files: List of markdown files (to exclude)
        image_directories: List of image directories (files in these will be handled separately)
        
    Returns:
        List of loose image files
    """
    # Common image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff', '.ico'}
    
    # Get all files in the directory
    all_files = [f for f in directory.iterdir() if f.is_file()]
    
    # Create sets for faster lookup
    markdown_file_names = {f.name for f in markdown_files}
    image_dir_names = {d.name for d in image_directories}
    
    loose_images = []
    
    for file_path in all_files:
        # Skip if it's a markdown file
        if file_path.name in markdown_file_names:
            continue
            
        # Skip if it's README.md (case-insensitive)
        if file_path.name.lower() == 'readme.md':
            continue
        
        # Check if it's an image file
        if file_path.suffix.lower() in image_extensions:
            loose_images.append(file_path)
    
    return loose_images


def get_image_references(markdown_content: str) -> List[str]:
    """
    Extract image references from markdown content.
    
    Matches patterns like:
    - ![alt text](path/to/image.jpg)
    - ![](image.png)
    - ![alt](folder/image.gif)
    """
    # Markdown image pattern: ![alt text](path)
    pattern = r'!\[.*?\]\(([^)]+)\)'
    matches = re.findall(pattern, markdown_content)
    return matches


def update_image_references(content: str, old_dir_name: str = None, loose_image_mapping: Dict[str, str] = None) -> str:
    """
    Update image references in markdown content to use standardized img/ directory.
    
    Args:
        content: Original markdown content
        old_dir_name: Original directory name from Bear export (optional)
        loose_image_mapping: Mapping of original filenames to img/ paths (optional)
        
    Returns:
        Updated markdown content with img/ paths
    """
    def replace_path(match):
        full_match = match.group(0)
        old_path = match.group(1)
        
        # Case 1: Bear export format - path starts with old directory name
        if old_dir_name and old_path.startswith(f"{old_dir_name}/"):
            # Replace "old-dir-name/image.jpg" with "img/image.jpg"
            filename = old_path[len(old_dir_name) + 1:]  # Remove "old-dir-name/"
            new_path = f"img/{filename}"
            return full_match.replace(old_path, new_path)
        
        # Case 2: Loose image - just a filename
        elif loose_image_mapping and old_path in loose_image_mapping:
            # Replace "image.jpg" with "img/image.jpg"
            new_path = loose_image_mapping[old_path]
            return full_match.replace(old_path, new_path)
        
        # Case 3: Already correct format or unrecognized - leave as-is
        return full_match
    
    # Replace image references
    pattern = r'!\[.*?\]\(([^)]+)\)'
    updated_content = re.sub(pattern, replace_path, content)
    
    return updated_content


def handle_naming_conflicts(target_path: Path, is_directory: bool = False) -> Path:
    """
    Handle naming conflicts by adding numeric suffixes.
    
    If '20250804_my-post' exists, try '20250804_my-post-01', '20250804_my-post-02', etc.
    """
    if not target_path.exists():
        return target_path
    
    base_path = target_path.parent
    
    if is_directory:
        base_name = target_path.name
        suffix = ""
    else:
        # Handle files with extensions
        if '.' in target_path.name:
            base_name, ext = target_path.name.rsplit('.', 1)
            suffix = f".{ext}"
        else:
            base_name = target_path.name
            suffix = ""
    
    counter = 1
    while True:
        new_name = f"{base_name}-{counter:02d}{suffix}"
        new_path = base_path / new_name
        
        if not new_path.exists():
            return new_path
        
        counter += 1
        
        # Safety valve
        if counter > 99:
            raise ValueError(f"Too many naming conflicts for {target_path}")


def process_directory(input_dir: Path, output_dir: Path) -> Dict[str, str]:
    """
    Process a directory by copying files to output and organizing into post directories.
    Enhanced to handle both Bear exports and loose image files.
    
    Args:
        input_dir: Source directory (ingest-external-md)
        output_dir: Destination directory (processed-staging)
        
    Returns:
        Dictionary mapping old paths to new paths for logging
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    if not input_dir.is_dir():
        raise ValueError(f"Input path is not a directory: {input_dir}")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing: {input_dir} → {output_dir}")
    
    # Track all renames for logging
    path_mapping = {}
    
    # Step 1: Find markdown files, image directories, and loose images
    markdown_files = find_markdown_files(input_dir)
    image_directories = find_image_directories(input_dir, markdown_files)
    loose_images = find_loose_images(input_dir, markdown_files, image_directories)
    
    print(f"Found {len(markdown_files)} markdown files")
    print(f"Found {len(image_directories)} image directories (Bear format)")
    print(f"Found {len(loose_images)} loose image files")
    
    # Step 2: Process each markdown file and its associated images
    for md_file in markdown_files:
        print(f"\n📝 Processing: {md_file.name}")
        
        # Read markdown content first (needed for date extraction)
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"  ⚠️ Encoding issue with {md_file.name}, trying latin-1")
            with open(md_file, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Create post directory name (using date from YAML if available)
        post_dir_name = create_post_directory_name(md_file.name, content)
        post_dir_path = output_dir / post_dir_name
        
        # Handle naming conflicts for post directory
        post_dir_path = handle_naming_conflicts(post_dir_path, is_directory=True)
        
        # Create the post directory
        post_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Check if we used YAML date vs current date and provide feedback
        yaml_date = extract_date_from_yaml(content)
        if yaml_date:
            print(f"  📁 Created directory: {post_dir_path.name} (using date from YAML: {yaml_date[:4]}-{yaml_date[4:6]}-{yaml_date[6:8]})")
        else:
            print(f"  📁 Created directory: {post_dir_path.name} (using current date)")
        
        # Find matching image directory for this markdown file (Bear export format)
        md_stem = md_file.stem
        matching_img_dir = None
        for img_dir in image_directories:
            if img_dir.name == md_stem:
                matching_img_dir = img_dir
                break
        
        # Create img directory in post folder
        img_dest_dir = post_dir_path / "img"
        images_processed = False
        
        # Process Bear export images if they exist
        if matching_img_dir:
            print(f"  🖼️ Processing Bear export images from: {matching_img_dir.name}")
            
            # Copy all images to img/ directory
            shutil.copytree(matching_img_dir, img_dest_dir)
            print(f"    Copied images: {matching_img_dir.name}/ → img/")
            images_processed = True
            
            # Update image references in markdown content
            content = update_image_references(content, old_dir_name=md_stem)
            print(f"    Updated Bear export image references to use img/ paths")
        
        # Process loose images (find images that might belong to this post)
        post_loose_images = []
        loose_image_mapping = {}
        
        # Extract image references from markdown to see what images this post expects
        referenced_images = get_image_references(content)
        
        for image_path in referenced_images:
            # Check if this reference matches a loose image file
            image_filename = Path(image_path).name  # Get just the filename part
            
            for loose_image in loose_images:
                if loose_image.name == image_filename:
                    post_loose_images.append(loose_image)
                    loose_image_mapping[image_path] = f"img/{image_filename}"
                    break
        
        if post_loose_images:
            print(f"  🖼️ Processing {len(post_loose_images)} loose image(s) for this post")
            
            # Create img directory if it doesn't exist
            if not img_dest_dir.exists():
                img_dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy loose images to img/ directory
            for loose_image in post_loose_images:
                dest_path = img_dest_dir / loose_image.name
                
                # Handle filename conflicts
                dest_path = handle_naming_conflicts(dest_path)
                
                shutil.copy2(loose_image, dest_path)
                print(f"    Copied loose image: {loose_image.name} → img/{dest_path.name}")
                
                # Update mapping if filename changed due to conflict
                if dest_path.name != loose_image.name:
                    # Update the mapping to reflect the new filename
                    for old_ref, new_ref in loose_image_mapping.items():
                        if new_ref == f"img/{loose_image.name}":
                            loose_image_mapping[old_ref] = f"img/{dest_path.name}"
            
            # Update image references for loose images
            content = update_image_references(content, loose_image_mapping=loose_image_mapping)
            print(f"    Updated loose image references to use img/ paths")
            images_processed = True
            
            # Remove processed loose images from the list so they don't get processed again
            for processed_image in post_loose_images:
                if processed_image in loose_images:
                    loose_images.remove(processed_image)
        
        # Handle remaining loose images that weren't referenced by any markdown file
        if not images_processed and len(markdown_files) == 1 and loose_images:
            # If there's only one markdown file and loose images, assume they belong together
            print(f"  🖼️ Processing {len(loose_images)} loose image(s) (single post assumption)")
            
            # Create img directory
            img_dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all remaining loose images
            for loose_image in loose_images:
                dest_path = img_dest_dir / loose_image.name
                dest_path = handle_naming_conflicts(dest_path)
                shutil.copy2(loose_image, dest_path)
                print(f"    Copied loose image: {loose_image.name} → img/{dest_path.name}")
            
            # Clear the loose images list since we processed them all
            loose_images.clear()
            images_processed = True
        
        # Write markdown content as index.qmd
        index_file_path = post_dir_path / "index.qmd"
        with open(index_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  📄 Created: index.qmd")
        
        # Track mapping for logging
        path_mapping[str(md_file)] = str(post_dir_path)
    
    # Handle any remaining loose images that weren't matched to posts
    if loose_images:
        print(f"\n⚠️ Warning: {len(loose_images)} loose image(s) found with no matching post:")
        for loose_image in loose_images:
            print(f"    - {loose_image.name}")
        print("These images will be ignored. Consider:")
        print("  - Adding image references to your markdown")
        print("  - Moving images to a folder matching your post name")
        print("  - Removing unused images")
    
    return path_mapping


def main():
    """Main entry point."""
    # Hardcoded paths relative to current working directory
    input_path = Path("ingest-external-md")
    output_path = Path("processed-staging")
    
    # Verify input directory exists
    if not input_path.exists():
        print(f"Error: Input directory '{input_path}' not found")
        print("Make sure you're running this from the blog root directory")
        sys.exit(1)
    
    if not input_path.is_dir():
        print(f"Error: '{input_path}' is not a directory")
        sys.exit(1)
    
    # Check if input directory is empty or has no processable files
    if not any(input_path.iterdir()):
        print(f"No files found in '{input_path}' - nothing to process")
        sys.exit(0)
    
    # Check specifically for markdown files (excluding README.md)
    markdown_files = find_markdown_files(input_path)
    if not markdown_files:
        print(f"No processable markdown files found in '{input_path}' - nothing to process")
        sys.exit(0)
    
    try:
        print(f"🔧 Sanitizing filenames and organizing posts (enhanced with loose image support and YAML date extraction)")
        print("=" * 100)
        path_mapping = process_directory(input_path, output_path)
        
        print(f"\n📊 Summary")
        print("=" * 20)
        if path_mapping:
            print("Posts created:")
            for old_path, new_path in path_mapping.items():
                old_name = Path(old_path).name
                new_name = Path(new_path).name
                print(f"  {old_name} → {new_name}/")
        else:
            print("No posts processed.")
            
        print(f"\n✅ Processed files are now in: {output_path}")
        print(f"🗂️ Each post is in its own date-prefixed directory with index.qmd")
        print(f"📅 Dates extracted from YAML frontmatter when available")
        print(f"📷 Images organized in standardized img/ directories")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()