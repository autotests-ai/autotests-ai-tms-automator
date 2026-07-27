"""Load machine-readable generator policy from vendored RAG."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_POLICY_REL = Path("config") / "gen-python-policy.json"
_POLICY_CHUNK_ID = "gen-python-policy"


@dataclass(frozen=True)
class GeneratorPolicy:
    layer: str
    default_epic: str
    negative_keywords: tuple[str, ...]
    page_defaults: dict[str, str]
    default_page_path: str
    locators: dict[str, str]
    credentials: dict[str, str]
    i18n: dict[str, str]
    assert_selectors: dict[str, str]
    assert_keywords: dict[str, tuple[str, ...]]

    @classmethod
    def defaults(cls) -> GeneratorPolicy:
        return cls.from_dict(
            {
                "layer": "e2e",
                "default_epic": "Одностраничная форма",
                "negative_keywords": ["неусп", "невер", "wrong", "fail"],
                "page_defaults": {"login.html": "login.html?ru"},
                "default_page_path": "login.html?ru",
                "locators": {
                    "login_input": "login-input",
                    "password_input": "password-input",
                    "submit_button": "submit-button",
                    "welcome_message": "welcome-message",
                    "error_message": "error-message",
                },
                "credentials": {
                    "valid_user": "user1",
                    "valid_password": "password1",
                    "wrong_password": "wrongpassword",
                },
                "i18n": {
                    "Wrong login or password": "Неверный логин или пароль",
                    "Welcome, user1!": "Добро пожаловать, user1!",
                },
                "assert_selectors": {
                    "welcome": "welcome_message",
                    "error": "error_message",
                },
                "assert_keywords": {
                    "welcome": ["привет", "welcome", "logged-in", "logged in", "success-panel"],
                    "error": [],
                },
            }
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GeneratorPolicy:
        locators = {str(k): str(v) for k, v in (data.get("locators") or {}).items()}
        credentials = {str(k): str(v) for k, v in (data.get("credentials") or {}).items()}
        i18n = {str(k): str(v) for k, v in (data.get("i18n") or {}).items()}
        page_defaults = {str(k): str(v) for k, v in (data.get("page_defaults") or {}).items()}
        assert_selectors = {
            str(k): str(v) for k, v in (data.get("assert_selectors") or {}).items()
        }
        raw_keywords = data.get("assert_keywords") or {}
        assert_keywords = {
            str(key): tuple(str(word) for word in (words or []))
            for key, words in raw_keywords.items()
        }
        negative = tuple(str(word) for word in (data.get("negative_keywords") or []))
        return cls(
            layer=str(data.get("layer", "e2e")),
            default_epic=str(data.get("default_epic", "Одностраничная форма")),
            negative_keywords=negative,
            page_defaults=page_defaults,
            default_page_path=str(data.get("default_page_path", "login.html?ru")),
            locators=locators,
            credentials=credentials,
            i18n=i18n,
            assert_selectors=assert_selectors,
            assert_keywords=assert_keywords,
        )

    @classmethod
    def from_json(cls, raw: str) -> GeneratorPolicy:
        return cls.from_dict(json.loads(raw))

    def locator(self, key: str) -> str:
        testid = self.locators.get(key)
        if not testid:
            raise KeyError(f"locator key missing in gen-python-policy: {key}")
        return testid

    def credential(self, key: str) -> str:
        value = self.credentials.get(key)
        if value is None:
            raise KeyError(f"credential key missing in gen-python-policy: {key}")
        return value

    def normalize_page_path(self, path: str) -> str:
        base = path.split("?", 1)[0]
        return self.page_defaults.get(base, path)

    def infer_tag(self, case_name: str) -> str:
        lowered = case_name.lower()
        if any(word in lowered for word in self.negative_keywords):
            return "negative"
        return "positive"

    def translate_expected(self, text: str, page_path: str) -> str:
        if "?ru" not in page_path:
            return text
        return self.i18n.get(text, text)

    def resolve_assert_testid(self, step_body: str) -> str:
        lowered = step_body.lower()
        for role, keywords in self.assert_keywords.items():
            if any(keyword in lowered for keyword in keywords):
                locator_key = self.assert_selectors.get(role, role)
                return self.locator(locator_key)
        return self.locator(self.assert_selectors.get("error", "error_message"))


def policy_path(rag_dir: Path) -> Path:
    return rag_dir / _POLICY_REL


def load_generator_policy(rag_dir: Path | None) -> GeneratorPolicy:
    """Load policy JSON from vendored RAG; fall back to built-in defaults."""
    if rag_dir is None:
        logger.warning("RAG dir not set; using built-in generator policy defaults")
        return GeneratorPolicy.defaults()

    path = policy_path(rag_dir)
    if not path.is_file():
        logger.warning("Missing %s; using built-in generator policy defaults", path)
        return GeneratorPolicy.defaults()

    try:
        return GeneratorPolicy.from_json(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.error("Invalid generator policy at %s: %s", path, exc)
        return GeneratorPolicy.defaults()


def generator_policy_chunk_id() -> str:
    return _POLICY_CHUNK_ID
