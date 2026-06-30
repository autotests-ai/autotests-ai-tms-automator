package config;

import org.aeonbits.owner.Config;

@Config.LoadPolicy(Config.LoadType.MERGE)
@Config.Sources({
        "system:properties",
        "classpath:config/${env}.properties",
})
public interface TestConfig extends Config {

    @Key("attachBrowserConsoleLogs")
    @DefaultValue("false")
    boolean attachBrowserConsoleLogs();
    
    @Key("attachHarLogs")
    @DefaultValue("false")
    boolean attachHarLogs();

    @Key("attachLastScreenshot")
    @DefaultValue("false")
    boolean attachLastScreenshot();

    @Key("attachPageSource")
    @DefaultValue("false")
    boolean attachPageSource();

    @Key("attachVideo")
    @DefaultValue("false")
    boolean attachVideo();

    @Key("allureReportMode")
    @DefaultValue("allure3")
    String allureReportMode();

    @Key("logToConsole")
    @DefaultValue("true")
    boolean logToConsole();

    @Key("selenideLogToConsole")
    @DefaultValue("true")
    boolean selenideLogToConsole();

    @Key("rootLogLevel")
    @DefaultValue("info")
    String rootLogLevel();

    @Key("baseUrl")
    @DefaultValue("")
    String baseUrl();

    @Key("basePath")
    @DefaultValue("")
    String basePath();

    @Key("browser")
    @DefaultValue("chrome")
    String browser();

    @Key("browserSize")
    @DefaultValue("1920x1280")
    String browserSize();

    @Key("browserVersion")
    @DefaultValue("148")
    String browserVersion();

    @Key("closeBrowserAfterEach")
    @DefaultValue("false")
    boolean closeBrowserAfterEach();

    @Key("enableAllureSelenideListener")
    @DefaultValue("false")
    boolean enableAllureSelenideListener();

    @Key("enableHar")
    @DefaultValue("false")
    boolean enableHar();

    @Key("enableVnc")
    @DefaultValue("false")
    boolean enableVnc();

    @Key("enableVideo")
    @DefaultValue("false")
    boolean enableVideo();

    @Key("headless")
    @DefaultValue("false")
    boolean headless();

    @Key("videoFolder")
    @DefaultValue("")
    String videoFolder();

    @Key("remoteUrl")
    @DefaultValue("")
    String remoteUrl();

    @Key("updateBaselines")
    @DefaultValue("false")
    boolean updateBaselines();

    @Key("baselinesDir")
    @DefaultValue("screenshots")
    String baselinesDir();

    @Key("visualDiffThreshold")
    @DefaultValue("0.015")
    double visualDiffThreshold();

}
