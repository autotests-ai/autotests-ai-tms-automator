package tests;

import helpers.Attachments;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import com.codeborne.selenide.logevents.SelenideLogger;
import io.qameta.allure.selenide.AllureSelenide;
import com.codeborne.selenide.Configuration;
import org.openqa.selenium.MutableCapabilities;
import org.openqa.selenium.chrome.ChromeOptions;

import java.util.Map;

import static com.codeborne.selenide.Selenide.closeWebDriver;
import static config.ConfigReader.config;


public class TestBase {

    @BeforeAll
    static void setup() {
        SelenideLogger.addListener("AllureSelenide",
        new AllureSelenide()
                .screenshots(true)
                .savePageSource(false));
    
        Configuration.baseUrl = config.baseUrl();
        Configuration.browser = config.browser();
        Configuration.browserVersion = config.browserVersion();
        Configuration.browserSize = config.browserSize();
        Configuration.headless = config.headless();
    
        if (!config.remoteUrl().isBlank()) {
            Configuration.remote = config.remoteUrl();
            var capabilities = new MutableCapabilities();
            capabilities.setCapability("selenoid:options", Map.of(
                    "enableVNC", true,
                    "enableVideo", !config.videoFolder().isBlank()
            ));
            Configuration.browserCapabilities = capabilities;
        } else if (config.headless()) {
            Configuration.browserCapabilities = new ChromeOptions()
                .addArguments("--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage");
        }
    }

    @AfterEach
    void afterEach() {
        Attachments.screenshotAs("Last screenshot");
        if (!config.videoFolder().isBlank()) {
            Attachments.video();
        }
        closeWebDriver();
    }
}
