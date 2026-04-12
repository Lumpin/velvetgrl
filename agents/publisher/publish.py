import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from agents.config import QUEUE_DIR, BLOG_DIR, IMAGES_DIR
from agents.db import get_connection


def publish_post(slug: str) -> bool:
    """Move an approved post from queue to website and deploy."""
    draft_path = QUEUE_DIR / "drafts" / f"{slug}.md"
    if not draft_path.exists():
        return False

    # Move to blog content directory
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    target_path = BLOG_DIR / f"{slug}.md"
    shutil.copy2(draft_path, target_path)

    # Update DB
    conn = get_connection()
    conn.execute(
        "UPDATE posts SET status = 'published', published_at = ? WHERE slug = ?",
        (datetime.now().isoformat(), slug)
    )
    conn.commit()
    conn.close()

    # Git commit the post + its images
    _git_commit(slug, target_path)

    # Clean up draft
    draft_path.unlink()

    return True


def _git_commit(slug: str, file_path: Path) -> None:
    """Commit the new post and its images."""
    repo_root = file_path.parents[4]
    images_dir = IMAGES_DIR / slug
    try:
        subprocess.run(["git", "add", str(file_path)], cwd=repo_root, check=True)
        if images_dir.exists():
            subprocess.run(["git", "add", str(images_dir)], cwd=repo_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"publish: {slug}"],
            cwd=repo_root, check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e}")


def _git_push(repo_root: Path) -> None:
    """Push to GitHub to trigger deploy."""
    try:
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=repo_root, check=True
        )
        print("Pushed to GitHub — deploy triggered.")
    except subprocess.CalledProcessError as e:
        print(f"Git push failed: {e}")


def publish_all_approved() -> list[str]:
    """Publish all posts with 'approved' status, then push to GitHub."""
    conn = get_connection()
    approved = conn.execute("SELECT slug FROM posts WHERE status = 'approved'").fetchall()
    conn.close()

    published = []
    for row in approved:
        if publish_post(row["slug"]):
            published.append(row["slug"])

    # Push website subtree to GitHub after all posts are committed
    if published:
        repo_root = BLOG_DIR.parents[3]
        _git_push(repo_root)

    return published
