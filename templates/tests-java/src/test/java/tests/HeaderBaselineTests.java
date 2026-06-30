package tests;

import annotations.Layer;
import annotations.SubSuite;
import annotations.Suite;
import helpers.ScreenshotBaseline;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.parallel.Execution;
import org.junit.jupiter.api.parallel.ExecutionMode;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import pages.HeaderPreviewPage;

import static helpers.ViewportHelper.setViewport;

@Layer("e2e")
@Epic("Template Header")
@Feature("Header")
@Suite("Header")
@SubSuite("baseline")
@Execution(ExecutionMode.SAME_THREAD)
class HeaderBaselineTests extends TestBase {

    private static final int VIEWPORT_HEIGHT = 900;

    private final HeaderPreviewPage headerPreview = new HeaderPreviewPage();

    @ParameterizedTest(name = "viewport {0}px")
    @ValueSource(ints = {390, 768, 1280})
    @Tag("visual")
    @Feature("Header screenshot")
    @DisplayName("Header matches baseline")
    void headerMatchesBaseline(int viewportWidth) {
        setViewport(viewportWidth, VIEWPORT_HEIGHT);
        var header = headerPreview.openPage();
        ScreenshotBaseline.captureAndCompare(
                header.root(),
                "header",
                viewportWidth,
                "header-" + viewportWidth);
    }
}
