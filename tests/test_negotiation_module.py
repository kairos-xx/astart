"""Negotiating a whole module: builders, solver and acceptance policy."""

from __future__ import annotations

from textwrap import dedent

from astart import CommentedModule, parse
from astart.rules.hints import escaped_function_names
from astart.rules.negotiation.run import Verdicts, negotiate_module

from tests.expectations import expect_equal, expect_in, expect_not_in


def _negotiate(
    *,
    source: str,
    engine: dict[str, str] | None = None,
) -> Verdicts:
    """Negotiate a module.

    Args:
        source: Module text.
        engine: Inference-engine proposals by node path.

    Returns:
        The verdicts.

    """
    module: CommentedModule = parse(source=dedent(text=source))
    return negotiate_module(
        module=module,
        corroboration=engine or {},
        escaped=escaped_function_names(module=module),
    )


def test_call_sites_plus_engine_type_a_parameter_and_its_return() -> None:
    """Check that agreeing callers and the engine annotate through a local."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            y = x
            return y

        f(1)
        f(2)
        """,
        engine={"f.x": "int", "f->": "int"},
    )
    expect_equal(actual=found.accepted, expected={"f.x": "int", "f->": "int"})


def test_disagreeing_callers_make_a_union_when_the_engine_agrees() -> None:
    """Check that ``int`` and ``str`` callers give a corroborated union."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            return x

        f(1)
        f("a")
        """,
        engine={"f.x": "int | str", "f->": "int | str"},
    )
    expect_equal(actual=found.accepted["f.x"], expected="int | str")


def test_engine_alone_never_creates_a_type() -> None:
    """Check that a proposal with no other evidence is ignored."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            return x
        """,
        engine={"f.x": "int", "f->": "int"},
    )
    expect_equal(actual=found.accepted, expected={})


def test_call_sites_alone_are_not_enough() -> None:
    """Check that one soft signal needs a second one."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            return x

        f(1)
        """,
    )
    expect_not_in(item="f.x", container=found.accepted)


def test_syntax_proven_return_flows_through_a_call() -> None:
    """Check that a proven return types the caller's local and return."""
    found: Verdicts = _negotiate(
        source="""
        def g():
            return 1

        def f():
            a = g()
            return a
        """,
    )
    expect_equal(actual=found.accepted, expected={"f->": "int", "g->": "int"})


def test_none_default_with_a_value_site_is_optional() -> None:
    """Check that ``x=None`` plus an ``int`` caller gives ``int | None``."""
    found: Verdicts = _negotiate(
        source="""
        def f(x=None):
            return x

        f(3)
        f(None)
        """,
        engine={"f.x": "int | None"},
    )
    expect_equal(actual=found.accepted["f.x"], expected="int | None")


def test_none_default_without_value_sites_is_refused() -> None:
    """Check that ``x: None`` is never written for a parameter."""
    found: Verdicts = _negotiate(
        source="""
        def f(x=None):
            return x

        f(None)
        """,
        engine={"f.x": "None"},
    )
    expect_not_in(item="f.x", container=found.accepted)


def test_an_unprovable_argument_blocks_the_parameter() -> None:
    """Check that one unknown caller makes the evidence incomplete."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            return x

        f(1)
        f(unknown())
        """,
        engine={"f.x": "int", "f->": "int"},
    )
    expect_not_in(item="f.x", container=found.accepted)
    expect_not_in(item="f->", container=found.accepted)


def test_an_escaping_function_is_not_closed_world() -> None:
    """Check that a function used as a value may have unseen callers."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            return x

        handler = f
        f(1)
        """,
        engine={"f.x": "int"},
    )
    expect_not_in(item="f.x", container=found.accepted)


def test_star_arguments_block_the_parameter() -> None:
    """Check that ``f(*xs)`` counts as unknown evidence."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            return x

        def g(xs):
            f(*xs)

        f(1)
        """,
        engine={"f.x": "int"},
    )
    expect_not_in(item="f.x", container=found.accepted)


