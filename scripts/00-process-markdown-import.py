#!/usr/bin/env python3
"""
Main orchestrator script for processing Bear markdown exports into Quarto blog posts.

This script runs the complete processing pipeline:
1. Sanitizes filenames and creates post directories
2. Standardizes YAML frontmatter  
3. Converts Bear highlights to HTML
4. Fixes image paths and organization
5. Validates final content
6. Optionally promotes validated content to posts/ directory

Usage:
    python scripts/00-process-markdown-import.py [--promote]
    
Arguments:
    --promote: Automatically promote validated content to posts/ directory
    
The script automatically processes ingest-external-md/ → processed-staging/ → posts/

Examples

# Process only (manual review)
python scripts/00-process-markdown-import.py

# Process and show what would be promoted
python scripts/00-process-markdown-import.py --dry-run

# Process and automatically promote
python scripts/00-process-markdown-import.py --promote

# Process, promote, and keep staging for review
python scripts/00-process-markdown-import.py --promote --keep-staging
"""

import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import argparse


def run_script(script_name: str, description: str) -> bool:
    """
    Run a processing script and return success status.
    
    Args:
        script_name: Name of the script to run (e.g., "01-sanitize-filenames.py")
        description: Human-readable description for console output
        
    Returns:
        True if script succeeded, False otherwise
    """
    script_path = Path("scripts") / script_name
    
    if not script_path.exists():
        print(f"❌ Error: Script not found: {script_path}")
        return False
    
    print(f"\n🔧 Step: {description}")
    print("=" * 60)
    
    try:
        # Run the script using the same Python interpreter
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=False, text=True, check=True)
        
        print(f"✅ {description} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error running {script_name}: {e}")
        return False


def check_prerequisites() -> bool:
    """Check that all required directories and scripts exist."""
    print("🔍 Checking prerequisites...")
    
    required_dirs = ["ingest-external-md", "scripts"]
    required_scripts = [
        "01-sanitize-filenames.py",
        "02-standardize-yaml.py", 
        "03-convert-highlights.py",
        "04-fix-image-paths.py",
        "05-validate-content.py"
    ]
    
    # Check directories
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            print(f"❌ Required directory not found: {dir_name}")
            return False
        print(f"  ✅ Found directory: {dir_name}")
    
    # Check scripts
    for script_name in required_scripts:
        script_path = Path("scripts") / script_name
        if not script_path.exists():
            print(f"❌ Required script not found: {script_path}")
            return False
        print(f"  ✅ Found script: {script_name}")
    
    # Check for content to process
    ingest_dir = Path("ingest-external-md")
    md_files = [f for f in ingest_dir.glob("*.md") if f.name.lower() != 'readme.md']
    if not md_files:
        print(f"ℹ️  No processable .md files found in {ingest_dir} - nothing to process")
        return False
    
    print(f"  📄 Found {len(md_files)} markdown file(s) to process")
    
    return True


