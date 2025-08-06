#!/usr/bin/env python3
"""
05-validate-content.py

Final validation script for processed markdown content.
Ensures all content is ready for promotion to posts/ directory.

Input/Output: processed-staging/ (validation only, no modifications)
Usage: python scripts/05-validate-content.py
"""

import os
import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def validate_yaml_frontmatter(content: str, filename: str) -> Tuple[bool, List[str], Dict]:
    """Validate YAML frontmatter structure and required fields."""
    errors = []
    warnings = []
    yaml_data = {}
    
    # Check if frontmatter exists
    if not content.strip().startswith('---'):
        errors.append(f"Missing YAML frontmatter")
        return False, errors, {}
    
    # Extract YAML frontmatter
    try:
        if content.count('---') < 2:
            errors.append("Incomplete YAML frontmatter (missing closing ---)")
            return False, errors, {}
        
        yaml_end = content.find('---', 3)
        yaml_content = content[3:yaml_end].strip()
        yaml_data = yaml.safe_load(yaml_content)
        
        if yaml_data is None:
            yaml_data = {}
    
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML syntax: {e}")
        return False, errors, {}
    
    # Validate required fields
    required_fields = ['title', 'author', 'date']
    for field in required_fields:
        if field not in yaml_data or not yaml_data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate field formats
    if 'title' in yaml_data:
        if not isinstance(yaml_data['title'], str) or not yaml_data['title'].strip():
            errors.append("Title must be a non-empty string")
    
    if 'author' in yaml_data:
        if yaml_data['author'] != "Nikhil Agarwal":
            warnings.append(f"Author is '{yaml_data['author']}', expected 'Nikhil Agarwal'")
    
    if 'date' in yaml_data:
        date_str = str(yaml_data['date'])
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            errors.append(f"Date format should be YYYY-MM-DD, got: {date_str}")
    
    if 'categories' in yaml_data:
        categories = yaml_data['categories']
        if not isinstance(categories, list):
            errors.append("Categories must be a YAML list")
        elif len(categories) == 0:
            warnings.append("Categories list is empty")
        elif len(categories) > 1:
            warnings.append(f"Multiple categories found: {categories} (expected single category)")
    
    if 'short-path' in yaml_data:
        short_path = yaml_data['short-path']
        if not isinstance(short_path, str) or not short_path.strip():
            errors.append("short-path must be a non-empty string")
        elif not re.match(r'^[a-z0-9-]+$', short_path):
            errors.append(f"short-path contains invalid characters: {short_path}")
    
    # Check for boolean fields
    boolean_fields = ['draft', 'toc', 'code-line-numbers']
    for field in boolean_fields:
        if field in yaml_data:
            if not isinstance(yaml_data[field], bool):
                errors.append(f"Field '{field}' should be boolean (true/false), got: {yaml_data[field]}")
    
    # Check description field
    if 'description' in yaml_data:
        if yaml_data['description'] == "":
            warnings.append("Description field is empty - consider adding a description for SEO")
    
    return len(errors) == 0, errors + warnings, yaml_data

def validate_image_references(content: str, post_dir: Path) -> Tuple[bool, List[str]]:
    """Validate that all referenced images exist."""
    errors = []
    warnings = []
    
    # Find all image references
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(image_pattern, content)
    
    if not matches:
        warnings.append("No images found in content")
        return True, warnings
    
    img_dir = post_dir / 'img'
    
    for alt_text, image_path in matches:
        # Handle different path formats
        if image_path.startswith('img/'):
            # Standard format: img/filename.jpg
            filename = image_path[4:]  # Remove 'img/' prefix
            full_path = img_dir / filename
        elif '/' not in image_path:
            # Just filename: filename.jpg (legacy format)
            full_path = img_dir / image_path
        else:
            # Other path formats shouldn't happen after processing
            errors.append(f"Non-standard image path found: {image_path}")
            continue
        
        if not full_path.exists():
            errors.append(f"Referenced image does not exist: {image_path} (looking for {full_path})")
        elif not full_path.is_file():
            errors.append(f"Image path exists but is not a file: {image_path}")
    
    # Check for orphaned images
    if img_dir.exists():
        existing_images = set()
        for img_file in img_dir.iterdir():
            if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
                existing_images.add(img_file.name)
        
        referenced_images = set()
        for _, image_path in matches:
            if image_path.startswith('img/'):
                referenced_images.add(image_path[4:])  # Remove 'img/' prefix
            elif '/' not in image_path:
                referenced_images.add(image_path)
        
        orphaned = existing_images - referenced_images
        if orphaned:
            warnings.append(f"Orphaned images found (not referenced in content): {', '.join(orphaned)}")
    
    return len(errors) == 0, errors + warnings