def test_opacity_flows_downstream() -> None:
    """Check that a return depending on an opaque parameter is refused."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            return x

        def g(y):
            return f(y)

        f(1)
        f(unknown())
        g(1)
        """,
        engine={"g.y": "int", "g->": "int"},
    )
    expect_not_in(item="g->", container=found.accepted)


def test_unprovable_return_path_blocks_the_return() -> None:
    """Check that one unaccounted return keeps the others from settling."""
    found: Verdicts = _negotiate(
        source="""
        def f(flag):
            if flag:
                return 1
            return compute()
        """,
        engine={"f->": "int"},
    )
    expect_not_in(item="f->", container=found.accepted)


def test_element_of_a_list_argument_types_the_loop_variable() -> None:
    """Check that ``for`` over a ``list[int]`` parameter yields ``int``."""
    found: Verdicts = _negotiate(
        source="""
        def total(xs):
            first = 0
            for x in xs:
                first = x
            return first

        total([1, 2])
        """,
        engine={"total.xs": "list[int]"},
    )
    expect_in(item="total.xs", container=found.accepted)


def test_methods_skip_the_receiver() -> None:
    """Check that ``self`` is not a node and method calls bind."""
    found: Verdicts = _negotiate(
        source="""
        class C:
            def m(self, x):
                return x

        C().m(1)
        C().m(2)
        """,
        engine={"C.m.x": "int", "C.m->": "int"},
    )
    expect_equal(
        actual=found.accepted,
        expected={"C.m.x": "int", "C.m->": "int"},
    )


def test_declared_annotations_conflict_with_incompatible_callers() -> None:
    """Check that a caller breaking a declaration is reported."""
    found: Verdicts = _negotiate(
        source="""
        def f(x: int):
            return x

        f("a")
        """,
    )
    expect_not_in(item="f.x", container=found.accepted)
    expect_equal(actual=len(found.conflicts), expected=1)


def test_stub_and_abstract_bodies_say_nothing_about_the_return() -> None:
    """Check that ``...`` and ``raise NotImplementedError`` are stubs."""
    found: Verdicts = _negotiate(
        source="""
        class Base:
            def a(self):
                ...

            def b(self):
                raise NotImplementedError
        """,
    )
    expect_equal(actual=found.accepted, expected={})


def test_exit_is_never_narrowed_to_none() -> None:
    """Check that ``__exit__`` keeps the protocol's ``bool | None``."""
    found: Verdicts = _negotiate(
        source="""
        class C:
            def __exit__(self, kind, value, trace):
                self.closed = True
        """,
    )
    expect_equal(actual=found.accepted["C.__exit__->"], expected="bool | None")


def test_constructor_call_is_the_class_not_the_init_return() -> None:
    """Check that ``return Result()`` is not typed ``None``."""
    found: Verdicts = _negotiate(
        source="""
        class Result:
            def __init__(self, code):
                self.code = code

        def run():
            return Result(1)
        """,
    )
    expect_equal(actual=found.accepted.get("run->"), expected="Result")


def test_calling_a_coroutine_function_is_not_its_awaited_type() -> None:
    """Check that an unawaited ``async def`` call is not typed ``int``."""
    found: Verdicts = _negotiate(
        source="""
        async def fetch():
            return 1

        def run():
            return fetch()
        """,
    )
    expect_not_in(item="run->", container=found.accepted)


def test_list_filled_by_append_is_a_list_of_the_elements() -> None:
    """Check that ``out = []`` plus appends types the returned list."""
    found: Verdicts = _negotiate(
        source="""
        def collect(xs):
            out = []
            for x in xs:
                out.append(x)
            return out

        collect([1, 2])
        """,
        engine={"collect.xs": "list[int]", "collect->": "list[int]"},
    )
    expect_equal(actual=found.accepted["collect->"], expected="list[int]")


