package com.codeatlas.parser;

import com.github.javaparser.ParseProblemException;
import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.TypeDeclaration;

import java.util.ArrayList;
import java.util.List;
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
            CompilationUnit compilationUnit = StaticJavaParser.parse(sourcePath);
            System.out.println(toJson(compilationUnit));
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

    private static String toJson(CompilationUnit compilationUnit) {
        StringBuilder output = new StringBuilder();
        output.append("{\"package_name\":");
        appendJsonString(output, compilationUnit.getPackageDeclaration()
            .map(declaration -> declaration.getNameAsString())
            .orElse(""));
        output.append(",\"classes\":[");

        boolean firstClass = true;
        for (ClassOrInterfaceDeclaration declaration : compilationUnit.findAll(ClassOrInterfaceDeclaration.class)) {
            if (!firstClass) {
                output.append(',');
            }
            firstClass = false;
            output.append("{\"class_name\":");
            appendJsonString(output, declaration.getNameAsString());
            output.append(",\"qualified_class_name\":");
            appendJsonString(output, qualifiedClassName(declaration));
            output.append(",\"annotations\":[");
            boolean firstAnnotation = true;
            for (com.github.javaparser.ast.expr.AnnotationExpr annotation : declaration.getAnnotations()) {
                if (!firstAnnotation) {
                    output.append(',');
                }
                firstAnnotation = false;
                appendJsonString(output, annotation.getNameAsString());
            }
            output.append("],\"extended_types\":[");
            boolean firstExtendedType = true;
            for (com.github.javaparser.ast.type.ClassOrInterfaceType extendedType : declaration.getExtendedTypes()) {
                if (!firstExtendedType) {
                    output.append(',');
                }
                firstExtendedType = false;
                appendJsonString(output, extendedType.toString());
            }
            for (com.github.javaparser.ast.type.ClassOrInterfaceType implementedType : declaration.getImplementedTypes()) {
                if (!firstExtendedType) {
                    output.append(',');
                }
                firstExtendedType = false;
                appendJsonString(output, implementedType.toString());
            }
            output.append("]}");
        }
        output.append("]}");
        return output.toString();
    }

    private static String qualifiedClassName(ClassOrInterfaceDeclaration declaration) {
        List<String> names = new ArrayList<>();
        Node current = declaration;
        while (current != null) {
            if (current instanceof TypeDeclaration) {
                names.add(0, ((TypeDeclaration<?>) current).getNameAsString());
            }
            current = current.getParentNode().orElse(null);
        }
        return String.join(".", names);
    }

    private static void appendJsonString(StringBuilder output, String value) {
        output.append('"');
        for (int index = 0; index < value.length(); index++) {
            char character = value.charAt(index);
            if (character == '"' || character == '\\') {
                output.append('\\');
            }
            if (character == '\n') {
                output.append("\\n");
            } else if (character == '\r') {
                output.append("\\r");
            } else if (character == '\t') {
                output.append("\\t");
            } else {
                output.append(character);
            }
        }
        output.append('"');
    }
}
