package pages.components;

import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import java.util.List;

import static com.codeborne.selenide.Condition.match;
import static com.codeborne.selenide.Condition.text;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.executeJavaScript;
import static helpers.LayoutCss.RESPONSIVE_BREAKPOINT_PX;

import helpers.HeaderLayout;

public class HeaderComponent {

    private final SelenideElement root = $("[data-testid='header']");
    private final SelenideElement brandLink = $("[data-testid='header-brand-link']");
    private final SelenideElement langToggle = $("[data-testid='header-lang-toggle']");
    private final SelenideElement langLabel = $("[data-testid='header-lang-label']");
    private final SelenideElement themeToggle = $("[data-testid='header-theme-toggle']");
    private final SelenideElement githubLink = $("[data-testid='header-github']");
    private final SelenideElement githubPagesLink = $("[data-testid='header-github-pages']");

    public SelenideElement root() {
        return root;
    }

    @Step("Verify external header links have href")
    public HeaderComponent shouldHaveExternalLinkHrefs() {
        for (var link : List.of(brandLink, githubLink, githubPagesLink)) {
            shouldHaveNonBlankHref(link);
        }
        return this;
    }

    @Step("Toggle theme")
    public HeaderComponent toggleTheme() {
        themeToggle.click();
        return this;
    }

    @Step("Verify theme class changes after toggle")
    public HeaderComponent shouldChangeThemeOnToggle() {
        var lightBefore = isThemeLight();
        toggleTheme();
        $("html").should(match("theme-light toggled", el -> isThemeLight() != lightBefore));
        var lightAfter = isThemeLight();
        toggleTheme();
        $("html").should(match("theme-light restored", el -> isThemeLight() != lightAfter));
        return this;
    }

    @Step("Toggle language")
    public HeaderComponent toggleLang() {
        langToggle.click();
        return this;
    }

    @Step("Verify lang label updates after toggle")
    public HeaderComponent shouldUpdateLangLabelOnToggle() {
        langLabel.shouldHave(text("EN"));
        toggleLang();
        langLabel.shouldHave(text("RU"));
        toggleLang();
        langLabel.shouldHave(text("EN"));
        return this;
    }

    @Step("Verify header inner gap is 16px at {viewportWidth}px viewport")
    public HeaderComponent shouldHaveUniformInnerGap(int viewportWidth) {
        HeaderLayout.assertCssGapNearCanonical(viewportWidth);
        if (viewportWidth > RESPONSIVE_BREAKPOINT_PX) {
            HeaderLayout.assertUniformGaps(HeaderLayout.readInnerGaps(), viewportWidth);
        }
        return this;
    }

    @Step("Verify header height is ~56px at {viewportWidth}px viewport")
    public HeaderComponent shouldHaveCanonicalHeight(int viewportWidth) {
        HeaderLayout.assertHeaderHeightNearCanonical(viewportWidth);
        return this;
    }

    @Step("Verify nav and search are hidden at {viewportWidth}px viewport")
    public HeaderComponent shouldHideNavAndSearch(int viewportWidth) {
        HeaderLayout.assertNavAndSearchVisible(false, viewportWidth);
        return this;
    }

    @Step("Verify nav and search are visible at {viewportWidth}px viewport")
    public HeaderComponent shouldShowNavAndSearch(int viewportWidth) {
        HeaderLayout.assertNavAndSearchVisible(true, viewportWidth);
        return this;
    }

    private void shouldHaveNonBlankHref(SelenideElement link) {
        link.should(match("non-blank href", el -> {
            var href = el.getAttribute("href");
            return href != null && !href.isBlank();
        }));
    }

    private boolean isThemeLight() {
        return Boolean.TRUE.equals(executeJavaScript(
                "return document.documentElement.classList.contains('theme-light');"));
    }
}