def test_set_filled_by_add_and_list_by_insert() -> None:
    """Check ``add`` for sets and ``insert`` for lists."""
    found: Verdicts = _negotiate(
        source="""
        def seen(a):
            out = set()
            out.add(a)
            return out

        def front(a):
            out = []
            out.insert(0, a)
            return out

        seen(1)
        front("s")
        """,
        engine={
            "seen.a": "int",
            "seen->": "set[int]",
            "front.a": "str",
            "front->": "list[str]",
        },
    )
    expect_equal(actual=found.accepted["seen->"], expected="set[int]")
    expect_equal(actual=found.accepted["front->"], expected="list[str]")


def test_container_passed_elsewhere_is_not_typed() -> None:
    """Check that handing the list to a function makes it escape."""
    found: Verdicts = _negotiate(
        source="""
        def collect(a):
            out = []
            out.append(a)
            fill(out)
            return out

        collect(1)
        """,
        engine={"collect->": "list[int]"},
    )
    expect_not_in(item="collect->", container=found.accepted)


def test_extend_is_not_understood_and_blocks_the_container() -> None:
    """Check that ``extend`` is refused rather than guessed."""
    found: Verdicts = _negotiate(
        source="""
        def collect(a):
            out = []
            out.append(1)
            out.extend(a)
            return out
        """,
        engine={"collect->": "list[int]"},
    )
    expect_not_in(item="collect->", container=found.accepted)


def test_unfilled_container_stays_unknown() -> None:
    """Check that an empty list nobody fills has no element type."""
    found: Verdicts = _negotiate(
        source="""
        def collect():
            out = []
            return out
        """,
        engine={"collect->": "list[int]"},
    )
    expect_not_in(item="collect->", container=found.accepted)


def test_closure_reading_the_container_blocks_it() -> None:
    """Check that a nested function using the list counts as an escape."""
    found: Verdicts = _negotiate(
        source="""
        def collect(a):
            out = []
            out.append(a)

            def later():
                out.append("x")

            return out

        collect(1)
        """,
        engine={"collect.a": "int", "collect->": "list[int]"},
    )
    expect_not_in(item="collect->", container=found.accepted)


def test_attribute_takes_the_parameter_it_is_assigned_from() -> None:
    """Check that ``self.x = x`` carries call-site evidence to ``self.x``."""
    found: Verdicts = _negotiate(
        source="""
        class C:
            def __init__(self, x):
                self.x = x

            def get(self):
                return self.x

        C(1)
        C(2)
        """,
        engine={"C.__init__.x": "int", "C.get->": "int"},
    )
    expect_equal(actual=found.accepted["C.get->"], expected="int")
    expect_equal(actual=found.accepted["C.__init__.x"], expected="int")


def test_attribute_written_from_outside_is_not_closed() -> None:
    """Check that ``obj.x = ...`` elsewhere makes the attribute unknown."""
    found: Verdicts = _negotiate(
        source="""
        class C:
            def __init__(self, x):
                self.x = x

            def get(self):
                return self.x

        c = C(1)
        c.x = "s"
        """,
        engine={"C.get->": "int"},
    )
    expect_not_in(item="C.get->", container=found.accepted)


def test_augmented_attribute_write_is_not_followed() -> None:
    """Check that ``self.n += 1`` blocks the attribute."""
    found: Verdicts = _negotiate(
        source="""
        class C:
            def __init__(self):
                self.n = 0

            def bump(self):
                self.n += 1

            def get(self):
                return self.n
        """,
        engine={"C.get->": "int"},
    )
    expect_not_in(item="C.get->", container=found.accepted)


def test_class_level_binding_blocks_the_attribute() -> None:
    """Check that a class attribute of the same name is a clash."""
    found: Verdicts = _negotiate(
        source="""
        class C:
            n = "s"

            def __init__(self):
                self.n = 0

            def get(self):
                return self.n
        """,
        engine={"C.get->": "int"},
    )
    expect_not_in(item="C.get->", container=found.accepted)


