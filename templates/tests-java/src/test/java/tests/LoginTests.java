package tests;

import annotations.Layer;
import annotations.Manual;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import static io.qameta.allure.Allure.step;

@Layer("e2e")
@Epic("One Page Form")
@Feature("Login")
@DisplayName("Login")
class LoginTests extends TestBase {

    @Test
    @Tag("smoke")
    @Tag("positive")
    @DisplayName("User is logged in with valid credentials")
    void shouldLoginWithValidCredentials() {
        loginPage.openPage()
                .fillAndSubmitForm("user1", "password1")
                .shouldHaveWelcomeMessage("Welcome, user1!");
    }

    @Test
    @Manual
    @Tag("manual")
    @Layer("manual")
    @DisplayName("Invalid credentials show readable error")
    void invalidCredentialsShowError() {
        step("Open /login.html in browser");
        step("Enter valid login and wrong password");
        step("Submit form");
        step("Verify error message is visible and readable");
    }

    @Test
    @Manual
    @Tag("manual")
    @Layer("manual")
    @DisplayName("Empty fields show validation hints")
    void emptyFieldsShowValidationHints() {
        step("Open /login.html");
        step("Submit without filling fields");
        step("Verify validation message for login and password");
    }
}