def clear_staging_directory() -> bool:
    """Clear the processed-staging directory if it exists, but preserve README.md."""
    staging_dir = Path("processed-staging")
    
    if staging_dir.exists():
        print(f"🧹 Clearing existing staging directory...")
        try:
            # Preserve README.md if it exists
            readme_file = staging_dir / "README.md"
            readme_content = None
            if readme_file.exists():
                with open(readme_file, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                print(f"  📄 Preserving README.md")
            
            # Remove the entire directory
            shutil.rmtree(staging_dir)
            
            # Recreate directory and restore README.md
            staging_dir.mkdir(parents=True, exist_ok=True)
            if readme_content is not None:
                with open(readme_file, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                print(f"  📄 Restored README.md")
            
            print(f"  ✅ Cleared {staging_dir}")
        except Exception as e:
            print(f"❌ Failed to clear {staging_dir}: {e}")
            return False
    
    return True


def promote_to_posts(dry_run: bool = False) -> bool:
    """
    Promote validated content from processed-staging/ to posts/ directory.
    
    Args:
        dry_run: If True, show what would be done without actually doing it
        
    Returns:
        True if promotion succeeded, False otherwise
    """
    staging_dir = Path("processed-staging")
    posts_dir = Path("posts")
    
    if not staging_dir.exists():
        print(f"❌ No staging directory found: {staging_dir}")
        return False
    
    # Find all post directories (exclude README.md)
    post_dirs = [d for d in staging_dir.iterdir() if d.is_dir()]
    
    if not post_dirs:
        print(f"ℹ️  No post directories found in {staging_dir}")
        return True
    
    print(f"📦 {'Would promote' if dry_run else 'Promoting'} {len(post_dirs)} post(s) to {posts_dir}")
    
    # Create posts directory if it doesn't exist
    if not dry_run:
        posts_dir.mkdir(exist_ok=True)
    
    success_count = 0
    
    for post_dir in sorted(post_dirs):
        destination = posts_dir / post_dir.name
        
        if destination.exists():
            print(f"  ⚠️  Destination already exists: {destination.name}")
            
            if not dry_run:
                # Ask for confirmation to overwrite
                response = input(f"    Overwrite {destination.name}? (y/N): ").strip().lower()
                if response != 'y':
                    print(f"    Skipped: {post_dir.name}")
                    continue
                
                # Remove existing destination
                try:
                    shutil.rmtree(destination)
                    print(f"    Removed existing: {destination.name}")
                except Exception as e:
                    print(f"    ❌ Failed to remove {destination.name}: {e}")
                    continue
        
        if dry_run:
            print(f"  📋 Would copy: {post_dir.name} → {destination.name}")
        else:
            try:
                shutil.copytree(post_dir, destination)
                print(f"  ✅ Promoted: {post_dir.name} → {destination.name}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ Failed to promote {post_dir.name}: {e}")
                continue
    
    if not dry_run:
        print(f"\n🎉 Successfully promoted {success_count} post(s)")
        
        if success_count > 0:
            print(f"\n📝 Next steps:")
            print(f"  1. Review the promoted posts in {posts_dir}")
            print(f"  2. Run 'quarto render' to build the site")
            print(f"  3. Commit and push to trigger deployment")
    
    return True


def cleanup_staging(keep_staging: bool = False) -> bool:
    """
    Clean up the staging directory after successful processing.
    
    Args:
        keep_staging: If True, keep the staging directory for review
        
    Returns:
        True if cleanup succeeded, False otherwise
    """
    if keep_staging:
        print(f"📂 Keeping processed-staging/ for review")
        return True
    
    staging_dir = Path("processed-staging")
    
    if staging_dir.exists():
        print(f"🧹 Cleaning up staging directory contents...")
        try:
            # Remove all items except README.md
            preserved_files = ["README.md", "readme.md"]
            removed_count = 0
            
            for item in staging_dir.iterdir():
                if item.name in preserved_files:
                    print(f"  📄 Preserved: {item.name}")
                    continue
                    
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"  🗂️  Removed directory: {item.name}")
                else:
                    item.unlink()
                    print(f"  📄 Removed file: {item.name}")
                    
                removed_count += 1
            
            if removed_count == 0:
                print(f"  ✨ No items to remove")
            else:
                print(f"  ✅ Cleaned {removed_count} item(s) from staging directory")
                
        except Exception as e:
            print(f"❌ Failed to clean staging directory: {e}")
            return False
    
    return True


def cleanup_ingest_directory() -> bool:
    """
    Clean up the ingest-external-md directory after successful processing and promotion.
    Preserves README.md but removes all other files and directories.
    
    Returns:
        True if cleanup succeeded, False otherwise
    """
    ingest_dir = Path("ingest-external-md")
    
    if not ingest_dir.exists():
        print(f"📂 Ingest directory doesn't exist - nothing to clean")
        return True
    
    print(f"🧹 Cleaning up ingest directory contents...")
    try:
        # Remove all items except README.md
        preserved_files = ["README.md", "readme.md"]
        removed_count = 0
        
        for item in ingest_dir.iterdir():
            if item.name in preserved_files:
                print(f"  📄 Preserved: {item.name}")
                continue
                
            if item.is_dir():
                shutil.rmtree(item)
                print(f"  🗂️  Removed directory: {item.name}")
            else:
                item.unlink()
                print(f"  📄 Removed file: {item.name}")
                
            removed_count += 1
        
        if removed_count == 0:
            print(f"  ✨ No items to remove from ingest directory")
        else:
            print(f"  ✅ Cleaned {removed_count} item(s) from ingest directory")
            
    except Exception as e:
        print(f"❌ Failed to clean ingest directory: {e}")
        return False
    
    return True


def main():
    """Main orchestrator function."""
    parser = argparse.ArgumentParser(
        description="Process Bear markdown exports into Quarto blog posts"
    )
    parser.add_argument(
        "--promote", 
        action="store_true",
        help="Automatically promote validated content to posts/ directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true", 
        help="Show what would be promoted without actually doing it"
    )
    parser.add_argument(
        "--keep-staging",
        action="store_true",
        help="Keep processed content in staging directory after promotion (default: clean it)"
    )
    
    args = parser.parse_args()
    
    print("🚀 Quarto Blog Processing Pipeline")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check prerequisites
    if not check_prerequisites():
        print(f"\n❌ Prerequisites check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Clear staging directory but preserve README.md
    if not clear_staging_directory():
        print(f"\n❌ Failed to clear staging directory.")
        sys.exit(1)
    
    # Define the processing pipeline
    pipeline_steps = [
        ("01-sanitize-filenames.py", "Sanitize filenames and create post directories"),
        ("02-standardize-yaml.py", "Standardize YAML frontmatter"),
        ("03-convert-highlights.py", "Convert Bear highlights to HTML"),
        ("04-fix-image-paths.py", "Fix image paths and organization"),
        ("05-validate-content.py", "Validate processed content")
    ]
    
    # Execute pipeline
    print(f"\n🔄 Starting processing pipeline...")
    
    for script_name, description in pipeline_steps:
        if not run_script(script_name, description):
            print(f"\n❌ Pipeline failed at: {description}")
            print(f"Check the error messages above and fix the issues.")
            sys.exit(1)
    
    print(f"\n🎉 Processing pipeline completed successfully!")
    
    # Handle promotion
    if args.promote or args.dry_run:
        print(f"\n📦 Content Promotion")
        print("=" * 30)
        
        if not promote_to_posts(dry_run=args.dry_run):
            print(f"\n❌ Content promotion failed.")
            sys.exit(1)
        
        if not args.dry_run and args.promote:
            # After successful promotion, clean staging directory but keep README.md
            if args.keep_staging:
                print(f"\n📂 Keeping processed-staging/ with processed content for review")
            else:
                cleanup_staging(keep_staging=False)
            
        # Clean up ingest directory after successful promotion (regardless of --keep-staging)
        if not args.dry_run and args.promote:
            print(f"\n🧹 Cleaning up source directory")
            print("=" * 35)
            if not cleanup_ingest_directory():
                print(f"\n⚠️  Warning: Failed to clean ingest directory, but promotion was successful")
            else:
                print(f"✅ Ingest directory cleaned - ready for next batch")
    else:
        print(f"\n📋 Manual Review Required")
        print("=" * 30)
        print(f"Content has been processed and validated in: processed-staging/")
        print(f"")
        print(f"Next steps:")
        print(f"  1. Review the processed content")
        print(f"  2. Run: python scripts/06-process-markdown-import.py --promote")
        print(f"  3. Or manually copy post directories to posts/")
    
    print(f"\n✅ Process completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()