def test_inherited_attribute_blocks_the_subclass() -> None:
    """Check that a name the base class writes is not followed."""
    found: Verdicts = _negotiate(
        source="""
        class Base:
            def __init__(self):
                self.n = "s"

        class Child(Base):
            def __init__(self):
                self.n = 0

            def get(self):
                return self.n
        """,
        engine={"Child.get->": "int"},
    )
    expect_not_in(item="Child.get->", container=found.accepted)


def test_dynamic_attribute_access_disables_attributes() -> None:
    """Check that ``setattr`` anywhere stops attribute reasoning."""
    found: Verdicts = _negotiate(
        source="""
        class C:
            def __init__(self):
                self.n = 0
                setattr(self, "n", "s")

            def get(self):
                return self.n
        """,
        engine={"C.get->": "int"},
    )
    expect_not_in(item="C.get->", container=found.accepted)


def test_a_rebound_parameter_no_longer_carries_its_call_sites() -> None:
    """Check that ``x = 5`` in the body cuts the link from the callers."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            x = 5
            return x

        f("a")
        """,
        engine={"f.x": "str", "f->": "str"},
    )
    expect_not_in(item="f->", container=found.accepted)


def test_early_return_on_none_narrows_what_follows() -> None:
    """Check that ``if x is None: return 0`` makes later ``x`` an ``int``."""
    found: Verdicts = _negotiate(
        source="""
        def f(x=None):
            if x is None:
                return 0
            return x

        f(3)
        """,
        engine={"f.x": "int | None", "f->": "int"},
    )
    expect_equal(actual=found.accepted["f->"], expected="int")
    expect_equal(actual=found.accepted["f.x"], expected="int | None")


def test_isinstance_arm_narrows_the_union() -> None:
    """Check that ``isinstance(x, str)`` returns the ``str`` member."""
    found: Verdicts = _negotiate(
        source="""
        def f(x):
            if isinstance(x, str):
                return x
            return ""

        f(1)
        f("a")
        """,
        engine={"f.x": "int | str", "f->": "str"},
    )
    expect_equal(actual=found.accepted["f->"], expected="str")


def test_truthiness_removes_none_on_the_true_arm() -> None:
    """Check that ``if x: return x`` drops ``None`` from the result."""
    found: Verdicts = _negotiate(
        source="""
        def f(x=None):
            if x:
                return x
            return 0

        f(3)
        """,
        engine={"f.x": "int | None", "f->": "int"},
    )
    expect_equal(actual=found.accepted["f->"], expected="int")


def test_else_arm_gets_the_opposite_narrowing() -> None:
    """Check that ``x is not None`` narrows its body, ``else`` the rest."""
    found: Verdicts = _negotiate(
        source="""
        def f(x=None):
            if x is not None:
                return x
            else:
                return 0

        f(3)
        """,
        engine={"f.x": "int | None", "f->": "int"},
    )
    expect_equal(actual=found.accepted["f->"], expected="int")


def test_narrowing_does_not_outlive_an_arm_that_falls_through() -> None:
    """Check that without an early exit the later ``x`` stays wide."""
    found: Verdicts = _negotiate(
        source="""
        def f(x=None):
            if x is None:
                print("none")
            return x

        f(3)
        """,
        engine={"f->": "int"},
    )
    expect_not_in(item="f->", container=found.accepted)


def test_unnarrowed_return_keeps_none() -> None:
    """Check that the wide path still yields ``int | None``."""
    found: Verdicts = _negotiate(
        source="""
        def f(x=None):
            if x is None:
                print("none")
            return x

        f(3)
        """,
        engine={"f->": "int | None"},
    )
    expect_equal(actual=found.accepted["f->"], expected="int | None")


def test_a_nested_function_does_not_inherit_the_narrowing() -> None:
    """Check that a closure reads the wide parameter, not the narrowed one."""
    found: Verdicts = _negotiate(
        source="""
        def f(x=None):
            if x is None:
                return 0

            def later():
                return x

            return later

        f(3)
        """,
        engine={"f.x": "int | None"},
    )
    expect_equal(actual=found.accepted["f.x"], expected="int | None")


