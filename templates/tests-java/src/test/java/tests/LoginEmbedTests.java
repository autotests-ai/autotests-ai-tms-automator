package tests;

import annotations.Layer;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Layer("integration")
@Epic("One Page Form")
@Feature("Header embed")
@DisplayName("Login header embed")
class LoginEmbedTests extends TestBase {

    @Test
    @Tag("mount")
    @DisplayName("Embedded header is visible on login page")
    void embeddedHeaderIsVisible() {
        loginPage.openPage()
                .shouldShowEmbeddedHeader();
    }
}
