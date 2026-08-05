package com.codeatlas.parser;

import com.github.javaparser.ParseProblemException;
import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.StaticJavaParser;

import java.nio.file.Path;
import java.nio.file.Paths;

/** Command-line bridge that parses one source file with JavaParser. */
public final class JavaParserRunner {
    private JavaParserRunner() {
    }

    public static void main(String[] arguments) {
        if (arguments.length != 1) {
            fail("InvalidArguments", "Expected exactly one Java source file path.");
            return;
        }

        try {
            Path sourcePath = Paths.get(arguments[0]);
            StaticJavaParser.setConfiguration(
                new ParserConfiguration()
                    .setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_21)
            );
            StaticJavaParser.parse(sourcePath);
        } catch (ParseProblemException exception) {
            fail(exception.getClass().getSimpleName(), exception.getMessage());
            return;
        } catch (Exception exception) {
            fail(exception.getClass().getSimpleName(), exception.getMessage());
            return;
        }
    }

    private static void fail(String exceptionType, String message) {
        String sanitizedMessage = message == null ? "" : message.replace("\r", " ").replace("\n", " ");
        System.err.println(exceptionType + "|" + sanitizedMessage);
        System.exit(1);
    }
}
