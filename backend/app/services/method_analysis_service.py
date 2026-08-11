"""Transform existing class metadata into method-level navigation metadata."""

from app.schemas.repositories import (
    JavaAnnotationMetadata,
    MethodAnalysisResponse,
    MethodMetadata,
    MethodParameterMetadata,
    RepositoryAnalyzeResponse,
)


class MethodAnalysisService:
    """Build method metadata from a completed repository analysis."""

    def build_method_analysis(
        self,
        analysis: RepositoryAnalyzeResponse,
    ) -> MethodAnalysisResponse:
        """Preserve class, method, parameter, annotation, and scope metadata."""
        methods = [
            MethodMetadata(
                file_path=class_metadata.file_path,
                package_name=class_metadata.package_name,
                class_name=class_metadata.class_name,
                qualified_class_name=class_metadata.qualified_class_name,
                method_name=method.method_name,
                visibility=method.visibility,
                return_type=method.return_type,
                parameters=[
                    MethodParameterMetadata(
                        name=parameter.name,
                        type=parameter.type,
                        annotations=[
                            self._copy_annotation(annotation)
                            for annotation in parameter.annotations
                        ],
                    )
                    for parameter in method.parameters
                ],
                annotations=[
                    self._copy_annotation(annotation)
                    for annotation in method.annotations
                ],
                scope=class_metadata.scope,
            )
            for class_metadata in analysis.classes
            for method in class_metadata.methods
        ]
        return MethodAnalysisResponse(methods=methods)

    @staticmethod
    def _copy_annotation(annotation: JavaAnnotationMetadata) -> JavaAnnotationMetadata:
        return JavaAnnotationMetadata(
            name=annotation.name,
            value=annotation.value,
            methods=list(annotation.methods),
        )
