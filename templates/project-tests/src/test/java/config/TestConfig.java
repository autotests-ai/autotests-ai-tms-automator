package config;

import org.aeonbits.owner.Config;

@Config.LoadPolicy(Config.LoadType.MERGE)
@Config.Sources({
        "system:properties",
        "classpath:config/${env}.properties"
})
public interface TestConfig extends Config {

    @Key("baseUrl")
    String baseUrl();

    @Key("browser")
    @DefaultValue("chrome")
    String browser();

    @Key("browserSize")
    @DefaultValue("1920x1280")
    String browserSize();

    @Key("browserVersion")
    @DefaultValue("148")
    String browserVersion();

    @Key("headless")
    @DefaultValue("false")
    boolean headless();

    @Key("remoteUrl")
    @DefaultValue("")
    String remoteUrl();

    @Key("videoFolder")
    @DefaultValue("")
    String videoFolder();
}
