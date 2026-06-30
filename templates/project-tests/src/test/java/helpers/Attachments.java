package helpers;

import com.codeborne.selenide.WebDriverRunner;
import io.qameta.allure.Attachment;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;

import static com.codeborne.selenide.Selenide.sessionId;
import static config.ConfigReader.config;

public class Attachments {

    @Attachment(value = "{0}", type = "image/png")
    public static byte[] screenshotAs(String name) {
        return ((TakesScreenshot) WebDriverRunner.getWebDriver())
                .getScreenshotAs(OutputType.BYTES);
    }

    @Attachment(value = "Video", type = "text/html", fileExtension = ".html")
    public static String video() {
        String videoUrl = config.videoFolder() + sessionId() + ".mp4";
        return "<html><body><video width='100%' height='100%' controls autoplay><source src='"
                + videoUrl
                + "' type='video/mp4'></video></body></html>";
    }
}
