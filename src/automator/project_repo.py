import logging
from pathlib import Path
from typing import Any

from automator.client.testops import AllureTestOpsClient
from automator.config import Settings
from automator.errors import AutomationError, RepositoryNotFoundError
from automator.generator.java_tests import (
    append_method,
    ensure_static_imports,
    has_allure_id,
    load_existing_test_classes,
    normalize_class_file,
    resolve_method_name,
    resolve_target_class,
)
from automator.generator.naming import TestNames
from automator.generator.test_java import GeneratedTest, build_test_class_file
from automator.github.client import GitHubClient
from automator.rag.policy import load_generator_policy
from automator.github.naming import build_repo_name
from automator.storage.db import StateStore

logger = logging.getLogger(__name__)


class ProjectRepositoryService:
    def __init__(
        self,
        settings: Settings,
        store: StateStore,
        testops: AllureTestOpsClient,
        github: GitHubClient,
        template_dir: Path,
        projects_dir: Path,
        rag_canon_dir: Path,
    ) -> None:
        self._settings = settings
        self._store = store
        self._testops = testops
        self._github = github
        self._template_dir = template_dir
        self._projects_dir = projects_dir
        self._rag_canon_dir = rag_canon_dir

    def project_workdir(self, repo_name: str) -> Path:
        return self._projects_dir / repo_name

    def tests_dir(self, workdir: Path) -> Path:
        return workdir / "src/test/java/tests"

    def ensure_local_project(self, repo_name: str) -> Path:
        workdir = self.project_workdir(repo_name)
        if workdir.exists():
            return workdir
        if self._github.repo_exists(repo_name):
            self._github.clone_repo(repo_name, workdir)
        return workdir

    def testops_project_url(self, project_id: int) -> str:
        return f"{self._settings.allure_endpoint.rstrip('/')}/project/{project_id}/test-cases"

    def testops_test_case_url(self, project_id: int, test_case_id: int) -> str:
        return f"{self._settings.allure_endpoint.rstrip('/')}/project/{project_id}/test-cases/{test_case_id}"

    def ensure_repository(self, project_id: int) -> dict[str, Any]:
        existing = self._store.get_project_repo(project_id)
        if existing and self._github.repo_exists(str(existing["repo_name"])):
            repo_name = str(existing["repo_name"])
            self.ensure_local_project(repo_name)
            self._github.ensure_github_pages(repo_name)
            return {**existing, "created": False}

        if existing:
            project_name = str(existing["project_name"])
            repo_name = str(existing["repo_name"])
        else:
            project = self._testops.get_project(project_id)
            project_name = str(project.get("name") or f"project-{project_id}")
            repo_name = build_repo_name(project_name, project_id)

        if self._github.repo_exists(repo_name):
            self.ensure_local_project(repo_name)
            self._github.ensure_github_pages(repo_name)
            repo_url = f"https://github.com/{self._settings.github_org}/{repo_name}"
            record = {
                "project_id": project_id,
                "project_name": project_name,
                "repo_name": repo_name,
                "repo_url": repo_url,
            }
            self._store.save_project_repo(**record)
            return {**record, "created": False}

        description = f"UI autotests for Allure TestOps project {project_id} ({project_name})"
        workdir = self.project_workdir(repo_name)

        repo_url = self._github.create_repo_from_template(
            repo_name=repo_name,
            template_dir=self._template_dir,
            workdir=workdir,
            allure_project_id=project_id,
            allure_endpoint=self._settings.allure_endpoint,
            allure_token=self._settings.allure_api_token,
            description=description,
            rag_source=self._rag_canon_dir,
        )
        record = {
            "project_id": project_id,
            "project_name": project_name,
            "repo_name": repo_name,
            "repo_url": repo_url,
        }
        self._store.save_project_repo(**record)
        return {**record, "created": True}

    def _materialize_test(
        self,
        workdir: Path,
        generated: GeneratedTest,
        test_case_id: int,
    ) -> tuple[str, str, TestNames, list[str]]:
        existing_classes = load_existing_test_classes(self.tests_dir(workdir))
        existing_match, canonical_class_name = resolve_target_class(existing_classes, generated.names)

        if existing_match and has_allure_id(existing_match, test_case_id):
            raise AutomationError(
                f"TestOps #{test_case_id} already automated in {existing_match.class_name}"
            )

        names = resolve_method_name(existing_match, generated.names, test_case_id)
        remove_paths: list[str] = []

        if existing_match:
            page_constant = existing_match.page_constant or names.page_constant
            method_source = generated.method_source
            if names.method_name != generated.names.method_name:
                method_source = method_source.replace(
                    f"void {generated.names.method_name}()",
                    f"void {names.method_name}()",
                )
            if page_constant != names.page_constant:
                method_source = method_source.replace(
                    f"open({names.page_constant})",
                    f"open({page_constant})",
                )

            content = normalize_class_file(existing_match.content, canonical_class_name)
            content = append_method(content, method_source)
            content = ensure_static_imports(content, method_source)
            relative_path = f"src/test/java/tests/{canonical_class_name}.java"
            old_relative = existing_match.file_path.relative_to(workdir).as_posix()
            if old_relative != relative_path:
                remove_paths.append(old_relative)
            return relative_path, content, names, remove_paths

        content = build_test_class_file(
            names=names,
            test_case_id=test_case_id,
            test_case_name=generated.test_case_name,
            step_bodies=generated.step_bodies,
            page_path=generated.page_path,
            tag=generated.tag,
            policy=load_generator_policy(self._rag_canon_dir),
        )
        return names.relative_path, content, names, remove_paths

    def push_generated_test(
        self,
        project_id: int,
        repo_name: str,
        test_case_id: int,
        generated: GeneratedTest,
    ) -> tuple[str, dict[str, Any] | None]:
        message = (
            f"Add {generated.names.method_name} to {generated.names.class_name} "
            f"for TestOps #{test_case_id}"
        )

        try:
            workdir = self.ensure_local_project(repo_name)
            return self._push_materialized(workdir, repo_name, generated, test_case_id, message), None
        except RepositoryNotFoundError:
            logger.info(
                "GitHub repo %s not found, creating new repository for project %s",
                repo_name,
                project_id,
            )
            repo_info = self.ensure_repository(project_id)
            workdir = self.ensure_local_project(str(repo_info["repo_name"]))
            qualified = self._push_materialized(
                workdir,
                str(repo_info["repo_name"]),
                generated,
                test_case_id,
                message,
            )
            return qualified, repo_info if repo_info.get("created") else None

    def _push_materialized(
        self,
        workdir: Path,
        repo_name: str,
        generated: GeneratedTest,
        test_case_id: int,
        message: str,
    ) -> str:
        relative_path, content, names, remove_paths = self._materialize_test(
            workdir, generated, test_case_id
        )
        self._github.push_test_file(
            repo_name=repo_name,
            workdir=workdir,
            relative_path=relative_path,
            content=content,
            message=message,
            remove_paths=remove_paths,
        )
        return names.qualified_test_name
