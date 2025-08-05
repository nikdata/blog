#!/usr/bin/env python3
"""
Sanitize filenames in Bear exports for Quarto blog processing.

This script:
1. Copies files from ingest-external-md/ to processed-staging/
2. Creates date-prefixed post directories (YYYYMMDD_post-name/)
3. Renames markdown files to index.qmd
4. Recursively copies and renames matching image directories to img/
5. Updates image references in markdown files
6. Handles edge cases like duplicate names and encoding issues
7. Ignores README.md files in the input directory

Usage:
    python scripts/01-sanitize-filenames.py
    
The script automatically processes ingest-external-md/ → processed-staging/
"""

import os
import re
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
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


def get_date_prefix() -> str:
    """Get current date in YYYYMMDD format for post directory naming."""
    return datetime.now().strftime("%Y%m%d")


def create_post_directory_name(markdown_filename: str) -> str:
    """
    Create a post directory name from markdown filename.
    
    Args:
        markdown_filename: Original filename like "My Blog Post.md"
        
    Returns:
        Directory name like "20250804_my-blog-post"
    """
    # Remove extension
    name_without_ext = Path(markdown_filename).stem
    
    # Sanitize the name
    sanitized_name = sanitize_filename(name_without_ext, is_directory=True)
    
    # Add date prefix
    date_prefix = get_date_prefix()
    
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


def update_image_references(content: str, old_dir_name: str) -> str:
    """
    Update image references in markdown content to use standardized img/ directory.
    
    Args:
        content: Original markdown content
        old_dir_name: Original directory name from Bear export
        
    Returns:
        Updated markdown content with img/ paths
    """
    def replace_path(match):
        full_match = match.group(0)
        old_path = match.group(1)
        
        # If the path starts with the old directory name, replace with img/
        if old_path.startswith(f"{old_dir_name}/"):
            # Replace "old-dir-name/image.jpg" with "img/image.jpg"
            filename = old_path[len(old_dir_name) + 1:]  # Remove "old-dir-name/"
            new_path = f"img/{filename}"
            return full_match.replace(old_path, new_path)
        
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
    
    # Step 1: Find markdown files and associated image directories in input
    markdown_files = find_markdown_files(input_dir)
    image_directories = find_image_directories(input_dir, markdown_files)
    
    print(f"Found {len(markdown_files)} markdown files")
    print(f"Found {len(image_directories)} image directories")
    
    # Step 2: Process each markdown file and its associated images
    for md_file in markdown_files:
        print(f"\n📝 Processing: {md_file.name}")
        
        # Create post directory name
        post_dir_name = create_post_directory_name(md_file.name)
        post_dir_path = output_dir / post_dir_name
        
        # Handle naming conflicts for post directory
        post_dir_path = handle_naming_conflicts(post_dir_path, is_directory=True)
        
        # Create the post directory
        post_dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  📁 Created directory: {post_dir_path.name}")
        
        # Read markdown content
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"  ⚠️ Encoding issue with {md_file.name}, trying latin-1")
            with open(md_file, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Find matching image directory for this markdown file
        md_stem = md_file.stem
        matching_img_dir = None
        for img_dir in image_directories:
            if img_dir.name == md_stem:
                matching_img_dir = img_dir
                break
        
        # Process images if they exist
        if matching_img_dir:
            print(f"  🖼️ Processing images from: {matching_img_dir.name}")
            
            # Create img directory in post folder
            img_dest_dir = post_dir_path / "img"
            
            # Copy all images to img/ directory
            shutil.copytree(matching_img_dir, img_dest_dir)
            print(f"    Copied images: {matching_img_dir.name}/ → img/")
            
            # Update image references in markdown content
            content = update_image_references(content, md_stem)
            print(f"    Updated image references to use img/ paths")
        
        # Write markdown content as index.qmd
        index_file_path = post_dir_path / "index.qmd"
        with open(index_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  📄 Created: index.qmd")
        
        # Track mapping for logging
        path_mapping[str(md_file)] = str(post_dir_path)
    
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
        print(f"🔧 Sanitizing filenames and organizing posts")
        print("=" * 50)
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
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()