def validate_quarto_syntax(content: str) -> Tuple[bool, List[str]]:
    """Validate Quarto-specific syntax and formatting."""
    errors = []
    warnings = []
    
    # Check for Bear highlight remnants
    bear_highlights = re.findall(r'==[🟢🔴🔵🟡🟣][^=]*==', content)
    if bear_highlights:
        errors.append(f"Unconverted Bear highlights found: {bear_highlights[:3]}...")  # Show first 3
    
    # Check for Bear hash references
    hash_refs = re.findall(r'\[HASH [a-f0-9]+\]', content)
    if hash_refs:
        errors.append(f"Bear hash references found: {hash_refs[:3]}...")  # Show first 3
    
    # Check for duplicate heading markers
    duplicate_headings = re.findall(r'^(#{1,6}) \1 ', content, re.MULTILINE)
    if duplicate_headings:
        errors.append(f"Duplicate heading markers found: {duplicate_headings}")
    
    # Check for old Bear image sizing syntax
    bear_sizing = re.findall(r'\{"width":\d+\}', content)
    if bear_sizing:
        errors.append(f"Unconverted Bear sizing syntax found: {bear_sizing}")
    
    # Check for proper Quarto image sizing
    quarto_sizing = re.findall(r'\{width=\d+\}', content)
    if quarto_sizing:
        warnings.append(f"Found {len(quarto_sizing)} images with Quarto sizing - verify they render correctly")
    
    # Check for PDF references (should be flagged for manual review)
    pdf_refs = re.findall(r'\[([^\]]*)\]\([^)]*\.pdf\)', content)
    if pdf_refs:
        warnings.append(f"PDF references found - may need manual review: {pdf_refs}")
    
    return len(errors) == 0, errors + warnings

def validate_content_structure(content: str) -> Tuple[bool, List[str]]:
    """Validate overall content structure and quality."""
    errors = []
    warnings = []
    
    # Split into frontmatter and content
    parts = content.split('---', 2)
    if len(parts) < 3:
        errors.append("Cannot split content into frontmatter and body")
        return False, errors
    
    markdown_content = parts[2].strip()
    
    if not markdown_content:
        errors.append("No content found after frontmatter")
        return False, errors
    
    if len(markdown_content) < 50:
        warnings.append(f"Content is very short ({len(markdown_content)} characters)")
    
    # Check for headings
    headings = re.findall(r'^#{1,6} .+$', markdown_content, re.MULTILINE)
    if not headings:
        warnings.append("No headings found in content")
    
    # Check for multiple H1s (usually okay, but worth noting)
    h1_headings = re.findall(r'^# .+$', markdown_content, re.MULTILINE)
    if len(h1_headings) > 1:
        warnings.append(f"Multiple H1 headings found ({len(h1_headings)}) - verify structure")
    
    return len(errors) == 0, errors + warnings

def validate_filename_structure(post_dir: Path) -> Tuple[bool, List[str]]:
    """Validate the post directory structure and naming."""
    errors = []
    warnings = []
    
    # Check directory name format (should be YYYYMMDD_slug after processing)
    dir_name = post_dir.name
    if not re.match(r'^\d{8}_[a-z0-9-]+$', dir_name):
        warnings.append(f"Directory name doesn't match expected format YYYYMMDD_slug: {dir_name}")
    
    # Check for required files
    index_file = post_dir / 'index.qmd'
    if not index_file.exists():
        # Check for .md file that should be renamed
        md_files = list(post_dir.glob('*.md'))
        if md_files:
            warnings.append(f"Found .md file that should be renamed to index.qmd: {md_files[0].name}")
        else:
            errors.append("No index.qmd or .md file found")
    
    # Check img directory structure
    img_dir = post_dir / 'img'
    if img_dir.exists():
        if not img_dir.is_dir():
            errors.append("img path exists but is not a directory")
        else:
            img_files = list(img_dir.glob('*'))
            if not img_files:
                warnings.append("img directory exists but is empty")
    
    return len(errors) == 0, errors + warnings

