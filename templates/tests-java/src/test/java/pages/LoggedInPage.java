package pages;

import static com.codeborne.selenide.Condition.text;
import static com.codeborne.selenide.Selenide.$;
import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

public class LoggedInPage {

    private final SelenideElement welcomeMessage = $("[data-testid='welcome-message']");
    private final SelenideElement logoutButton = $("[data-testid='logout-button']");
    private final SelenideElement formTitle = $("[data-testid='logged-in-title']");
    private final SelenideElement successPanel = $("[data-testid='success-panel']");

    public SelenideElement successPanel() {
        return successPanel;
    }

    @Step("Verify form title message: {message}")
    public LoggedInPage shouldHaveFormTitle(String message) {
        formTitle.shouldHave(text(message));
        return this;
    }

    @Step("Verify welcome message: {message}")
    public LoggedInPage shouldHaveWelcomeMessage(String message) {
        welcomeMessage.shouldHave(text(message));
        return this;
    }

    @Step("Click logout button")
    public LoginPage clickLogoutButton() {
        logoutButton.click();
        return new LoginPage();
    }

}
