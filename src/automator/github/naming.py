import re


def build_repo_name(project_name: str, project_id: int) -> str:
    """project_with_qa_guru_automator + 5265 → project_with_qa_guru_automator-5265"""
    slug = project_name.strip().replace(" ", "-")
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return f"{slug}-{project_id}"