def test_protocol_dunder_gets_its_declared_result_when_the_body_fits() -> None:
    """Check ``__len__``, ``__exit__``, ``__str__`` take the declared type."""
    found: Verdicts = _negotiate(
        source="""
        class C:
            def __init__(self, items):
                self.items = items

            def __len__(self):
                return len(self.items)

            def __exit__(self, kind, value, trace):
                self.closed = True

            def __str__(self):
                return "c"
        """,
    )
    expect_equal(actual=found.accepted["C.__len__->"], expected="int")
    expect_equal(actual=found.accepted["C.__exit__->"], expected="bool | None")
    expect_equal(actual=found.accepted["C.__str__->"], expected="str")


def test_protocol_dunder_whose_body_does_not_fit_is_refused() -> None:
    """Check that ``__len__`` returning a string gets no annotation."""
    found: Verdicts = _negotiate(
        source="""
        class C:
            def __len__(self):
                return "many"
        """,
    )
    expect_not_in(item="C.__len__->", container=found.accepted)


def test_boolean_by_syntax_return_needs_the_engine() -> None:
    """Check the calibrated ``bool`` rule: syntax plus engine agreement."""
    source: str = """
        def big(x):
            return x > 3

        def both(a, b):
            return a is None or b is None
        """
    with_engine: Verdicts = _negotiate(
        source=source,
        engine={"big->": "bool", "both->": "bool"},
    )
    expect_equal(actual=with_engine.accepted["big->"], expected="bool")
    expect_equal(actual=with_engine.accepted["both->"], expected="bool")
    expect_equal(actual=_negotiate(source=source).accepted, expected={})


def test_a_float_default_keeps_a_bool_call_site_from_deciding() -> None:
    """Check that a float default stops ``return flag`` being ``bool``."""
    found: Verdicts = _negotiate(
        source="""
        def f(flag=1.5):
            return flag

        f(True)
        """,
        engine={"f->": "bool"},
    )
    expect_not_in(item="f->", container=found.accepted)


def test_none_only_return_needs_a_proof_not_just_callers() -> None:
    """Check that callers passing only ``None`` do not make ``-> None``."""
    found: Verdicts = _negotiate(
        source="""
        class R:
            def __init__(self, error):
                self.error = error

            def get(self):
                return self.error

        R(None)
        """,
        engine={"R.get->": "None", "R.__init__.error": "None"},
    )
    expect_not_in(item="R.get->", container=found.accepted)


def test_syntax_proven_none_return_is_still_accepted() -> None:
    """Check that ``return None`` stays a proven ``None``."""
    found: Verdicts = _negotiate(
        source="""
        def f():
            return None
        """,
    )
    expect_equal(actual=found.accepted["f->"], expected="None")


def test_a_source_with_no_evidence_makes_its_target_unknown() -> None:
    """Check that an uncalled parameter feeding an attribute blocks it."""
    found: Verdicts = _negotiate(
        source="""
        class R:
            def __init__(self, error):
                self.error = error

            def clear(self):
                self.error = None

            def get(self):
                return self.error
        """,
        engine={"R.get->": "None"},
    )
    expect_not_in(item="R.get->", container=found.accepted)


def test_a_dropped_contribution_makes_the_node_unknown() -> None:
    """Check that an element the algebra cannot take does not vanish."""
    found: Verdicts = _negotiate(
        source="""
        class Box:
            pass

        def first(box: Box):
            for item in box:
                return item
            return 1
        """,
        engine={"first->": "int"},
    )
    expect_not_in(item="first->", container=found.accepted)


def test_arithmetic_over_parameters_is_typed_from_the_operands() -> None:
    """Check ``a + b`` is ``int`` when both callers pass ``int``."""
    found: Verdicts = _negotiate(
        source="""
        def add(a, b):
            return a + b

        add(1, 2)
        add(3, 4)
        """,
        engine={"add.a": "int", "add.b": "int", "add->": "int"},
    )
    expect_equal(actual=found.accepted["add->"], expected="int")


