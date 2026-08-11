"""Repository-wide Java parsing orchestration."""

import logging
from pathlib import Path

from app.analyzers.controller_analyzer import ControllerAnalyzer
from app.analyzers.dependency_analyzer import DependencyAnalyzer
from app.analyzers.endpoint_analyzer import EndpointAnalyzer
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.service_analyzer import ServiceAnalyzer
from app.exceptions.repository import (
    InvalidRepositoryPathError,
    JavaParsingError,
    RepositoryAnalysisError,
)
from app.schemas.repositories import (
    ControllerMetadata,
    DependencyMetadata,
    EndpointMetadata,
    JavaAnnotationMetadata,
    JavaClassMetadata,
    JavaFileMetadata,
    JavaMethodMetadata,
    JavaParameterMetadata,
    RepositoryAnalyzeResponse,
    RepositoryControllersResponse,
    RepositoryMetadata,
    ServiceMetadata,
)
from app.services.java_parser_service import JavaParserService
from app.services.source_scope_service import SourceScopeService

logger = logging.getLogger(__name__)


class AnalysisService:
    """Discover and parse Java files in a cloned repository."""

    def __init__(
        self,
        java_parser_service: JavaParserService,
        controller_analyzer: ControllerAnalyzer,
        service_analyzer: ServiceAnalyzer,
        repository_analyzer: RepositoryAnalyzer,
        endpoint_analyzer: EndpointAnalyzer,
        dependency_analyzer: DependencyAnalyzer,
        source_scope_service: SourceScopeService,
    ) -> None:
        self._java_parser_service = java_parser_service
        self._controller_analyzer = controller_analyzer
        self._service_analyzer = service_analyzer
        self._repository_analyzer = repository_analyzer
        self._endpoint_analyzer = endpoint_analyzer
        self._dependency_analyzer = dependency_analyzer
        self._source_scope_service = source_scope_service

    def analyze_repository(self, local_path: str | Path) -> RepositoryAnalyzeResponse:
        """Parse every Java file and return aggregate parsing counts."""
        repository_path = self._resolve_repository_path(local_path)
        try:
            java_files = tuple(self._java_files(repository_path))
        except OSError as error:
            logger.exception(
                "Java file discovery failed",
                extra={"local_path": repository_path},
            )
            raise RepositoryAnalysisError("Unable to discover Java source files.") from error

        parsed_successfully = 0
        parse_failures = 0
        files: list[JavaFileMetadata] = []
        classes: list[JavaClassMetadata] = []
        controllers: list[ControllerMetadata] = []
        services: list[ServiceMetadata] = []
        repositories: list[RepositoryMetadata] = []
        endpoints: list[EndpointMetadata] = []
        dependencies: list[DependencyMetadata] = []
        for java_file in java_files:
            scope = self._source_scope_service.get_scope(java_file)
            try:
                parse_result = self._java_parser_service.parse_file(java_file)
                parsed_successfully += 1
                files.append(
                    JavaFileMetadata(
                        file_path=str(parse_result.file_path),
                        scope=scope,
                        parsed_successfully=True,
                    )
                )
                classes.extend(
                    JavaClassMetadata(
                        file_path=str(parse_result.file_path),
                        package_name=parse_result.compilation_unit.package_name,
                        class_name=class_declaration.class_name,
                        qualified_class_name=class_declaration.qualified_class_name,
                        annotations=list(class_declaration.annotations),
                        methods=[
                            JavaMethodMetadata(
                                method_name=method_declaration.method_name,
                                visibility=method_declaration.visibility,
                                return_type=method_declaration.return_type,
                                annotations=[
                                    JavaAnnotationMetadata(
                                        name=annotation.name,
                                        value=annotation.value,
                                        methods=list(annotation.methods),
                                    )
                                    for annotation in method_declaration.annotations
                                ],
                                parameters=[
                                    JavaParameterMetadata(
                                        name=parameter.name,
                                        type=parameter.type,
                                        annotations=[
                                            JavaAnnotationMetadata(
                                                name=annotation.name,
                                                value=annotation.value,
                                                methods=list(annotation.methods),
                                            )
                                            for annotation in parameter.annotations
                                        ],
                                    )
                                    for parameter in method_declaration.parameters
                                ],
                            )
                            for method_declaration in class_declaration.methods
                        ],
                        scope=scope,
                    )
                    for class_declaration in parse_result.compilation_unit.classes
                )
                parsed_controllers = self._controller_analyzer.analyze(
                    file_path=str(parse_result.file_path),
                    compilation_unit=parse_result.compilation_unit,
                    scope=scope,
                )
                controllers.extend(parsed_controllers)
                services.extend(
                    self._service_analyzer.analyze(
                        file_path=str(parse_result.file_path),
                        compilation_unit=parse_result.compilation_unit,
                        scope=scope,
                    )
                )
                repositories.extend(
                    self._repository_analyzer.analyze(
                        file_path=str(parse_result.file_path),
                        compilation_unit=parse_result.compilation_unit,
                        scope=scope,
                    )
                )
                endpoints.extend(
                    self._endpoint_analyzer.analyze(
                        file_path=str(parse_result.file_path),
                        compilation_unit=parse_result.compilation_unit,
                        controllers=parsed_controllers,
                        scope=scope,
                    )
                )
                dependencies.extend(
                    self._dependency_analyzer.analyze(
                        file_path=str(parse_result.file_path),
                        compilation_unit=parse_result.compilation_unit,
                        scope=scope,
                    )
                )
            except JavaParsingError as error:
                parse_failures += 1
                files.append(
                    JavaFileMetadata(
                        file_path=str(java_file.resolve()),
                        scope=scope,
                        parsed_successfully=False,
                    )
                )
                self._log_parse_failure(java_file, error)

        response = RepositoryAnalyzeResponse(
            total_java_files=len(java_files),
            parsed_successfully=parsed_successfully,
            parse_failures=parse_failures,
            files=files,
            classes=classes,
            controllers=controllers,
            services=services,
            repositories=repositories,
            endpoints=endpoints,
            dependencies=dependencies,
        )
        logger.info(
            "Repository Java parsing analysis completed",
            extra={
                "local_path": repository_path,
                "total_java_files": response.total_java_files,
                "parsed_successfully": response.parsed_successfully,
                "parse_failures": response.parse_failures,
            },
        )
        return response

    def extract_controllers(self, local_path: str | Path) -> RepositoryControllersResponse:
        """Parse Java files and extract Spring controller class metadata."""
        repository_path = self._resolve_repository_path(local_path)
        try:
            java_files = tuple(self._java_files(repository_path))
        except OSError as error:
            logger.exception(
                "Java file discovery failed",
                extra={"local_path": repository_path},
            )
            raise RepositoryAnalysisError("Unable to discover Java source files.") from error

        controllers: list[ControllerMetadata] = []
        for java_file in java_files:
            scope = self._source_scope_service.get_scope(java_file)
            try:
                parse_result = self._java_parser_service.parse_file(java_file)
            except JavaParsingError as error:
                self._log_parse_failure(java_file, error)
                continue
            controllers.extend(
                self._controller_analyzer.analyze(
                    file_path=str(parse_result.file_path),
                    compilation_unit=parse_result.compilation_unit,
                    scope=scope,
                )
            )

        response = RepositoryControllersResponse(
            controller_count=len(controllers),
            controllers=controllers,
        )
        logger.info(
            "Repository controller extraction completed",
            extra={
                "local_path": repository_path,
                "controller_count": response.controller_count,
            },
        )
        return response

    @staticmethod
    def _resolve_repository_path(local_path: str | Path) -> Path:
        """Resolve and validate the repository directory to analyze."""
        repository_path = Path(local_path).expanduser().resolve()
        if not repository_path.is_dir():
            raise InvalidRepositoryPathError(
                "Repository path must exist and reference a directory."
            )
        return repository_path

    @staticmethod
    def _java_files(repository_path: Path) -> list[Path]:
        """Recursively discover Java source files outside Git metadata."""
        return [
            path
            for path in repository_path.rglob("*.java")
            if ".git" not in path.relative_to(repository_path).parts
        ]

    @staticmethod
    def _error_message(error: Exception) -> str:
        """Return the parser's descriptive message when one is available."""
        return str(error) or str(getattr(error, "description", "")) or repr(error)

    def _log_parse_failure(self, java_file: Path, error: JavaParsingError) -> None:
        """Log the original JavaParser failure without altering its diagnostics."""
        parser_error = error.__cause__ or error
        logger.error(
            "Java source file could not be parsed",
            extra={
                "file_path": java_file,
                "exception_type": getattr(
                    parser_error,
                    "exception_type",
                    type(parser_error).__name__,
                ),
                "exception_message": self._error_message(parser_error),
            },
            exc_info=(
                type(parser_error),
                parser_error,
                parser_error.__traceback__,
            ),
        )
