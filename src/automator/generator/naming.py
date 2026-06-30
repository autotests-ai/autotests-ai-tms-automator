from __future__ import annotations

import re
from dataclasses import dataclass

CYRILLIC_TO_LATIN = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
)

RU_EN_WORDS = {
    "успеш": "successful",
    "неуспеш": "unsuccessful",
    "авториза": "authorization",
    "логин": "login",
    "парол": "password",
    "невер": "wrong",
    "неправильн": "wrong",
    "валид": "valid",
    "учетн": "credentials",
    "данн": "data",
    "привет": "welcome",
    "сообщен": "message",
    "ошибк": "error",
    "регистра": "registration",
    "форма": "form",
    "отправк": "submit",
    "кнопк": "button",
    "поле": "field",
    "страниц": "page",
    "открыт": "open",
    "провер": "verify",
    "текст": "text",
    "клон": "clone",
    "профил": "profile",
    "кабинет": "account",
    "корзин": "cart",
    "заказ": "order",
    "оформлен": "checkout",
    "контакт": "contact",
    "обратн": "feedback",
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "by",
    "case",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "а",
    "в",
    "для",
    "до",
    "если",
    "из",
    "или",
    "и",
    "как",
    "кейс",
    "на",
    "не",
    "но",
    "от",
    "по",
    "при",
    "проходит",
    "с",
    "со",
    "тест",
    "что",
}

METHOD_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"успеш.*авториза|successful.*auth"), "successfulAuthorization"),
    (re.compile(r"авториза.*(?:не проходит|не проход).*парол|auth.*wrong.*password"), "wrongPasswordAuthorization"),
    (re.compile(r"логин.*(?:невер|неправил)|wrong.*password.*login|неуспеш.*логин.*парол"), "wrongPasswordLogin"),
    (re.compile(r"успеш.*логин|successful.*login"), "successfulLogin"),
    (re.compile(r"неуспеш.*логин|unsuccessful.*login|failed.*login"), "unsuccessfulLogin"),
    (re.compile(r"успеш.*регистра|successful.*regist"), "successfulRegistration"),
    (re.compile(r"регистра.*(?:ошиб|неусп|duplicate|существ)", re.I), "failedRegistration"),
]

FEATURE_RULES: list[tuple[re.Pattern[str], str, str, str]] = [
    (
        re.compile(r"login\.html|авториза|логин|sign[\s-]?in|log[\s-]?in|вход в систему", re.I),
        "Авторизация",
        "LoginTests",
        "LOGIN_PAGE",
    ),
    (
        re.compile(r"registration\.html|регистра|sign[\s-]?up|register", re.I),
        "Регистрация",
        "RegistrationTests",
        "REGISTRATION_PAGE",
    ),
    (
        re.compile(r"profile|профил|личн.*кабинет|account", re.I),
        "Профиль",
        "ProfileTests",
        "PROFILE_PAGE",
    ),
    (
        re.compile(r"checkout|оформлен.*заказ|корзин|cart", re.I),
        "Оформление заказа",
        "CheckoutTests",
        "CHECKOUT_PAGE",
    ),
    (
        re.compile(r"contact|обратн.*связ|feedback", re.I),
        "Обратная связь",
        "ContactFormTests",
        "CONTACT_FORM_PAGE",
    ),
]

CLASS_EQUIVALENTS: dict[str, frozenset[str]] = {
    "LoginTests": frozenset({"LoginTests", "SignInTests", "AuthorizationTests", "AuthTests", "LogInTests"}),
    "RegistrationTests": frozenset({"RegistrationTests", "SignUpTests", "RegisterTests"}),
    "ProfileTests": frozenset({"ProfileTests", "AccountTests", "UserProfileTests"}),
    "CheckoutTests": frozenset({"CheckoutTests", "OrderTests", "CartTests"}),
    "ContactFormTests": frozenset({"ContactFormTests", "FeedbackTests", "ContactTests"}),
}


