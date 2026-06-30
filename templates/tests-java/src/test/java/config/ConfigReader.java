package config;

import org.aeonbits.owner.ConfigFactory;

import java.nio.file.Files;
import java.nio.file.Path;

public class ConfigReader {
    public static final TestConfig testConfig = ConfigFactory.create(TestConfig.class);

    public static String resolveBaseUrl() {
        return resolveBaseUrl(testConfig);
    }

    public static String resolveBaseUrl(TestConfig config) {
        var url = config.baseUrl().trim();
        if (!url.isEmpty()) return withSlash(url);

        var basePath = config.basePath().trim();
        if (!basePath.isEmpty()) return withSlash(toDirectoryUrl(basePath));

        throw new IllegalStateException("Set baseUrl or basePath in config/${env}.properties");
    }

    private static String toDirectoryUrl(String pathString) {
        var path = Path.of(pathString);
        if (!path.isAbsolute()) path = Path.of(System.getProperty("user.dir")).resolve(path);
        path = path.normalize();
        if (!Files.isDirectory(path)) throw new IllegalStateException("basePath not found: " + path);
        verifyLoginAppDir(path);
        return path.toUri().toString();
    }

    private static void verifyLoginAppDir(Path dir) {
        if (!Files.isDirectory(dir)) {
            throw new IllegalStateException("Login app target must be a directory: " + dir);
        }
        var loginHtml = dir.resolve("login.html");
        if (!Files.isRegularFile(loginHtml)) {
            throw new IllegalStateException("login.html not found in: " + dir);
        }
    }

    private static String withSlash(String s) {
        return s.endsWith("/") ? s : s + "/";
    }
}