def validate_single_post(post_dir: Path) -> Tuple[bool, Dict]:
    """Validate a single post directory and its contents."""
    result = {
        'name': post_dir.name,
        'valid': True,
        'errors': [],
        'warnings': [],
        'yaml_data': {}
    }
    
    print(f"\n📝 Validating: {post_dir.name}")
    
    # Check directory structure
    structure_valid, structure_messages = validate_filename_structure(post_dir)
    if not structure_valid:
        result['valid'] = False
    result['errors'].extend([msg for msg in structure_messages if 'error' in msg.lower() or not structure_valid])
    result['warnings'].extend([msg for msg in structure_messages if msg not in result['errors']])
    
    # Find the content file
    content_file = post_dir / 'index.qmd'
    if not content_file.exists():
        md_files = list(post_dir.glob('*.md'))
        if md_files:
            content_file = md_files[0]
        else:
            result['valid'] = False
            result['errors'].append("No content file found")
            return result['valid'], result
    
    # Read and validate content
    try:
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Failed to read content file: {e}")
        return result['valid'], result
    
    # Validate YAML frontmatter
    yaml_valid, yaml_messages, yaml_data = validate_yaml_frontmatter(content, content_file.name)
    if not yaml_valid:
        result['valid'] = False
    result['yaml_data'] = yaml_data
    result['errors'].extend([msg for msg in yaml_messages if any(word in msg.lower() for word in ['error', 'missing', 'invalid'])])
    result['warnings'].extend([msg for msg in yaml_messages if msg not in result['errors']])
    
    # Validate image references
    images_valid, image_messages = validate_image_references(content, post_dir)
    if not images_valid:
        result['valid'] = False
    result['errors'].extend([msg for msg in image_messages if 'does not exist' in msg or 'not a file' in msg])
    result['warnings'].extend([msg for msg in image_messages if msg not in result['errors']])
    
    # Validate Quarto syntax
    syntax_valid, syntax_messages = validate_quarto_syntax(content)
    if not syntax_valid:
        result['valid'] = False
    result['errors'].extend([msg for msg in syntax_messages if any(word in msg.lower() for word in ['found', 'unconverted'])])
    result['warnings'].extend([msg for msg in syntax_messages if msg not in result['errors']])
    
    # Validate content structure
    content_valid, content_messages = validate_content_structure(content)
    if not content_valid:
        result['valid'] = False
    result['errors'].extend([msg for msg in content_messages if 'cannot' in msg.lower() or 'no content' in msg.lower()])
    result['warnings'].extend([msg for msg in content_messages if msg not in result['errors']])
    
    # Print results
    if result['valid']:
        print(f"   ✅ Valid")
    else:
        print(f"   ❌ Invalid")
    
    if result['errors']:
        print(f"   🚨 Errors ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"      • {error}")
    
    if result['warnings']:
        print(f"   ⚠️  Warnings ({len(result['warnings'])}):")
        for warning in result['warnings']:
            print(f"      • {warning}")
    
    return result['valid'], result

def main():
    """Main validation function."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    staging_dir = repo_root / 'processed-staging'
    
    print("🔍 Quarto Blog Content Validation")
    print("=" * 50)
    
    if not staging_dir.exists():
        print(f"❌ Error: processed-staging directory not found: {staging_dir}")
        sys.exit(1)
    
    # Find all post directories
    post_dirs = [d for d in staging_dir.iterdir() if d.is_dir()]
    
    if not post_dirs:
        print("ℹ️  No posts found in processed-staging directory")
        return
    
    print(f"📂 Found {len(post_dirs)} post(s) to validate")
    
    # Validate each post
    results = []
    valid_count = 0
    
    for post_dir in sorted(post_dirs):
        is_valid, result = validate_single_post(post_dir)
        results.append(result)
        if is_valid:
            valid_count += 1
    
    # Summary
    print(f"\n📊 Validation Summary")
    print("=" * 30)
    print(f"Total posts: {len(results)}")
    print(f"Valid posts: {valid_count}")
    print(f"Invalid posts: {len(results) - valid_count}")
    
    if valid_count == len(results):
        print(f"\n🎉 All posts are valid and ready for promotion!")
    else:
        print(f"\n⚠️  {len(results) - valid_count} post(s) need attention before promotion")
        
        # List invalid posts
        invalid_posts = [r for r in results if not r['valid']]
        if invalid_posts:
            print(f"\n❌ Invalid posts:")
            for result in invalid_posts:
                print(f"   • {result['name']} ({len(result['errors'])} errors)")
    
    # Check for short-path conflicts
    print(f"\n🔍 Checking for short-path conflicts...")
    short_paths = {}
    conflicts = []
    
    for result in results:
        if result['yaml_data'].get('short-path'):
            short_path = result['yaml_data']['short-path']
            if short_path in short_paths:
                conflicts.append((short_path, [short_paths[short_path], result['name']]))
            else:
                short_paths[short_path] = result['name']
    
    if conflicts:
        print(f"⚠️  Short-path conflicts found:")
        for short_path, posts in conflicts:
            print(f"   • '{short_path}' used by: {', '.join(posts)}")
    else:
        print("✅ No short-path conflicts found")
    
    # Exit with appropriate code
    if valid_count == len(results) and not conflicts:
        print(f"\n✅ Validation complete - all content ready for promotion!")
        sys.exit(0)
    else:
        print(f"\n❌ Validation failed - please fix issues before promotion")
        sys.exit(1)

if __name__ == "__main__":
    main()