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

import static helpers.ViewportHelper.setViewport;

@Layer("e2e")
@Epic("One Page Form")
@Feature("Login")
@Suite("Logged-in")
@SubSuite("baseline")
@Execution(ExecutionMode.SAME_THREAD)
class LoggedInBaselineTests extends TestBase {

    private static final int VIEWPORT_HEIGHT = 900;

    @ParameterizedTest(name = "viewport {0}px")
    @ValueSource(ints = {390, 768, 1280})
    @Tag("visual")
    @Feature("Logged-in screenshot")
    @DisplayName("Welcome panel matches baseline")
    void welcomePanelMatchesBaseline(int viewportWidth) {
        setViewport(viewportWidth, VIEWPORT_HEIGHT);
        loginPage.openPage()
                .fillAndSubmitForm("user1", "password1")
                .shouldHaveWelcomeMessage("Welcome, user1!");
        ScreenshotBaseline.captureAndCompare(
                loggedInPage.successPanel(),
                "logged-in",
                viewportWidth,
                "logged-in-" + viewportWidth);
    }
}
