package tests;

import annotations.Layer;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.parallel.Execution;
import org.junit.jupiter.api.parallel.ExecutionMode;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import pages.HeaderPreviewPage;

import static helpers.LayoutCss.WIDE_LAYOUT_MIN_VIEWPORT_PX;
import static helpers.ViewportHelper.setViewport;

@Layer("integration")
@Epic("Template Header")
@Feature("Header layout")
@DisplayName("Header layout")
@Execution(ExecutionMode.SAME_THREAD)
class HeaderLayoutTests extends TestBase {

    private static final int VIEWPORT_HEIGHT = 900;

    private final HeaderPreviewPage headerPreview = new HeaderPreviewPage();

    @ParameterizedTest(name = "viewport {0}px")
    @ValueSource(ints = {390, 768, 1280})
    @Tag("layout")
    @DisplayName("Header inner keeps uniform 16px gaps")
    void headerInnerUniformGaps(int viewportWidth) {
        setViewport(viewportWidth, VIEWPORT_HEIGHT);
        headerPreview.openPage()
                .shouldHaveUniformInnerGap(viewportWidth);
    }

    @ParameterizedTest(name = "viewport {0}px")
    @ValueSource(ints = {390, 768, 1280})
    @Tag("layout")
    @DisplayName("Header shell height stays near 56px")
    void headerHeightNearCanonical(int viewportWidth) {
        setViewport(viewportWidth, VIEWPORT_HEIGHT);
        headerPreview.openPage()
                .shouldHaveCanonicalHeight(viewportWidth);
    }

    @ParameterizedTest(name = "viewport {0}px")
    @ValueSource(ints = {390, 768})
    @Tag("layout")
    @DisplayName("Nav and search hidden at mobile breakpoint")
    void navAndSearchHiddenOnMobile(int viewportWidth) {
        setViewport(viewportWidth, VIEWPORT_HEIGHT);
        headerPreview.openPage()
                .shouldHideNavAndSearch(viewportWidth);
    }

    @ParameterizedTest(name = "viewport {0}px")
    @ValueSource(ints = {WIDE_LAYOUT_MIN_VIEWPORT_PX, 1280})
    @Tag("layout")
    @DisplayName("Nav and search visible above mobile breakpoint")
    void navAndSearchVisibleOnDesktop(int viewportWidth) {
        setViewport(viewportWidth, VIEWPORT_HEIGHT);
        headerPreview.openPage()
                .shouldShowNavAndSearch(viewportWidth);
    }
}
