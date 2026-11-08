"""Graph-based type refinements using AST document API.

This module contains refinements that operate on the AST graph API
rather than direct AST traversal. These refinements are integrated
into the inference pipeline rather than applied as post-processing.
"""

from __future__ import annotations

from ast import (
    Attribute,
    BinOp,
    Call,
    ClassDef,
    FunctionDef,
    List,
    Module,
    Name,
    Subscript,
    Tuple,
    expr,
)
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

from astart._graph.backend.refiner import (
    self_attr_assignment_param_map,
    self_attr_return_attr_name,
)
from astart._graph.inference.post_refinements import (
    class_instance_attributes,
    refine_keyword_arguments,
)

if TYPE_CHECKING:
    from astart._graph.graph.document import AstDocument, AstGraphNode


@dataclass(slots=True)
class GraphRefinementStats:
    """Summary of graph-based refinements.

    Attributes:
        changed_annotations: Changed annotations retained as int by this
            instance.
        changed_calls: Changed calls retained as int by this instance.
        changed_returns: Changed returns retained as int by this instance.

    """

    changed_annotations: int = 0
    changed_returns: int = 0
    changed_calls: int = 0

    def changed(self) -> bool:
        """Return whether at least one refinement changed the tree.

        Returns:
            Whether the requested condition holds.

        """
        return (
            self.changed_annotations > 0
            or self.changed_returns > 0
            or self.changed_calls > 0
        )


def _replace_in_name(*, node: Name, old_name: str, new_name: str) -> None:
    """Replace a type variable in a Name node.

    Args:
        node: Name node to update in place.
        old_name: Type variable name to replace.
        new_name: Replacement type variable name.

    """
    if node.id == old_name:
        node.id = new_name


