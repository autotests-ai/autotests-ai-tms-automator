package config;

import org.aeonbits.owner.ConfigFactory;

public class ConfigReader {

  public static final TestConfig config = ConfigFactory.create(TestConfig.class);
}
