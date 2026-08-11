"""Java source parsing through the JavaParser engine."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.exceptions.repository import InvalidJavaSourceFileError, JavaParsingError


@dataclass(frozen=True)
class JavaParserResult:
    """Parser representation for a successfully parsed Java compilation unit."""

    file_path: Path
    compilation_unit: "JavaCompilationUnit"


@dataclass(frozen=True)
class JavaAnnotation:
    """Structured Java annotation information from a declaration."""

    name: str
    value: str | None
    methods: tuple[str, ...]


@dataclass(frozen=True)
class JavaMethodDeclaration:
    """A method declaration represented from a JavaParser class declaration."""

    method_name: str
    annotations: tuple[JavaAnnotation, ...]
    visibility: str
    return_type: str
    parameters: tuple["JavaParameterDeclaration", ...]


@dataclass(frozen=True)
class JavaParameterDeclaration:
    """A method or constructor parameter declaration from JavaParser."""

    name: str
    type: str
    annotations: tuple[JavaAnnotation, ...]


@dataclass(frozen=True)
class JavaClassDeclaration:
    """A class declaration represented from a JavaParser compilation unit."""

    class_name: str
    qualified_class_name: str
    annotations: tuple[str, ...]
    extended_types: tuple[str, ...] = ()
    annotation_details: tuple[JavaAnnotation, ...] = ()
    methods: tuple[JavaMethodDeclaration, ...] = ()
    fields: tuple["JavaFieldDeclaration", ...] = ()
    constructors: tuple["JavaConstructorDeclaration", ...] = ()


@dataclass(frozen=True)
class JavaFieldDeclaration:
    """A class field declaration represented from JavaParser."""

    name: str
    type: str
    visibility: str
    annotations: tuple[JavaAnnotation, ...]


@dataclass(frozen=True)
class JavaConstructorDeclaration:
    """A constructor declaration represented from JavaParser."""

    visibility: str
    annotations: tuple[JavaAnnotation, ...]
    parameters: tuple[JavaParameterDeclaration, ...]


@dataclass(frozen=True)
class JavaCompilationUnit:
    """The JavaParser AST data needed by the first analysis stage."""

    package_name: str
    classes: tuple[JavaClassDeclaration, ...]


class JavaParserEngineError(RuntimeError):
    """Error details reported by the JavaParser bridge process."""

    def __init__(self, exception_type: str, exception_message: str) -> None:
        super().__init__(exception_message)
        self.exception_type = exception_type


class JavaParserService:
    """Parse one Java source file with the JavaParser Java library."""

    def __init__(self, runner_jar: Path, java_executable: str = "java") -> None:
        self._runner_jar = runner_jar.expanduser().resolve()
        self._java_executable = java_executable

    def parse_file(self, file_path: str | Path) -> JavaParserResult:
        """Validate and parse a single Java source file."""
        source_path = Path(file_path).expanduser().resolve()
        if source_path.suffix.lower() != ".java" or not source_path.is_file():
            raise InvalidJavaSourceFileError(
                "File path must exist and reference a Java source file."
            )
        if not self._runner_jar.is_file():
            raise JavaParsingError(
                "JavaParser runner JAR is unavailable. Build backend/java_parser first."
            )

        try:
            completed_process = subprocess.run(
                [self._java_executable, "-jar", str(self._runner_jar), str(source_path)],
                capture_output=True,
                check=False,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise JavaParsingError(
                f"Unable to start JavaParser for {source_path.name}."
            ) from error

        if completed_process.returncode != 0:
            engine_error = self._engine_error(completed_process.stderr)
            raise JavaParsingError(
                f"Unable to parse Java source file: {source_path.name}."
            ) from engine_error
        try:
            compilation_unit = self._compilation_unit(completed_process.stdout)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise JavaParsingError(
                f"JavaParser returned an invalid AST representation for {source_path.name}."
            ) from JavaParserEngineError("InvalidJavaParserOutput", str(error))
        return JavaParserResult(
            file_path=source_path,
            compilation_unit=compilation_unit,
        )

    @staticmethod
    def _engine_error(error_output: str) -> JavaParserEngineError:
        """Convert structured bridge error output into a Python exception."""
        exception_type, separator, exception_message = error_output.strip().partition("|")
        if separator:
            return JavaParserEngineError(exception_type, exception_message)
        return JavaParserEngineError("JavaParserProcessError", error_output.strip())

    @staticmethod
    def _compilation_unit(parser_output: str) -> JavaCompilationUnit:
        """Deserialize the compact AST representation emitted by the bridge."""
        payload = json.loads(parser_output)
        return JavaCompilationUnit(
            package_name=payload["package_name"],
            classes=tuple(
                JavaClassDeclaration(
                    class_name=class_declaration["class_name"],
                    qualified_class_name=class_declaration["qualified_class_name"],
                    annotations=tuple(class_declaration["annotations"]),
                    extended_types=tuple(class_declaration["extended_types"]),
                    annotation_details=tuple(
                        JavaAnnotation(
                            name=annotation["name"],
                            value=annotation.get("value"),
                            methods=tuple(annotation.get("methods", ())),
                        )
                        for annotation in class_declaration["annotation_details"]
                    ),
                    methods=tuple(
                        JavaMethodDeclaration(
                            method_name=method["method_name"],
                            annotations=tuple(
                                JavaAnnotation(
                                    name=annotation["name"],
                                    value=annotation.get("value"),
                                    methods=tuple(annotation.get("methods", ())),
                                )
                                for annotation in method["annotations"]
                            ),
                            visibility=method["visibility"],
                            return_type=method["return_type"],
                            parameters=tuple(
                                JavaParameterDeclaration(
                                    name=parameter["name"],
                                    type=parameter["type"],
                                    annotations=tuple(
                                        JavaAnnotation(
                                            name=annotation["name"],
                                            value=annotation.get("value"),
                                            methods=tuple(annotation.get("methods", ())),
                                        )
                                        for annotation in parameter["annotations"]
                                    ),
                                )
                                for parameter in method["parameters"]
                            ),
                        )
                        for method in class_declaration["methods"]
                    ),
                    fields=tuple(
                        JavaFieldDeclaration(
                            name=field["name"],
                            type=field["type"],
                            visibility=field["visibility"],
                            annotations=tuple(
                                JavaAnnotation(
                                    name=annotation["name"],
                                    value=annotation.get("value"),
                                    methods=tuple(annotation.get("methods", ())),
                                )
                                for annotation in field["annotations"]
                            ),
                        )
                        for field in class_declaration["fields"]
                    ),
                    constructors=tuple(
                        JavaConstructorDeclaration(
                            visibility=constructor["visibility"],
                            annotations=tuple(
                                JavaAnnotation(
                                    name=annotation["name"],
                                    value=annotation.get("value"),
                                    methods=tuple(annotation.get("methods", ())),
                                )
                                for annotation in constructor["annotations"]
                            ),
                            parameters=tuple(
                                JavaParameterDeclaration(
                                    name=parameter["name"],
                                    type=parameter["type"],
                                    annotations=tuple(
                                        JavaAnnotation(
                                            name=annotation["name"],
                                            value=annotation.get("value"),
                                            methods=tuple(annotation.get("methods", ())),
                                        )
                                        for annotation in parameter["annotations"]
                                    ),
                                )
                                for parameter in constructor["parameters"]
                            ),
                        )
                        for constructor in class_declaration["constructors"]
                    ),
                )
                for class_declaration in payload["classes"]
            ),
        )