@dataclass(slots=True)
class GraphRefiner:
    """Apply graph-based type refinements using AST document API.

    Attributes:
        document: Document retained as AstDocument by this instance.
        stats: Stats retained as GraphRefinementStats by this instance.

    """

    document: AstDocument
    stats: GraphRefinementStats = field(default_factory=GraphRefinementStats)

    @staticmethod
    def slice_tuple_contains_typevar(
        *,
        slice_tuple: tuple[expr, ...],
        typevar_name: str,
    ) -> bool:
        """Check if a slice tuple contains a type variable.

        Args:
            slice_tuple: Slice tuple supplied as tuple[expr, ...] for this
                operation.
            typevar_name: Identifier of the typevar being resolved.

        Returns:
            Whether the requested condition holds.

        """
        for item in slice_tuple:
            if isinstance(item, Name) and item.id == typevar_name:
                return True
        return False

    @staticmethod
    def replace_typevar_in_slice_tuple(
        *,
        slice_tuple: tuple[expr, ...],
        old_name: str,
        new_name: str,
    ) -> None:
        """Replace type variable name in a slice tuple.

        Args:
            new_name: Identifier of the new being resolved.
            old_name: Identifier of the old being resolved.
            slice_tuple: Slice tuple supplied as tuple[expr, ...] for this
                operation.

        """
        for item in slice_tuple:
            if isinstance(item, Name) and item.id == old_name:
                item.id = new_name

    @staticmethod
    def has_decorator(
        *,
        function: FunctionDef,
        decorator_name: str,
    ) -> bool:
        """Check if function has a specific decorator.

        Args:
            decorator_name: Identifier of the decorator being resolved.
            function: The function examined while check if function has a
                specific decorator.

        Returns:
            Whether the requested condition holds.

        """
        for decorator in function.decorator_list:
            if isinstance(decorator, Name) and decorator.id == decorator_name:
                return True
            if (
                isinstance(decorator, Attribute)
                and decorator.attr == decorator_name
            ):
                return True
        return False

    def refine(self) -> None:
        """Apply all graph-based refinements."""
        self._refine_stringifiable_parameters()
        self._refine_property_getter_returns()
        self._refine_property_setter_parameters()
        self._refine_keyword_arguments()
        # Typevar constraints must be applied after other refinements
        # to ensure type parameters are already added
        self._refine_typevar_constraints()

    def replace_all_typevars_in_node(
        self,
        *,
        node: expr,
        old_name: str,
        new_name: str,
    ) -> None:
        """Recursively replace all type variable occurrences in an AST node.

        Args:
            new_name: Identifier of the new being resolved.
            node: The node examined while recursively replace all type variable
                occurrences in an AST node.
            old_name: Identifier of the old being resolved.

        """
        if isinstance(node, Name):
            _replace_in_name(
                node=node,
                old_name=old_name,
                new_name=new_name,
            )
        elif isinstance(node, Subscript):
            self._replace_in_subscript(
                node=node,
                old_name=old_name,
                new_name=new_name,
            )
        elif isinstance(node, BinOp):
            self.replace_in_binop(
                node=node,
                old_name=old_name,
                new_name=new_name,
            )
        elif isinstance(node, Call):
            self.replace_in_call(
                node=node,
                old_name=old_name,
                new_name=new_name,
            )
        elif isinstance(node, (Tuple, List)):
            self.replace_in_sequence(
                node=node,
                old_name=old_name,
                new_name=new_name,
            )

    def replace_in_slice(
        self,
        *,
        slice_value: expr | tuple[expr, ...],
        old_name: str,
        new_name: str,
    ) -> None:
        """Replace type variable in slice.

        Args:
            new_name: Identifier of the new being resolved.
            old_name: Identifier of the old being resolved.
            slice_value: Slice value supplied as expr | tuple[expr, ...] for
                this operation.

        """
        if isinstance(slice_value, Name):
            if slice_value.id == old_name:
                slice_value.id = new_name
        elif isinstance(slice_value, tuple):
            for item in slice_value:
                if isinstance(item, Name):
                    if item.id == old_name:
                        item.id = new_name
                else:
                    self.replace_all_typevars_in_node(
                        node=item,
                        old_name=old_name,
                        new_name=new_name,
                    )
        else:
            self.replace_all_typevars_in_node(
                node=slice_value,
                old_name=old_name,
                new_name=new_name,
            )

    def replace_in_binop(
        self,
        *,
        node: BinOp,
        old_name: str,
        new_name: str,
    ) -> None:
        """Replace type variable in BinOp node.

        Args:
            new_name: Identifier of the new being resolved.
            node: The node examined while replace type variable in BinOp node.
            old_name: Identifier of the old being resolved.

        """
        self.replace_all_typevars_in_node(
            node=node.left,
            old_name=old_name,
            new_name=new_name,
        )
        self.replace_all_typevars_in_node(
            node=node.right,
            old_name=old_name,
            new_name=new_name,
        )

    def replace_in_call(
        self,
        *,
        node: Call,
        old_name: str,
        new_name: str,
    ) -> None:
        """Replace type variable in Call node.

        Args:
            new_name: Identifier of the new being resolved.
            node: The node examined while replace type variable in Call node.
            old_name: Identifier of the old being resolved.

        """
        self.replace_all_typevars_in_node(
            node=node.func,
            old_name=old_name,
            new_name=new_name,
        )
        for argument in node.args:
            self.replace_all_typevars_in_node(
                node=argument,
                old_name=old_name,
                new_name=new_name,
            )
        for kw in node.keywords:
            self.replace_all_typevars_in_node(
                node=kw.value,
                old_name=old_name,
                new_name=new_name,
            )

    def replace_in_sequence(
        self,
        *,
        node: Tuple | List,
        old_name: str,
        new_name: str,
    ) -> None:
        """Replace type variable in Tuple or List node.

        Args:
            new_name: Identifier of the new being resolved.
            node: The node examined while replace type variable in Tuple or
                List node.
            old_name: Identifier of the old being resolved.

        """
        for elt in node.elts:
            self.replace_all_typevars_in_node(
                node=elt,
                old_name=old_name,
                new_name=new_name,
            )

    def annotation_uses_typevar(
        self,
        *,
        annotation: expr,
        typevar_name: str,
    ) -> bool:
        """Check if annotation uses a specific type variable.

        Args:
            annotation: The annotation examined while check if annotation uses
                a specific type variable.
            typevar_name: Identifier of the typevar being resolved.

        Returns:
            Whether the requested condition holds.

        """
        if isinstance(annotation, Name):
            return annotation.id == typevar_name
        if isinstance(annotation, Subscript):
            if (
                isinstance(annotation.value, Name)
                and annotation.value.id == typevar_name
            ):
                return True
            if annotation.slice:
                if (
                    isinstance(annotation.slice, Name)
                    and annotation.slice.id == typevar_name
                ):
                    return True
                if isinstance(
                    annotation.slice,
                    tuple,
                ) and self.slice_tuple_contains_typevar(
                    slice_tuple=annotation.slice,
                    typevar_name=typevar_name,
                ):
                    return True
        return False

    def replace_typevar_in_annotation(
        self,
        *,
        annotation: expr,
        old_name: str,
        new_name: str,
    ) -> None:
        """Replace type variable name in annotation.

        Args:
            annotation: The annotation examined while replace type variable
                name in annotation.
            new_name: Identifier of the new being resolved.
            old_name: Identifier of the old being resolved.

        """
        if isinstance(annotation, Name):
            if annotation.id == old_name:
                annotation.id = new_name
        elif isinstance(annotation, Subscript):
            if (
                isinstance(annotation.value, Name)
                and annotation.value.id == old_name
            ):
                annotation.value.id = new_name
            if annotation.slice:
                if (
                    isinstance(annotation.slice, Name)
                    and annotation.slice.id == old_name
                ):
                    annotation.slice.id = new_name
                elif isinstance(annotation.slice, tuple):
                    self.replace_typevar_in_slice_tuple(
                        slice_tuple=annotation.slice,
                        old_name=old_name,
                        new_name=new_name,
                    )

    @staticmethod
    def _refine_typevar_constraints() -> None:
        """Apply type variable constraints based on body operations."""
        return

    @staticmethod
    def _refine_stringifiable_parameters() -> None:
        """Add SupportsStr protocol and widen param types for str() calls."""
        # This refinement is disabled to avoid complex protocol generation
        return

    def _replace_in_subscript(
        self,
        *,
        node: Subscript,
        old_name: str,
        new_name: str,
    ) -> None:
        """Replace type variable in Subscript node.

        Args:
            new_name: Identifier of the new being resolved.
            node: The node examined while replace type variable in Subscript
                node.
            old_name: Identifier of the old being resolved.

        """
        self.replace_all_typevars_in_node(
            node=node.value,
            old_name=old_name,
            new_name=new_name,
        )
        if node.slice:
            self.replace_in_slice(
                slice_value=node.slice,
                old_name=old_name,
                new_name=new_name,
            )

    def _refine_property_getter_returns(self) -> None:
        """Refine property getter return types from attribute types."""
        class_nodes: tuple[AstGraphNode, ...] = self.document.nodes_of_kind(
            kind="ClassDef",
        )
        for class_node in class_nodes:
            class_def: ClassDef = cast(typ="ClassDef", val=class_node.node)
            class_attributes: dict[str, expr] = class_instance_attributes(
                class_node=class_def,
            )
            for item in class_def.body:
                if not isinstance(item, FunctionDef):
                    continue
                if not self.has_decorator(
                    function=item,
                    decorator_name="property",
                ):
                    continue
                attr_name: str | None = self_attr_return_attr_name(
                    function=item,
                )
                if attr_name is None:
                    continue
                attr_key: str = f"self.{attr_name}"
                if attr_key not in class_attributes:
                    continue
                attr_type: expr = class_attributes[attr_key]
                if item.returns is None or (
                    isinstance(item.returns, Name)
                    and item.returns.id == "object"
                ):
                    item.returns = attr_type
                    self.stats.changed_returns += 1

    def _refine_property_setter_parameters(self) -> None:
        """Refine property setter parameters from attribute types."""
        class_nodes: tuple[AstGraphNode, ...] = self.document.nodes_of_kind(
            kind="ClassDef",
        )
        for class_node in class_nodes:
            class_def: ClassDef = cast(typ="ClassDef", val=class_node.node)
            class_attributes: dict[str, expr] = class_instance_attributes(
                class_node=class_def,
            )
            for item in class_def.body:
                if not isinstance(item, FunctionDef):
                    continue
                if not self.has_decorator(
                    function=item,
                    decorator_name="setter",
                ):
                    continue
                attr_to_param: dict[str, str] = self_attr_assignment_param_map(
                    function=item,
                )
                for attr_name, param_name in attr_to_param.items():
                    attr_key: str = f"self.{attr_name}"
                    if attr_key not in class_attributes:
                        continue
                    attr_type: expr = class_attributes[attr_key]
                    for parameter in item.args.args:
                        if parameter.arg != param_name:
                            continue
                        if parameter.annotation is None or (
                            isinstance(parameter.annotation, Name)
                            and parameter.annotation.id == "object"
                        ):
                            parameter.annotation = attr_type
                            self.stats.changed_annotations += 1

    def _refine_keyword_arguments(self) -> None:
        """Rewrite safe positional calls to keyword-argument calls."""
        module: Module = self.document.tree
        changed_calls: int = refine_keyword_arguments(module=module)
        self.stats.changed_calls += changed_calls