@dataclass(frozen=True)
class TestNames:
    class_name: str
    method_name: str
    feature: str
    epic: str
    class_display_name: str
    page_constant: str

    @property
    def file_name(self) -> str:
        return f"{self.class_name}.java"

    @property
    def qualified_class_name(self) -> str:
        return f"tests.{self.class_name}"

    @property
    def qualified_test_name(self) -> str:
        return f"{self.qualified_class_name}.{self.method_name}"

    @property
    def relative_path(self) -> str:
        return f"src/test/java/tests/{self.file_name}"

    def with_method_suffix(self, test_case_id: int) -> TestNames:
        suffix = str(test_case_id)
        return TestNames(
            class_name=self.class_name,
            method_name=f"{self.method_name}{suffix}",
            feature=self.feature,
            epic=self.epic,
            class_display_name=self.class_display_name,
            page_constant=self.page_constant,
        )


def equivalent_class_names(class_name: str) -> frozenset[str]:
    for canonical, aliases in CLASS_EQUIVALENTS.items():
        if class_name in aliases:
            return aliases
    return frozenset({class_name})


def canonical_class_name(class_name: str) -> str:
    for canonical, aliases in CLASS_EQUIVALENTS.items():
        if class_name in aliases:
            return canonical
    return class_name


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower().replace("ё", "е"))


def _map_token(token: str) -> str | None:
    if token in STOP_WORDS or len(token) < 3:
        return None
    for prefix, english in RU_EN_WORDS.items():
        if token.startswith(prefix):
            return english
    if token.isascii() and token.isalpha():
        return token
    return None


def _tokens_to_base(tokens: list[str]) -> str:
    if not tokens:
        return ""
    head, *tail = tokens
    return head + "".join(word.capitalize() for word in tail)


def _match_method_pattern(text: str) -> str | None:
    for pattern, base in METHOD_PATTERNS:
        if pattern.search(text):
            return base
    return None


def _tokenize(text: str) -> list[str]:
    normalized = text.translate(CYRILLIC_TO_LATIN)
    raw_tokens = re.findall(r"[a-z0-9]+", normalized)
    mapped: list[str] = []
    for token in raw_tokens:
        english = _map_token(token)
        if english and english not in mapped:
            mapped.append(english)
        elif token.isascii() and token.isalpha() and token not in STOP_WORDS and len(token) > 2:
            if token not in mapped:
                mapped.append(token)
    return mapped


def _infer_feature_rule(name: str, step_bodies: list[str]) -> tuple[str, str, str, str] | None:
    combined = _normalize_text(name) + " " + _normalize_text(" ".join(step_bodies))
    for pattern, feature, class_name, page_constant in FEATURE_RULES:
        if pattern.search(combined):
            return feature, class_name, page_constant, feature
    return None


def _feature_class_name(feature_label: str) -> str:
    tokens = _tokenize(_normalize_text(feature_label))
    base = _tokens_to_base(tokens) or "Feature"
    if not base.endswith("Tests"):
        base = f"{base}Tests"
    return base[0].upper() + base[1:] if base else "FeatureTests"


def infer_feature_context(name: str, step_bodies: list[str]) -> tuple[str, str, str, str]:
    matched = _infer_feature_rule(name, step_bodies)
    if matched:
        feature, class_name, page_constant, class_display_name = matched
        return feature, class_name, page_constant, class_display_name

    tokens = _tokenize(_normalize_text(name))
    feature = name.strip() or "Функциональность"
    if tokens:
        feature = tokens[0].capitalize()
        if tokens[0] == "authorization":
            feature = "Авторизация"
        elif tokens[0] == "registration":
            feature = "Регистрация"
        elif tokens[0] == "profile":
            feature = "Профиль"

    class_name = _feature_class_name(feature)
    page_constant = "TARGET_PAGE"
    return feature, class_name, page_constant, feature


def build_method_name(name: str, test_case_id: int) -> str:
    raw_lower = _normalize_text(name)
    base = _match_method_pattern(raw_lower)
    if base is None:
        normalized = raw_lower.translate(CYRILLIC_TO_LATIN)
        base = _tokens_to_base(_tokenize(normalized))
    if not base:
        base = f"autotest{test_case_id}"

    method_name = base[0].lower() + base[1:]
    if not method_name.endswith("Test"):
        method_name = f"{method_name}Test"
    return method_name


def build_test_names(name: str, step_bodies: list[str], test_case_id: int) -> TestNames:
    feature, class_name, page_constant, class_display_name = infer_feature_context(name, step_bodies)
    method_name = build_method_name(name, test_case_id)
    return TestNames(
        class_name=class_name,
        method_name=method_name,
        feature=feature,
        epic="Одностраничная форма",
        class_display_name=class_display_name,
        page_constant=page_constant,
    )
