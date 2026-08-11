package com.codeatlas.parser;

import com.github.javaparser.ParseProblemException;
import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.TypeDeclaration;
import com.github.javaparser.ast.expr.AnnotationExpr;
import com.github.javaparser.ast.expr.ArrayInitializerExpr;
import com.github.javaparser.ast.expr.Expression;
import com.github.javaparser.ast.expr.MemberValuePair;
import com.github.javaparser.ast.expr.NormalAnnotationExpr;
import com.github.javaparser.ast.expr.SingleMemberAnnotationExpr;
import com.github.javaparser.ast.expr.StringLiteralExpr;

import java.util.ArrayList;
import java.util.LinkedHashSet;
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
            output.append("],\"annotation_details\":[");
            appendAnnotationsJson(output, extractAnnotations(declaration.getAnnotations()));
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
            output.append("],\"methods\":[");
            boolean firstMethod = true;
            for (MethodDeclaration methodDeclaration : declaration.getMethods()) {
                if (!firstMethod) {
                    output.append(',');
                }
                firstMethod = false;
                output.append("{\"method_name\":");
                appendJsonString(output, methodDeclaration.getNameAsString());
                output.append(",\"annotations\":[");
                appendAnnotationsJson(output, extractAnnotations(methodDeclaration.getAnnotations()));
                output.append("]}");
            }
            output.append("]}");
        }
        output.append("]}");
        return output.toString();
    }

    private static void appendAnnotationsJson(StringBuilder output, List<AnnotationData> annotations) {
        boolean firstAnnotationDetail = true;
        for (AnnotationData annotation : annotations) {
            if (!firstAnnotationDetail) {
                output.append(',');
            }
            firstAnnotationDetail = false;
            output.append("{\"name\":");
            appendJsonString(output, annotation.name);
            output.append(",\"value\":");
            if (annotation.value == null) {
                output.append("null");
            } else {
                appendJsonString(output, annotation.value);
            }
            output.append(",\"methods\":[");
            boolean firstMethodValue = true;
            for (String methodValue : annotation.methods) {
                if (!firstMethodValue) {
                    output.append(',');
                }
                firstMethodValue = false;
                appendJsonString(output, methodValue);
            }
            output.append("]}");
        }
    }

    private static List<AnnotationData> extractAnnotations(List<AnnotationExpr> annotations) {
        List<AnnotationData> parsedAnnotations = new ArrayList<>();
        for (AnnotationExpr annotation : annotations) {
            String annotationName = annotation.getName().getIdentifier();
            List<String> annotationValues = annotationValues(annotation);
            List<String> annotationMethods = annotationMethods(annotation);
            if (annotationValues.isEmpty()) {
                parsedAnnotations.add(new AnnotationData(annotationName, null, annotationMethods));
                continue;
            }
            for (String annotationValue : annotationValues) {
                parsedAnnotations.add(new AnnotationData(annotationName, annotationValue, annotationMethods));
            }
        }
        return parsedAnnotations;
    }

    private static List<String> annotationValues(AnnotationExpr annotation) {
        List<String> values = new ArrayList<>();
        if (annotation instanceof SingleMemberAnnotationExpr) {
            values.addAll(expressionStringValues(((SingleMemberAnnotationExpr) annotation).getMemberValue()));
            return values;
        }
        if (!(annotation instanceof NormalAnnotationExpr)) {
            return values;
        }

        for (MemberValuePair pair : ((NormalAnnotationExpr) annotation).getPairs()) {
            String name = pair.getNameAsString();
            if ("value".equals(name) || "path".equals(name)) {
                values.addAll(expressionStringValues(pair.getValue()));
            }
        }
        return values;
    }

    private static List<String> annotationMethods(AnnotationExpr annotation) {
        LinkedHashSet<String> methods = new LinkedHashSet<>();
        if (!(annotation instanceof NormalAnnotationExpr)) {
            return new ArrayList<>();
        }
        for (MemberValuePair pair : ((NormalAnnotationExpr) annotation).getPairs()) {
            String name = pair.getNameAsString();
            if (!"method".equals(name) && !"methods".equals(name)) {
                continue;
            }
            methods.addAll(expressionMethodValues(pair.getValue()));
        }
        return new ArrayList<>(methods);
    }

    private static List<String> expressionStringValues(Expression expression) {
        List<String> values = new ArrayList<>();
        if (expression instanceof StringLiteralExpr) {
            values.add(((StringLiteralExpr) expression).getValue());
            return values;
        }
        if (expression instanceof ArrayInitializerExpr) {
            for (Expression valueExpression : ((ArrayInitializerExpr) expression).getValues()) {
                if (valueExpression instanceof StringLiteralExpr) {
                    values.add(((StringLiteralExpr) valueExpression).getValue());
                } else {
                    values.add(valueExpression.toString());
                }
            }
            return values;
        }
        values.add(expression.toString());
        return values;
    }

    private static List<String> expressionMethodValues(Expression expression) {
        List<String> values = new ArrayList<>();
        if (expression instanceof ArrayInitializerExpr) {
            for (Expression valueExpression : ((ArrayInitializerExpr) expression).getValues()) {
                values.add(simpleMethodName(valueExpression.toString()));
            }
            return values;
        }
        values.add(simpleMethodName(expression.toString()));
        return values;
    }

    private static String simpleMethodName(String methodExpression) {
        String normalized = methodExpression.trim();
        int separatorIndex = normalized.lastIndexOf('.');
        if (separatorIndex >= 0 && separatorIndex + 1 < normalized.length()) {
            return normalized.substring(separatorIndex + 1);
        }
        return normalized;
    }

    private static final class AnnotationData {
        private final String name;
        private final String value;
        private final List<String> methods;

        private AnnotationData(String name, String value, List<String> methods) {
            this.name = name;
            this.value = value;
            this.methods = methods;
        }
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
