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
@Suite("Login")
@SubSuite("baseline")
@Execution(ExecutionMode.SAME_THREAD)
class LoginBaselineTests extends TestBase {

    private static final int VIEWPORT_HEIGHT = 900;

    @ParameterizedTest(name = "viewport {0}px")
    @ValueSource(ints = {390, 768, 1280})
    @Tag("visual")
    @Feature("Login screenshot")
    @DisplayName("Login form matches baseline")
    void loginFormMatchesBaseline(int viewportWidth) {
        setViewport(viewportWidth, VIEWPORT_HEIGHT);
        loginPage.openPage();
        ScreenshotBaseline.captureAndCompare(
                loginPage.loginForm(),
                "login",
                viewportWidth,
                "login-" + viewportWidth);
    }
}
