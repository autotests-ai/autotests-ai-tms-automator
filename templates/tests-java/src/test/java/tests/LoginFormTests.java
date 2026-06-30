package tests;

import annotations.Layer;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Layer("integration")
@Epic("One Page Form")
@Feature("Login form")
@DisplayName("Login form mount")
class LoginFormTests extends TestBase {

    @Test
    @Tag("mount")
    @DisplayName("Login form fields and submit are visible")
    void loginFormIsMounted() {
        loginPage.openPage()
                .shouldShowLoginForm()
                .shouldHaveFormTitle("Login Form");
    }
}
