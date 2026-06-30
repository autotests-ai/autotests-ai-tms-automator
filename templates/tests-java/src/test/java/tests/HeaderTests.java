package tests;

import annotations.Layer;
import annotations.Manual;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import pages.HeaderPreviewPage;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.parallel.Execution;
import org.junit.jupiter.api.parallel.ExecutionMode;

import static helpers.ViewportHelper.setViewport;
import static io.qameta.allure.Allure.step;

@Layer("e2e")
@Epic("Template Header")
@Feature("Header")
@DisplayName("Header")
@Execution(ExecutionMode.SAME_THREAD)
class HeaderTests extends TestBase {

    private static final int VIEWPORT_HEIGHT = 900;

    private final HeaderPreviewPage headerPreview = new HeaderPreviewPage();

    @Test
    @Tag("smoke")
    @Feature("Header behavior")
    @DisplayName("External header links have href attribute")
    void externalLinksHaveHref() {
        setViewport(1280, VIEWPORT_HEIGHT);
        headerPreview.openPage()
                .shouldHaveExternalLinkHrefs();
    }

    @Test
    @Tag("smoke")
    @Feature("Header behavior")
    @DisplayName("Theme toggle switches theme-light class")
    void themeToggleChangesTheme() {
        setViewport(1280, VIEWPORT_HEIGHT);
        headerPreview.openPage()
                .shouldChangeThemeOnToggle();
    }

    @Test
    @Tag("smoke")
    @Feature("Header behavior")
    @DisplayName("Lang toggle updates lang label")
    void langToggleUpdatesLabel() {
        setViewport(1280, VIEWPORT_HEIGHT);
        headerPreview.openPage()
                .shouldUpdateLangLabelOnToggle();
    }

    @Test
    @Manual
    @Tag("manual")
    @Layer("manual")
    @Feature("Header behavior")
    @DisplayName("Lang and theme toggles work when nav is hidden on mobile")
    void langAndThemeTogglesWorkWhenNavHiddenOnMobile() {
        step("Open /header.html at 390px viewport");
        step("Verify nav and search are hidden");
        step("Tap lang toggle — label switches EN ↔ RU");
        step("Tap theme toggle — html.theme-light toggles, sun/moon icon updates");
        step("Repeat at 1280px — nav visible, toggles still work");
    }
}
