from typing import Any


def format_stage_comment(title: str, lines: list[str]) -> str:
    body = [f"## {title}", ""]
    body.extend(lines)
    return "\n".join(body)


def repo_created_comment(repo_url: str, repo_name: str, testops_project_url: str) -> str:
    return format_stage_comment(
        "🚀 Репозиторий автотестов создан",
        [
            f"**GitHub:** [{repo_name}]({repo_url})",
            f"**TestOps проект:** {testops_project_url}",
            "",
            "Шаблон: Selenide + JUnit 5 + Allure 3, прогон в Selenoid.",
        ],
    )


def test_pushed_comment(repo_url: str, class_name: str, test_case_url: str) -> str:
    return format_stage_comment(
        "📝 Автотест сгенерирован",
        [
            f"**Класс:** `{class_name}`",
            f"**Репозиторий:** {repo_url}",
            f"**Тест-кейс:** {test_case_url}",
        ],
    )


def ci_started_comment(run_url: str, report_url_hint: str) -> str:
    return format_stage_comment(
        "⚙️ Запущен GitHub Actions",
        [
            f"**Workflow:** [открыть прогон]({run_url})",
            f"**Allure 3 отчёт** появится здесь после завершения: {report_url_hint}",
        ],
    )


def ci_finished_comment(
    run_url: str,
    report_url: str | None,
    conclusion: str | None,
    video_attached: bool,
) -> str:
    status = conclusion or "unknown"
    lines = [
        f"**Статус прогона:** `{status}`",
        f"**GitHub Actions:** [run]({run_url})",
    ]
    if report_url:
        lines.append(f"**Allure 3 отчёт:** [открыть]({report_url})")
    if video_attached:
        lines.append("**Видео:** прикреплено к тест-кейсу как артефакт.")
    else:
        lines.append("**Видео:** не найдено в артефактах прогона.")
    return format_stage_comment("✅ Прогон завершён", lines)
