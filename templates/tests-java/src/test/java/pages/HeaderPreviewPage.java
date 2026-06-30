package pages;

import pages.components.HeaderComponent;
import io.qameta.allure.Step;

import java.time.Duration;

import static com.codeborne.selenide.Condition.visible;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.open;

public class HeaderPreviewPage {

    @Step("Open header harness")
    public HeaderComponent openPage() {
        open("/header.html");
        $("[data-testid='header']").shouldBe(visible, Duration.ofSeconds(10));
        return new HeaderComponent();
    }
}