def test_mixed_operand_types_do_not_guess_the_result() -> None:
    """Check that ``int | float`` operands give no derived type."""
    found: Verdicts = _negotiate(
        source="""
        def add(a, b):
            return a + b

        add(1, 2)
        add(1.5, 2)
        """,
        engine={"add->": "float"},
    )
    expect_not_in(item="add->", container=found.accepted)


def test_a_tuple_of_locals_is_a_tuple_of_their_types() -> None:
    """Check that ``return a, b`` gives ``tuple[int, str]``."""
    found: Verdicts = _negotiate(
        source="""
        def pair():
            a = 1
            b = "s"
            return a, b
        """,
    )
    expect_equal(actual=found.accepted["pair->"], expected="tuple[int, str]")


def test_comparison_and_formatting_over_nodes() -> None:
    """Check ``bool`` for ``a > 1`` and ``str`` for an f-string."""
    found: Verdicts = _negotiate(
        source="""
        def big(a):
            return a > 1

        def show(a):
            return f"{a}!"

        big(2)
        show(2)
        """,
        engine={"big.a": "int", "big->": "bool", "show.a": "int"},
    )
    expect_equal(actual=found.accepted["big->"], expected="bool")
    expect_equal(actual=found.accepted["show->"], expected="str")


def test_an_expression_over_an_unknown_name_is_unknown() -> None:
    """Check that a name nobody types blocks the derived value."""
    found: Verdicts = _negotiate(
        source="""
        def f(a):
            return a + mystery

        f(1)
        """,
        engine={"f->": "int"},
    )
    expect_not_in(item="f->", container=found.accepted)


def test_derived_values_chain_through_locals() -> None:
    """Check that ``t = a + b; return t * 2`` types both steps."""
    found: Verdicts = _negotiate(
        source="""
        def f(a, b):
            total = a + b
            return total * 2

        f(1, 2)
        """,
        engine={"f.a": "int", "f.b": "int", "f->": "int"},
    )
    expect_equal(actual=found.accepted["f->"], expected="int")


def test_a_rebound_parameter_is_not_also_a_local_variable() -> None:
    """Check that ``x = None`` after a test does not feed the parameter."""
    found: Verdicts = _negotiate(
        source="""
        def m(x: int | None):
            if x is None:
                return 0
            x = None
            return x
        """,
        engine={"m->": "int"},
    )
    expect_not_in(item="m->", container=found.accepted)


def test_a_method_that_rebinds_self_reads_no_attributes() -> None:
    """Check that ``self = other`` cuts the link to this instance's fields."""
    found: Verdicts = _negotiate(
        source="""
        class Box:
            def __init__(self):
                self.size = 3

            def get(self, other):
                self = other
                return self.size
        """,
        engine={"Box.get->": "int"},
    )
    expect_not_in(item="Box.get->", container=found.accepted)


def test_a_local_rebound_by_a_nested_nonlocal_is_not_followed() -> None:
    """Check that ``nonlocal v`` in an inner function blocks ``v``."""
    found: Verdicts = _negotiate(
        source="""
        def show(n):
            print(n)

        def main():
            v = 1

            def inner():
                nonlocal v
                v = "a"

            inner()
            show(v)
        """,
        engine={"show.n": "int"},
    )
    expect_not_in(item="show.n", container=found.accepted)


def test_an_annotated_local_is_taken_at_its_word() -> None:
    """Check that ``a: int = f()`` types what is derived from ``a``."""
    found: Verdicts = _negotiate(
        source="""
        def f():
            a: int = compute()
            return a + 1
        """,
    )
    expect_equal(actual=found.accepted["f->"], expected="int")


def test_a_bare_declaration_without_a_value_stays_unknown() -> None:
    """Check that ``a: int`` alone gives no reliable binding."""
    found: Verdicts = _negotiate(
        source="""
        def f(flag):
            a: int
            if flag:
                a = 1
            return a
        """,
        engine={"f->": "int"},
    )
    expect_not_in(item="f->", container=found.accepted)
