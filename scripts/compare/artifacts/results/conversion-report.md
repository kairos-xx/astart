# Conversion report: [`fixtures/untyped.py`](../../../../fixtures/untyped.py) to [`typed.py`](../../../../fixtures/typed.py)

*Generated Tue 10 Nov 2026, 02:33 WET by [`scripts/compare`](../../__main__.py). Do not edit; run the script again.*

In every code example `-` is how the converted code is ([result.py](result.py)) and `+` is the reference contract; the links go to the exact lines.

| Field | Value |
| --- | --- |
| files | [fixtures/untyped.py](../../../../fixtures/untyped.py) · [typed.py](../../../../fixtures/typed.py) · [result.py](result.py) |
| tree | 28afad92ec59 |
| reference SHA-256 | aa45e16eb59e550be7997a19bf2200241f7209ba3d0627cbec34e4689e84a2d7 |
| converted in | 59 s |
| untyped / typed | 2725 / 5811 lines |
| settings | conversion mode (engine), negotiation on, variables on, minimum confidence 0.5, checker off |
| command | python scripts/compare --min-confidence 0.5 |
| reference-only targets | Reported separately; excluded from recovery totals |
| converted SHA-256 | 2e5ba3c9f5f2121a8792f09c758c4272507698af80bf460f83ed98f0f8424a04 |

## Summary

| Scope | To recover | Exact spelling | Equivalent | Narrower | Looser | Unresolved | Wrong | Missing | Extra |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Parameters and returns | 471 | 158 (33.5 %) | 31 | 42 | 6 | 36 | 8 | 190 | 15 |
| Variables | 294 | 99 (33.7 %) | 66 | 21 | 5 | 2 | 12 | 89 | 13 |

```text
Parameters and returns   same type ████████░░░░░░░░░░░░  40.1 %   wrong ░░░░░░░░░░░░░░░░░░░░   1.7 %
Variables                same type ███████████░░░░░░░░░  56.1 %   wrong █░░░░░░░░░░░░░░░░░░░   4.1 %
```

**Exact spelling** compares normalized annotation text. **Equivalent** is the scorer's semantic equivalence result after expanding aliases or comparing protocol structure. **Same type** adds these two counts. Narrower and looser types remain separate; changing a fixed tuple to a variadic tuple changes its length contract.

## Documentation and generated declarations

These counts are separate from annotation accuracy. Documentation uses normalized text; declarations use AST structure. Changed prose does not prove incorrect behavior. Renamed structural matches do not prove that all references use the declaration.

| Category | Exact | Equivalent structure | Changed | Missing | Extra |
| --- | ---: | ---: | ---: | ---: | ---: |
| Docstrings | 125 | 0 | 209 | 89 | 40 |
| Type aliases | 1 | 0 | 0 | 116 | 0 |
| Protocols | 0 | 0 | 0 | 17 | 8 |
| TypeVar | 0 | 0 | 1 | 51 | 3 |
| ParamSpec | 0 | 0 | 0 | 6 | 0 |
| TypeVarTuple | 0 | 0 | 0 | 0 | 0 |
| Classes | 18 | 0 | 46 | 24 | 6 |
| Declaration uses | 0 | 0 | 1 | 133 | 8 |

Full contracts and source locations are retained in `conversion-report.json` under `artifacts`.

### Docstrings

<details><summary><module> — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: description, summary. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: <module>](../../../../fixtures/typed.py#L1)**

````python
Strictly typed test file for inference, calls, decorators, and kwargs.
````

**[Produced: <module>](result.py#L1)**

````python
Untyped test file for resolver inference with merged edge cases.

This companion intentionally removes type hints and keyword-style calls from
the typed corpus while preserving the same runtime scenarios.
````

</details>

<details><summary>NodeMetadata — missing</summary>

No generated artifact has this qualified identity.

**[Reference: NodeMetadata](../../../../fixtures/typed.py#L258)**

````python
Optional depth and ancestry stored on an internal tree node.
````

</details>

<details><summary>SupportsMetadataAndName — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsMetadataAndName](../../../../fixtures/typed.py#L265)**

````python
Public, recursively mutable node-attribute contract.
````

</details>

<details><summary>AmountRecord — missing</summary>

No generated artifact has this qualified identity.

**[Reference: AmountRecord](../../../../fixtures/typed.py#L272)**

````python
Optional record fields accepted by the name/amount accumulator.
````

</details>

<details><summary>RecursiveRoot — missing</summary>

No generated artifact has this qualified identity.

**[Reference: RecursiveRoot](../../../../fixtures/typed.py#L279)**

````python
A root holding children that reference their parent.
````

</details>

<details><summary>RecursiveChild — missing</summary>

No generated artifact has this qualified identity.

**[Reference: RecursiveChild](../../../../fixtures/typed.py#L286)**

````python
Child of a recursive root with a mutable integer payload.
````

</details>

<details><summary>GroupInput — missing</summary>

No generated artifact has this qualified identity.

**[Reference: GroupInput](../../../../fixtures/typed.py#L293)**

````python
Required fields in a groupable input record.
````

</details>

<details><summary>NormalizedRow — missing</summary>

No generated artifact has this qualified identity.

**[Reference: NormalizedRow](../../../../fixtures/typed.py#L300)**

````python
Normalized group name and validated numeric score.
````

</details>

<details><summary>BuilderStructured — missing</summary>

No generated artifact has this qualified identity.

**[Reference: BuilderStructured](../../../../fixtures/typed.py#L307)**

````python
Structured result produced by a noncompact builder.
````

</details>

<details><summary>JSONRoundtrip — missing</summary>

No generated artifact has this qualified identity.

**[Reference: JSONRoundtrip](../../../../fixtures/typed.py#L314)**

````python
Round-tripped JSON record with statically known fields.
````

</details>

<details><summary>SyncContext — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SyncContext](../../../../fixtures/typed.py#L322)**

````python
Mutable synchronous context with typed event history.
````

</details>

<details><summary>AsyncPayload — missing</summary>

No generated artifact has this qualified identity.

**[Reference: AsyncPayload](../../../../fixtures/typed.py#L329)**

````python
Named asynchronous fetch result.
````

</details>

<details><summary>CallablePayload — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallablePayload](../../../../fixtures/typed.py#L336)**

````python
Fallback result of a stateful callable.
````

</details>

<details><summary>TestCallsPart1 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TestCallsPart1](../../../../fixtures/typed.py#L343)**

````python
Typed output keys from test_function_calls_part1.
````

</details>

<details><summary>TestCallsPart2 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TestCallsPart2](../../../../fixtures/typed.py#L370)**

````python
Typed output keys from test_function_calls_part2.
````

</details>

<details><summary>TestCallsPart3 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TestCallsPart3](../../../../fixtures/typed.py#L397)**

````python
Typed output keys from test_function_calls_part3.
````

</details>

<details><summary>ClassInstantiationResults — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ClassInstantiationResults](../../../../fixtures/typed.py#L424)**

````python
Typed output keys from test_class_instantiations.
````

</details>

<details><summary>OtherOperationResults — missing</summary>

No generated artifact has this qualified identity.

**[Reference: OtherOperationResults](../../../../fixtures/typed.py#L435)**

````python
Typed output keys from test_other_operations.
````

</details>

<details><summary>NewInferenceResults — missing</summary>

No generated artifact has this qualified identity.

**[Reference: NewInferenceResults](../../../../fixtures/typed.py#L444)**

````python
Typed output keys from test_new_inference_edge_cases.
````

</details>

<details><summary>ExtendedResultsPart1 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedResultsPart1](../../../../fixtures/typed.py#L457)**

````python
Typed output keys from test_extended_inference_edge_cases_part1.
````

</details>

<details><summary>ExtendedResultsPart2 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedResultsPart2](../../../../fixtures/typed.py#L481)**

````python
Typed output keys from test_extended_inference_edge_cases_part2.
````

</details>

<details><summary>ExtendedResultsPart3 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedResultsPart3](../../../../fixtures/typed.py#L496)**

````python
Typed output keys from test_extended_inference_edge_cases_part3.
````

</details>

<details><summary>TestCallsResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TestCallsResult](../../../../fixtures/typed.py#L522)**

````python
All result fields of the call-inference suite.
````

</details>

<details><summary>ExtendedTestResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedTestResult](../../../../fixtures/typed.py#L526)**

````python
Complete extended inference results with field-specific types.
````

</details>

<details><summary>Constants — missing</summary>

No generated artifact has this qualified identity.

**[Reference: Constants](../../../../fixtures/typed.py#L535)**

````python
Constants for the test.

Attributes:
    threshold (int): TODO.
    max_value (int): TODO.
    min_length (int): TODO.
    extended_sentinel (object): TODO.
    extended_context (ContextVar[DictObjectOrNone]): TODO.
````

</details>

<details><summary>SupportsUpdate.update — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.message. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: SupportsUpdate.update](../../../../fixtures/typed.py#L560)**

````python
Receive an update message.

Args:
    message (str): TODO.
````

**[Produced: SupportsUpdate.update](result.py#L59)**

````python
Receive an update message.

Args:
    message: TODO.
````

</details>

<details><summary>SupportsExecute — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsExecute](../../../../fixtures/typed.py#L570)**

````python
Protocol for integer strategies.
````

</details>

<details><summary>SupportsExecute.execute — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsExecute.execute](../../../../fixtures/typed.py#L573)**

````python
Execute with two integer inputs.

Args:
    a (int): TODO.
    b (int): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>SupportsAction.action — changed</summary>

Missing fields: returns.0. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: SupportsAction.action](../../../../fixtures/typed.py#L590)**

````python
Perform the action.

Returns:
    str: TODO.
````

**[Produced: SupportsAction.action](result.py#L82)**

````python
Perform the action.
````

</details>

<details><summary>SupportsClassMethodAndInstanceMethodAndStaticMethod — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsClassMethodAndInstanceMethodAndStaticMethod](../../../../fixtures/typed.py#L600)**

````python
Common interface of the nested class-method example.
````

</details>

<details><summary>SupportsClassMethodAndInstanceMethodAndStaticMethod.class_method — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsClassMethodAndInstanceMethodAndStaticMethod.class_method](../../../../fixtures/typed.py#L604)**

````python
Return the class name.
````

</details>

<details><summary>SupportsClassMethodAndInstanceMethodAndStaticMethod.static_method — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsClassMethodAndInstanceMethodAndStaticMethod.static_method](../../../../fixtures/typed.py#L609)**

````python
Return the static marker.
````

</details>

<details><summary>SupportsClassMethodAndInstanceMethodAndStaticMethod.instance_method — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsClassMethodAndInstanceMethodAndStaticMethod.instance_method](../../../../fixtures/typed.py#L613)**

````python
Return the instance marker.
````

</details>

<details><summary>SupportsValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsValue](../../../../fixtures/typed.py#L618)**

````python
An instance carrying a writable integer property.
````

</details>

<details><summary>SupportsValue.value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsValue.value](../../../../fixtures/typed.py#L622)**

````python
Read the integer value.
````

</details>

<details><summary>SupportsValue.value#definition:2 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsValue.value#definition:2](../../../../fixtures/typed.py#L627)**

````python
Write the integer value.
````

</details>

<details><summary>SupportsMatrixMultiplicationAndData — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsMatrixMultiplicationAndData](../../../../fixtures/typed.py#L632)**

````python
An integer matrix supporting matrix multiplication.
````

</details>

<details><summary>SupportsMatrixMultiplicationAndData.__matmul__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsMatrixMultiplicationAndData.__matmul__](../../../../fixtures/typed.py#L637)**

````python
Return the product of two matrices.
````

</details>

<details><summary>SupportsInstance — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsInstance](../../../../fixtures/typed.py#L642)**

````python
Wrapper holding a precisely typed original instance.
````

</details>

<details><summary>SupportsJoin — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsJoin](../../../../fixtures/typed.py#L648)**

````python
Subset of os.path whose join operation produces a string.
````

</details>

<details><summary>SupportsJoin.join — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsJoin.join](../../../../fixtures/typed.py#L651)**

````python
Join path components.
````

</details>

<details><summary>SupportsNameAndPath — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsNameAndPath](../../../../fixtures/typed.py#L656)**

````python
Features of the os module returned by __import__('os.path').
````

</details>

<details><summary>SupportsCall — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall](../../../../fixtures/typed.py#L663)**

````python
Invoke any unary callable without erasing its argument/return types.
````

</details>

<details><summary>SupportsCall.__call__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall.__call__](../../../../fixtures/typed.py#L666)**

````python
Apply a unary callable to its correctly typed argument.
````

</details>

<details><summary>SupportsCall2 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall2](../../../../fixtures/typed.py#L675)**

````python
Preserve a provided value or produce the default string.
````

</details>

<details><summary>SupportsInitializedByMeta — changed</summary>

Missing fields: attributes.initialized_by_meta. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: SupportsInitializedByMeta](../../../../fixtures/typed.py#L685)**

````python
Protocol for objects initialized by metaclass.

Attributes:
    initialized_by_meta (bool): TODO.
````

**[Produced: SupportsInitializedByMeta](result.py#L86)**

````python
Protocol for objects initialized by metaclass.
````

</details>

<details><summary>SupportsNewMethod.new_method — changed</summary>

Missing fields: returns.0. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: SupportsNewMethod.new_method](../../../../fixtures/typed.py#L699)**

````python
Return new method for testing.

Returns:
    str: TODO.
````

**[Produced: SupportsNewMethod.new_method](result.py#L95)**

````python
Return new method for testing.
````

</details>

<details><summary>SupportsAdditionAndXAndY — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsAdditionAndXAndY](../../../../fixtures/typed.py#L709)**

````python
Protocol for vector-like objects.

Attributes:
    x (int): TODO.
    y (int): TODO.
````

</details>

<details><summary>SupportsAdditionAndXAndY.__add__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsAdditionAndXAndY.__add__](../../../../fixtures/typed.py#L721)**

````python
Add vectors.

Args:
    other (SupportsAdditionAndXAndY): TODO.

Returns:
    SupportsAdditionAndXAndY: TODO.
````

</details>

<details><summary>MetaClass.__new__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters._kwargs, parameters.bases, parameters.mcs, parameters.namespace, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: MetaClass.__new__](../../../../fixtures/typed.py#L744)**

````python
Create a new class with ``meta_added``.

Args:
    mcs (TypeValue[MetaClass]): TODO.
    name (str): TODO.
    bases (TupleTypeObjectVariadic): TODO.
    namespace (DictObject): TODO.
    _kwargs (object): TODO.

Returns:
    MetaClass: TODO.
````

**[Produced: MetaClass.__new__](result.py#L116)**

````python
Create a new class with ``meta_added``.

Args:
    mcs: TODO.
    name (str): TODO.
    bases: TODO.
    namespace: TODO.
    _kwargs: TODO.

Returns:
    TODO.
````

</details>

<details><summary>MetaClass.__call__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.args, parameters.kwargs, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: MetaClass.__call__](../../../../fixtures/typed.py#L769)**

````python
Create instance with ``initialized_by_meta``.

Args:
    args (object): TODO.
    kwargs (object): TODO.

Returns:
    object: TODO.
````

**[Produced: MetaClass.__call__](result.py#L132)**

````python
Create instance with ``initialized_by_meta``.

Args:
    args: TODO.
    kwargs: TODO.

Returns:
    TODO.
````

</details>

<details><summary>AbstractBase.abstract_method — changed</summary>

Missing fields: returns.0. Additional fields: none. Changed fields: parameters.value. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: AbstractBase.abstract_method](../../../../fixtures/typed.py#L793)**

````python
Abstract method for testing.

Args:
    value (int): TODO.

Returns:
    int: TODO.
````

**[Produced: AbstractBase.abstract_method](result.py#L152)**

````python
Abstract method for testing.

Args:
    value (int): TODO.
````

</details>

<details><summary>BaseClass.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.y. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: BaseClass.__init__](../../../../fixtures/typed.py#L818)**

````python
Initialize base class.

Args:
    x (int): TODO.
    y (IntOrNone): TODO.
````

**[Produced: BaseClass.__init__](result.py#L182)**

````python
Initialize base class.

Args:
    x (int): TODO.
    y (int | None): TODO.
````

</details>

<details><summary>BaseClass.base_method — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.a. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: BaseClass.base_method](../../../../fixtures/typed.py#L829)**

````python
Test base method.

Args:
    a (int): TODO.
    b (int): TODO.

Returns:
    int: TODO.
````

**[Produced: BaseClass.base_method](result.py#L192)**

````python
Test base method.

Args:
    a (SupportsAddition): TODO.
    b (int): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>BaseClass.base_property — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: BaseClass.base_property](../../../../fixtures/typed.py#L843)**

````python
Base property getter.

Returns:
    int: TODO.
````

**[Produced: BaseClass.base_property](result.py#L205)**

````python
Base property getter.

Returns:
    TODO.
````

</details>

<details><summary>BaseClass.base_property#definition:2 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: BaseClass.base_property#definition:2](../../../../fixtures/typed.py#L853)**

````python
Set base property.

Args:
    value (int): TODO.
````

**[Produced: BaseClass.base_property#definition:2](result.py#L214)**

````python
Set base property.

Args:
    value: TODO.
````

</details>

<details><summary>DerivedClass.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.y. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: DerivedClass.__init__](../../../../fixtures/typed.py#L866)**

````python
Initialize derived class.

Args:
    x (int): TODO.
    y (IntOrNone): TODO.
    z (int): TODO.
````

**[Produced: DerivedClass.__init__](result.py#L226)**

````python
Initialize derived class.

Args:
    x (int): TODO.
    y (int | None): TODO.
    z (int): TODO.
````

</details>

<details><summary>MetaDecoratedClass.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: MetaDecoratedClass.__init__](../../../../fixtures/typed.py#L924)**

````python
Initialize meta decorated class.

Args:
    value (int): TODO.
````

**[Produced: MetaDecoratedClass.__init__](result.py#L278)**

````python
Initialize meta decorated class.

Args:
    value: TODO.
````

</details>

<details><summary>decorator — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.func, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: decorator](../../../../fixtures/typed.py#L934)**

````python
Multiply result by 2.

Args:
    func (CallableParametersToResult[P, R]): TODO.

Returns:
    CallableParametersToResult[P, ValueOrInt[R]]: TODO.
````

**[Produced: decorator](result.py#L287)**

````python
Multiply result by 2.

Args:
    func: TODO.

Returns:
    TODO.
````

</details>

<details><summary>decorator.wrapper — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator.wrapper](../../../../fixtures/typed.py#L948)**

````python
TODO.

Args:
    args (P.args): TODO.
    kwargs (P.kwargs): TODO.

Returns:
    ValueOrInt[R]: TODO.
````

</details>

<details><summary>decorator_with_args — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: decorator_with_args](../../../../fixtures/typed.py#L967)**

````python
Create decorator with configurable multiplier.

Args:
    multiplier (int): TODO.

Returns:
    CallableValueToResult[ CallableParametersToResult[P, R], CallableParametersToResult[P, ValueOrInt[R]], ]: TODO.
````

**[Produced: decorator_with_args](result.py#L305)**

````python
Create decorator with configurable multiplier.

Args:
    multiplier (int): TODO.

Returns:
    TODO.
````

</details>

<details><summary>decorator_with_args.actual_decorator — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_with_args.actual_decorator](../../../../fixtures/typed.py#L983)**

````python
TODO.

Args:
    func (CallableParametersToResult[P, R]): TODO.

Returns:
    CallableParametersToResult[P, ValueOrInt[R]]: TODO.
````

</details>

<details><summary>decorator_with_args.actual_decorator.wrapper — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_with_args.actual_decorator.wrapper](../../../../fixtures/typed.py#L997)**

````python
TODO.

Args:
    args (P.args): TODO.
    kwargs (P.kwargs): TODO.

Returns:
    ValueOrInt[R]: TODO.
````

</details>

<details><summary>decorator_with_class — changed</summary>

Missing fields: parameters.cls. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: decorator_with_class](../../../../fixtures/typed.py#L1018)**

````python
Wrap class in a proxy class.

Args:
    cls (TypeValue[T]): TODO.

Returns:
    Callable[..., SupportsInstance[T]]: TODO.
````

**[Produced: decorator_with_class](result.py#L326)**

````python
Wrap class in a proxy class.

Returns:
    TODO.
````

</details>

<details><summary>decorator_with_class.Wrapper.__init__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_with_class.Wrapper.__init__](../../../../fixtures/typed.py#L1034)**

````python
TODO.

Args:
    args (object): TODO.
    _kwargs (object): TODO.
````

</details>

<details><summary>decorator_with_class.Wrapper.__getattr__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_with_class.Wrapper.__getattr__](../../../../fixtures/typed.py#L1044)**

````python
Get attribute from wrapped instance.

Args:
    name (str): TODO.

Returns:
    object: TODO.
````

</details>

<details><summary>simple_function — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.x. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: simple_function](../../../../fixtures/typed.py#L1060)**

````python
Test simple function.

Args:
    x (int): TODO.

Returns:
    int: TODO.
````

**[Produced: simple_function](result.py#L356)**

````python
Test simple function.

Args:
    x (SupportsAddition2): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_args — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.x. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_args](../../../../fixtures/typed.py#L1074)**

````python
Test function with args.

Args:
    x (int): TODO.
    y (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_args](result.py#L369)**

````python
Test function with args.

Args:
    x (SupportsAddition): TODO.
    y (int): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>DataClassExample — changed</summary>

Missing fields: attributes.x, attributes.y, attributes.z. Additional fields: none. Changed fields: summary. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: DataClassExample](../../../../fixtures/typed.py#L1112)**

````python
Dataclass for testing type inference.

Attributes:
    x (int): TODO.
    y (str): TODO.
    z (ListInt): TODO.
````

**[Produced: DataClassExample](result.py#L404)**

````python
Dataclass-like class for testing type inference.
````

</details>

<details><summary>EnumClass — changed</summary>

Missing fields: attributes.VALUE_A, attributes.VALUE_B, attributes.VALUE_C. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: EnumClass](../../../../fixtures/typed.py#L1127)**

````python
Enum class for testing type inference.

Attributes:
    VALUE_A (EnumClass): TODO.
    VALUE_B (EnumClass): TODO.
    VALUE_C (EnumClass): TODO.
````

**[Produced: EnumClass](result.py#L424)**

````python
Enum class for testing type inference.
````

</details>

<details><summary>function_without_hints — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.c. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_without_hints](../../../../fixtures/typed.py#L1142)**

````python
Test function without missing type hints.

Args:
    a (int): TODO.
    b (int): TODO.
    c (IntOrNone): TODO.
    d (int): TODO.
    e (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_without_hints](result.py#L432)**

````python
Test function without missing type hints.

Args:
    a (int): TODO.
    b (int): TODO.
    c (int | None): TODO.
    d (int): TODO.
    e (int): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_kwargs — changed</summary>

Missing fields: none. Additional fields: parameters.args. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_kwargs](../../../../fixtures/typed.py#L1166)**

````python
Test function with kwargs.

Args:
    a (int): TODO.
    b (int): TODO.
    kwargs (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_kwargs](result.py#L449)**

````python
Test function with kwargs.

Args:
    a (int): TODO.
    b (int): TODO.
    args (int): TODO.
    kwargs (int): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>nested_function.inner.deeper — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.c, parameters.d, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: nested_function.inner.deeper](../../../../fixtures/typed.py#L1226)**

````python
Deeper function for testing.

Args:
    c (int): TODO.
    d (int): TODO.

Returns:
    int: TODO.
````

**[Produced: nested_function.inner.deeper](result.py#L509)**

````python
Deeper function for testing.

Args:
    c (T): TODO.
    d (T): TODO.

Returns:
    T: TODO.
````

</details>

<details><summary>closure_function — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: closure_function](../../../../fixtures/typed.py#L1244)**

````python
Test closure function.

Args:
    x (int): TODO.

Returns:
    CallableIntInt: TODO.
````

**[Produced: closure_function](result.py#L535)**

````python
Test closure function.

Args:
    x (int): TODO.

Returns:
    Callable[[int], int]: TODO.
````

</details>

<details><summary>closure_function.inner — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.y. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: closure_function.inner](../../../../fixtures/typed.py#L1255)**

````python
Inner closure for testing.

Args:
    y (int): TODO.

Returns:
    int: TODO.
````

**[Produced: closure_function.inner](result.py#L545)**

````python
Inner closure for testing.

Args:
    y (SupportsRadd): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_slices — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.data, parameters.step, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_slices](../../../../fixtures/typed.py#L1270)**

````python
Test function with slices.

Args:
    data (SequenceValue[T]): TODO.
    start (int): TODO.
    end (int): TODO.
    step (IntOrNone): TODO.

Returns:
    SequenceValue[T]: TODO.
````

**[Produced: function_with_slices](result.py#L559)**

````python
Test function with slices.

Args:
    data (list[int]): TODO.
    start (int): TODO.
    end (int): TODO.
    step (int | None): TODO.

Returns:
    list[int]: TODO.
````

</details>

<details><summary>function_with_comprehensions — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.items, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_comprehensions](../../../../fixtures/typed.py#L1293)**

````python
Test function with comprehensions.

Args:
    items (SequenceInt): TODO.

Returns:
    TupleListIntDictIntIntGeneratorInt: TODO.
````

**[Produced: function_with_comprehensions](result.py#L576)**

````python
Test function with comprehensions.

Args:
    items (list[int]): TODO.

Returns:
    tuple[list[int], dict[int, int], Generator[int]]: TODO.
````

</details>

<details><summary>function_with_lambdas — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.items, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_lambdas](../../../../fixtures/typed.py#L1313)**

````python
Test function with lambdas.

Args:
    items (SequenceStr): TODO.

Returns:
    TupleListStrVariadic: TODO.
````

**[Produced: function_with_lambdas](result.py#L591)**

````python
Test function with lambdas.

Args:
    items (list[str]): TODO.

Returns:
    tuple[list[str], list[str], list[str]]: TODO.
````

</details>

<details><summary>function_with_recursion — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.n. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_recursion](../../../../fixtures/typed.py#L1331)**

````python
Test function with recursion.

Args:
    n (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_recursion](result.py#L634)**

````python
Test function with recursion.

Args:
    n (SupportsLeAndMultiplicationAndSub): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_generators — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_generators](../../../../fixtures/typed.py#L1418)**

````python
Test function with generators.

Returns:
    ListInt: TODO.
````

**[Produced: function_with_generators](result.py#L715)**

````python
Test function with generators.

Returns:
    TODO.
````

</details>

<details><summary>function_with_coroutines — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_coroutines](../../../../fixtures/typed.py#L1438)**

````python
Test function with coroutines.

Returns:
    CallableValueToResult[int, AwaitableInt]: TODO.
````

**[Produced: function_with_coroutines](result.py#L743)**

````python
Test function with coroutines.

Returns:
    Callable[[int], Awaitable[int]]: TODO.
````

</details>

<details><summary>function_with_coroutines.async_function — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.x. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_coroutines.async_function](../../../../fixtures/typed.py#L1446)**

````python
Test async function.

Args:
    x (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_coroutines.async_function](result.py#L750)**

````python
Test async function.

Args:
    x (SupportsMultiplication): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_class_methods — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_class_methods](../../../../fixtures/typed.py#L1462)**

````python
Test function with class methods.

Returns:
    TypeSupportsClassMethods: TODO.
````

**[Produced: function_with_class_methods](result.py#L765)**

````python
Test function with class methods.

Returns:
    TODO.
````

</details>

<details><summary>function_with_property — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_property](../../../../fixtures/typed.py#L1505)**

````python
Test function with property.

Returns:
    TypeSupportsValue: TODO.
````

**[Produced: function_with_property](result.py#L804)**

````python
Test function with property.

Returns:
    TODO.
````

</details>

<details><summary>function_with_property.PropertyClass.value — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_property.PropertyClass.value](../../../../fixtures/typed.py#L1521)**

````python
Get value property.

Returns:
    int: TODO.
````

**[Produced: function_with_property.PropertyClass.value](result.py#L819)**

````python
Get value property.

Returns:
    TODO.
````

</details>

<details><summary>function_with_property.PropertyClass.value#definition:2 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.val. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_property.PropertyClass.value#definition:2](../../../../fixtures/typed.py#L1531)**

````python
Set value property.

Args:
    val (int): TODO.
````

**[Produced: function_with_property.PropertyClass.value#definition:2](result.py#L828)**

````python
Set value property.

Args:
    val: TODO.
````

</details>

<details><summary>function_with_descriptor — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_descriptor](../../../../fixtures/typed.py#L1548)**

````python
Test function with descriptor.

Returns:
    TypeObject: TODO.
````

**[Produced: function_with_descriptor](result.py#L844)**

````python
Test function with descriptor.

Returns:
    TODO.
````

</details>

<details><summary>function_with_descriptor.Descriptor.__init__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_descriptor.Descriptor.__init__](../../../../fixtures/typed.py#L1559)**

````python
TODO.
````

</details>

<details><summary>function_with_descriptor.Descriptor.__get__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.obj, parameters.objtype. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_descriptor.Descriptor.__get__](../../../../fixtures/typed.py#L1563)**

````python
Get descriptor value.

Args:
    obj (object): TODO.
    objtype (TypeObject): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_descriptor.Descriptor.__get__](result.py#L857)**

````python
Get descriptor value.

Args:
    obj: TODO.
    objtype: TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_descriptor.Descriptor.__set__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.obj. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_descriptor.Descriptor.__set__](../../../../fixtures/typed.py#L1577)**

````python
Set descriptor value.

Args:
    obj (object): TODO.
    value (int): TODO.
````

**[Produced: function_with_descriptor.Descriptor.__set__](result.py#L870)**

````python
Set descriptor value.

Args:
    obj: TODO.
    value (int): TODO.
````

</details>

<details><summary>function_with_descriptor.Descriptor.__delete__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.obj. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_descriptor.Descriptor.__delete__](../../../../fixtures/typed.py#L1588)**

````python
Delete descriptor value.

Args:
    obj (object): TODO.
````

**[Produced: function_with_descriptor.Descriptor.__delete__](result.py#L880)**

````python
Delete descriptor value.

Args:
    obj: TODO.
````

</details>

<details><summary>function_with_operator_overloading — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_operator_overloading](../../../../fixtures/typed.py#L1601)**

````python
Test function with operator overloading.

Returns:
    CallableIntIntSupportsAdditionAndXAndY: TODO.
````

**[Produced: function_with_operator_overloading](result.py#L892)**

````python
Test function with operator overloading.

Returns:
    TODO.
````

</details>

<details><summary>function_with_operator_overloading.Vector.__add__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.other. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_operator_overloading.Vector.__add__](../../../../fixtures/typed.py#L1625)**

````python
Add vectors.

Args:
    other (SupportsAdditionAndXAndY): TODO.

Returns:
    Vector: TODO.
````

**[Produced: function_with_operator_overloading.Vector.__add__](result.py#L912)**

````python
Add vectors.

Args:
    other (Vector): TODO.

Returns:
    Vector: TODO.
````

</details>

<details><summary>function_with_operator_overloading.Vector.__eq__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.other. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_operator_overloading.Vector.__eq__](../../../../fixtures/typed.py#L1662)**

````python
Check vector equality.

Args:
    other (object): TODO.

Returns:
    bool: TODO.
````

**[Produced: function_with_operator_overloading.Vector.__eq__](result.py#L945)**

````python
Check vector equality.

Args:
    other: TODO.

Returns:
    bool: TODO.
````

</details>

<details><summary>function_with_metaclass_usage — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_metaclass_usage](../../../../fixtures/typed.py#L1711)**

````python
Test function with metaclass usage.

Returns:
    object: TODO.
````

**[Produced: function_with_metaclass_usage](result.py#L988)**

````python
Test function with metaclass usage.

Returns:
    TODO.
````

</details>

<details><summary>function_with_multiple_inheritance — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_multiple_inheritance](../../../../fixtures/typed.py#L1725)**

````python
Test function with multiple inheritance.

Returns:
    TypeObject: TODO.
````

**[Produced: function_with_multiple_inheritance](result.py#L1001)**

````python
Test function with multiple inheritance.

Returns:
    TODO.
````

</details>

<details><summary>function_with_abstract_methods — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_abstract_methods](../../../../fixtures/typed.py#L1772)**

````python
Test function with abstract methods.

Returns:
    TypeAbstractBase: TODO.
````

**[Produced: function_with_abstract_methods](result.py#L1044)**

````python
Test function with abstract methods.

Returns:
    type[AbstractBase]: TODO.
````

</details>

<details><summary>function_with_protocol — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_protocol](../../../../fixtures/typed.py#L1809)**

````python
Test function with protocol.

Returns:
    TypeObject: TODO.
````

**[Produced: function_with_protocol](result.py#L1076)**

````python
Test function with protocol.

Returns:
    TODO.
````

</details>

<details><summary>function_with_protocol.ProtocolImplementation.protocol_method — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.x. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_protocol.ProtocolImplementation.protocol_method](../../../../fixtures/typed.py#L1820)**

````python
Test protocol method.

Args:
    x (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_protocol.ProtocolImplementation.protocol_method](result.py#L1086)**

````python
Test protocol method.

Args:
    x (SupportsMultiplication): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_generic_types — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_generic_types](../../../../fixtures/typed.py#L1835)**

````python
Test function with generic types.

Returns:
    TupleIntVariadicStr: TODO.
````

**[Produced: function_with_generic_types](result.py#L1100)**

````python
Test function with generic types.

Returns:
    tuple[int, int, str]: TODO.
````

</details>

<details><summary>function_with_generic_types.generic_function#definition:3 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_generic_types.generic_function#definition:3](../../../../fixtures/typed.py#L1849)**

````python
Test generic function.

Args:
    container (ValueOrOther[SequenceValue[T], MappingValueToResult[K, U]]): TODO.

Returns:
    ValueOrOther[T, U]: TODO.
````

</details>

<details><summary>function_with_union_types — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_union_types](../../../../fixtures/typed.py#L1871)**

````python
Test function with union types.

Returns:
    CallableIntOrStrToIntOrStr: TODO.
````

**[Produced: function_with_union_types](result.py#L1126)**

````python
Test function with union types.

Returns:
    TODO.
````

</details>

<details><summary>function_with_union_types.union_function — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_union_types.union_function](../../../../fixtures/typed.py#L1879)**

````python
Test union function.

Args:
    value (IntOrStr): TODO.

Returns:
    IntOrStr: TODO.
````

**[Produced: function_with_union_types.union_function](result.py#L1133)**

````python
Test union function.

Args:
    value: TODO.

Returns:
    int | str: TODO.
````

</details>

<details><summary>function_with_optional_types — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_optional_types](../../../../fixtures/typed.py#L1898)**

````python
Test function with optional types.

Returns:
    SupportsCall2: TODO.
````

**[Produced: function_with_optional_types](result.py#L1151)**

````python
Test function with optional types.

Returns:
    Callable[[None | int], int | str]: TODO.
````

</details>

<details><summary>function_with_optional_types.optional_function#definition:3 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_optional_types.optional_function#definition:3](../../../../fixtures/typed.py#L1912)**

````python
Test optional function.

Args:
    value (object): TODO.

Returns:
    object: TODO.
````

</details>

<details><summary>function_with_callable — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_callable](../../../../fixtures/typed.py#L1929)**

````python
Test function with callable.

Returns:
    SupportsCall: TODO.
````

**[Produced: function_with_callable](result.py#L1174)**

````python
Test function with callable.

Returns:
    TODO.
````

</details>

<details><summary>function_with_callable.callable_function — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.arg, parameters.func, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_callable.callable_function](../../../../fixtures/typed.py#L1937)**

````python
Test callable function.

Args:
    func (CallableValueToResult[InputT, OutputT]): TODO.
    arg (InputT): TODO.

Returns:
    OutputT: TODO.
````

**[Produced: function_with_callable.callable_function](result.py#L1181)**

````python
Test callable function.

Args:
    func (Callable[..., object]): TODO.
    arg: TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_tuple_unpacking — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_tuple_unpacking](../../../../fixtures/typed.py#L1956)**

````python
Test function with tuple unpacking.

Returns:
    TupleIntVariadic: TODO.
````

**[Produced: function_with_tuple_unpacking](result.py#L1196)**

````python
Test function with tuple unpacking.

Returns:
    tuple[int, int, int, int, int]: TODO.
````

</details>

<details><summary>function_with_dict_operations — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_dict_operations](../../../../fixtures/typed.py#L1969)**

````python
Test function with dict operations.

Returns:
    TupleDictIntVariadic: TODO.
````

**[Produced: function_with_dict_operations](result.py#L1208)**

````python
Test function with dict operations.

Returns:
    tuple[dict[str, int], dict[str, int]]: TODO.
````

</details>

<details><summary>function_with_set_operations — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_set_operations](../../../../fixtures/typed.py#L1983)**

````python
Test function with set operations.

Returns:
    TupleSetIntVariadic: TODO.
````

**[Produced: function_with_set_operations](result.py#L1221)**

````python
Test function with set operations.

Returns:
    tuple[set[int], set[int], set[int]]: TODO.
````

</details>

<details><summary>function_with_bitwise_operations — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_bitwise_operations](../../../../fixtures/typed.py#L1998)**

````python
Test function with bitwise operations.

Returns:
    TupleIntVariadic: TODO.
````

**[Produced: function_with_bitwise_operations](result.py#L1235)**

````python
Test function with bitwise operations.

Returns:
    tuple[int, int, int, int, int, int]: TODO.
````

</details>

<details><summary>function_with_ternary — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_ternary](../../../../fixtures/typed.py#L2046)**

````python
Test function with ternary.

Returns:
    TupleIntVariadic: TODO.
````

**[Produced: function_with_ternary](result.py#L1281)**

````python
Test function with ternary.

Returns:
    tuple[int, int]: TODO.
````

</details>

<details><summary>function_with_chained_comparisons — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_chained_comparisons](../../../../fixtures/typed.py#L2060)**

````python
Test function with chained comparisons.

Returns:
    TupleBoolVariadic: TODO.
````

**[Produced: function_with_chained_comparisons](result.py#L1294)**

````python
Test function with chained comparisons.

Returns:
    tuple[bool, bool, bool]: TODO.
````

</details>

<details><summary>function_with_boolean_logic — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_boolean_logic](../../../../fixtures/typed.py#L2074)**

````python
Test function with boolean logic.

Returns:
    TupleBoolVariadic: TODO.
````

**[Produced: function_with_boolean_logic](result.py#L1307)**

````python
Test function with boolean logic.

Returns:
    tuple[bool, bool, bool, bool, bool]: TODO.
````

</details>

<details><summary>function_with_none_handling — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_none_handling](../../../../fixtures/typed.py#L2092)**

````python
Test function with none handling.

Returns:
    TupleIntOrNoneVariadic: TODO.
````

**[Produced: function_with_none_handling](result.py#L1324)**

````python
Test function with none handling.

Returns:
    tuple[int | None, int | None]: TODO.
````

</details>

<details><summary>function_with_none_handling.maybe_none — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_none_handling.maybe_none](../../../../fixtures/typed.py#L2100)**

````python
Maybe none function for testing.

Args:
    value (IntOrNone): TODO.

Returns:
    IntOrNone: TODO.
````

**[Produced: function_with_none_handling.maybe_none](result.py#L1331)**

````python
Maybe none function for testing.

Args:
    value (int | None): TODO.

Returns:
    int | None: TODO.
````

</details>

<details><summary>function_with_ellipsis — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_ellipsis](../../../../fixtures/typed.py#L2119)**

````python
Test function with ellipsis.

Returns:
    CallableIntIntInt: TODO.
````

**[Produced: function_with_ellipsis](result.py#L1350)**

````python
Test function with ellipsis.

Returns:
    Callable[[int, int], int]: TODO.
````

</details>

<details><summary>function_with_ellipsis.ellipsis_function — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.a, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_ellipsis.ellipsis_function](../../../../fixtures/typed.py#L2127)**

````python
Ellipsis function for testing.

Args:
    a (int): TODO.
    b (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_ellipsis.ellipsis_function](result.py#L1357)**

````python
Ellipsis function for testing.

Args:
    a (T2): TODO.
    b (int): TODO.

Returns:
    T2: TODO.
````

</details>

<details><summary>function_with_star_expressions — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_star_expressions](../../../../fixtures/typed.py#L2143)**

````python
Test function with star expressions.

Returns:
    ListInt: TODO.
````

**[Produced: function_with_star_expressions](result.py#L1372)**

````python
Test function with star expressions.

Returns:
    list[int]: TODO.
````

</details>

<details><summary>function_with_double_star_expressions — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_double_star_expressions](../../../../fixtures/typed.py#L2154)**

````python
Test function with double star expressions.

Returns:
    DictInt: TODO.
````

**[Produced: function_with_double_star_expressions](result.py#L1382)**

````python
Test function with double star expressions.

Returns:
    dict[str, int]: TODO.
````

</details>

<details><summary>function_with_matrix_multiplication — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_matrix_multiplication](../../../../fixtures/typed.py#L2166)**

````python
Test function with matrix multiplication.

Returns:
    TypeValue[ SupportsMatrixMultiplicationAndData ]: TODO.
````

**[Produced: function_with_matrix_multiplication](result.py#L1393)**

````python
Test function with matrix multiplication.

Returns:
    TODO.
````

</details>

<details><summary>function_with_matrix_multiplication.Matrix.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.data. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_matrix_multiplication.Matrix.__init__](../../../../fixtures/typed.py#L2179)**

````python
Initialize matrix with data.

Args:
    data (ListListInt): TODO.
````

**[Produced: function_with_matrix_multiplication.Matrix.__init__](result.py#L1403)**

````python
Initialize matrix with data.

Args:
    data (list[list[int]]): TODO.
````

</details>

<details><summary>function_with_async_await — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_async_await](../../../../fixtures/typed.py#L2211)**

````python
Test function with async await.

Returns:
    Callable[[], AwaitableInt]: TODO.
````

**[Produced: function_with_async_await](result.py#L1435)**

````python
Test function with async await.

Returns:
    Callable[[], Awaitable[int]]: TODO.
````

</details>

<details><summary>function_with_type_annotations_missing — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_type_annotations_missing](../../../../fixtures/typed.py#L2232)**

````python
Test formerly missing type annotations.

Returns:
    CallableExamples: TODO.
````

**[Produced: function_with_type_annotations_missing](result.py#L1464)**

````python
Test formerly missing type annotations.

Returns:
    tuple[
            Callable[[int], int],
            Callable[[int, int], int],
            Callable[[int, int], int],
            Callable[[], int],
            Callable[[], int],
            Callable[[], int]
        ]:
        TODO.
````

</details>

<details><summary>function_with_type_annotations_missing.func1 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.x. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_type_annotations_missing.func1](../../../../fixtures/typed.py#L2240)**

````python
Func1 for testing.

Args:
    x (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_type_annotations_missing.func1](result.py#L1479)**

````python
Func1 for testing.

Args:
    x (SupportsAddition2): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_type_annotations_missing.func2 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.x, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_type_annotations_missing.func2](../../../../fixtures/typed.py#L2252)**

````python
Func2 for testing.

Args:
    x (int): TODO.
    y (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_type_annotations_missing.func2](result.py#L1490)**

````python
Func2 for testing.

Args:
    x (T3): TODO.
    y (int): TODO.

Returns:
    T3: TODO.
````

</details>

<details><summary>function_with_type_annotations_missing.func3 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.x. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_type_annotations_missing.func3](../../../../fixtures/typed.py#L2265)**

````python
Func3 for testing.

Args:
    x (int): TODO.
    y (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_type_annotations_missing.func3](result.py#L1502)**

````python
Func3 for testing.

Args:
    x (SupportsMultiplication2): TODO.
    y (int): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_complex_conditionals.complex_func — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.x, parameters.y, parameters.z. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_complex_conditionals.complex_func](../../../../fixtures/typed.py#L2326)**

````python
Complex function for testing.

Args:
    x (int): TODO.
    y (int): TODO.
    z (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_complex_conditionals.complex_func](result.py#L1578)**

````python
Complex function for testing.

Args:
    x (SupportsGtAndRmul): TODO.
    y (SupportsGtAndRmul): TODO.
    z (SupportsGtAndRmul): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_nested_loops — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_nested_loops](../../../../fixtures/typed.py#L2346)**

````python
Test function with nested loops.

Returns:
    CallableSequenceSequenceIntListInt: TODO.
````

**[Produced: function_with_nested_loops](result.py#L1597)**

````python
Test function with nested loops.

Returns:
    Callable[[Sequence[Sequence[int]]], list[int]]: TODO.
````

</details>

<details><summary>function_with_nested_loops.nested_loop_func — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.matrix, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_nested_loops.nested_loop_func](../../../../fixtures/typed.py#L2354)**

````python
Nested loop function for testing.

Args:
    matrix (SequenceSequenceInt): TODO.

Returns:
    ListInt: TODO.
````

**[Produced: function_with_nested_loops.nested_loop_func](result.py#L1604)**

````python
Nested loop function for testing.

Args:
    matrix (Iterable): TODO.

Returns:
    list[int]: TODO.
````

</details>

<details><summary>function_with_exception_chaining — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_exception_chaining](../../../../fixtures/typed.py#L2375)**

````python
Test function with exception chaining.

Returns:
    CallableNone: TODO.
````

**[Produced: function_with_exception_chaining](result.py#L1624)**

````python
Test function with exception chaining.

Returns:
    Callable[[], None]: TODO.
````

</details>

<details><summary>function_with_exception_chaining.exception_chain_func.raise_first_error — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_exception_chaining.exception_chain_func.raise_first_error](../../../../fixtures/typed.py#L2386)**

````python
TODO.

Raises:
    ValueError: TODO.
````

</details>

<details><summary>function_with_exception_chaining.exception_chain_func.raise_second_error — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_exception_chaining.exception_chain_func.raise_second_error](../../../../fixtures/typed.py#L2396)**

````python
TODO.

Args:
    original_error (ValueError): TODO.

Raises:
    TypeError: TODO.
````

</details>

<details><summary>function_with_custom_exceptions — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_custom_exceptions](../../../../fixtures/typed.py#L2417)**

````python
Test function with custom exceptions.

Returns:
    CallableNone: TODO.
````

**[Produced: function_with_custom_exceptions](result.py#L1650)**

````python
Test function with custom exceptions.

Returns:
    Callable[[], None]: TODO.
````

</details>

<details><summary>function_with_weak_refs — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_weak_refs](../../../../fixtures/typed.py#L2444)**

````python
Test function with weak refs.

Returns:
    ReferenceType[object]: TODO.
````

**[Produced: function_with_weak_refs](result.py#L1675)**

````python
Test function with weak refs.

Returns:
    TODO.
````

</details>

<details><summary>function_with_slots — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_slots](../../../../fixtures/typed.py#L2459)**

````python
Test function with slots.

Returns:
    TypeObject: TODO.
````

**[Produced: function_with_slots](result.py#L1689)**

````python
Test function with slots.

Returns:
    TODO.
````

</details>

<details><summary>function_with_slots.SlottedClass — changed</summary>

Missing fields: attributes.__slots__. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_slots.SlottedClass](../../../../fixtures/typed.py#L2467)**

````python
Slotted class for testing.

Attributes:
    __slots__ (TupleStrVariadic): TODO.
````

**[Produced: function_with_slots.SlottedClass](result.py#L1696)**

````python
Slotted class for testing.
````

</details>

<details><summary>function_with_slots.SlottedClass.__init__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_slots.SlottedClass.__init__](../../../../fixtures/typed.py#L2477)**

````python
TODO.

Args:
    x (int): TODO.
    y (int): TODO.
````

</details>

<details><summary>function_with_class_decorator — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_class_decorator](../../../../fixtures/typed.py#L2491)**

````python
Test function with class decorator.

Returns:
    TypeObject: TODO.
````

**[Produced: function_with_class_decorator](result.py#L1708)**

````python
Test function with class decorator.

Returns:
    TODO.
````

</details>

<details><summary>function_with_class_decorator.add_method — changed</summary>

Missing fields: parameters.cls. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_class_decorator.add_method](../../../../fixtures/typed.py#L2499)**

````python
Add method for testing.

Args:
    cls (TypeValue[T]): TODO.

Returns:
    TypeValue[T]: TODO.
````

**[Produced: function_with_class_decorator.add_method](result.py#L1715)**

````python
Add method for testing.

Returns:
    TODO.
````

</details>

<details><summary>function_with_class_decorator.add_method.new_method — changed</summary>

Missing fields: parameters.self. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_class_decorator.add_method.new_method](../../../../fixtures/typed.py#L2510)**

````python
Add new method.

Args:
    self (T): TODO.

Returns:
    str: TODO.
````

**[Produced: function_with_class_decorator.add_method.new_method](result.py#L1722)**

````python
Add new method.

Returns:
    str: TODO.
````

</details>

<details><summary>function_with_singleton — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_singleton](../../../../fixtures/typed.py#L2534)**

````python
Test function with singleton.

Returns:
    TypeObject: TODO.
````

**[Produced: function_with_singleton](result.py#L1742)**

````python
Test function with singleton.

Returns:
    TODO.
````

</details>

<details><summary>function_with_singleton.Singleton — changed</summary>

Missing fields: attributes._instance. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_singleton.Singleton](../../../../fixtures/typed.py#L2542)**

````python
Test singleton class.

Attributes:
    _instance (Self | None): TODO.
````

**[Produced: function_with_singleton.Singleton](result.py#L1749)**

````python
Test singleton class.
````

</details>

<details><summary>function_with_factory — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_factory](../../../../fixtures/typed.py#L2566)**

````python
Test function with factory.

Returns:
    TypeObject: TODO.
````

**[Produced: function_with_factory](result.py#L1767)**

````python
Test function with factory.

Returns:
    TODO.
````

</details>

<details><summary>function_with_factory.Factory.create — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.type_name. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_factory.Factory.create](../../../../fixtures/typed.py#L2584)**

````python
Create type for testing.

Args:
    type_name (str): TODO.

Returns:
    TypeA | TypeB | None: TODO.
````

**[Produced: function_with_factory.Factory.create](result.py#L1784)**

````python
Create type for testing.

Args:
    type_name: TODO.

Returns:
    TypeA | TypeB | None: TODO.
````

</details>

<details><summary>function_with_builder — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_builder](../../../../fixtures/typed.py#L2603)**

````python
Test function with builder.

Returns:
    TypeObject: TODO.
````

**[Produced: function_with_builder](result.py#L1802)**

````python
Test function with builder.

Returns:
    TODO.
````

</details>

<details><summary>function_with_builder.Product.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.parts. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_builder.Product.__init__](../../../../fixtures/typed.py#L2614)**

````python
Initialize product with parts.

Args:
    parts (SequenceStr): TODO.
````

**[Produced: function_with_builder.Product.__init__](result.py#L1812)**

````python
Initialize product with parts.

Args:
    parts: TODO.
````

</details>

<details><summary>function_with_builder.Builder.__init__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_builder.Builder.__init__](../../../../fixtures/typed.py#L2626)**

````python
TODO.
````

</details>

<details><summary>function_with_builder.Builder.add_part — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_builder.Builder.add_part](../../../../fixtures/typed.py#L2630)**

````python
TODO.

Args:
    part (str): TODO.

Returns:
    Self: TODO.
````

</details>

<details><summary>function_with_builder.Builder.build — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_builder.Builder.build](../../../../fixtures/typed.py#L2643)**

````python
TODO.

Returns:
    Product: TODO.
````

</details>

<details><summary>function_with_observer — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_observer](../../../../fixtures/typed.py#L2655)**

````python
Test function with observer.

Returns:
    TupleTypeObjectVariadic: TODO.
````

**[Produced: function_with_observer](result.py#L1836)**

````python
Test function with observer.

Returns:
    TODO.
````

</details>

<details><summary>function_with_observer.Observer.update — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.message. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_observer.Observer.update](../../../../fixtures/typed.py#L2666)**

````python
Update observer with message.

Args:
    message (str): TODO.
````

**[Produced: function_with_observer.Observer.update](result.py#L1846)**

````python
Update observer with message.

Args:
    message: TODO.
````

</details>

<details><summary>function_with_observer.Subject.attach — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.observer. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_observer.Subject.attach](../../../../fixtures/typed.py#L2682)**

````python
Attach observer to subject.

Args:
    observer (SupportsUpdate): TODO.
````

**[Produced: function_with_observer.Subject.attach](result.py#L1861)**

````python
Attach observer to subject.

Args:
    observer: TODO.
````

</details>

<details><summary>function_with_observer.Subject.notify — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.message. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_observer.Subject.notify](../../../../fixtures/typed.py#L2691)**

````python
Notify all observers with message.

Args:
    message (str): TODO.
````

**[Produced: function_with_observer.Subject.notify](result.py#L1869)**

````python
Notify all observers with message.

Args:
    message: TODO.
````

</details>

<details><summary>function_with_strategy — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_strategy](../../../../fixtures/typed.py#L2704)**

````python
Test function with strategy.

Returns:
    TupleTypeObjectVariadic: TODO.
````

**[Produced: function_with_strategy](result.py#L1881)**

````python
Test function with strategy.

Returns:
    TODO.
````

</details>

<details><summary>function_with_command — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_command](../../../../fixtures/typed.py#L2766)**

````python
Test function with command.

Returns:
    TupleTypeObjectVariadic: TODO.
````

**[Produced: function_with_command](result.py#L1937)**

````python
Test function with command.

Returns:
    TODO.
````

</details>

<details><summary>function_with_command.ConcreteCommand.__init__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_command.ConcreteCommand.__init__](../../../../fixtures/typed.py#L2795)**

````python
TODO.

Args:
    receiver (SupportsAction): TODO.
````

</details>

<details><summary>function_with_command.ConcreteCommand.execute — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_command.ConcreteCommand.execute](../../../../fixtures/typed.py#L2805)**

````python
TODO.
````

</details>

<details><summary>function_with_chain_of_responsibility — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_chain_of_responsibility](../../../../fixtures/typed.py#L2812)**

````python
Test function with chain of responsibility.

Returns:
    TypeObject: TODO.
````

**[Produced: function_with_chain_of_responsibility](result.py#L1973)**

````python
Test function with chain of responsibility.

Returns:
    TODO.
````

</details>

<details><summary>function_with_chain_of_responsibility.Handler.set_next — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.handler, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_chain_of_responsibility.Handler.set_next](../../../../fixtures/typed.py#L2827)**

````python
Set next handler.

Args:
    handler (Handler): TODO.

Returns:
    Handler: TODO.
````

**[Produced: function_with_chain_of_responsibility.Handler.set_next](result.py#L1987)**

````python
Set next handler.

Args:
    handler: TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_chain_of_responsibility.Handler.handle — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.request, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_chain_of_responsibility.Handler.handle](../../../../fixtures/typed.py#L2840)**

````python
Handle request.

Args:
    request (str): TODO.

Returns:
    StrOrNone: TODO.
````

**[Produced: function_with_chain_of_responsibility.Handler.handle](result.py#L1999)**

````python
Handle request.

Args:
    request: TODO.

Returns:
    None: TODO.
````

</details>

<details><summary>function_with_decorator_stack — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_decorator_stack](../../../../fixtures/typed.py#L2857)**

````python
Test function with decorator stack.

Returns:
    CallableStr: TODO.
````

**[Produced: function_with_decorator_stack](result.py#L2015)**

````python
Test function with decorator stack.

Returns:
    Callable[[], str]: TODO.
````

</details>

<details><summary>function_with_decorator_stack.decorator1 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.func, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_decorator_stack.decorator1](../../../../fixtures/typed.py#L2865)**

````python
Test decorator 1.

Args:
    func (CallableParametersToResult[P, R]): TODO.

Returns:
    CallableParametersToResult[P, R]: TODO.
````

**[Produced: function_with_decorator_stack.decorator1](result.py#L2022)**

````python
Test decorator 1.

Args:
    func: TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_decorator_stack.decorator1.wrapper — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.args, parameters.kwargs, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_decorator_stack.decorator1.wrapper](../../../../fixtures/typed.py#L2879)**

````python
Wrap decorator 1.

Args:
    args (P.args): TODO.
    kwargs (P.kwargs): TODO.

Returns:
    R: TODO.
````

**[Produced: function_with_decorator_stack.decorator1.wrapper](result.py#L2033)**

````python
Wrap decorator 1.

Args:
    args: TODO.
    kwargs: TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_decorator_stack.decorator2 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.func, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_decorator_stack.decorator2](../../../../fixtures/typed.py#L2894)**

````python
Test decorator 2.

Args:
    func (CallableParametersToResult[P, R]): TODO.

Returns:
    CallableParametersToResult[P, R]: TODO.
````

**[Produced: function_with_decorator_stack.decorator2](result.py#L2047)**

````python
Test decorator 2.

Args:
    func: TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_decorator_stack.decorator2.wrapper — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.args, parameters.kwargs, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_decorator_stack.decorator2.wrapper](../../../../fixtures/typed.py#L2908)**

````python
Wrap decorator 2.

Args:
    args (P.args): TODO.
    kwargs (P.kwargs): TODO.

Returns:
    R: TODO.
````

**[Produced: function_with_decorator_stack.decorator2.wrapper](result.py#L2058)**

````python
Wrap decorator 2.

Args:
    args: TODO.
    kwargs: TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_partial — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_partial](../../../../fixtures/typed.py#L2937)**

````python
Test function with partial.

Returns:
    CallableIntInt: TODO.
````

**[Produced: function_with_partial](result.py#L2086)**

````python
Test function with partial.

Returns:
    Callable[[int], int]: TODO.
````

</details>

<details><summary>function_with_partial.multiply — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.a, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_partial.multiply](../../../../fixtures/typed.py#L2945)**

````python
Test multiply function.

Args:
    a (int): TODO.
    b (int): TODO.

Returns:
    int: TODO.
````

**[Produced: function_with_partial.multiply](result.py#L2093)**

````python
Test multiply function.

Args:
    a (T4): TODO.
    b (int): TODO.

Returns:
    T4: TODO.
````

</details>

<details><summary>function_with_groupby — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_groupby](../../../../fixtures/typed.py#L2972)**

````python
Test function with groupby.

Returns:
    DictListInt: TODO.
````

**[Produced: function_with_groupby](result.py#L2118)**

````python
Test function with groupby.

Returns:
    TODO.
````

</details>

<details><summary>function_with_permutations_combinations — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_permutations_combinations](../../../../fixtures/typed.py#L2986)**

````python
Test function with permutations and combinations.

Returns:
    TupleListTupleIntVariadicVariadic: TODO.
````

**[Produced: function_with_permutations_combinations](result.py#L2131)**

````python
Test function with permutations and combinations.

Returns:
    TODO.
````

</details>

<details><summary>function_with_defaultdict — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_defaultdict](../../../../fixtures/typed.py#L3001)**

````python
Test function with defaultdict.

Returns:
    DefaultdictStrInt: TODO.
````

**[Produced: function_with_defaultdict](result.py#L2143)**

````python
Test function with defaultdict.

Returns:
    defaultdict[str, int]: TODO.
````

</details>

<details><summary>function_with_counter — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_counter](../../../../fixtures/typed.py#L3014)**

````python
Test function with counter.

Returns:
    CounterInt: TODO.
````

**[Produced: function_with_counter](result.py#L2155)**

````python
Test function with counter.

Returns:
    Counter[int]: TODO.
````

</details>

<details><summary>function_with_deque — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_deque](../../../../fixtures/typed.py#L3024)**

````python
Test function with deque.

Returns:
    DequeInt: TODO.
````

**[Produced: function_with_deque](result.py#L2164)**

````python
Test function with deque.

Returns:
    list[int]: TODO.
````

</details>

<details><summary>function_with_ordereddict — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_ordereddict](../../../../fixtures/typed.py#L3039)**

````python
Test function with ordereddict.

Returns:
    OrderedDictStrInt: TODO.
````

**[Produced: function_with_ordereddict](result.py#L2178)**

````python
Test function with ordereddict.

Returns:
    OrderedDict[str, int]: TODO.
````

</details>

<details><summary>function_with_namedtuple — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_namedtuple](../../../../fixtures/typed.py#L3049)**

````python
Test function with namedtuple.

Returns:
    Point: TODO.
````

**[Produced: function_with_namedtuple](result.py#L2187)**

````python
Test function with namedtuple.

Returns:
    TODO.
````

</details>

<details><summary>Point — changed</summary>

Missing fields: attributes.x, attributes.y. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: Point](../../../../fixtures/typed.py#L3059)**

````python
Test point.

Attributes:
    x (int): TODO.
    y (int): TODO.
````

**[Produced: Point](result.py#L2196)**

````python
Test point.
````

</details>

<details><summary>function_with_chain — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_chain](../../../../fixtures/typed.py#L3072)**

````python
Test function with chain.

Returns:
    ListInt: TODO.
````

**[Produced: function_with_chain](result.py#L2210)**

````python
Test function with chain.

Returns:
    list[int]: TODO.
````

</details>

<details><summary>function_with_islice — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_islice](../../../../fixtures/typed.py#L3084)**

````python
Test function with islice.

Returns:
    ListInt: TODO.
````

**[Produced: function_with_islice](result.py#L2221)**

````python
Test function with islice.

Returns:
    list[int]: TODO.
````

</details>

<details><summary>function_with_takewhile_dropwhile — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_takewhile_dropwhile](../../../../fixtures/typed.py#L3095)**

````python
Test function with takewhile and dropwhile.

Returns:
    TupleListIntVariadic: TODO.
````

**[Produced: function_with_takewhile_dropwhile](result.py#L2231)**

````python
Test function with takewhile and dropwhile.

Returns:
    tuple[list[int], list[int]]: TODO.
````

</details>

<details><summary>function_with_zip_longest — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_zip_longest](../../../../fixtures/typed.py#L3110)**

````python
Test function with zip longest.

Returns:
    ListTupleIntOrNoneStrOrNone: TODO.
````

**[Produced: function_with_zip_longest](result.py#L2243)**

````python
Test function with zip longest.

Returns:
    TODO.
````

</details>

<details><summary>function_with_product — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_product](../../../../fixtures/typed.py#L3122)**

````python
Test function with product.

Returns:
    ListTupleIntStr: TODO.
````

**[Produced: function_with_product](result.py#L2254)**

````python
Test function with product.

Returns:
    list[tuple[int, str]]: TODO.
````

</details>

<details><summary>function_with_compress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_compress](../../../../fixtures/typed.py#L3155)**

````python
Test function with compress.

Returns:
    ListInt: TODO.
````

**[Produced: function_with_compress](result.py#L2265)**

````python
Test function with compress.

Returns:
    TODO.
````

</details>

<details><summary>function_with_accumulate — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_accumulate](../../../../fixtures/typed.py#L3167)**

````python
Test function with accumulate.

Returns:
    ListInt: TODO.
````

**[Produced: function_with_accumulate](result.py#L2276)**

````python
Test function with accumulate.

Returns:
    TODO.
````

</details>

<details><summary>function_with_conditional_output — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_conditional_output](../../../../fixtures/typed.py#L3178)**

````python
Test function with conditions, globals, and conditional output type.

Args:
    value (int): TODO.
    mode (str): TODO.

Returns:
    ListIntOrDictIntOrStrOrInt: TODO.
````

**[Produced: function_with_conditional_output](result.py#L2286)**

````python
Test function with conditions, globals, and conditional output type.

Args:
    value (int): TODO.
    mode (str): TODO.

Returns:
    int | str | dict[str, int] | list[int]: TODO.
````

</details>

<details><summary>test_function_calls_part1 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_function_calls_part1](../../../../fixtures/typed.py#L3201)**

````python
Test basic function calls with kwargs where possible.

Returns:
    TestCallsPart1: TODO.
````

**[Produced: test_function_calls_part1](result.py#L2305)**

````python
Test basic function calls with kwargs where possible.

Returns:
    TODO.
````

</details>

<details><summary>test_function_calls_part2 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_function_calls_part2](../../../../fixtures/typed.py#L3271)**

````python
Test intermediate function calls with kwargs where possible.

Returns:
    TestCallsPart2: TODO.
````

**[Produced: test_function_calls_part2](result.py#L2359)**

````python
Test intermediate function calls with kwargs where possible.

Returns:
    TODO.
````

</details>

<details><summary>test_function_calls_part3 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_function_calls_part3](../../../../fixtures/typed.py#L3329)**

````python
Test advanced function calls with kwargs where possible.

Returns:
    TestCallsPart3: TODO.
````

**[Produced: test_function_calls_part3](result.py#L2414)**

````python
Test advanced function calls with kwargs where possible.

Returns:
    TODO.
````

</details>

<details><summary>test_function_calls — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_function_calls](../../../../fixtures/typed.py#L3398)**

````python
Test various function calls with kwargs where possible.

Returns:
    TestCallsResult: TODO.
````

**[Produced: test_function_calls](result.py#L2468)**

````python
Test various function calls with kwargs where possible.

Returns:
    TODO.
````

</details>

<details><summary>test_class_instantiations — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_class_instantiations](../../../../fixtures/typed.py#L3412)**

````python
Test class instantiations with kwargs where possible.

Returns:
    ClassInstantiationResults: TODO.
````

**[Produced: test_class_instantiations](result.py#L2481)**

````python
Test class instantiations with kwargs where possible.

Returns:
    dict[
            str,
            BaseClass | DataClassExample | DecoratedClass | DerivedClass |
            MetaDecoratedClass
        ]:
        TODO.
````

</details>

<details><summary>test_other_operations — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_other_operations](../../../../fixtures/typed.py#L3429)**

````python
Test enum, closure, context, and vector operations.

Returns:
    OtherOperationResults: TODO.
````

**[Produced: test_other_operations](result.py#L2502)**

````python
Test enum, closure, context, and vector operations.

Returns:
    dict[str, str | EnumClass]: TODO.
````

</details>

<details><summary>SliceExampleResult — changed</summary>

Missing fields: attributes.dict_key_slice, attributes.dict_slice, attributes.dict_value_slice, attributes.list_slice, attributes.list_stride_slice. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: SliceExampleResult](../../../../fixtures/typed.py#L3455)**

````python
Result for list and dictionary slice inference examples.

Attributes:
    list_slice (ListInt): TODO.
    list_stride_slice (ListInt): TODO.
    dict_slice (DictInt): TODO.
    dict_key_slice (ListStr): TODO.
    dict_value_slice (ListInt): TODO.
````

**[Produced: SliceExampleResult](result.py#L2525)**

````python
Result for list and dictionary slice inference examples.
````

</details>

<details><summary>CustomAdder.add — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.element. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: CustomAdder.add](../../../../fixtures/typed.py#L3531)**

````python
Return an arithmetic result instead of mutating a set.

Args:
    element (int): TODO.

Returns:
    int: TODO.
````

**[Produced: CustomAdder.add](result.py#L2631)**

````python
Return an arithmetic result instead of mutating a set.

Args:
    element (SupportsRadd): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>ImportExampleResult — changed</summary>

Missing fields: attributes.dunder_module_name, attributes.imported_join_result, attributes.importlib_module_name. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: ImportExampleResult](../../../../fixtures/typed.py#L3544)**

````python
Result for importlib and ``__import__`` inference examples.

Attributes:
    importlib_module_name (str): TODO.
    dunder_module_name (str): TODO.
    imported_join_result (str): TODO.
````

**[Produced: ImportExampleResult](result.py#L2643)**

````python
Result for importlib and ``__import__`` inference examples.
````

</details>

<details><summary>RedefinitionResult — changed</summary>

Missing fields: attributes.first_type_value, attributes.second_type_value, attributes.third_type_value, attributes.union_final_value. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: RedefinitionResult](../../../../fixtures/typed.py#L3559)**

````python
Result for variable type redefinition examples.

Attributes:
    first_type_value (int): TODO.
    second_type_value (str): TODO.
    third_type_value (ListInt): TODO.
    union_final_value (DictInt): TODO.
````

**[Produced: RedefinitionResult](result.py#L2664)**

````python
Result for variable type redefinition examples.
````

</details>

<details><summary>ScopeResolutionResult — changed</summary>

Missing fields: attributes.class_value, attributes.inner_value, attributes.method_and_nested_results, attributes.module_value, attributes.outer_value. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: ScopeResolutionResult](../../../../fixtures/typed.py#L3576)**

````python
Result for same names in nested, class, and module scopes.

Attributes:
    module_value (str): TODO.
    outer_value (int): TODO.
    inner_value (ListInt): TODO.
    class_value (str): TODO.
    method_and_nested_results (ListValue[float | str]): TODO.
````

**[Produced: ScopeResolutionResult](result.py#L2688)**

````python
Result for same names in nested, class, and module scopes.
````

</details>

<details><summary>duplicate_scope_name — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: duplicate_scope_name](../../../../fixtures/typed.py#L3595)**

````python
Module-scope function intentionally reused in inner scopes.

Args:
    value (str): TODO.

Returns:
    str: TODO.
````

**[Produced: duplicate_scope_name](result.py#L2715)**

````python
Module-scope function intentionally reused in inner scopes.

Args:
    value: TODO.

Returns:
    str: TODO.
````

</details>

<details><summary>function_with_builtin_name_collisions — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_builtin_name_collisions](../../../../fixtures/typed.py#L3636)**

````python
Disambiguate builtin method names from custom method names.

Returns:
    TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt: TODO.
````

**[Produced: function_with_builtin_name_collisions](result.py#L2749)**

````python
Disambiguate builtin method names from custom method names.

Returns:
    tuple[BuiltinMethodList, BuiltinMethodDict, CustomAddSet, int]: TODO.
````

</details>

<details><summary>function_with_scope_resolution.duplicate_scope_name.deepest — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_scope_resolution.duplicate_scope_name.deepest](../../../../fixtures/typed.py#L3730)**

````python
Return the innermost variable with the reused name.

Returns:
    ListInt: TODO.
````

**[Produced: function_with_scope_resolution.duplicate_scope_name.deepest](result.py#L2833)**

````python
Return the innermost variable with the reused name.

Returns:
    TODO.
````

</details>

<details><summary>function_with_scope_resolution.DuplicateScopeNameClass — changed</summary>

Missing fields: attributes.duplicated_name. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_scope_resolution.DuplicateScopeNameClass](../../../../fixtures/typed.py#L3741)**

````python
Class with same conceptual name family as outer symbols.

Attributes:
    duplicated_name (str): TODO.
````

**[Produced: function_with_scope_resolution.DuplicateScopeNameClass](result.py#L2843)**

````python
Class with same conceptual name family as outer symbols.
````

</details>

<details><summary>test_new_inference_edge_cases — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_new_inference_edge_cases](../../../../fixtures/typed.py#L3773)**

````python
Run extra tests for slices, builtins, imports, and scoping.

Returns:
    NewInferenceResults: TODO.
````

**[Produced: test_new_inference_edge_cases](result.py#L2882)**

````python
Run extra tests for slices, builtins, imports, and scoping.

Returns:
    dict[
            str,
            ImportExampleResult | RedefinitionResult |
            ScopeResolutionResult | SliceExampleResult | list[int] |
            tuple[BuiltinMethodList, BuiltinMethodDict, CustomAddSet, int]
        ]:
        TODO.
````

</details>

<details><summary>ExtendedResult — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: summary. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: ExtendedResult](../../../../fixtures/typed.py#L3800)**

````python
Tiny tuple-like result container preserving its payload type.
````

**[Produced: ExtendedResult](result.py#L2914)**

````python
Tiny tuple-like result container intentionally left untyped.
````

</details>

<details><summary>ExtendedResult.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.metadata, parameters.payload. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: ExtendedResult.__init__](../../../../fixtures/typed.py#L3803)**

````python
Store a name, payload, and metadata mapping.

Args:
    name (str): TODO.
    payload (PayloadT): TODO.
    metadata (DictObjectOrNone): TODO.
````

**[Produced: ExtendedResult.__init__](result.py#L2917)**

````python
Store a name, payload, and metadata mapping.

Args:
    name (str): TODO.
    payload (list[int]): TODO.
    metadata: TODO.
````

</details>

<details><summary>ExtendedResult.__iter__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: yields.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: ExtendedResult.__iter__](../../../../fixtures/typed.py#L3821)**

````python
Iterate over stored fields.

Yields:
    ValueOrOther[StrOrValue[PayloadT], DictObject]: TODO.
````

**[Produced: ExtendedResult.__iter__](result.py#L2929)**

````python
Iterate over stored fields.

Yields:
    TODO.
````

</details>

<details><summary>ExtendedResult.__getitem__#definition:5 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedResult.__getitem__#definition:5](../../../../fixtures/typed.py#L3861)**

````python
Return one field by index or name.

Args:
    index (IntOrStr): TODO.

Returns:
    ValueOrOther[StrOrValue[PayloadT], DictObject]: TODO.

Raises:
    IndexError: TODO.
````

</details>

<details><summary>ExtendedDataclassStress.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.flags, parameters.lookup, parameters.values. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: ExtendedDataclassStress.__init__](../../../../fixtures/typed.py#L3890)**

````python
Initialize values without leaking mutable defaults.

Args:
    name (str): TODO.
    values (ListInt | None): TODO.
    lookup (DictInt | None): TODO.
    flags (SetBool | None): TODO.
````

**[Produced: ExtendedDataclassStress.__init__](result.py#L2972)**

````python
Initialize values without leaking mutable defaults.

Args:
    name (str): TODO.
    values: TODO.
    lookup: TODO.
    flags (set[bool]): TODO.
````

</details>

<details><summary>DescriptorWithOwnerCache — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: summary. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: DescriptorWithOwnerCache](../../../../fixtures/typed.py#L3917)**

````python
Weakly keyed descriptor that preserves its stored value type.
````

**[Produced: DescriptorWithOwnerCache](result.py#L2996)**

````python
Descriptor using WeakKeyDictionary to stress descriptor inference.
````

</details>

<details><summary>DescriptorWithOwnerCache.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.default. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: DescriptorWithOwnerCache.__init__](../../../../fixtures/typed.py#L3920)**

````python
Initialize descriptor storage.

Args:
    default (ValueT): TODO.
````

**[Produced: DescriptorWithOwnerCache.__init__](result.py#L2999)**

````python
Initialize descriptor storage.

Args:
    default (int | str): TODO.
````

</details>

<details><summary>DescriptorWithOwnerCache.__set_name__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.owner. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: DescriptorWithOwnerCache.__set_name__](../../../../fixtures/typed.py#L3932)**

````python
Store the owner/name pair.

Args:
    owner (TypeObject): TODO.
    name (str): TODO.
````

**[Produced: DescriptorWithOwnerCache.__set_name__](result.py#L3008)**

````python
Store the owner/name pair.

Args:
    owner: TODO.
    name (str): TODO.
````

</details>

<details><summary>DescriptorWithOwnerCache.__get__#definition:3 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DescriptorWithOwnerCache.__get__#definition:3](../../../../fixtures/typed.py#L3957)**

````python
Return descriptor or stored instance value.

Args:
    instance (ObjectOrNone): TODO.
    owner (TypeObjectOrNone): TODO.

Returns:
    ValueT | Self: TODO.
````

</details>

<details><summary>DescriptorWithOwnerCache.__set__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.instance, parameters.value. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: DescriptorWithOwnerCache.__set__](../../../../fixtures/typed.py#L3977)**

````python
Set a value in weak storage.

Args:
    instance (object): TODO.
    value (ValueT): TODO.
````

**[Produced: DescriptorWithOwnerCache.__set__](result.py#L3032)**

````python
Set a value in weak storage.

Args:
    instance: TODO.
    value: TODO.
````

</details>

<details><summary>DescriptorWithOwnerCache.__delete__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.instance. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: DescriptorWithOwnerCache.__delete__](../../../../fixtures/typed.py#L3987)**

````python
Delete value if present.

Args:
    instance (object): TODO.
````

**[Produced: DescriptorWithOwnerCache.__delete__](result.py#L3041)**

````python
Delete value if present.

Args:
    instance: TODO.
````

</details>

<details><summary>DescriptorSummary — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DescriptorSummary](../../../../fixtures/typed.py#L3998)**

````python
Cached descriptor value snapshot.
````

</details>

<details><summary>DescriptorStressOwner — changed</summary>

Missing fields: attributes.label, attributes.score. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: DescriptorStressOwner](../../../../fixtures/typed.py#L4005)**

````python
Owner class for descriptor stress.

Attributes:
    score (DescriptorWithOwnerCacheInt): TODO.
    label (DescriptorWithOwnerCache[str]): TODO.
````

**[Produced: DescriptorStressOwner](result.py#L3051)**

````python
Owner class for descriptor stress.
````

</details>

<details><summary>DescriptorStressOwner.summary — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: DescriptorStressOwner.summary](../../../../fixtures/typed.py#L4033)**

````python
Return cached mixed summary.

Returns:
    DescriptorSummary: TODO.
````

**[Produced: DescriptorStressOwner.summary](result.py#L3068)**

````python
Return cached mixed summary.

Returns:
    TODO.
````

</details>

<details><summary>RegistryMeta — changed</summary>

Missing fields: attributes.registry. Additional fields: none. Changed fields: none. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: RegistryMeta](../../../../fixtures/typed.py#L4043)**

````python
Metaclass that registers subclasses and injects attributes.

Attributes:
    registry (DictRegistryMeta): TODO.
````

**[Produced: RegistryMeta](result.py#L3077)**

````python
Metaclass that registers subclasses and injects attributes.
````

</details>

<details><summary>RegistryMeta.__new__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters._kwargs, parameters.bases, parameters.mcls, parameters.namespace, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: RegistryMeta.__new__](../../../../fixtures/typed.py#L4053)**

````python
Create class and register it by lower-case name.

Args:
    mcls (TypeValue[RegistryMeta]): TODO.
    name (str): TODO.
    bases (TupleTypeObjectVariadic): TODO.
    namespace (DictObject): TODO.
    _kwargs (object): TODO.

Returns:
    RegistryMeta: TODO.
````

**[Produced: RegistryMeta.__new__](result.py#L3082)**

````python
Create class and register it by lower-case name.

Args:
    mcls: TODO.
    name (str): TODO.
    bases: TODO.
    namespace: TODO.
    _kwargs: TODO.

Returns:
    TODO.
````

</details>

<details><summary>RegistryMeta.__call__ — changed</summary>

Missing fields: parameters.kwargs. Additional fields: parameters._kwargs. Changed fields: parameters.args, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: RegistryMeta.__call__](../../../../fixtures/typed.py#L4080)**

````python
Create instance and mark it.

Args:
    args (object): TODO.
    kwargs (object): TODO.

Returns:
    InstanceT: TODO.
````

**[Produced: RegistryMeta.__call__](result.py#L3103)**

````python
Create instance and mark it.

Args:
    args: TODO.
    _kwargs: TODO.

Returns:
    TODO.
````

</details>

<details><summary>RegistryBase.clone — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.overrides, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: RegistryBase.clone](../../../../fixtures/typed.py#L4105)**

````python
Clone using the current instance dictionary.

Args:
    overrides (object): TODO.

Returns:
    Self: TODO.
````

**[Produced: RegistryBase.clone](result.py#L3121)**

````python
Clone using the current instance dictionary.

Args:
    overrides: TODO.

Returns:
    TODO.
````

</details>

<details><summary>RegistryItem.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.extras, parameters.tags. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: RegistryItem.__init__](../../../../fixtures/typed.py#L4123)**

````python
Initialize with optional tags and arbitrary extras.

Args:
    name (str): TODO.
    count (int): TODO.
    tags (ListStr | None): TODO.
    extras (object): TODO.
````

**[Produced: RegistryItem.__init__](result.py#L3138)**

````python
Initialize with optional tags and arbitrary extras.

Args:
    name (str): TODO.
    count (int): TODO.
    tags: TODO.
    extras: TODO.
````

</details>

<details><summary>FluentBuilder.configure — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.options. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: FluentBuilder.configure](../../../../fixtures/typed.py#L4181)**

````python
Merge options and return self.

Args:
    options (object): TODO.

Returns:
    Self: TODO.
````

**[Produced: FluentBuilder.configure](result.py#L3187)**

````python
Merge options and return self.

Args:
    options: TODO.

Returns:
    Self: TODO.
````

</details>

<details><summary>FluentBuilder.build#definition:4 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: FluentBuilder.build#definition:4](../../../../fixtures/typed.py#L4207)**

````python
Return a compact string or a structured result.

Args:
    compact (bool): TODO.

Returns:
    StrOrBuilderStructured: TODO.
````

</details>

<details><summary>HybridContainer — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: summary. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: HybridContainer](../../../../fixtures/typed.py#L4222)**

````python
Typed positional and named storage with distinct element types.
````

**[Produced: HybridContainer](result.py#L3213)**

````python
Container exposing list-like and dict-like operations.
````

</details>

<details><summary>HybridContainer.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.items, parameters.named. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: HybridContainer.__init__](../../../../fixtures/typed.py#L4225)**

````python
Initialize mixed storage.

Args:
    items (ItemT): TODO.
    named (NamedT): TODO.
````

**[Produced: HybridContainer.__init__](result.py#L3216)**

````python
Initialize mixed storage.

Args:
    items: TODO.
    named: TODO.
````

</details>

<details><summary>HybridContainer.__iter__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: HybridContainer.__iter__](../../../../fixtures/typed.py#L4236)**

````python
Iterate over positional items.

Returns:
    Iterator[ItemT]: TODO.
````

**[Produced: HybridContainer.__iter__](result.py#L3226)**

````python
Iterate over positional items.

Returns:
    TODO.
````

</details>

<details><summary>HybridContainer.__contains__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.item. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: HybridContainer.__contains__](../../../../fixtures/typed.py#L4245)**

````python
Check both positional and named storage.

Args:
    item (object): TODO.

Returns:
    bool: TODO.
````

**[Produced: HybridContainer.__contains__](result.py#L3234)**

````python
Check both positional and named storage.

Args:
    item: TODO.

Returns:
    bool: TODO.
````

</details>

<details><summary>HybridContainer.__getitem__#definition:3 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: HybridContainer.__getitem__#definition:3](../../../../fixtures/typed.py#L4263)**

````python
Return item by int index or dict key.

Args:
    key (IntOrStr): TODO.

Returns:
    ValueOrOther[ItemT, NamedT]: TODO.
````

</details>

<details><summary>HybridContainer.__setitem__#definition:3 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: HybridContainer.__setitem__#definition:3](../../../../fixtures/typed.py#L4283)**

````python
Set item by int index or dict key.

Args:
    key (IntOrStr): TODO.
    value (ValueOrOther[ItemT, NamedT]): TODO.
````

</details>

<details><summary>HybridContainer.__or__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.other, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: HybridContainer.__or__](../../../../fixtures/typed.py#L4298)**

````python
Merge with another container or mapping.

Args:
    other (ValueOrOther[ HybridContainer[ItemT, NamedT], MappingValueToResult[str, NamedT] ]): TODO.

Returns:
    Self: TODO.
````

**[Produced: HybridContainer.__or__](result.py#L3270)**

````python
Merge with another container or mapping.

Args:
    other: TODO.

Returns:
    TODO.
````

</details>

<details><summary>CallableObject.__call__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: CallableObject.__call__](../../../../fixtures/typed.py#L4334)**

````python
Return different types based on mode.

Args:
    value (ValueT): TODO.
    scale (int): TODO.

Returns:
    IntOrStr | CallablePayload[ValueT]: TODO.
````

**[Produced: CallableObject.__call__](result.py#L3299)**

````python
Return different types based on mode.

Args:
    value (int): TODO.
    scale (int): TODO.

Returns:
    int | str | dict[str, int]: TODO.
````

</details>

<details><summary>AsyncResource.__init__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.name. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: AsyncResource.__init__](../../../../fixtures/typed.py#L4360)**

````python
Initialize resource.

Args:
    name (str): TODO.
````

**[Produced: AsyncResource.__init__](result.py#L3319)**

````python
Initialize resource.

Args:
    name: TODO.
````

</details>

<details><summary>AsyncResource.__aenter__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: AsyncResource.__aenter__](../../../../fixtures/typed.py#L4370)**

````python
Enter async context.

Returns:
    Self: TODO.
````

**[Produced: AsyncResource.__aenter__](result.py#L3328)**

````python
Enter async context.

Returns:
    TODO.
````

</details>

<details><summary>AsyncResource.__aexit__ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.exc, parameters.exc_type, parameters.tb, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: AsyncResource.__aexit__](../../../../fixtures/typed.py#L4380)**

````python
Exit async context.

Args:
    exc_type (TypeValue[BaseException] | None): TODO.
    exc (BaseException | None): TODO.
    tb (object): TODO.

Returns:
    bool: TODO.
````

**[Produced: AsyncResource.__aexit__](result.py#L3337)**

````python
Exit async context.

Args:
    exc_type: TODO.
    exc: TODO.
    tb: TODO.

Returns:
    TODO.
````

</details>

<details><summary>AsyncResource.fetch — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: AsyncResource.fetch](../../../../fixtures/typed.py#L4401)**

````python
Return async payload.

Args:
    value (int): TODO.

Returns:
    AsyncPayload: TODO.
````

**[Produced: AsyncResource.fetch](result.py#L3351)**

````python
Return async payload.

Args:
    value: TODO.

Returns:
    TODO.
````

</details>

<details><summary>extended_sync_context — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.seed, yields.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: extended_sync_context](../../../../fixtures/typed.py#L4416)**

````python
Yield a mutable context dictionary.

Args:
    seed (int): TODO.

Yields:
    SyncContext: TODO.
````

**[Produced: extended_sync_context](result.py#L3365)**

````python
Yield a mutable context dictionary.

Args:
    seed: TODO.

Yields:
    TODO.
````

</details>

<details><summary>extended_async_context — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.seed, yields.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: extended_async_context](../../../../fixtures/typed.py#L4436)**

````python
Yield an async resource and mutate its events.

Args:
    seed (int): TODO.

Yields:
    AsyncResource: TODO.
````

**[Produced: extended_async_context](result.py#L3383)**

````python
Yield an async resource and mutate its events.

Args:
    seed: TODO.

Yields:
    TODO.
````

</details>

<details><summary>preserve_signature_decorator — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.func, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: preserve_signature_decorator](../../../../fixtures/typed.py#L4451)**

````python
Preserve arbitrary args and kwargs through a decorator.

Args:
    func (CallableParametersToResult[P, R]): TODO.

Returns:
    CallableParametersToResult[P, ValueOrListObject[R]]: TODO.
````

**[Produced: preserve_signature_decorator](result.py#L3397)**

````python
Preserve arbitrary args and kwargs through a decorator.

Args:
    func: TODO.

Returns:
    TODO.
````

</details>

<details><summary>preserve_signature_decorator.wrapper — missing</summary>

No generated artifact has this qualified identity.

**[Reference: preserve_signature_decorator.wrapper](../../../../fixtures/typed.py#L4465)**

````python
TODO.

Args:
    args (P.args): TODO.
    kwargs (P.kwargs): TODO.

Returns:
    ValueOrListObject[R]: TODO.
````

</details>

<details><summary>decorator_factory — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.prefix, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: decorator_factory](../../../../fixtures/typed.py#L4490)**

````python
Create a decorator factory changing string outputs.

Args:
    prefix (str): TODO.
    uppercase (bool): TODO.

Returns:
    CallableValueToResult[ CallableParametersToResult[P, object], CallableParametersToResult[P, str] ]: TODO.
````

**[Produced: decorator_factory](result.py#L3417)**

````python
Create a decorator factory changing string outputs.

Args:
    prefix: TODO.
    uppercase (bool): TODO.

Returns:
    TODO.
````

</details>

<details><summary>decorator_factory.decorate — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_factory.decorate](../../../../fixtures/typed.py#L4508)**

````python
TODO.

Args:
    func (CallableParametersToResult[P, object]): TODO.

Returns:
    CallableParametersToResult[P, str]: TODO.
````

</details>

<details><summary>decorator_factory.decorate.wrapper — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_factory.decorate.wrapper](../../../../fixtures/typed.py#L4522)**

````python
TODO.

Args:
    args (P.args): TODO.
    kwargs (P.kwargs): TODO.

Returns:
    str: TODO.
````

</details>

<details><summary>decorated_pipeline_value — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: decorated_pipeline_value](../../../../fixtures/typed.py#L4546)**

````python
Return decorated text.

Args:
    value (str): TODO.
    suffix (str): TODO.

Returns:
    str: TODO.
````

**[Produced: decorated_pipeline_value](result.py#L3444)**

````python
Return decorated text.

Args:
    value: TODO.
    suffix (str): TODO.

Returns:
    str: TODO.
````

</details>

<details><summary>singledispatch_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: singledispatch_stress](../../../../fixtures/typed.py#L4561)**

````python
Return the default singledispatch branch.

Args:
    value (object): TODO.

Returns:
    object: TODO.
````

**[Produced: singledispatch_stress](result.py#L3458)**

````python
Return the default singledispatch branch.

Args:
    value (int | str | list[int]): TODO.

Returns:
    dict[str, list[int] | int | str]: TODO.
````

</details>

<details><summary>_ — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: _](../../../../fixtures/typed.py#L4575)**

````python
Integer branch.

Args:
    value (int): TODO.

Returns:
    int: TODO.
````

**[Produced: _](result.py#L3471)**

````python
Integer branch.

Args:
    value (SupportsMultiplication): TODO.

Returns:
    TODO.
````

</details>

<details><summary>_#definition:2 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: _#definition:2](../../../../fixtures/typed.py#L4589)**

````python
Return the string branch.

Args:
    value (str): TODO.

Returns:
    str: TODO.
````

**[Produced: _#definition:2](result.py#L3490)**

````python
Return the string branch.

Args:
    value (SupportsUpper): TODO.

Returns:
    TODO.
````

</details>

<details><summary>cached_recursive_pair — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: cached_recursive_pair](../../../../fixtures/typed.py#L4603)**

````python
Return Fibonacci-like pair with recursion and cache.

Args:
    n (int): TODO.

Returns:
    TupleIntVariadic: TODO.
````

**[Produced: cached_recursive_pair](result.py#L3503)**

````python
Return Fibonacci-like pair with recursion and cache.

Args:
    n (int): TODO.

Returns:
    tuple[int, int]: TODO.
````

</details>

<details><summary>function_with_pattern_matching_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.value, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_pattern_matching_stress](../../../../fixtures/typed.py#L4620)**

````python
Exercise match/case inference across structural patterns.

Args:
    value (MappingStrObjectOrSequenceObjectOrNone): TODO.

Returns:
    TupleIntIntOrListObjectOrDictObjectOrStrOrObject: TODO.
````

**[Produced: function_with_pattern_matching_stress](result.py#L3519)**

````python
Exercise match/case inference across structural patterns.

Args:
    value (dict[str, list[int] | int | str]): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_chained_exceptions — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_chained_exceptions](../../../../fixtures/typed.py#L4687)**

````python
Exercise exception value types and chained exceptions.

Args:
    mode (str): TODO.

Returns:
    StrOrDictStr: TODO.

Raises:
    RuntimeError: TODO.
````

**[Produced: function_with_chained_exceptions](result.py#L3673)**

````python
Exercise exception value types and chained exceptions.

Args:
    mode (str): TODO.

Returns:
    str | dict[str, str]: TODO.

Raises:
    RuntimeError: TODO.
````

</details>

<details><summary>function_with_walrus_and_narrowing — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.records, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_walrus_and_narrowing](../../../../fixtures/typed.py#L4718)**

````python
Use walrus, truthiness, regex, and narrowing.

Args:
    records (SequenceValue[MappingStrObject]): TODO.

Returns:
    TupleDefaultdictStrIntListStr: TODO.
````

**[Produced: function_with_walrus_and_narrowing](result.py#L3543)**

````python
Use walrus, truthiness, regex, and narrowing.

Args:
    records (Iterable): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_recursive_containers — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_recursive_containers](../../../../fixtures/typed.py#L4751)**

````python
Create recursive containers and aliased references.

Args:
    seed (int): TODO.

Returns:
    RecursiveRoot: TODO.
````

**[Produced: function_with_recursive_containers](result.py#L3573)**

````python
Create recursive containers and aliased references.

Args:
    seed (int): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_numeric_tower — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.values, returns.0, summary. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_numeric_tower](../../../../fixtures/typed.py#L4771)**

````python
Mix int, float, string fallback, and math/operator functions.

Args:
    values (SequenceValue[IntOrFloat | str]): TODO.

Returns:
    TupleIntFloatVariadicListInt: TODO.
````

**[Produced: function_with_numeric_tower](result.py#L3590)**

````python
Mix int, float, complex, bool, and math/operator functions.

Args:
    values (list[float]): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_type_reassignment_maze — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.payload, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_type_reassignment_maze](../../../../fixtures/typed.py#L4794)**

````python
Stress linear reassignment across unrelated runtime shapes.

Args:
    flag (str): TODO.
    payload (PayloadT): TODO.

Returns:
    ValueOrNone[ ValueOrOther[ ValueOrOther[ (ValueOrOther[ValueOrOther[int, ListValue[ValueOrOther[PayloadT, str]]], dict[str, ValueOrOther[PayloadT, bool]]], TupleStrValue[PayloadT]) ], str, ] ]: TODO.
````

**[Produced: function_with_type_reassignment_maze](result.py#L3610)**

````python
Stress linear reassignment across unrelated runtime shapes.

Args:
    flag (str): TODO.
    payload (int | str): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_type_reassignment_maze.callback — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_type_reassignment_maze.callback](../../../../fixtures/typed.py#L4827)**

````python
TODO.

Args:
    item (str): TODO.

Returns:
    TupleStrValue[PayloadT]: TODO.
````

</details>

<details><summary>function_with_exception_group_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.values, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_exception_group_stress](../../../../fixtures/typed.py#L4843)**

````python
Exercise except* branches and collected errors.

Args:
    values (SequenceValue[IntOrNone]): TODO.

Returns:
    TupleListIntListStr: TODO.
````

**[Produced: function_with_exception_group_stress](result.py#L3703)**

````python
Exercise except* branches and collected errors.

Args:
    values (Iterable): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_exception_group_stress.raise_error_group — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_exception_group_stress.raise_error_group](../../../../fixtures/typed.py#L4856)**

````python
TODO.

Args:
    errors (ListException): TODO.

Raises:
    ExceptionGroup: TODO.
````

</details>

<details><summary>function_with_import_and_reflection_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_import_and_reflection_stress](../../../../fixtures/typed.py#L4888)**

````python
Import module dynamically and inspect attributes.

Args:
    module_name (str): TODO.
    attr_name (str): TODO.

Returns:
    DictObject: TODO.
````

**[Produced: function_with_import_and_reflection_stress](result.py#L3736)**

````python
Import module dynamically and inspect attributes.

Args:
    module_name (str): TODO.
    attr_name (str): TODO.

Returns:
    dict[str, bool | str]: TODO.
````

</details>

<details><summary>function_with_json_uuid_and_path_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_json_uuid_and_path_stress](../../../../fixtures/typed.py#L4913)**

````python
Exercise JSON, UUID, Path, and text round-tripping.

Args:
    tmp_name (str): TODO.

Returns:
    JSONRoundtrip: TODO.
````

**[Produced: function_with_json_uuid_and_path_stress](result.py#L3757)**

````python
Exercise JSON, UUID, Path, and text round-tripping.

Args:
    tmp_name (str): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_contextvars_and_chainmap — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.configs, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_contextvars_and_chainmap](../../../../fixtures/typed.py#L4936)**

````python
Use ContextVar and ChainMap layered lookup.

Args:
    configs (SequenceValue[MutableMappingStrObject]): TODO.

Returns:
    MappingStrObject: TODO.
````

**[Produced: function_with_contextvars_and_chainmap](result.py#L3775)**

````python
Use ContextVar and ChainMap layered lookup.

Args:
    configs (list[dict[str, int]]): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_iterable_unpacking_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.data, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_iterable_unpacking_stress](../../../../fixtures/typed.py#L4960)**

````python
Mix star-unpacking, zip, enumerate, and heterogeneous outputs.

Args:
    data (SequenceInt): TODO.

Returns:
    UnpackingStressResult: TODO.
````

**[Produced: function_with_iterable_unpacking_stress](result.py#L3794)**

````python
Mix star-unpacking, zip, enumerate, and heterogeneous outputs.

Args:
    data (list[int]): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_generator_send_throw_close — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_generator_send_throw_close](../../../../fixtures/typed.py#L4980)**

````python
Return a generator supporting send/throw/close interactions.

Args:
    limit (int): TODO.

Returns:
    TupleIntVariadicGeneratorIntIntOrStrOrNoneInt: TODO.
````

**[Produced: function_with_generator_send_throw_close](result.py#L3809)**

````python
Return a generator supporting send/throw/close interactions.

Args:
    limit (int): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_generator_send_throw_close.controlled_generator — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_generator_send_throw_close.controlled_generator](../../../../fixtures/typed.py#L4993)**

````python
TODO.

Yields:
    int: TODO.
````

</details>

<details><summary>function_with_property_and_descriptor_interaction — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_property_and_descriptor_interaction](../../../../fixtures/typed.py#L5018)**

````python
Use descriptor owner, cached property, deletion, and reset.

Returns:
    TupleDescriptorSummaryIntStr: TODO.
````

**[Produced: function_with_property_and_descriptor_interaction](result.py#L3837)**

````python
Use descriptor owner, cached property, deletion, and reset.

Returns:
    TODO.
````

</details>

<details><summary>function_with_metaclass_registry_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_metaclass_registry_stress](../../../../fixtures/typed.py#L5039)**

````python
Create registry instances and clone them.

Returns:
    TupleRegistryItemVariadicListStr: TODO.
````

**[Produced: function_with_metaclass_registry_stress](result.py#L3857)**

````python
Create registry instances and clone them.

Returns:
    TODO.
````

</details>

<details><summary>function_with_fluent_builder_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_fluent_builder_stress](../../../../fixtures/typed.py#L5060)**

````python
Use fluent builder and mixed finalization modes.

Returns:
    TupleBuilderStructuredStr: TODO.
````

**[Produced: function_with_fluent_builder_stress](result.py#L3870)**

````python
Use fluent builder and mixed finalization modes.

Returns:
    TODO.
````

</details>

<details><summary>function_with_hybrid_container_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_hybrid_container_stress](../../../../fixtures/typed.py#L5078)**

````python
Stress custom container protocols and operator overloads.

Returns:
    TupleHybridContainerIntOrFloatStrOrBoolOrListIntBoolListInt: TODO.
````

**[Produced: function_with_hybrid_container_stress](result.py#L3884)**

````python
Stress custom container protocols and operator overloads.

Returns:
    TODO.
````

</details>

<details><summary>function_with_callable_object_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_callable_object_stress](../../../../fixtures/typed.py#L5105)**

````python
Call stateful callable objects with keyword-only args.

Returns:
    TupleIntOrStrOrCallablePayloadIntIntOrStrOrCallablePayloadStrVariadic: TODO.
````

**[Produced: function_with_callable_object_stress](result.py#L3898)**

````python
Call stateful callable objects with keyword-only args.

Returns:
    TODO.
````

</details>

<details><summary>function_with_async_comprehension_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.values, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_async_comprehension_stress](../../../../fixtures/typed.py#L5122)**

````python
Use async context, async helper, and async comprehension.

Args:
    values (SequenceInt): TODO.

Returns:
    TupleAsyncPayloadListInt: TODO.
````

**[Produced: function_with_async_comprehension_stress](result.py#L3914)**

````python
Use async context, async helper, and async comprehension.

Args:
    values (list[int]): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_async_comprehension_stress.produce — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_async_comprehension_stress.produce](../../../../fixtures/typed.py#L5135)**

````python
TODO.

Yields:
    int: TODO.
````

</details>

<details><summary>SupportsApplyAndOffset — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsApplyAndOffset](../../../../fixtures/typed.py#L5152)**

````python
Protocol for local multiplier instances.

Attributes:
    offset (int): TODO.
````

</details>

<details><summary>SupportsApplyAndOffset.apply — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsApplyAndOffset.apply](../../../../fixtures/typed.py#L5162)**

````python
Apply multiplier.

Args:
    value (int): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>SupportsCallAndFromValues — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCallAndFromValues](../../../../fixtures/typed.py#L5175)**

````python
Protocol for local multiplier classes.
````

</details>

<details><summary>SupportsCallAndFromValues.__call__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCallAndFromValues.__call__](../../../../fixtures/typed.py#L5178)**

````python
Create a local multiplier.

Args:
    offset (int): TODO.

Returns:
    SupportsApplyAndOffset: TODO.
````

</details>

<details><summary>SupportsCallAndFromValues.from_values — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCallAndFromValues.from_values](../../../../fixtures/typed.py#L5190)**

````python
Create from values.

Args:
    values (SequenceInt): TODO.

Returns:
    SupportsApplyAndOffset: TODO.
````

</details>

<details><summary>function_with_local_class_closure_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_local_class_closure_stress](../../../../fixtures/typed.py#L5206)**

````python
Return a local class capturing outer state.

Args:
    multiplier (int): TODO.

Returns:
    SupportsCallAndFromValues: TODO.
````

**[Produced: function_with_local_class_closure_stress](result.py#L3935)**

````python
Return a local class capturing outer state.

Args:
    multiplier (int): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_local_class_closure_stress.LocalMultiplier.__init__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_local_class_closure_stress.LocalMultiplier.__init__](../../../../fixtures/typed.py#L5222)**

````python
TODO.

Args:
    offset (int): TODO.
````

</details>

<details><summary>function_with_local_class_closure_stress.LocalMultiplier.apply — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_local_class_closure_stress.LocalMultiplier.apply](../../../../fixtures/typed.py#L5231)**

````python
TODO.

Args:
    value (int): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>function_with_local_class_closure_stress.LocalMultiplier.from_values — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_local_class_closure_stress.LocalMultiplier.from_values](../../../../fixtures/typed.py#L5244)**

````python
TODO.

Args:
    values (SequenceInt): TODO.

Returns:
    Self: TODO.
````

</details>

<details><summary>function_with_nested_default_factories — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_nested_default_factories](../../../../fixtures/typed.py#L5259)**

````python
Build nested defaultdict structures.

Returns:
    TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic: TODO.
````

**[Produced: function_with_nested_default_factories](result.py#L3961)**

````python
Build nested defaultdict structures.

Returns:
    TODO.
````

</details>

<details><summary>function_with_sort_key_and_grouping_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.rows, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_sort_key_and_grouping_stress](../../../../fixtures/typed.py#L5285)**

````python
Sort/group by computed keys and return nested groups.

Args:
    rows (SequenceValue[GroupInput]): TODO.

Returns:
    TupleListNormalizedRowDictListInt: TODO.
````

**[Produced: function_with_sort_key_and_grouping_stress](result.py#L3982)**

````python
Sort/group by computed keys and return nested groups.

Args:
    rows (Iterable): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_partial_reduce_and_operator_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.numbers, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_partial_reduce_and_operator_stress](../../../../fixtures/typed.py#L5320)**

````python
Mix partial, reduce, and operator functions.

Args:
    numbers (SequenceInt): TODO.

Returns:
    TupleListIntIntVariadic: TODO.
````

**[Produced: function_with_partial_reduce_and_operator_stress](result.py#L4003)**

````python
Mix partial, reduce, and operator functions.

Args:
    numbers (list[int]): TODO.

Returns:
    tuple[list[int], int, int]: TODO.
````

</details>

<details><summary>function_with_protocol_like_runtime_checks — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.candidate, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_protocol_like_runtime_checks](../../../../fixtures/typed.py#L5339)**

````python
Infer from hasattr/callable runtime protocol checks.

Args:
    candidate (object): TODO.

Returns:
    object: TODO.
````

**[Produced: function_with_protocol_like_runtime_checks](result.py#L4019)**

````python
Infer from hasattr/callable runtime protocol checks.

Args:
    candidate (CallableObject | DescriptorStressOwner): TODO.

Returns:
    str | None: TODO.
````

</details>

<details><summary>function_with_deep_attribute_assignment — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_deep_attribute_assignment](../../../../fixtures/typed.py#L5365)**

````python
Assign attributes at several depths and return snapshots.

Returns:
    TupleSupportsMetadataAndNameVariadicNodeMetadata: TODO.
````

**[Produced: function_with_deep_attribute_assignment](result.py#L4038)**

````python
Assign attributes at several depths and return snapshots.

Returns:
    TODO.
````

</details>

<details><summary>function_with_deep_attribute_assignment.Node — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_deep_attribute_assignment.Node](../../../../fixtures/typed.py#L5375)**

````python
TODO.
````

</details>

<details><summary>function_with_deep_attribute_assignment.Node.__init__ — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_deep_attribute_assignment.Node.__init__](../../../../fixtures/typed.py#L5378)**

````python
TODO.

Args:
    name (str): TODO.
````

</details>

<details><summary>function_with_deep_attribute_assignment.Node.add — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_deep_attribute_assignment.Node.add](../../../../fixtures/typed.py#L5390)**

````python
TODO.

Args:
    child (Node): TODO.

Returns:
    Node: TODO.
````

</details>

<details><summary>function_with_bytes_memoryview_and_slices — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_bytes_memoryview_and_slices](../../../../fixtures/typed.py#L5411)**

````python
Exercise bytes, bytearray, memoryview, and slice inference.

Args:
    data (bytes): TODO.

Returns:
    TupleBytearrayMemoryviewBytesInt: TODO.
````

**[Produced: function_with_bytes_memoryview_and_slices](result.py#L4063)**

````python
Exercise bytes, bytearray, memoryview, and slice inference.

Args:
    data (bytes): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_map_filter_zip_stress — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.values, returns.0, summary. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_map_filter_zip_stress](../../../../fixtures/typed.py#L5431)**

````python
Use map/filter/zip pipelines with generator expressions.

Args:
    values (SequenceInt): TODO.

Returns:
    ListTupleIntVariadic: TODO.
````

**[Produced: function_with_map_filter_zip_stress](result.py#L4080)**

````python
Use map/filter/zip pipelines with lambdas.

Args:
    values (list[int]): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_composed_inner_functions — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_composed_inner_functions](../../../../fixtures/typed.py#L5449)**

````python
Compose inner functions where each narrows a value.

Args:
    seed (int): TODO.

Returns:
    DictInt: TODO.
````

**[Produced: function_with_composed_inner_functions](result.py#L4095)**

````python
Compose inner functions where each narrows a value.

Args:
    seed (int): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_composed_inner_functions.normalize — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_composed_inner_functions.normalize](../../../../fixtures/typed.py#L5460)**

````python
TODO.

Args:
    value (object): TODO.

Returns:
    str: TODO.
````

</details>

<details><summary>function_with_composed_inner_functions.tokenize — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_composed_inner_functions.tokenize](../../../../fixtures/typed.py#L5476)**

````python
TODO.

Args:
    value (object): TODO.

Returns:
    ListStr: TODO.
````

</details>

<details><summary>function_with_composed_inner_functions.score — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_composed_inner_functions.score](../../../../fixtures/typed.py#L5492)**

````python
TODO.

Args:
    tokens (SequenceStr): TODO.

Returns:
    DictInt: TODO.
````

</details>

<details><summary>function_with_mutable_default_like_pattern — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: parameters.store, parameters.value, returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_mutable_default_like_pattern](../../../../fixtures/typed.py#L5509)**

````python
Avoid mutable defaults while preserving accumulator type.

Args:
    value (ItemT): TODO.
    store (ValueOrNone[ListValue[ItemT]]): TODO.

Returns:
    tuple[(ListValue[ItemT], TupleValueVariadic[ItemT], set[ItemT])]: TODO.
````

**[Produced: function_with_mutable_default_like_pattern](result.py#L4127)**

````python
Avoid mutable defaults while preserving accumulator type.

Args:
    value (str): TODO.
    store (int | None): TODO.

Returns:
    TODO.
````

</details>

<details><summary>function_with_literal_mode_dispatch#definition:4 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_literal_mode_dispatch#definition:4](../../../../fixtures/typed.py#L5550)**

````python
Dispatch by string literal-like mode.

Args:
    mode (str): TODO.
    value (T): TODO.

Returns:
    ValueOrOther[ValueOrInt[T], str]: TODO.
````

</details>

<details><summary>function_with_complex_boolean_narrowing#definition:5 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_complex_boolean_narrowing#definition:5](../../../../fixtures/typed.py#L5604)**

````python
Exercise bool-op narrowing with dict/list/tuple/string paths.

Args:
    value (object): TODO.
    fallback (ObjectOrNone): TODO.

Returns:
    object: TODO.
````

</details>

<details><summary>function_with_extended_named_results — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: function_with_extended_named_results](../../../../fixtures/typed.py#L5629)**

````python
Return custom result objects and tuple-unpacking behavior.

Returns:
    TupleExtendedResultListIntStrIntBool: TODO.
````

**[Produced: function_with_extended_named_results](result.py#L4186)**

````python
Return custom result objects and tuple-unpacking behavior.

Returns:
    TODO.
````

</details>

<details><summary>test_extended_inference_edge_cases_part1 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_extended_inference_edge_cases_part1](../../../../fixtures/typed.py#L5650)**

````python
Run extended stress cases part 1.

Returns:
    ExtendedResultsPart1: TODO.
````

**[Produced: test_extended_inference_edge_cases_part1](result.py#L4199)**

````python
Run extended stress cases part 1.

Returns:
    TODO.
````

</details>

<details><summary>test_extended_inference_edge_cases_part2 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_extended_inference_edge_cases_part2](../../../../fixtures/typed.py#L5691)**

````python
Run extended stress cases part 2.

Returns:
    ExtendedResultsPart2: TODO.
````

**[Produced: test_extended_inference_edge_cases_part2](result.py#L4235)**

````python
Run extended stress cases part 2.

Returns:
    TODO.
````

</details>

<details><summary>test_extended_inference_edge_cases_part3 — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_extended_inference_edge_cases_part3](../../../../fixtures/typed.py#L5725)**

````python
Run extended stress cases part 3.

Returns:
    ExtendedResultsPart3: TODO.
````

**[Produced: test_extended_inference_edge_cases_part3](result.py#L4264)**

````python
Run extended stress cases part 3.

Returns:
    dict[str, int]: TODO.
````

</details>

<details><summary>test_extended_inference_edge_cases — changed</summary>

Missing fields: none. Additional fields: none. Changed fields: returns.0. Types and description text are compared structurally; prose meaning and inference causes are not assessed.

**[Reference: test_extended_inference_edge_cases](../../../../fixtures/typed.py#L5787)**

````python
Run all extended inference stress cases.

Returns:
    ExtendedTestResult: TODO.
````

**[Produced: test_extended_inference_edge_cases](result.py#L4317)**

````python
Run all extended inference stress cases.

Returns:
    dict[str, int]: TODO.
````

</details>

<details><summary>SupportsExecuteInt — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsExecuteInt](result.py#L67)**

````python
Protocol for integer strategies.
````

</details>

<details><summary>SupportsExecuteInt.execute — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsExecuteInt.execute](result.py#L70)**

````python
Execute with two integer inputs.

Args:
    a: TODO.
    b: TODO.
````

</details>

<details><summary>SupportsVector — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsVector](result.py#L99)**

````python
Protocol for vector-like objects.
````

</details>

<details><summary>SupportsVector.__add__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsVector.__add__](result.py#L105)**

````python
Add vectors.

Args:
    other (int): TODO.
````

</details>

<details><summary>SupportsAddition — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsAddition](result.py#L168)**

````python
Structural contract requiring ``__add__``.
````

</details>

<details><summary>SupportsAddition.__add__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsAddition.__add__](result.py#L171)**

````python
Return the addition result for the declared operands.

Args:
    arg0: TODO.
````

</details>

<details><summary>SupportsAddition2 — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsAddition2](result.py#L343)**

````python
Structural contract requiring ``__add__``.
````

</details>

<details><summary>SupportsAddition2.__add__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsAddition2.__add__](result.py#L346)**

````python
Return the addition result for the declared operands.

Args:
    arg0 (int): TODO.
````

</details>

<details><summary>DataClassExample.__init__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: DataClassExample.__init__](result.py#L411)**

````python
Initialize dataclass-like example.

Args:
    x: TODO.
    y (str): TODO.
    z: TODO.
````

</details>

<details><summary>SupportsRadd — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsRadd](result.py#L524)**

````python
Structural contract requiring ``__radd__``.
````

</details>

<details><summary>SupportsRadd.__radd__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsRadd.__radd__](result.py#L527)**

````python
Provide the required ``__radd__`` operation.

Args:
    arg0: TODO.
````

</details>

<details><summary>SupportsLeAndMultiplicationAndSub — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsLeAndMultiplicationAndSub](result.py#L604)**

````python
Structural contract requiring ``__le__``, ``__mul__``, ``__sub__``.
````

</details>

<details><summary>SupportsLeAndMultiplicationAndSub.__le__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsLeAndMultiplicationAndSub.__le__](result.py#L607)**

````python
Provide the required ``__le__`` operation.

Args:
    arg0 (int): TODO.

Returns:
    TODO.
````

</details>

<details><summary>SupportsLeAndMultiplicationAndSub.__mul__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsLeAndMultiplicationAndSub.__mul__](result.py#L618)**

````python
Return the product for the declared operands.

Args:
    arg0: TODO.
````

</details>

<details><summary>SupportsLeAndMultiplicationAndSub.__sub__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsLeAndMultiplicationAndSub.__sub__](result.py#L625)**

````python
Provide the required ``__sub__`` operation.

Args:
    arg0 (int): TODO.
````

</details>

<details><summary>SupportsMultiplication — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsMultiplication](result.py#L731)**

````python
Structural contract requiring ``__mul__``.
````

</details>

<details><summary>SupportsMultiplication.__mul__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsMultiplication.__mul__](result.py#L734)**

````python
Return the product for the declared operands.

Args:
    arg0 (int): TODO.
````

</details>

<details><summary>function_with_generic_types.generic_function — extra</summary>

Generated artifact absent from the reference.

**[Produced: function_with_generic_types.generic_function](result.py#L1107)**

````python
Test generic function.

Args:
    container (str | dict[str, int] | list[int]): TODO.

Returns:
    int | str: TODO.
````

</details>

<details><summary>function_with_optional_types.optional_function — extra</summary>

Generated artifact absent from the reference.

**[Produced: function_with_optional_types.optional_function](result.py#L1158)**

````python
Test optional function.

Args:
    value (int | None): TODO.

Returns:
    int | str: TODO.
````

</details>

<details><summary>SupportsMultiplication2 — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsMultiplication2](result.py#L1452)**

````python
Structural contract requiring ``__mul__``.
````

</details>

<details><summary>SupportsMultiplication2.__mul__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsMultiplication2.__mul__](result.py#L1455)**

````python
Return the product for the declared operands.

Args:
    arg0: TODO.
````

</details>

<details><summary>SupportsGtAndRmul — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsGtAndRmul](result.py#L1549)**

````python
Structural contract requiring ``__gt__``, ``__rmul__``.
````

</details>

<details><summary>SupportsGtAndRmul.__gt__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsGtAndRmul.__gt__](result.py#L1552)**

````python
Provide the required ``__gt__`` operation.

Args:
    arg0 (int): TODO.

Returns:
    TODO.
````

</details>

<details><summary>SupportsGtAndRmul.__rmul__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsGtAndRmul.__rmul__](result.py#L1563)**

````python
Provide the required ``__rmul__`` operation.

Args:
    arg0: TODO.
````

</details>

<details><summary>Point.__init__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: Point.__init__](result.py#L2199)**

````python
Initialize point.

Args:
    x: TODO.
    y: TODO.
````

</details>

<details><summary>SliceExampleResult.__init__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: SliceExampleResult.__init__](result.py#L2528)**

````python
Initialize slice example result.

Args:
    list_slice: TODO.
    list_stride_slice: TODO.
    dict_slice: TODO.
    dict_key_slice: TODO.
    dict_value_slice: TODO.
````

</details>

<details><summary>BuiltinMethodDict.get — extra</summary>

Generated artifact absent from the reference.

**[Produced: BuiltinMethodDict.get](result.py#L2578)**

````python
Return a stored value or a narrowed integer default.

Args:
    key (str): TODO.
    default (int | str | None): TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>BuiltinMethodDict.update — extra</summary>

Generated artifact absent from the reference.

**[Produced: BuiltinMethodDict.update](result.py#L2591)**

````python
Update values while multiplying every incoming integer.

Args:
    other (dict[str, int] | tuple[()]): TODO.
    values: TODO.
    kwargs: TODO.
    other (dict[str, int] | tuple[()]): TODO.
````

</details>

<details><summary>ImportExampleResult.__init__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: ImportExampleResult.__init__](result.py#L2646)**

````python
Initialize import example result.

Args:
    importlib_module_name: TODO.
    dunder_module_name: TODO.
    imported_join_result: TODO.
````

</details>

<details><summary>RedefinitionResult.__init__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: RedefinitionResult.__init__](result.py#L2667)**

````python
Initialize redefinition result.

Args:
    first_type_value: TODO.
    second_type_value: TODO.
    third_type_value: TODO.
    union_final_value: TODO.
````

</details>

<details><summary>ScopeResolutionResult.__init__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: ScopeResolutionResult.__init__](result.py#L2691)**

````python
Initialize scope resolution result.

Args:
    module_value: TODO.
    outer_value: TODO.
    inner_value: TODO.
    class_value: TODO.
    method_and_nested_results: TODO.
````

</details>

<details><summary>ExtendedResult.__getitem__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: ExtendedResult.__getitem__](result.py#L2947)**

````python
Return one field by index or name.

Args:
    index: TODO.

Returns:
    TODO.

Raises:
    IndexError: TODO.
````

</details>

<details><summary>DescriptorWithOwnerCache.__get__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: DescriptorWithOwnerCache.__get__](result.py#L3018)**

````python
Return descriptor or stored instance value.

Args:
    instance: TODO.
    owner: TODO.

Returns:
    Self: TODO.
````

</details>

<details><summary>FluentBuilder.build — extra</summary>

Generated artifact absent from the reference.

**[Produced: FluentBuilder.build](result.py#L3199)**

````python
Return a compact string or a structured result.

Args:
    compact (bool): TODO.

Returns:
    TODO.
````

</details>

<details><summary>HybridContainer.__getitem__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: HybridContainer.__getitem__](result.py#L3245)**

````python
Return item by int index or dict key.

Args:
    key: TODO.

Returns:
    int: TODO.
````

</details>

<details><summary>HybridContainer.__setitem__ — extra</summary>

Generated artifact absent from the reference.

**[Produced: HybridContainer.__setitem__](result.py#L3258)**

````python
Set item by int index or dict key.

Args:
    key: TODO.
    value: TODO.
````

</details>

<details><summary>SupportsUpper — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsUpper](result.py#L3481)**

````python
Structural contract requiring ``upper``.
````

</details>

<details><summary>SupportsUpper.upper — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsUpper.upper](result.py#L3484)**

````python
Provide the required ``upper`` operation.
````

</details>

<details><summary>function_with_literal_mode_dispatch — extra</summary>

Generated artifact absent from the reference.

**[Produced: function_with_literal_mode_dispatch](result.py#L4143)**

````python
Dispatch by string literal-like mode.

Args:
    mode (str): TODO.
    value (dict[str, int]): TODO.

Returns:
    dict[str, int]: TODO.
````

</details>

<details><summary>function_with_complex_boolean_narrowing — extra</summary>

Generated artifact absent from the reference.

**[Produced: function_with_complex_boolean_narrowing](result.py#L4165)**

````python
Exercise bool-op narrowing with dict/list/tuple/string paths.

Args:
    value (dict[str, int]): TODO.
    fallback (bool): TODO.

Returns:
    int | str | bool: TODO.
````

</details>

### Type aliases

<details><summary>StrOrBufferOrSupportsIntOrSupportsIndex — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrBufferOrSupportsIntOrSupportsIndex](../../../../fixtures/typed.py#L89)**

````python
type StrOrBufferOrSupportsIntOrSupportsIndex = str | Buffer | SupportsInt | SupportsIndex
````

</details>

<details><summary>ListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListInt](../../../../fixtures/typed.py#L92)**

````python
type ListInt = list[int]
````

</details>

<details><summary>ListIntOrDictIntOrStrOrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListIntOrDictIntOrStrOrInt](../../../../fixtures/typed.py#L94)**

````python
type ListIntOrDictIntOrStrOrInt = ListInt | DictInt | str | int
````

</details>

<details><summary>CallableSequenceSequenceIntListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableSequenceSequenceIntListInt](../../../../fixtures/typed.py#L95)**

````python
type CallableSequenceSequenceIntListInt = Callable[[SequenceSequenceInt], ListInt]
````

</details>

<details><summary>DictObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictObject](../../../../fixtures/typed.py#L98)**

````python
type DictObject = dict[str, object]
````

</details>

<details><summary>TupleExtendedResultListIntStrIntBool — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleExtendedResultListIntStrIntBool](../../../../fixtures/typed.py#L99)**

````python
type TupleExtendedResultListIntStrIntBool = tuple['ExtendedResult[ListInt]', str, int, bool]
````

</details>

<details><summary>MappingStrObjectOrSequenceObjectOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MappingStrObjectOrSequenceObjectOrNone](../../../../fixtures/typed.py#L102)**

````python
type MappingStrObjectOrSequenceObjectOrNone = MappingStrObject | SequenceValue[object] | None
````

</details>

<details><summary>TupleIntIntOrListObjectOrDictObjectOrStrOrObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntIntOrListObjectOrDictObjectOrStrOrObject](../../../../fixtures/typed.py#L105)**

````python
type TupleIntIntOrListObjectOrDictObjectOrStrOrObject = TupleIntVariadic | ListObject | DictObject | str | object
````

</details>

<details><summary>MutableMappingStrObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MutableMappingStrObject](../../../../fixtures/typed.py#L108)**

````python
type MutableMappingStrObject = MutableMapping[str, object]
````

</details>

<details><summary>ListStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListStr](../../../../fixtures/typed.py#L112)**

````python
type ListStr = list[str]
````

</details>

<details><summary>ListObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListObject](../../../../fixtures/typed.py#L113)**

````python
type ListObject = list[object]
````

</details>

<details><summary>SetInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SetInt](../../../../fixtures/typed.py#L114)**

````python
type SetInt = set[int]
````

</details>

<details><summary>SetBool — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SetBool](../../../../fixtures/typed.py#L115)**

````python
type SetBool = set[bool]
````

</details>

<details><summary>TypeObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeObject](../../../../fixtures/typed.py#L116)**

````python
type TypeObject = type[object]
````

</details>

<details><summary>TypeObjectOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeObjectOrNone](../../../../fixtures/typed.py#L117)**

````python
type TypeObjectOrNone = TypeObject | None
````

</details>

<details><summary>TupleTypeObjectVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleTypeObjectVariadic](../../../../fixtures/typed.py#L118)**

````python
type TupleTypeObjectVariadic = tuple[TypeObject, ...]
````

</details>

<details><summary>IntOrStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrStr](../../../../fixtures/typed.py#L119)**

````python
type IntOrStr = int | str
````

</details>

<details><summary>IntOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrNone](../../../../fixtures/typed.py#L120)**

````python
type IntOrNone = int | None
````

</details>

<details><summary>StrOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrNone](../../../../fixtures/typed.py#L121)**

````python
type StrOrNone = str | None
````

</details>

<details><summary>IntOrFloat — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrFloat](../../../../fixtures/typed.py#L122)**

````python
type IntOrFloat = int | float
````

</details>

<details><summary>IntOrStrOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrStrOrNone](../../../../fixtures/typed.py#L123)**

````python
type IntOrStrOrNone = IntOrStr | None
````

</details>

<details><summary>StrOrBoolOrListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrBoolOrListInt](../../../../fixtures/typed.py#L124)**

````python
type StrOrBoolOrListInt = str | bool | ListInt
````

</details>

<details><summary>TupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntVariadic](../../../../fixtures/typed.py#L125)**

````python
type TupleIntVariadic = tuple[int, ...]
````

</details>

<details><summary>TupleIntStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntStr](../../../../fixtures/typed.py#L126)**

````python
type TupleIntStr = tuple[int, str]
````

</details>

<details><summary>TupleStrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleStrInt](../../../../fixtures/typed.py#L127)**

````python
type TupleStrInt = tuple[str, int]
````

</details>

<details><summary>TupleStrVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleStrVariadic](../../../../fixtures/typed.py#L128)**

````python
type TupleStrVariadic = tuple[str, ...]
````

</details>

<details><summary>TupleIntVariadicStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntVariadicStr](../../../../fixtures/typed.py#L129)**

````python
type TupleIntVariadicStr = tuple[*TupleIntVariadic, str]
````

</details>

<details><summary>TupleBoolVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleBoolVariadic](../../../../fixtures/typed.py#L130)**

````python
type TupleBoolVariadic = tuple[bool, ...]
````

</details>

<details><summary>TupleIntOrNoneVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntOrNoneVariadic](../../../../fixtures/typed.py#L131)**

````python
type TupleIntOrNoneVariadic = tuple[IntOrNone, ...]
````

</details>

<details><summary>TupleIntOrNoneStrOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntOrNoneStrOrNone](../../../../fixtures/typed.py#L132)**

````python
type TupleIntOrNoneStrOrNone = tuple[IntOrNone, StrOrNone]
````

</details>

<details><summary>ListTupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListTupleIntVariadic](../../../../fixtures/typed.py#L133)**

````python
type ListTupleIntVariadic = list[TupleIntVariadic]
````

</details>

<details><summary>ListTupleIntStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListTupleIntStr](../../../../fixtures/typed.py#L134)**

````python
type ListTupleIntStr = list[TupleIntStr]
````

</details>

<details><summary>ListTupleIntOrNoneStrOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListTupleIntOrNoneStrOrNone](../../../../fixtures/typed.py#L135)**

````python
type ListTupleIntOrNoneStrOrNone = list[TupleIntOrNoneStrOrNone]
````

</details>

<details><summary>TupleListIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListIntVariadic](../../../../fixtures/typed.py#L136)**

````python
type TupleListIntVariadic = tuple[ListInt, ...]
````

</details>

<details><summary>TupleDictIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleDictIntVariadic](../../../../fixtures/typed.py#L137)**

````python
type TupleDictIntVariadic = tuple[DictInt, ...]
````

</details>

<details><summary>TupleListStrVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListStrVariadic](../../../../fixtures/typed.py#L138)**

````python
type TupleListStrVariadic = tuple[ListStr, ...]
````

</details>

<details><summary>TupleSetIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleSetIntVariadic](../../../../fixtures/typed.py#L139)**

````python
type TupleSetIntVariadic = tuple[SetInt, ...]
````

</details>

<details><summary>DictListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictListInt](../../../../fixtures/typed.py#L140)**

````python
type DictListInt = dict[str, ListInt]
````

</details>

<details><summary>DictIntInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictIntInt](../../../../fixtures/typed.py#L141)**

````python
type DictIntInt = dict[int, int]
````

</details>

<details><summary>DictStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictStr](../../../../fixtures/typed.py#L142)**

````python
type DictStr = dict[str, str]
````

</details>

<details><summary>DictTupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictTupleIntVariadic](../../../../fixtures/typed.py#L143)**

````python
type DictTupleIntVariadic = dict[str, TupleIntVariadic]
````

</details>

<details><summary>DictDictTupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictDictTupleIntVariadic](../../../../fixtures/typed.py#L144)**

````python
type DictDictTupleIntVariadic = dict[str, DictTupleIntVariadic]
````

</details>

<details><summary>MappingStrObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MappingStrObject](../../../../fixtures/typed.py#L145)**

````python
type MappingStrObject = Mapping[str, object]
````

</details>

<details><summary>SequenceInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SequenceInt](../../../../fixtures/typed.py#L146)**

````python
type SequenceInt = Sequence[int]
````

</details>

<details><summary>SequenceStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SequenceStr](../../../../fixtures/typed.py#L147)**

````python
type SequenceStr = Sequence[str]
````

</details>

<details><summary>SequenceSequenceInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SequenceSequenceInt](../../../../fixtures/typed.py#L148)**

````python
type SequenceSequenceInt = Sequence[SequenceInt]
````

</details>

<details><summary>CallableIntInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableIntInt](../../../../fixtures/typed.py#L149)**

````python
type CallableIntInt = Callable[[int], int]
````

</details>

<details><summary>CallableIntIntInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableIntIntInt](../../../../fixtures/typed.py#L150)**

````python
type CallableIntIntInt = Callable[[int, int], int]
````

</details>

<details><summary>CallableVariadicInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableVariadicInt](../../../../fixtures/typed.py#L151)**

````python
type CallableVariadicInt = Callable[..., int]
````

</details>

<details><summary>CallableStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableStr](../../../../fixtures/typed.py#L152)**

````python
type CallableStr = Callable[[], str]
````

</details>

<details><summary>CallableNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableNone](../../../../fixtures/typed.py#L153)**

````python
type CallableNone = Callable[[], None]
````

</details>

<details><summary>AwaitableInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: AwaitableInt](../../../../fixtures/typed.py#L154)**

````python
type AwaitableInt = Awaitable[int]
````

</details>

<details><summary>GeneratorInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: GeneratorInt](../../../../fixtures/typed.py#L155)**

````python
type GeneratorInt = Generator[int]
````

</details>

<details><summary>GeneratorIntIntOrStrOrNoneInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: GeneratorIntIntOrStrOrNoneInt](../../../../fixtures/typed.py#L156)**

````python
type GeneratorIntIntOrStrOrNoneInt = Generator[int, IntOrStrOrNone, int]
````

</details>

<details><summary>DequeInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DequeInt](../../../../fixtures/typed.py#L157)**

````python
type DequeInt = deque[int]
````

</details>

<details><summary>CounterInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CounterInt](../../../../fixtures/typed.py#L158)**

````python
type CounterInt = Counter[int]
````

</details>

<details><summary>OrderedDictStrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: OrderedDictStrInt](../../../../fixtures/typed.py#L159)**

````python
type OrderedDictStrInt = OrderedDict[str, int]
````

</details>

<details><summary>DefaultdictStrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DefaultdictStrInt](../../../../fixtures/typed.py#L160)**

````python
type DefaultdictStrInt = defaultdict[str, int]
````

</details>

<details><summary>DefaultdictStrListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DefaultdictStrListInt](../../../../fixtures/typed.py#L161)**

````python
type DefaultdictStrListInt = defaultdict[str, ListInt]
````

</details>

<details><summary>DefaultdictStrDefaultdictStrListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DefaultdictStrDefaultdictStrListInt](../../../../fixtures/typed.py#L162)**

````python
type DefaultdictStrDefaultdictStrListInt = defaultdict[str, DefaultdictStrListInt]
````

</details>

<details><summary>CallableParametersToResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableParametersToResult](../../../../fixtures/typed.py#L168)**

````python
type CallableParametersToResult[**Parameters, Result] = Callable[Parameters, Result]
````

</details>

<details><summary>CallableValueToResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableValueToResult](../../../../fixtures/typed.py#L171)**

````python
type CallableValueToResult[Value, Result] = Callable[[Value], Result]
````

</details>

<details><summary>ListValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListValue](../../../../fixtures/typed.py#L172)**

````python
type ListValue[Value] = list[Value]
````

</details>

<details><summary>SequenceValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SequenceValue](../../../../fixtures/typed.py#L173)**

````python
type SequenceValue[Value] = Sequence[Value]
````

</details>

<details><summary>MappingValueToResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MappingValueToResult](../../../../fixtures/typed.py#L174)**

````python
type MappingValueToResult[Value, Result] = Mapping[Value, Result]
````

</details>

<details><summary>TypeValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeValue](../../../../fixtures/typed.py#L175)**

````python
type TypeValue[Value] = type[Value]
````

</details>

<details><summary>TupleValueVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleValueVariadic](../../../../fixtures/typed.py#L176)**

````python
type TupleValueVariadic[Value] = tuple[Value, ...]
````

</details>

<details><summary>ValueOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrNone](../../../../fixtures/typed.py#L177)**

````python
type ValueOrNone[Value] = Value | None
````

</details>

<details><summary>ValueOrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrInt](../../../../fixtures/typed.py#L178)**

````python
type ValueOrInt[Value] = Value | int
````

</details>

<details><summary>ValueOrIntOrStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrIntOrStr](../../../../fixtures/typed.py#L179)**

````python
type ValueOrIntOrStr[Value] = Value | IntOrStr
````

</details>

<details><summary>ValueOrListObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrListObject](../../../../fixtures/typed.py#L180)**

````python
type ValueOrListObject[Value] = Value | ListObject
````

</details>

<details><summary>StrOrValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrValue](../../../../fixtures/typed.py#L181)**

````python
type StrOrValue[Value] = str | Value
````

</details>

<details><summary>StrOrValueOrDictObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrValueOrDictObject](../../../../fixtures/typed.py#L182)**

````python
type StrOrValueOrDictObject[Value] = StrOrValue[Value] | DictObject
````

</details>

<details><summary>ValueOrOther — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrOther](../../../../fixtures/typed.py#L183)**

````python
type ValueOrOther[Value, Other] = Value | Other
````

</details>

<details><summary>ValueOrOtherOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrOtherOrNone](../../../../fixtures/typed.py#L184)**

````python
type ValueOrOtherOrNone[Value, Other] = ValueOrOther[Value, Other] | None
````

</details>

<details><summary>TupleStrValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleStrValue](../../../../fixtures/typed.py#L185)**

````python
type TupleStrValue[Value] = tuple[str, Value]
````

</details>

<details><summary>ObjectOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ObjectOrNone](../../../../fixtures/typed.py#L188)**

````python
type ObjectOrNone = object | None
````

</details>

<details><summary>DictObjectOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictObjectOrNone](../../../../fixtures/typed.py#L189)**

````python
type DictObjectOrNone = DictObject | None
````

</details>

<details><summary>DictRegistryMeta — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictRegistryMeta](../../../../fixtures/typed.py#L190)**

````python
type DictRegistryMeta = dict[str, RegistryMeta]
````

</details>

<details><summary>StrOrBuilderStructured — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrBuilderStructured](../../../../fixtures/typed.py#L191)**

````python
type StrOrBuilderStructured = str | BuilderStructured
````

</details>

<details><summary>StrOrDictStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrDictStr](../../../../fixtures/typed.py#L192)**

````python
type StrOrDictStr = str | DictStr
````

</details>

<details><summary>ListRecursiveChild — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListRecursiveChild](../../../../fixtures/typed.py#L193)**

````python
type ListRecursiveChild = list[RecursiveChild]
````

</details>

<details><summary>ListNormalizedRow — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListNormalizedRow](../../../../fixtures/typed.py#L194)**

````python
type ListNormalizedRow = list[NormalizedRow]
````

</details>

<details><summary>ListException — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListException](../../../../fixtures/typed.py#L195)**

````python
type ListException = list[Exception]
````

</details>

<details><summary>ListListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListListInt](../../../../fixtures/typed.py#L196)**

````python
type ListListInt = list[ListInt]
````

</details>

<details><summary>DescriptorWithOwnerCacheInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DescriptorWithOwnerCacheInt](../../../../fixtures/typed.py#L197)**

````python
type DescriptorWithOwnerCacheInt = DescriptorWithOwnerCache[int]
````

</details>

<details><summary>TypeAbstractBase — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeAbstractBase](../../../../fixtures/typed.py#L198)**

````python
type TypeAbstractBase = type[AbstractBase]
````

</details>

<details><summary>TypeSupportsValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeSupportsValue](../../../../fixtures/typed.py#L199)**

````python
type TypeSupportsValue = type[SupportsValue]
````

</details>

<details><summary>TypeSupportsClassMethods — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeSupportsClassMethods](../../../../fixtures/typed.py#L200)**

````python
type TypeSupportsClassMethods = type[SupportsClassMethodAndInstanceMethodAndStaticMethod]
````

</details>

<details><summary>CallableIntOrStrToIntOrStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableIntOrStrToIntOrStr](../../../../fixtures/typed.py#L203)**

````python
type CallableIntOrStrToIntOrStr = Callable[[IntOrStr], IntOrStr]
````

</details>

<details><summary>CallablePayloadInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallablePayloadInt](../../../../fixtures/typed.py#L204)**

````python
type CallablePayloadInt = CallablePayload[int]
````

</details>

<details><summary>CallablePayloadStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallablePayloadStr](../../../../fixtures/typed.py#L205)**

````python
type CallablePayloadStr = CallablePayload[str]
````

</details>

<details><summary>IntOrStrOrCallablePayloadInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrStrOrCallablePayloadInt](../../../../fixtures/typed.py#L206)**

````python
type IntOrStrOrCallablePayloadInt = IntOrStr | CallablePayloadInt
````

</details>

<details><summary>IntOrStrOrCallablePayloadStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrStrOrCallablePayloadStr](../../../../fixtures/typed.py#L207)**

````python
type IntOrStrOrCallablePayloadStr = IntOrStr | CallablePayloadStr
````

</details>

<details><summary>HybridContainerIntOrFloatStrOrBoolOrListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: HybridContainerIntOrFloatStrOrBoolOrListInt](../../../../fixtures/typed.py#L208)**

````python
type HybridContainerIntOrFloatStrOrBoolOrListInt = HybridContainer[IntOrFloat, StrOrBoolOrListInt]
````

</details>

<details><summary>TupleListTupleIntVariadicVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListTupleIntVariadicVariadic](../../../../fixtures/typed.py#L211)**

````python
type TupleListTupleIntVariadicVariadic = tuple[ListTupleIntVariadic, ...]
````

</details>

<details><summary>TupleAsyncPayloadListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleAsyncPayloadListInt](../../../../fixtures/typed.py#L212)**

````python
type TupleAsyncPayloadListInt = tuple[AsyncPayload, ListInt]
````

</details>

<details><summary>TupleListIntListStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListIntListStr](../../../../fixtures/typed.py#L213)**

````python
type TupleListIntListStr = tuple[ListInt, ListStr]
````

</details>

<details><summary>TupleListIntIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListIntIntVariadic](../../../../fixtures/typed.py#L214)**

````python
type TupleListIntIntVariadic = tuple[ListInt, *TupleIntVariadic]
````

</details>

<details><summary>TupleDefaultdictStrIntListStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleDefaultdictStrIntListStr](../../../../fixtures/typed.py#L215)**

````python
type TupleDefaultdictStrIntListStr = tuple[DefaultdictStrInt, ListStr]
````

</details>

<details><summary>TupleListIntDictIntIntGeneratorInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListIntDictIntIntGeneratorInt](../../../../fixtures/typed.py#L216)**

````python
type TupleListIntDictIntIntGeneratorInt = tuple[ListInt, DictIntInt, GeneratorInt]
````

</details>

<details><summary>TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic](../../../../fixtures/typed.py#L219)**

````python
type TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic = tuple[DefaultdictStrDefaultdictStrListInt, DictDictTupleIntVariadic]
````

</details>

<details><summary>TupleListNormalizedRowDictListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListNormalizedRowDictListInt](../../../../fixtures/typed.py#L222)**

````python
type TupleListNormalizedRowDictListInt = tuple[ListNormalizedRow, DictListInt]
````

</details>

<details><summary>TupleBuilderStructuredStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleBuilderStructuredStr](../../../../fixtures/typed.py#L223)**

````python
type TupleBuilderStructuredStr = tuple[BuilderStructured, str]
````

</details>

<details><summary>TupleDescriptorSummaryIntStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleDescriptorSummaryIntStr](../../../../fixtures/typed.py#L224)**

````python
type TupleDescriptorSummaryIntStr = tuple[DescriptorSummary, int, str]
````

</details>

<details><summary>TupleRegistryItemVariadicListStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleRegistryItemVariadicListStr](../../../../fixtures/typed.py#L225)**

````python
type TupleRegistryItemVariadicListStr = tuple[*TupleValueVariadic[RegistryItem], ListStr]
````

</details>

<details><summary>TupleIntFloatVariadicListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntFloatVariadicListInt](../../../../fixtures/typed.py#L228)**

````python
type TupleIntFloatVariadicListInt = tuple[int, *TupleValueVariadic[float], ListInt]
````

</details>

<details><summary>TupleIntVariadicGeneratorIntIntOrStrOrNoneInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntVariadicGeneratorIntIntOrStrOrNoneInt](../../../../fixtures/typed.py#L231)**

````python
type TupleIntVariadicGeneratorIntIntOrStrOrNoneInt = tuple[*TupleIntVariadic, GeneratorIntIntOrStrOrNoneInt]
````

</details>

<details><summary>TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt](../../../../fixtures/typed.py#L234)**

````python
type TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt = tuple[BuiltinMethodList, BuiltinMethodDict, CustomAddSet, int]
````

</details>

<details><summary>TupleHybridContainerIntOrFloatStrOrBoolOrListIntBoolListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleHybridContainerIntOrFloatStrOrBoolOrListIntBoolListInt](../../../../fixtures/typed.py#L237)**

````python
type TupleHybridContainerIntOrFloatStrOrBoolOrListIntBoolListInt = tuple[HybridContainerIntOrFloatStrOrBoolOrListInt, bool, ListInt]
````

</details>

<details><summary>TupleIntOrStrOrCallablePayloadIntIntOrStrOrCallablePayloadStrVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntOrStrOrCallablePayloadIntIntOrStrOrCallablePayloadStrVariadic](../../../../fixtures/typed.py#L240)**

````python
type TupleIntOrStrOrCallablePayloadIntIntOrStrOrCallablePayloadStrVariadic = tuple[IntOrStrOrCallablePayloadInt, *TupleValueVariadic[IntOrStrOrCallablePayloadStr]]
````

</details>

<details><summary>TupleSupportsMetadataAndNameVariadicNodeMetadata — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleSupportsMetadataAndNameVariadicNodeMetadata](../../../../fixtures/typed.py#L246)**

````python
type TupleSupportsMetadataAndNameVariadicNodeMetadata = tuple[*TupleValueVariadic[SupportsMetadataAndName], NodeMetadata]
````

</details>

<details><summary>TupleBytearrayMemoryviewBytesInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleBytearrayMemoryviewBytesInt](../../../../fixtures/typed.py#L249)**

````python
type TupleBytearrayMemoryviewBytesInt = tuple[bytearray, memoryview, bytes, int]
````

</details>

<details><summary>UnpackingStressResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: UnpackingStressResult](../../../../fixtures/typed.py#L252)**

````python
type UnpackingStressResult = tuple[int, ListInt, int, *TupleListTupleIntVariadicVariadic]
````

</details>

<details><summary>CallableExamples — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableExamples](../../../../fixtures/typed.py#L255)**

````python
type CallableExamples = tuple[CallableVariadicInt, ...]
````

</details>

<details><summary>CallableIntIntSupportsAdditionAndXAndY — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableIntIntSupportsAdditionAndXAndY](../../../../fixtures/typed.py#L736)**

````python
type CallableIntIntSupportsAdditionAndXAndY = Callable[[int, int], SupportsAdditionAndXAndY]
````

</details>

### Protocols

<details><summary>SupportsMetadataAndName — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsMetadataAndName](../../../../fixtures/typed.py#L265)**

````python
class SupportsMetadataAndName(Protocol):
    """Public, recursively mutable node-attribute contract."""
    name: str
    metadata: NodeMetadata
````

</details>

<details><summary>SupportsUpdate — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsUpdate](../../../../fixtures/typed.py#L557)**

````python
class SupportsUpdate(Protocol):
    """Protocol for observer-like objects."""

    def update(self, message: str) -> None:
        """Receive an update message.

        Args:
            message (str): TODO.

        """
        ...
````

</details>

<details><summary>SupportsExecute — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsExecute](../../../../fixtures/typed.py#L570)**

````python
class SupportsExecute(Protocol):
    """Protocol for integer strategies."""

    def execute(self, a: int, b: int) -> int:
        """Execute with two integer inputs.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """
        ...
````

</details>

<details><summary>SupportsAction — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsAction](../../../../fixtures/typed.py#L587)**

````python
class SupportsAction(Protocol):
    """Protocol for receiver objects."""

    def action(self) -> str:
        """Perform the action.

        Returns:
            str: TODO.

        """
        ...
````

</details>

<details><summary>SupportsClassMethodAndInstanceMethodAndStaticMethod — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsClassMethodAndInstanceMethodAndStaticMethod](../../../../fixtures/typed.py#L600)**

````python
class SupportsClassMethodAndInstanceMethodAndStaticMethod(Protocol):
    """Common interface of the nested class-method example."""

    @classmethod
    def class_method(cls) -> str:
        """Return the class name."""
        ...

    @staticmethod
    def static_method() -> str:
        """Return the static marker."""
        ...

    def instance_method(self) -> str:
        """Return the instance marker."""
        ...
````

</details>

<details><summary>SupportsValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsValue](../../../../fixtures/typed.py#L618)**

````python
class SupportsValue(Protocol):
    """An instance carrying a writable integer property."""

    @property
    def value(self) -> int:
        """Read the integer value."""
        ...

    @value.setter
    def value(self, val: int) -> None:
        """Write the integer value."""
        ...
````

</details>

<details><summary>SupportsMatrixMultiplicationAndData — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsMatrixMultiplicationAndData](../../../../fixtures/typed.py#L632)**

````python
class SupportsMatrixMultiplicationAndData(Protocol):
    """An integer matrix supporting matrix multiplication."""
    data: ListListInt

    def __matmul__(self, other: Self) -> Self:
        """Return the product of two matrices."""
        ...
````

</details>

<details><summary>SupportsInstance — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsInstance](../../../../fixtures/typed.py#L642)**

````python
class SupportsInstance[ValueT](Protocol):
    """Wrapper holding a precisely typed original instance."""
    instance: ValueT
````

</details>

<details><summary>SupportsJoin — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsJoin](../../../../fixtures/typed.py#L648)**

````python
class SupportsJoin(Protocol):
    """Subset of os.path whose join operation produces a string."""

    def join(self, path: str, *paths: str) -> str:
        """Join path components."""
        ...
````

</details>

<details><summary>SupportsNameAndPath — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsNameAndPath](../../../../fixtures/typed.py#L656)**

````python
class SupportsNameAndPath(Protocol):
    """Features of the os module returned by __import__('os.path')."""
    __name__: str
    path: SupportsJoin
````

</details>

<details><summary>SupportsCall — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall](../../../../fixtures/typed.py#L663)**

````python
class SupportsCall(Protocol):
    """Invoke any unary callable without erasing its argument/return types."""

    def __call__[InputT, OutputT](self, func: CallableValueToResult[InputT, OutputT], arg: InputT) -> OutputT:
        """Apply a unary callable to its correctly typed argument."""
        ...
````

</details>

<details><summary>SupportsCall2 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall2](../../../../fixtures/typed.py#L675)**

````python
class SupportsCall2(Protocol):
    """Preserve a provided value or produce the default string."""

    @overload
    def __call__(self, value: None=None) -> str:
        ...

    @overload
    def __call__[ValueT](self, value: ValueT) -> ValueT | str:
        ...
````

</details>

<details><summary>SupportsInitializedByMeta — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsInitializedByMeta](../../../../fixtures/typed.py#L685)**

````python
class SupportsInitializedByMeta(Protocol):
    """Protocol for objects initialized by metaclass.

    Attributes:
        initialized_by_meta (bool): TODO.

    """
    initialized_by_meta: bool
````

</details>

<details><summary>SupportsNewMethod — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsNewMethod](../../../../fixtures/typed.py#L696)**

````python
class SupportsNewMethod(Protocol):
    """Protocol for objects with new_method."""

    def new_method(self) -> str:
        """Return new method for testing.

        Returns:
            str: TODO.

        """
        ...
````

</details>

<details><summary>SupportsAdditionAndXAndY — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsAdditionAndXAndY](../../../../fixtures/typed.py#L709)**

````python
class SupportsAdditionAndXAndY(Protocol):
    """Protocol for vector-like objects.

    Attributes:
        x (int): TODO.
        y (int): TODO.

    """
    x: int
    y: int

    def __add__(self, other: SupportsAdditionAndXAndY) -> SupportsAdditionAndXAndY:
        """Add vectors.

        Args:
            other (SupportsAdditionAndXAndY): TODO.

        Returns:
            SupportsAdditionAndXAndY: TODO.

        """
        ...
````

</details>

<details><summary>SupportsApplyAndOffset — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsApplyAndOffset](../../../../fixtures/typed.py#L5152)**

````python
class SupportsApplyAndOffset(Protocol):
    """Protocol for local multiplier instances.

    Attributes:
        offset (int): TODO.

    """
    offset: int

    def apply(self, value: int) -> int:
        """Apply multiplier.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.

        """
        ...
````

</details>

<details><summary>SupportsCallAndFromValues — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCallAndFromValues](../../../../fixtures/typed.py#L5175)**

````python
class SupportsCallAndFromValues(Protocol):
    """Protocol for local multiplier classes."""

    def __call__(self, offset: int=0) -> SupportsApplyAndOffset:
        """Create a local multiplier.

        Args:
            offset (int): TODO.

        Returns:
            SupportsApplyAndOffset: TODO.

        """
        ...

    def from_values(self, values: SequenceInt) -> SupportsApplyAndOffset:
        """Create from values.

        Args:
            values (SequenceInt): TODO.

        Returns:
            SupportsApplyAndOffset: TODO.

        """
        ...
````

</details>

<details><summary>SupportsAddition — extra</summary>

Generated artifact absent from the reference. Output-only class: candidate synthesized declaration; source absence alone does not prove its creation history.

**[Produced: SupportsAddition](result.py#L168)**

````python
class SupportsAddition(Protocol):
    """Structural contract requiring ``__add__``."""

    def __add__(self, arg0, /):
        """Return the addition result for the declared operands.

        Args:
            arg0: TODO."""
        ...
````

</details>

<details><summary>SupportsAddition2 — extra</summary>

Generated artifact absent from the reference. Output-only class: candidate synthesized declaration; source absence alone does not prove its creation history.

**[Produced: SupportsAddition2](result.py#L343)**

````python
class SupportsAddition2(Protocol):
    """Structural contract requiring ``__add__``."""

    def __add__(self, arg0: int, /):
        """Return the addition result for the declared operands.

        Args:
            arg0 (int): TODO.
        """
        ...
````

</details>

<details><summary>SupportsRadd — extra</summary>

Generated artifact absent from the reference. Output-only class: candidate synthesized declaration; source absence alone does not prove its creation history.

**[Produced: SupportsRadd](result.py#L524)**

````python
class SupportsRadd(Protocol):
    """Structural contract requiring ``__radd__``."""

    def __radd__(self, arg0, /):
        """Provide the required ``__radd__`` operation.

        Args:
            arg0: TODO."""
        ...
````

</details>

<details><summary>SupportsLeAndMultiplicationAndSub — extra</summary>

Generated artifact absent from the reference. Output-only class: candidate synthesized declaration; source absence alone does not prove its creation history.

**[Produced: SupportsLeAndMultiplicationAndSub](result.py#L604)**

````python
class SupportsLeAndMultiplicationAndSub(Protocol):
    """Structural contract requiring ``__le__``, ``__mul__``, ``__sub__``."""

    def __le__(self, arg0: int, /) -> bool:
        """Provide the required ``__le__`` operation.

        Args:
            arg0 (int): TODO.

        Returns:
            TODO.
        """
        ...

    def __mul__(self, arg0, /):
        """Return the product for the declared operands.

        Args:
            arg0: TODO."""
        ...

    def __sub__(self, arg0: int, /):
        """Provide the required ``__sub__`` operation.

        Args:
            arg0 (int): TODO.
        """
        ...
````

</details>

<details><summary>SupportsMultiplication — extra</summary>

Generated artifact absent from the reference. Output-only class: candidate synthesized declaration; source absence alone does not prove its creation history.

**[Produced: SupportsMultiplication](result.py#L731)**

````python
class SupportsMultiplication(Protocol):
    """Structural contract requiring ``__mul__``."""

    def __mul__(self, arg0: int, /):
        """Return the product for the declared operands.

        Args:
            arg0 (int): TODO.
        """
        ...
````

</details>

<details><summary>SupportsMultiplication2 — extra</summary>

Generated artifact absent from the reference. Output-only class: candidate synthesized declaration; source absence alone does not prove its creation history.

**[Produced: SupportsMultiplication2](result.py#L1452)**

````python
class SupportsMultiplication2(Protocol):
    """Structural contract requiring ``__mul__``."""

    def __mul__(self, arg0, /):
        """Return the product for the declared operands.

        Args:
            arg0: TODO."""
        ...
````

</details>

<details><summary>SupportsGtAndRmul — extra</summary>

Generated artifact absent from the reference. Output-only class: candidate synthesized declaration; source absence alone does not prove its creation history.

**[Produced: SupportsGtAndRmul](result.py#L1549)**

````python
class SupportsGtAndRmul(Protocol):
    """Structural contract requiring ``__gt__``, ``__rmul__``."""

    def __gt__(self, arg0: int, /) -> bool:
        """Provide the required ``__gt__`` operation.

        Args:
            arg0 (int): TODO.

        Returns:
            TODO.
        """
        ...

    def __rmul__(self, arg0, /):
        """Provide the required ``__rmul__`` operation.

        Args:
            arg0: TODO."""
        ...
````

</details>

<details><summary>SupportsUpper — extra</summary>

Generated artifact absent from the reference. Output-only class: candidate synthesized declaration; source absence alone does not prove its creation history.

**[Produced: SupportsUpper](result.py#L3481)**

````python
class SupportsUpper(Protocol):
    """Structural contract requiring ``upper``."""

    def upper(self):
        """Provide the required ``upper`` operation."""
        ...
````

</details>

### TypeVar

<details><summary>R — missing</summary>

No generated artifact has this qualified identity.

**[Reference: R](../../../../fixtures/typed.py#L80)**

````python
R = TypeVar(name='R')
````

</details>

<details><summary>T — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: T](../../../../fixtures/typed.py#L81)**

````python
T = TypeVar(name='T')
````

**[Produced: T](result.py#L483)**

````python
T = TypeVar('T')
````

</details>

<details><summary>U — missing</summary>

No generated artifact has this qualified identity.

**[Reference: U](../../../../fixtures/typed.py#L82)**

````python
U = TypeVar(name='U')
````

</details>

<details><summary>V — missing</summary>

No generated artifact has this qualified identity.

**[Reference: V](../../../../fixtures/typed.py#L83)**

````python
V = TypeVar(name='V')
````

</details>

<details><summary>W — missing</summary>

No generated artifact has this qualified identity.

**[Reference: W](../../../../fixtures/typed.py#L84)**

````python
W = TypeVar(name='W')
````

</details>

<details><summary>K — missing</summary>

No generated artifact has this qualified identity.

**[Reference: K](../../../../fixtures/typed.py#L85)**

````python
K = TypeVar(name='K')
````

</details>

<details><summary>N — missing</summary>

No generated artifact has this qualified identity.

**[Reference: N](../../../../fixtures/typed.py#L86)**

````python
N = TypeVar('N', int, float, complex)
````

</details>

<details><summary>CallableParametersToResult.Result — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableParametersToResult.Result](../../../../fixtures/typed.py#L168)**

````python
Result
````

</details>

<details><summary>CallableValueToResult.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableValueToResult.Value](../../../../fixtures/typed.py#L171)**

````python
Value
````

</details>

<details><summary>CallableValueToResult.Result — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableValueToResult.Result](../../../../fixtures/typed.py#L171)**

````python
Result
````

</details>

<details><summary>ListValue.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListValue.Value](../../../../fixtures/typed.py#L172)**

````python
Value
````

</details>

<details><summary>SequenceValue.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SequenceValue.Value](../../../../fixtures/typed.py#L173)**

````python
Value
````

</details>

<details><summary>MappingValueToResult.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MappingValueToResult.Value](../../../../fixtures/typed.py#L174)**

````python
Value
````

</details>

<details><summary>MappingValueToResult.Result — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MappingValueToResult.Result](../../../../fixtures/typed.py#L174)**

````python
Result
````

</details>

<details><summary>TypeValue.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeValue.Value](../../../../fixtures/typed.py#L175)**

````python
Value
````

</details>

<details><summary>TupleValueVariadic.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleValueVariadic.Value](../../../../fixtures/typed.py#L176)**

````python
Value
````

</details>

<details><summary>ValueOrNone.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrNone.Value](../../../../fixtures/typed.py#L177)**

````python
Value
````

</details>

<details><summary>ValueOrInt.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrInt.Value](../../../../fixtures/typed.py#L178)**

````python
Value
````

</details>

<details><summary>ValueOrIntOrStr.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrIntOrStr.Value](../../../../fixtures/typed.py#L179)**

````python
Value
````

</details>

<details><summary>ValueOrListObject.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrListObject.Value](../../../../fixtures/typed.py#L180)**

````python
Value
````

</details>

<details><summary>StrOrValue.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrValue.Value](../../../../fixtures/typed.py#L181)**

````python
Value
````

</details>

<details><summary>StrOrValueOrDictObject.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrValueOrDictObject.Value](../../../../fixtures/typed.py#L182)**

````python
Value
````

</details>

<details><summary>ValueOrOther.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrOther.Value](../../../../fixtures/typed.py#L183)**

````python
Value
````

</details>

<details><summary>ValueOrOther.Other — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrOther.Other](../../../../fixtures/typed.py#L183)**

````python
Other
````

</details>

<details><summary>ValueOrOtherOrNone.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrOtherOrNone.Value](../../../../fixtures/typed.py#L184)**

````python
Value
````

</details>

<details><summary>ValueOrOtherOrNone.Other — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrOtherOrNone.Other](../../../../fixtures/typed.py#L184)**

````python
Other
````

</details>

<details><summary>TupleStrValue.Value — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleStrValue.Value](../../../../fixtures/typed.py#L185)**

````python
Value
````

</details>

<details><summary>CallablePayload.T — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallablePayload.T](../../../../fixtures/typed.py#L336)**

````python
T
````

</details>

<details><summary>SupportsInstance.ValueT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsInstance.ValueT](../../../../fixtures/typed.py#L642)**

````python
ValueT
````

</details>

<details><summary>SupportsCall.__call__.InputT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall.__call__.InputT](../../../../fixtures/typed.py#L666)**

````python
InputT
````

</details>

<details><summary>SupportsCall.__call__.OutputT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall.__call__.OutputT](../../../../fixtures/typed.py#L666)**

````python
OutputT
````

</details>

<details><summary>SupportsCall2.__call__#definition:2.ValueT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall2.__call__#definition:2.ValueT](../../../../fixtures/typed.py#L682)**

````python
ValueT
````

</details>

<details><summary>decorator.R — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator.R](../../../../fixtures/typed.py#L934)**

````python
R
````

</details>

<details><summary>decorator_with_args.R — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_with_args.R](../../../../fixtures/typed.py#L967)**

````python
R
````

</details>

<details><summary>decorator_with_class.T — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_with_class.T](../../../../fixtures/typed.py#L1018)**

````python
T
````

</details>

<details><summary>function_with_optional_types.optional_function#definition:2.T — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_optional_types.optional_function#definition:2.T](../../../../fixtures/typed.py#L1910)**

````python
T
````

</details>

<details><summary>function_with_callable.callable_function.InputT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_callable.callable_function.InputT](../../../../fixtures/typed.py#L1937)**

````python
InputT
````

</details>

<details><summary>function_with_callable.callable_function.OutputT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_callable.callable_function.OutputT](../../../../fixtures/typed.py#L1937)**

````python
OutputT
````

</details>

<details><summary>ExtendedResult.PayloadT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedResult.PayloadT](../../../../fixtures/typed.py#L3800)**

````python
PayloadT
````

</details>

<details><summary>DescriptorWithOwnerCache.ValueT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DescriptorWithOwnerCache.ValueT](../../../../fixtures/typed.py#L3917)**

````python
ValueT
````

</details>

<details><summary>RegistryMeta.__call__.InstanceT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: RegistryMeta.__call__.InstanceT](../../../../fixtures/typed.py#L4080)**

````python
InstanceT: RegistryBase
````

</details>

<details><summary>HybridContainer.ItemT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: HybridContainer.ItemT](../../../../fixtures/typed.py#L4222)**

````python
ItemT
````

</details>

<details><summary>HybridContainer.NamedT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: HybridContainer.NamedT](../../../../fixtures/typed.py#L4222)**

````python
NamedT
````

</details>

<details><summary>CallableObject.__call__.ValueT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableObject.__call__.ValueT](../../../../fixtures/typed.py#L4334)**

````python
ValueT
````

</details>

<details><summary>preserve_signature_decorator.R — missing</summary>

No generated artifact has this qualified identity.

**[Reference: preserve_signature_decorator.R](../../../../fixtures/typed.py#L4451)**

````python
R
````

</details>

<details><summary>function_with_type_reassignment_maze.PayloadT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_type_reassignment_maze.PayloadT](../../../../fixtures/typed.py#L4794)**

````python
PayloadT
````

</details>

<details><summary>function_with_mutable_default_like_pattern.ItemT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_mutable_default_like_pattern.ItemT](../../../../fixtures/typed.py#L5509)**

````python
ItemT: Hashable
````

</details>

<details><summary>function_with_complex_boolean_narrowing.ItemT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_complex_boolean_narrowing.ItemT](../../../../fixtures/typed.py#L5577)**

````python
ItemT
````

</details>

<details><summary>function_with_complex_boolean_narrowing.FallbackT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_complex_boolean_narrowing.FallbackT](../../../../fixtures/typed.py#L5577)**

````python
FallbackT
````

</details>

<details><summary>function_with_complex_boolean_narrowing#definition:2.ItemT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_complex_boolean_narrowing#definition:2.ItemT](../../../../fixtures/typed.py#L5584)**

````python
ItemT
````

</details>

<details><summary>function_with_complex_boolean_narrowing#definition:2.FallbackT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_complex_boolean_narrowing#definition:2.FallbackT](../../../../fixtures/typed.py#L5584)**

````python
FallbackT
````

</details>

<details><summary>function_with_complex_boolean_narrowing#definition:3.FallbackT — missing</summary>

No generated artifact has this qualified identity.

**[Reference: function_with_complex_boolean_narrowing#definition:3.FallbackT](../../../../fixtures/typed.py#L5591)**

````python
FallbackT
````

</details>

<details><summary>T2 — extra</summary>

Generated artifact absent from the reference.

**[Produced: T2](result.py#L1347)**

````python
T2 = TypeVar('T2')
````

</details>

<details><summary>T3 — extra</summary>

Generated artifact absent from the reference.

**[Produced: T3](result.py#L1461)**

````python
T3 = TypeVar('T3')
````

</details>

<details><summary>T4 — extra</summary>

Generated artifact absent from the reference.

**[Produced: T4](result.py#L2083)**

````python
T4 = TypeVar('T4')
````

</details>

### ParamSpec

<details><summary>P — missing</summary>

No generated artifact has this qualified identity.

**[Reference: P](../../../../fixtures/typed.py#L79)**

````python
P = ParamSpec(name='P')
````

</details>

<details><summary>CallableParametersToResult.Parameters — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableParametersToResult.Parameters](../../../../fixtures/typed.py#L168)**

````python
**Parameters
````

</details>

<details><summary>decorator.P — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator.P](../../../../fixtures/typed.py#L934)**

````python
**P
````

</details>

<details><summary>decorator_with_args.P — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_with_args.P](../../../../fixtures/typed.py#L967)**

````python
**P
````

</details>

<details><summary>preserve_signature_decorator.P — missing</summary>

No generated artifact has this qualified identity.

**[Reference: preserve_signature_decorator.P](../../../../fixtures/typed.py#L4451)**

````python
**P
````

</details>

<details><summary>decorator_factory.P — missing</summary>

No generated artifact has this qualified identity.

**[Reference: decorator_factory.P](../../../../fixtures/typed.py#L4490)**

````python
**P
````

</details>

### TypeVarTuple

### Classes

<details><summary>NodeMetadata — missing</summary>

No generated artifact has this qualified identity.

**[Reference: NodeMetadata](../../../../fixtures/typed.py#L258)**

````python
class NodeMetadata(TypedDict, total=False):
    """Optional depth and ancestry stored on an internal tree node."""
    depth: int
    path: ListStr
````

</details>

<details><summary>AmountRecord — missing</summary>

No generated artifact has this qualified identity.

**[Reference: AmountRecord](../../../../fixtures/typed.py#L272)**

````python
class AmountRecord(TypedDict, total=False):
    """Optional record fields accepted by the name/amount accumulator."""
    name: StrOrNone
    amount: str | int | None
````

</details>

<details><summary>RecursiveRoot — missing</summary>

No generated artifact has this qualified identity.

**[Reference: RecursiveRoot](../../../../fixtures/typed.py#L279)**

````python
class RecursiveRoot(TypedDict):
    """A root holding children that reference their parent."""
    seed: int
    children: ListRecursiveChild
````

</details>

<details><summary>RecursiveChild — missing</summary>

No generated artifact has this qualified identity.

**[Reference: RecursiveChild](../../../../fixtures/typed.py#L286)**

````python
class RecursiveChild(TypedDict):
    """Child of a recursive root with a mutable integer payload."""
    parent: RecursiveRoot
    values: ListInt
````

</details>

<details><summary>GroupInput — missing</summary>

No generated artifact has this qualified identity.

**[Reference: GroupInput](../../../../fixtures/typed.py#L293)**

````python
class GroupInput(TypedDict):
    """Required fields in a groupable input record."""
    name: object
    score: IntOrStr
````

</details>

<details><summary>NormalizedRow — missing</summary>

No generated artifact has this qualified identity.

**[Reference: NormalizedRow](../../../../fixtures/typed.py#L300)**

````python
class NormalizedRow(TypedDict):
    """Normalized group name and validated numeric score."""
    name: str
    score: int
````

</details>

<details><summary>BuilderStructured — missing</summary>

No generated artifact has this qualified identity.

**[Reference: BuilderStructured](../../../../fixtures/typed.py#L307)**

````python
class BuilderStructured(TypedDict):
    """Structured result produced by a noncompact builder."""
    parts: ListStr
    options: DictObject
````

</details>

<details><summary>JSONRoundtrip — missing</summary>

No generated artifact has this qualified identity.

**[Reference: JSONRoundtrip](../../../../fixtures/typed.py#L314)**

````python
class JSONRoundtrip(TypedDict):
    """Round-tripped JSON record with statically known fields."""
    id: str
    parts: ListStr
    exists: bool
````

</details>

<details><summary>SyncContext — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SyncContext](../../../../fixtures/typed.py#L322)**

````python
class SyncContext(TypedDict):
    """Mutable synchronous context with typed event history."""
    seed: int
    events: ListStr
````

</details>

<details><summary>AsyncPayload — missing</summary>

No generated artifact has this qualified identity.

**[Reference: AsyncPayload](../../../../fixtures/typed.py#L329)**

````python
class AsyncPayload(TypedDict):
    """Named asynchronous fetch result."""
    resource: str
    value: int
````

</details>

<details><summary>CallablePayload — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallablePayload](../../../../fixtures/typed.py#L336)**

````python
class CallablePayload[T](TypedDict):
    """Fallback result of a stateful callable."""
    value: T
    scale: int
````

</details>

<details><summary>TestCallsPart1 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TestCallsPart1](../../../../fixtures/typed.py#L343)**

````python
class TestCallsPart1(TypedDict):
    """Typed output keys from test_function_calls_part1."""
    result1: int
    result2: int
    result3: int
    result4: int
    result5: int
    result6: SequenceInt
    result7: SequenceInt
    result8: TupleListIntDictIntIntGeneratorInt
    result9: TupleListStrVariadic
    result10: int
    result11: int
    result12: int
    result13: ListInt
    result14: TypeSupportsClassMethods
    result15: TypeSupportsValue
    result16: CallableIntIntSupportsAdditionAndXAndY
    result17: object
    result18: TypeObject
    result19: TypeAbstractBase
    result20: TupleIntVariadicStr
    result21: CallableIntOrStrToIntOrStr
    result22: SupportsCall2
````

</details>

<details><summary>TestCallsPart2 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TestCallsPart2](../../../../fixtures/typed.py#L370)**

````python
class TestCallsPart2(TypedDict):
    """Typed output keys from test_function_calls_part2."""
    result23: TupleIntVariadic
    result24: TupleDictIntVariadic
    result25: TupleSetIntVariadic
    result26: TupleIntVariadic
    result27: int
    result28: TupleIntVariadic
    result29: TupleBoolVariadic
    result30: TupleBoolVariadic
    result31: TupleIntOrNoneVariadic
    result32: ListInt
    result33: DictInt
    result34: CallableExamples
    result35: int
    result36: ListInt
    result37: TypeObject
    result38: TypeObject
    result39: TypeObject
    result40: TypeObject
    result41: TypeObject
    result42: TupleTypeObjectVariadic
    result43: TupleTypeObjectVariadic
    result44: TupleTypeObjectVariadic
````

</details>

<details><summary>TestCallsPart3 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TestCallsPart3](../../../../fixtures/typed.py#L397)**

````python
class TestCallsPart3(TypedDict):
    """Typed output keys from test_function_calls_part3."""
    result45: TypeObject
    result46: CallableStr
    result47: CallableIntInt
    result48: int
    result49: DictListInt
    result50: TupleListTupleIntVariadicVariadic
    result51: DefaultdictStrInt
    result52: CounterInt
    result53: DequeInt
    result54: OrderedDictStrInt
    result55: Point
    result56: ListInt
    result57: ListInt
    result58: TupleListIntVariadic
    result59: ListTupleIntOrNoneStrOrNone
    result60: ListTupleIntStr
    result61: ListInt
    result62: ListInt
    result63: ListIntOrDictIntOrStrOrInt
    result64: ListIntOrDictIntOrStrOrInt
    result65: ListIntOrDictIntOrStrOrInt
    result66: ListIntOrDictIntOrStrOrInt
````

</details>

<details><summary>ClassInstantiationResults — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ClassInstantiationResults](../../../../fixtures/typed.py#L424)**

````python
class ClassInstantiationResults(TypedDict):
    """Typed output keys from test_class_instantiations."""
    obj1: BaseClass
    obj2: BaseClass
    obj3: DerivedClass
    obj4: MetaDecoratedClass
    obj5: DataClassExample
    obj6: object
````

</details>

<details><summary>OtherOperationResults — missing</summary>

No generated artifact has this qualified identity.

**[Reference: OtherOperationResults](../../../../fixtures/typed.py#L435)**

````python
class OtherOperationResults(TypedDict):
    """Typed output keys from test_other_operations."""
    enum_val: EnumClass
    closure_result: int
    context_result: object
    vec_sum: SupportsAdditionAndXAndY
````

</details>

<details><summary>NewInferenceResults — missing</summary>

No generated artifact has this qualified identity.

**[Reference: NewInferenceResults](../../../../fixtures/typed.py#L444)**

````python
class NewInferenceResults(TypedDict):
    """Typed output keys from test_new_inference_edge_cases."""
    slices: SliceExampleResult
    builtin_name_collisions: TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt
    imports: ImportExampleResult
    redefinitions: RedefinitionResult
    scope_resolution: ScopeResolutionResult
    positional_and_keyword_only: ListInt
````

</details>

<details><summary>ExtendedResultsPart1 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedResultsPart1](../../../../fixtures/typed.py#L457)**

````python
class ExtendedResultsPart1(TypedDict):
    """Typed output keys from test_extended_inference_edge_cases_part1."""
    pattern_point: TupleIntIntOrListObjectOrDictObjectOrStrOrObject
    pattern_line: TupleIntIntOrListObjectOrDictObjectOrStrOrObject
    walrus: TupleDefaultdictStrIntListStr
    recursive: RecursiveRoot
    numeric: TupleIntFloatVariadicListInt
    reassignment_int: int | ListValue[IntOrStr] | dict[str, int | bool] | TupleStrInt | str | None
    reassignment_callable: int | ListStr | dict[str, str | bool] | TupleStrVariadic | str | None
    exceptions: StrOrDictStr
    exception_group: TupleListIntListStr
    reflection: DictObject
````

</details>

<details><summary>ExtendedResultsPart2 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedResultsPart2](../../../../fixtures/typed.py#L481)**

````python
class ExtendedResultsPart2(TypedDict):
    """Typed output keys from test_extended_inference_edge_cases_part2."""
    json_uuid_path: JSONRoundtrip
    contextvars: MappingStrObject
    unpacking: UnpackingStressResult
    generator_control: TupleIntVariadicGeneratorIntIntOrStrOrNoneInt
    descriptor: TupleDescriptorSummaryIntStr
    metaclass_registry: TupleRegistryItemVariadicListStr
    builder: TupleBuilderStructuredStr
    container: TupleHybridContainerIntOrFloatStrOrBoolOrListIntBoolListInt
    callable_object: TupleIntOrStrOrCallablePayloadIntIntOrStrOrCallablePayloadStrVariadic
    grouping: TupleListNormalizedRowDictListInt
````

</details>

<details><summary>ExtendedResultsPart3 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedResultsPart3](../../../../fixtures/typed.py#L496)**

````python
class ExtendedResultsPart3(TypedDict):
    """Typed output keys from test_extended_inference_edge_cases_part3."""
    local_class: int
    nested_defaultdict: TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic
    partial_reduce: TupleListIntIntVariadic
    runtime_protocol_update: object
    runtime_protocol_callable: object
    deep_attributes: TupleSupportsMetadataAndNameVariadicNodeMetadata
    bytes_memoryview: TupleBytearrayMemoryviewBytesInt
    map_filter_zip: ListTupleIntVariadic
    composed_inner: DictInt
    mutable_store: tuple[ListStr, TupleStrVariadic, set[str]]
    literal_dispatch: str
    boolean_narrowing: IntOrNone
    extended_result: TupleExtendedResultListIntStrIntBool
    decorated_pipeline: str | ListObject
    singledispatch_int: object
    singledispatch_str: object
    singledispatch_default: object
    cached_recursive: TupleIntVariadic
    async_result: TupleAsyncPayloadListInt
````

</details>

<details><summary>TestCallsResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TestCallsResult](../../../../fixtures/typed.py#L522)**

````python
class TestCallsResult(TestCallsPart1, TestCallsPart2, TestCallsPart3):
    """All result fields of the call-inference suite."""
````

</details>

<details><summary>ExtendedTestResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ExtendedTestResult](../../../../fixtures/typed.py#L526)**

````python
class ExtendedTestResult(ExtendedResultsPart1, ExtendedResultsPart2, ExtendedResultsPart3):
    """Complete extended inference results with field-specific types."""
````

</details>

<details><summary>Constants — missing</summary>

No generated artifact has this qualified identity.

**[Reference: Constants](../../../../fixtures/typed.py#L535)**

````python
@final
class Constants:
    """Constants for the test.

    Attributes:
        threshold (int): TODO.
        max_value (int): TODO.
        min_length (int): TODO.
        extended_sentinel (object): TODO.
        extended_context (ContextVar[DictObjectOrNone]): TODO.

    """
    threshold: Final[int] = 5
    max_value: Final[int] = 10
    min_length: Final[int] = 3
    extended_sentinel: Final[object] = object()
    extended_context: ContextVar[DictObjectOrNone] = ContextVar('extended_context', default=None)
````

</details>

<details><summary>MetaClass — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: MetaClass](../../../../fixtures/typed.py#L741)**

````python
class MetaClass(type):
    """Metaclass for testing type inference."""

    def __new__(mcs: TypeValue[MetaClass], name: str, bases: TupleTypeObjectVariadic, namespace: DictObject, **_kwargs: object) -> MetaClass:
        """Create a new class with ``meta_added``.

        Args:
            mcs (TypeValue[MetaClass]): TODO.
            name (str): TODO.
            bases (TupleTypeObjectVariadic): TODO.
            namespace (DictObject): TODO.
            _kwargs (object): TODO.

        Returns:
            MetaClass: TODO.

        """
        namespace['meta_added'] = True
        created: MetaClass = super().__new__(mcs, name, bases, namespace)
        return created

    @override
    def __call__(cls, *args: object, **kwargs: object) -> object:
        """Create instance with ``initialized_by_meta``.

        Args:
            args (object): TODO.
            kwargs (object): TODO.

        Returns:
            object: TODO.

        """
        instance: SupportsInitializedByMeta = super().__call__(*args, **kwargs)
        instance.initialized_by_meta = True
        return instance
````

**[Produced: MetaClass](result.py#L113)**

````python
class MetaClass(type):
    """Metaclass for testing type inference."""

    def __new__(mcs, name: str, bases, namespace, **_kwargs):
        """Create a new class with ``meta_added``.

        Args:
            mcs: TODO.
            name (str): TODO.
            bases: TODO.
            namespace: TODO.
            _kwargs: TODO.

        Returns:
            TODO.
        """
        namespace['meta_added'] = True
        return super().__new__(mcs, name, bases, namespace)

    def __call__(cls, *args, **kwargs):
        """Create instance with ``initialized_by_meta``.

        Args:
            args: TODO.
            kwargs: TODO.

        Returns:
            TODO.
        """
        instance = super().__call__(*args, **kwargs)
        initialized = instance
        initialized.initialized_by_meta = True
        return initialized
````

</details>

<details><summary>BaseClass — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: BaseClass](../../../../fixtures/typed.py#L815)**

````python
class BaseClass:
    """Base class for testing type inference."""

    def __init__(self, x: int, y: IntOrNone=None) -> None:
        """Initialize base class.

        Args:
            x (int): TODO.
            y (IntOrNone): TODO.

        """
        self.x: int = x
        self.y: IntOrNone = y

    def base_method(self, a: int, b: int=10) -> int:
        """Test base method.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """
        return a + b

    @property
    def base_property(self) -> int:
        """Base property getter.

        Returns:
            int: TODO.

        """
        return self.x

    @base_property.setter
    def base_property(self, value: int) -> None:
        """Set base property.

        Args:
            value (int): TODO.

        """
        self.x = value
````

**[Produced: BaseClass](result.py#L179)**

````python
class BaseClass:
    """Base class for testing type inference."""

    def __init__(self, x: int, y: int | None=None) -> None:
        """Initialize base class.

        Args:
            x (int): TODO.
            y (int | None): TODO.
        """
        self.x = x
        self.y = y

    def base_method(self, a: SupportsAddition, b: int=10) -> int:
        """Test base method.

        Args:
            a (SupportsAddition): TODO.
            b (int): TODO.

        Returns:
            int: TODO.
        """
        return a + b

    @property
    def base_property(self):
        """Base property getter.

        Returns:
            TODO.
        """
        return self.x

    @base_property.setter
    def base_property(self, value) -> None:
        """Set base property.

        Args:
            value: TODO.
        """
        self.x = value
````

</details>

<details><summary>DerivedClass — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: DerivedClass](../../../../fixtures/typed.py#L863)**

````python
class DerivedClass(BaseClass, AbstractBase):
    """Derived class for testing type inference."""

    def __init__(self, x: int, y: IntOrNone=None, z: int=0) -> None:
        """Initialize derived class.

        Args:
            x (int): TODO.
            y (IntOrNone): TODO.
            z (int): TODO.

        """
        super().__init__(x=x, y=y)
        self.z: int = z

    @override
    def abstract_method(self, value: int) -> int:
        """Implement abstract method.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.

        """
        return value * 2

    @classmethod
    @override
    def class_method(cls) -> None:
        """Implement class method."""

    @staticmethod
    @override
    def static_method() -> None:
        """Implement static method."""

    def derived_method(self, a: int, b: int, c: int=5, d: int=10) -> int:
        """Test derived method.

        Args:
            a (int): TODO.
            b (int): TODO.
            c (int): TODO.
            d (int): TODO.

        Returns:
            int: TODO.

        """
        if a > b:
            return a - b
        if a < b:
            return b - a
        return c + d
````

**[Produced: DerivedClass](result.py#L223)**

````python
class DerivedClass(BaseClass, AbstractBase):
    """Derived class for testing type inference."""

    def __init__(self, x: int, y: int | None=None, z: int=0) -> None:
        """Initialize derived class.

        Args:
            x (int): TODO.
            y (int | None): TODO.
            z (int): TODO.
        """
        super().__init__(x=x, y=y)
        self.z = z

    def abstract_method(self, value: int) -> int:
        """Implement abstract method.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.
        """
        return value * 2

    @classmethod
    def class_method(cls) -> None:
        """Implement class method."""

    @staticmethod
    def static_method() -> None:
        """Implement static method."""

    def derived_method(self, a: int, b: int, c: int=5, d: int=10) -> int:
        """Test derived method.

        Args:
            a (int): TODO.
            b (int): TODO.
            c (int): TODO.
            d (int): TODO.

        Returns:
            int: TODO.
        """
        if a > b:
            return a - b
        if a < b:
            return b - a
        return c + d
````

</details>

<details><summary>MetaDecoratedClass — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: MetaDecoratedClass](../../../../fixtures/typed.py#L921)**

````python
class MetaDecoratedClass:
    """Class with metaclass for testing."""

    def __init__(self, value: int) -> None:
        """Initialize meta decorated class.

        Args:
            value (int): TODO.

        """
        self.value: int = value
````

**[Produced: MetaDecoratedClass](result.py#L275)**

````python
class MetaDecoratedClass:
    """Class with metaclass for testing."""

    def __init__(self, value) -> None:
        """Initialize meta decorated class.

        Args:
            value: TODO.
        """
        self.value = value
````

</details>

<details><summary>decorator_with_class.Wrapper — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: decorator_with_class.Wrapper](../../../../fixtures/typed.py#L1031)**

````python
class Wrapper:
    """Proxy wrapper created by a class decorator."""

    def __init__(self, *args: object, **_kwargs: object) -> None:
        """TODO.

            Args:
                args (object): TODO.
                _kwargs (object): TODO.

            """
        self.instance: T = cls(*args)

    def __getattr__(self, name: str) -> object:
        """Get attribute from wrapped instance.

            Args:
                name (str): TODO.

            Returns:
                object: TODO.

            """
        return getattr(self.instance, name)
````

**[Produced: decorator_with_class.Wrapper](result.py#L333)**

````python
class Wrapper:
    """Proxy wrapper created by a class decorator."""

    def __init__(self, *args, **kwargs) -> None:
        self.instance = cls(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(self.instance, name)
````

</details>

<details><summary>DataClassExample — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: DataClassExample](../../../../fixtures/typed.py#L1112)**

````python
@dataclass(slots=True)
class DataClassExample:
    """Dataclass for testing type inference.

    Attributes:
        x (int): TODO.
        y (str): TODO.
        z (ListInt): TODO.

    """
    x: int
    y: str = 'default'
    z: ListInt = field(default_factory=list)
````

**[Produced: DataClassExample](result.py#L404)**

````python
@dataclass(init=False)
class DataClassExample:
    """Dataclass-like class for testing type inference."""
    x = None
    y = 'default'
    z = None

    def __init__(self, x, y: str='default', z=None) -> None:
        """Initialize dataclass-like example.

        Args:
            x: TODO.
            y (str): TODO.
            z: TODO.
        """
        self.x = x
        self.y = y
        self.z = [] if z is None else z
````

</details>

<details><summary>function_with_property.PropertyClass — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_property.PropertyClass](../../../../fixtures/typed.py#L1513)**

````python
class PropertyClass:
    """Test property class."""

    def __init__(self) -> None:
        """Initialize property class."""
        self._value: int = 0

    @property
    def value(self) -> int:
        """Get value property.

            Returns:
                int: TODO.

            """
        return self._value

    @value.setter
    def value(self, val: int) -> None:
        """Set value property.

            Args:
                val (int): TODO.

            """
        self._value = val

    @value.deleter
    def value(self) -> None:
        """Delete value property."""
        del self._value
````

**[Produced: function_with_property.PropertyClass](result.py#L811)**

````python
class PropertyClass:
    """Test property class."""

    def __init__(self) -> None:
        """Initialize property class."""
        self._value = 0

    @property
    def value(self):
        """Get value property.

            Returns:
                TODO.
            """
        return self._value

    @value.setter
    def value(self, val) -> None:
        """Set value property.

            Args:
                val: TODO.
            """
        self._value = val

    @value.deleter
    def value(self) -> None:
        """Delete value property."""
        del self._value
````

</details>

<details><summary>function_with_descriptor.Descriptor — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_descriptor.Descriptor](../../../../fixtures/typed.py#L1556)**

````python
class Descriptor:
    """Test descriptor class."""

    def __init__(self) -> None:
        """TODO."""
        self._value: int = 0

    def __get__(self, obj: object, objtype: TypeObject) -> int:
        """Get descriptor value.

            Args:
                obj (object): TODO.
                objtype (TypeObject): TODO.

            Returns:
                int: TODO.

            """
        _ = (obj, objtype)
        return self._value

    def __set__(self, obj: object, value: int) -> None:
        """Set descriptor value.

            Args:
                obj (object): TODO.
                value (int): TODO.

            """
        _ = obj
        self._value = value

    def __delete__(self, obj: object) -> None:
        """Delete descriptor value.

            Args:
                obj (object): TODO.

            """
        _ = obj
        del self._value
````

**[Produced: function_with_descriptor.Descriptor](result.py#L851)**

````python
class Descriptor:
    """Test descriptor class."""

    def __init__(self) -> None:
        self._value = 0

    def __get__(self, obj, objtype) -> int:
        """Get descriptor value.

            Args:
                obj: TODO.
                objtype: TODO.

            Returns:
                int: TODO.
            """
        _ = (obj, objtype)
        return self._value

    def __set__(self, obj, value: int) -> None:
        """Set descriptor value.

            Args:
                obj: TODO.
                value (int): TODO.
            """
        _ = obj
        self._value = value

    def __delete__(self, obj) -> None:
        """Delete descriptor value.

            Args:
                obj: TODO.
            """
        _ = obj
        del self._value
````

</details>

<details><summary>function_with_operator_overloading.Vector — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_operator_overloading.Vector](../../../../fixtures/typed.py#L1611)**

````python
class Vector:
    """Test vector class."""

    def __init__(self, x: int, y: int) -> None:
        """Initialize vector.

            Args:
                x (int): TODO.
                y (int): TODO.

            """
        self.x: int = x
        self.y: int = y

    def __add__(self, other: SupportsAdditionAndXAndY) -> Vector:
        """Add vectors.

            Args:
                other (SupportsAdditionAndXAndY): TODO.

            Returns:
                Vector: TODO.

            """
        return Vector(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other: Vector) -> Vector:
        """Subtract vectors.

            Args:
                other (Vector): TODO.

            Returns:
                Vector: TODO.

            """
        return Vector(x=self.x - other.x, y=self.y - other.y)

    def __mul__(self, scalar: int) -> Vector:
        """Multiply vector by scalar.

            Args:
                scalar (int): TODO.

            Returns:
                Vector: TODO.

            """
        return Vector(x=self.x * scalar, y=self.y * scalar)

    @override
    def __eq__(self, other: object) -> bool:
        """Check vector equality.

            Args:
                other (object): TODO.

            Returns:
                bool: TODO.

            """
        if not isinstance(other, Vector):
            return False
        return self.x == other.x and self.y == other.y

    @override
    def __hash__(self) -> int:
        """Return hash of vector.

            Returns:
                int: TODO.

            """
        return hash((self.x, self.y))

    def __lt__(self, other: Vector) -> bool:
        """Check if vector is less than other.

            Args:
                other (Vector): TODO.

            Returns:
                bool: TODO.

            """
        return self.x < other.x

    @override
    def __repr__(self) -> str:
        """Return vector representation.

            Returns:
                st
````

Preview truncated; full content is in JSON.

**[Produced: function_with_operator_overloading.Vector](result.py#L899)**

````python
class Vector:
    """Test vector class."""

    def __init__(self, x: int, y: int) -> None:
        """Initialize vector.

            Args:
                x (int): TODO.
                y (int): TODO.
            """
        self.x = x
        self.y = y

    def __add__(self, other: Vector) -> Vector:
        """Add vectors.

            Args:
                other (Vector): TODO.

            Returns:
                Vector: TODO.
            """
        return Vector(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other: Vector) -> Vector:
        """Subtract vectors.

            Args:
                other (Vector): TODO.

            Returns:
                Vector: TODO.
            """
        return Vector(x=self.x - other.x, y=self.y - other.y)

    def __mul__(self, scalar: int) -> Vector:
        """Multiply vector by scalar.

            Args:
                scalar (int): TODO.

            Returns:
                Vector: TODO.
            """
        return Vector(x=self.x * scalar, y=self.y * scalar)

    def __eq__(self, other) -> bool:
        """Check vector equality.

            Args:
                other: TODO.

            Returns:
                bool: TODO.
            """
        if not isinstance(other, Vector):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        """Return hash of vector.

            Returns:
                int: TODO.
            """
        return hash((self.x, self.y))

    def __lt__(self, other: Vector) -> bool:
        """Check if vector is less than other.

            Args:
                other (Vector): TODO.

            Returns:
                bool: TODO.
            """
        return self.x < other.x

    def __repr__(self) -> str:
        """Return vector representation.

            Returns:
                str: TODO.
            """
        return f'Vector({self.x}, {self.y})'
````

</details>

<details><summary>function_with_abstract_methods.AbstractImplementation — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_abstract_methods.AbstractImplementation](../../../../fixtures/typed.py#L1780)**

````python
class AbstractImplementation(AbstractBase):
    """Test abstract implementation class."""

    @override
    def abstract_method(self, value: int) -> int:
        """Test abstract method.

            Args:
                value (int): TODO.

            Returns:
                int: TODO.

            """
        return value + 10

    @classmethod
    @override
    def class_method(cls) -> None:
        """Implement class method."""

    @staticmethod
    @override
    def static_method() -> None:
        """Implement static method."""
````

**[Produced: function_with_abstract_methods.AbstractImplementation](result.py#L1051)**

````python
class AbstractImplementation(AbstractBase):
    """Test abstract implementation class."""

    def abstract_method(self, value: int) -> int:
        """Test abstract method.

            Args:
                value (int): TODO.

            Returns:
                int: TODO.
            """
        return value + 10

    @classmethod
    def class_method(cls) -> None:
        """Implement class method."""

    @staticmethod
    def static_method() -> None:
        """Implement static method."""
````

</details>

<details><summary>function_with_protocol.ProtocolImplementation — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_protocol.ProtocolImplementation](../../../../fixtures/typed.py#L1817)**

````python
class ProtocolImplementation:
    """Test protocol implementation class."""

    def protocol_method(self, x: int) -> int:
        """Test protocol method.

            Args:
                x (int): TODO.

            Returns:
                int: TODO.

            """
        return x * 2
````

**[Produced: function_with_protocol.ProtocolImplementation](result.py#L1083)**

````python
class ProtocolImplementation:
    """Test protocol implementation class."""

    def protocol_method(self, x: SupportsMultiplication) -> int:
        """Test protocol method.

            Args:
                x (SupportsMultiplication): TODO.

            Returns:
                int: TODO.
            """
        return x * 2
````

</details>

<details><summary>function_with_matrix_multiplication.Matrix — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_matrix_multiplication.Matrix](../../../../fixtures/typed.py#L2176)**

````python
class Matrix:
    """Test matrix class."""

    def __init__(self, data: ListListInt) -> None:
        """Initialize matrix with data.

            Args:
                data (ListListInt): TODO.

            """
        self.data: ListListInt = data

    def __matmul__(self, other: Matrix) -> Matrix:
        """Matrix multiplication operator.

            Args:
                other (Matrix): TODO.

            Returns:
                Matrix: TODO.

            """
        return Matrix(data=[[sum((a * b for a, b in zip(row, col, strict=True))) for col in zip(*other.data, strict=True)] for row in self.data])
````

**[Produced: function_with_matrix_multiplication.Matrix](result.py#L1400)**

````python
class Matrix:
    """Test matrix class."""

    def __init__(self, data: list[list[int]]) -> None:
        """Initialize matrix with data.

            Args:
                data (list[list[int]]): TODO.
            """
        self.data = data

    def __matmul__(self, other: Matrix) -> Matrix:
        """Matrix multiplication operator.

            Args:
                other (Matrix): TODO.

            Returns:
                Matrix: TODO.
            """
        return Matrix(data=[[sum((a * b for a, b in zip(row, col, strict=False))) for col in zip(*other.data, strict=False)] for row in self.data])
````

</details>

<details><summary>function_with_slots.SlottedClass — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_slots.SlottedClass](../../../../fixtures/typed.py#L2467)**

````python
class SlottedClass:
    """Slotted class for testing.

        Attributes:
            __slots__ (TupleStrVariadic): TODO.

        """
    __slots__: ClassVar[TupleStrVariadic] = ('x', 'y')

    def __init__(self, x: int, y: int) -> None:
        """TODO.

            Args:
                x (int): TODO.
                y (int): TODO.

            """
        self.x: int = x
        self.y: int = y
````

**[Produced: function_with_slots.SlottedClass](result.py#L1696)**

````python
class SlottedClass:
    """Slotted class for testing."""
    __slots__ = ('x', 'y')

    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y
````

</details>

<details><summary>function_with_singleton.Singleton — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_singleton.Singleton](../../../../fixtures/typed.py#L2542)**

````python
class Singleton:
    """Test singleton class.

        Attributes:
            _instance (Self | None): TODO.

        """
    _instance: ClassVar[Self | None] = None

    def __new__(cls) -> Self:
        """Create singleton instance.

            Returns:
                Self: TODO.

            """
        if cls._instance is None:
            cls._instance = super().__new__(cls=cls)
        return cls._instance
````

**[Produced: function_with_singleton.Singleton](result.py#L1749)**

````python
class Singleton:
    """Test singleton class."""
    _instance = None

    def __new__(cls) -> Self:
        """Create singleton instance.

            Returns:
                Self: TODO.
            """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
````

</details>

<details><summary>function_with_factory.Factory — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_factory.Factory](../../../../fixtures/typed.py#L2580)**

````python
class Factory:
    """Test factory class."""

    @staticmethod
    def create(type_name: str) -> TypeA | TypeB | None:
        """Create type for testing.

            Args:
                type_name (str): TODO.

            Returns:
                TypeA | TypeB | None: TODO.

            """
        if type_name == 'a':
            return TypeA()
        if type_name == 'b':
            return TypeB()
        return None
````

**[Produced: function_with_factory.Factory](result.py#L1780)**

````python
class Factory:
    """Test factory class."""

    @staticmethod
    def create(type_name) -> TypeA | TypeB | None:
        """Create type for testing.

            Args:
                type_name: TODO.

            Returns:
                TypeA | TypeB | None: TODO.
            """
        if type_name == 'a':
            return TypeA()
        if type_name == 'b':
            return TypeB()
        return None
````

</details>

<details><summary>function_with_builder.Product — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_builder.Product](../../../../fixtures/typed.py#L2611)**

````python
class Product:
    """Product class for testing."""

    def __init__(self, parts: SequenceStr) -> None:
        """Initialize product with parts.

            Args:
                parts (SequenceStr): TODO.

            """
        self.parts: ListStr = list(parts)
````

**[Produced: function_with_builder.Product](result.py#L1809)**

````python
class Product:
    """Product class for testing."""

    def __init__(self, parts) -> None:
        """Initialize product with parts.

            Args:
                parts: TODO.
            """
        self.parts = list(parts)
````

</details>

<details><summary>function_with_builder.Builder — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_builder.Builder](../../../../fixtures/typed.py#L2623)**

````python
class Builder:
    """Test builder class."""

    def __init__(self) -> None:
        """TODO."""
        self.parts: ListStr = []

    def add_part(self, part: str) -> Self:
        """TODO.

            Args:
                part (str): TODO.

            Returns:
                Self: TODO.

            """
        self.parts.append(part)
        return self

    def build(self) -> Product:
        """TODO.

            Returns:
                Product: TODO.

            """
        return Product(parts=self.parts)
````

**[Produced: function_with_builder.Builder](result.py#L1820)**

````python
class Builder:
    """Test builder class."""

    def __init__(self) -> None:
        self.parts = []

    def add_part(self, part) -> Self:
        self.parts.append(part)
        return self

    def build(self) -> Product:
        return Product(parts=self.parts)
````

</details>

<details><summary>function_with_observer.Observer — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_observer.Observer](../../../../fixtures/typed.py#L2663)**

````python
class Observer:
    """Test observer class."""

    def update(self, message: str) -> None:
        """Update observer with message.

            Args:
                message (str): TODO.

            """
        _ = (self, message)
````

**[Produced: function_with_observer.Observer](result.py#L1843)**

````python
class Observer:
    """Test observer class."""

    def update(self, message) -> None:
        """Update observer with message.

            Args:
                message: TODO.
            """
        _ = (self, message)
````

</details>

<details><summary>function_with_observer.Subject — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_observer.Subject](../../../../fixtures/typed.py#L2675)**

````python
class Subject:
    """Test subject class."""

    def __init__(self) -> None:
        """Initialize subject."""
        self.observers: ListValue[SupportsUpdate] = []

    def attach(self, observer: SupportsUpdate) -> None:
        """Attach observer to subject.

            Args:
                observer (SupportsUpdate): TODO.

            """
        self.observers.append(observer)

    def notify(self, message: str) -> None:
        """Notify all observers with message.

            Args:
                message (str): TODO.

            """
        for observer in self.observers:
            observer.update(message=message)
````

**[Produced: function_with_observer.Subject](result.py#L1854)**

````python
class Subject:
    """Test subject class."""

    def __init__(self) -> None:
        """Initialize subject."""
        self.observers = []

    def attach(self, observer) -> None:
        """Attach observer to subject.

            Args:
                observer: TODO.
            """
        self.observers.append(observer)

    def notify(self, message) -> None:
        """Notify all observers with message.

            Args:
                message: TODO.
            """
        for observer in self.observers:
            observer.update(message)
````

</details>

<details><summary>function_with_strategy.AddStrategy — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_strategy.AddStrategy](../../../../fixtures/typed.py#L2729)**

````python
class AddStrategy(Strategy):
    """Test add strategy."""

    @override
    def execute(self, a: int, b: int) -> int:
        """Execute add strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.

            """
        return a + b
````

**[Produced: function_with_strategy.AddStrategy](result.py#L1904)**

````python
class AddStrategy(Strategy):
    """Test add strategy."""

    def execute(self, a: int, b: int) -> int:
        """Execute add strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.
            """
        return a + b
````

</details>

<details><summary>function_with_strategy.MultiplyStrategy — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_strategy.MultiplyStrategy](../../../../fixtures/typed.py#L2746)**

````python
class MultiplyStrategy(Strategy):
    """Test multiply strategy."""

    @override
    def execute(self, a: int, b: int) -> int:
        """Execute multiply strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.

            """
        return a * b
````

**[Produced: function_with_strategy.MultiplyStrategy](result.py#L1919)**

````python
class MultiplyStrategy(Strategy):
    """Test multiply strategy."""

    def execute(self, a: int, b: int) -> int:
        """Execute multiply strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.
            """
        return a * b
````

</details>

<details><summary>function_with_command.ConcreteCommand — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_command.ConcreteCommand](../../../../fixtures/typed.py#L2792)**

````python
class ConcreteCommand(Command):
    """Test concrete command."""

    def __init__(self, receiver: SupportsAction) -> None:
        """TODO.

            Args:
                receiver (SupportsAction): TODO.

            """
        self.receiver: SupportsAction = receiver

    @override
    def execute(self) -> None:
        """TODO."""
        _ = self.receiver.action()
````

**[Produced: function_with_command.ConcreteCommand](result.py#L1961)**

````python
class ConcreteCommand(Command):
    """Test concrete command."""

    def __init__(self, receiver) -> None:
        self.receiver = receiver

    def execute(self) -> None:
        self.receiver.action()
````

</details>

<details><summary>function_with_chain_of_responsibility.Handler — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_chain_of_responsibility.Handler](../../../../fixtures/typed.py#L2820)**

````python
class Handler:
    """Test handler class."""

    def __init__(self) -> None:
        """Initialize handler."""
        self.next: Handler | None = None

    def set_next(self, handler: Handler) -> Handler:
        """Set next handler.

            Args:
                handler (Handler): TODO.

            Returns:
                Handler: TODO.

            """
        self.next = handler
        return handler

    def handle(self, request: str) -> StrOrNone:
        """Handle request.

            Args:
                request (str): TODO.

            Returns:
                StrOrNone: TODO.

            """
        if self.next is not None:
            return self.next.handle(request=request)
        return None
````

**[Produced: function_with_chain_of_responsibility.Handler](result.py#L1980)**

````python
class Handler:
    """Test handler class."""

    def __init__(self) -> None:
        """Initialize handler."""
        self.next = None

    def set_next(self, handler):
        """Set next handler.

            Args:
                handler: TODO.

            Returns:
                TODO.
            """
        self.next = handler
        return handler

    def handle(self, request) -> None:
        """Handle request.

            Args:
                request: TODO.

            Returns:
                None: TODO.
            """
        if self.next is not None:
            return self.next.handle(request)
        return None
````

</details>

<details><summary>Point — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: Point](../../../../fixtures/typed.py#L3059)**

````python
class Point(NamedTuple):
    """Test point.

    Attributes:
        x (int): TODO.
        y (int): TODO.

    """
    x: int
    y: int
````

**[Produced: Point](result.py#L2196)**

````python
class Point:
    """Test point."""

    def __init__(self, x, y) -> None:
        """Initialize point.

        Args:
            x: TODO.
            y: TODO.
        """
        self.x = x
        self.y = y
````

</details>

<details><summary>SliceExampleResult — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: SliceExampleResult](../../../../fixtures/typed.py#L3455)**

````python
class SliceExampleResult(NamedTuple):
    """Result for list and dictionary slice inference examples.

    Attributes:
        list_slice (ListInt): TODO.
        list_stride_slice (ListInt): TODO.
        dict_slice (DictInt): TODO.
        dict_key_slice (ListStr): TODO.
        dict_value_slice (ListInt): TODO.

    """
    list_slice: ListInt
    list_stride_slice: ListInt
    dict_slice: DictInt
    dict_key_slice: ListStr
    dict_value_slice: ListInt
````

**[Produced: SliceExampleResult](result.py#L2525)**

````python
class SliceExampleResult:
    """Result for list and dictionary slice inference examples."""

    def __init__(self, list_slice, list_stride_slice, dict_slice, dict_key_slice, dict_value_slice) -> None:
        """Initialize slice example result.

        Args:
            list_slice: TODO.
            list_stride_slice: TODO.
            dict_slice: TODO.
            dict_key_slice: TODO.
            dict_value_slice: TODO.
        """
        self.list_slice = list_slice
        self.list_stride_slice = list_stride_slice
        self.dict_slice = dict_slice
        self.dict_key_slice = dict_key_slice
        self.dict_value_slice = dict_value_slice
````

</details>

<details><summary>BuiltinMethodList — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: BuiltinMethodList](../../../../fixtures/typed.py#L3474)**

````python
class BuiltinMethodList(list[int]):
    """List subclass whose method names intentionally shadow builtins."""

    @override
    def append(self, value: int) -> None:
        """Append a doubled integer, unlike ``list.append`` semantics.

        Args:
            value (int): TODO.

        """
        super().append(value * 2)

    @override
    def count(self, value: int) -> int:
        """Return the normal list count plus one for disambiguation.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.

        """
        return super().count(value) + 1
````

**[Produced: BuiltinMethodList](result.py#L2552)**

````python
class BuiltinMethodList(list[int]):
    """List subclass whose method names intentionally shadow builtins."""

    def append(self, value: int) -> None:
        """Append a doubled integer, unlike ``list.append`` semantics.

        Args:
            value (int): TODO.
        """
        super().append(value * 2)

    def count(self, value: int) -> int:
        """Return the normal list count plus one for disambiguation.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.
        """
        return super().count(value) + 1
````

</details>

<details><summary>BuiltinMethodDict — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: BuiltinMethodDict](../../../../fixtures/typed.py#L3501)**

````python
class BuiltinMethodDict(dict[str, int]):
    """Dict subclass with names shared by built-in dict methods."""
````

**[Produced: BuiltinMethodDict](result.py#L2575)**

````python
class BuiltinMethodDict(dict[str, int]):
    """Dict subclass with names shared by built-in dict methods."""

    def get(self, key: str, default: int | str | None=None) -> int:
        """Return a stored value or a narrowed integer default.

        Args:
            key (str): TODO.
            default (int | str | None): TODO.

        Returns:
            int: TODO.
        """
        fallback: int = -1 if default is None else default
        return super().get(key, fallback)

    def update(self, other: DictInt | tuple[()]=(), *values, **kwargs) -> None:
        """Update values while multiplying every incoming integer.

        Args:
            other (dict[str, int] | tuple[()]): TODO.
            values: TODO.
            kwargs: TODO.
            other (dict[str, int] | tuple[()]): TODO.
        """
        incoming: DictInt = dict(other)
        for index, value in enumerate(iterable=values):
            incoming[str(object=index)] = value
        incoming.update(kwargs)
        multiplied = {key: value * 10 for key, value in incoming.items()}
        super().update(multiplied)
````

</details>

<details><summary>CustomAddSet — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: CustomAddSet](../../../../fixtures/typed.py#L3505)**

````python
class CustomAddSet(set[int]):
    """Set subclass with the same method name as a custom class below."""

    @override
    def add(self, element: int) -> None:
        """Add a shifted element.

        Args:
            element (int): TODO.

        """
        super().add(element + 100)
````

**[Produced: CustomAddSet](result.py#L2608)**

````python
class CustomAddSet(set[int]):
    """Set subclass with the same method name as a custom class below."""

    def add(self, element: int) -> None:
        """Add a shifted element.

        Args:
            element (int): TODO.
        """
        super().add(element + 100)
````

</details>

<details><summary>CustomAdder — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: CustomAdder](../../../../fixtures/typed.py#L3519)**

````python
class CustomAdder:
    """Plain custom class with ``add`` sharing a name with ``set.add``."""

    def __init__(self, seed: int) -> None:
        """Initialize custom adder.

        Args:
            seed (int): TODO.

        """
        self.seed: int = seed

    def add(self, element: int) -> int:
        """Return an arithmetic result instead of mutating a set.

        Args:
            element (int): TODO.

        Returns:
            int: TODO.

        """
        return self.seed + element
````

**[Produced: CustomAdder](result.py#L2620)**

````python
class CustomAdder:
    """Plain custom class with ``add`` sharing a name with ``set.add``."""

    def __init__(self, seed: int) -> None:
        """Initialize custom adder.

        Args:
            seed (int): TODO.
        """
        self.seed = seed

    def add(self, element: SupportsRadd) -> int:
        """Return an arithmetic result instead of mutating a set.

        Args:
            element (SupportsRadd): TODO.

        Returns:
            int: TODO.
        """
        return self.seed + element
````

</details>

<details><summary>ImportExampleResult — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: ImportExampleResult](../../../../fixtures/typed.py#L3544)**

````python
class ImportExampleResult(NamedTuple):
    """Result for importlib and ``__import__`` inference examples.

    Attributes:
        importlib_module_name (str): TODO.
        dunder_module_name (str): TODO.
        imported_join_result (str): TODO.

    """
    importlib_module_name: str
    dunder_module_name: str
    imported_join_result: str
````

**[Produced: ImportExampleResult](result.py#L2643)**

````python
class ImportExampleResult:
    """Result for importlib and ``__import__`` inference examples."""

    def __init__(self, importlib_module_name, dunder_module_name, imported_join_result) -> None:
        """Initialize import example result.

        Args:
            importlib_module_name: TODO.
            dunder_module_name: TODO.
            imported_join_result: TODO.
        """
        self.importlib_module_name = importlib_module_name
        self.dunder_module_name = dunder_module_name
        self.imported_join_result = imported_join_result
````

</details>

<details><summary>RedefinitionResult — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: RedefinitionResult](../../../../fixtures/typed.py#L3559)**

````python
class RedefinitionResult(NamedTuple):
    """Result for variable type redefinition examples.

    Attributes:
        first_type_value (int): TODO.
        second_type_value (str): TODO.
        third_type_value (ListInt): TODO.
        union_final_value (DictInt): TODO.

    """
    first_type_value: int
    second_type_value: str
    third_type_value: ListInt
    union_final_value: DictInt
````

**[Produced: RedefinitionResult](result.py#L2664)**

````python
class RedefinitionResult:
    """Result for variable type redefinition examples."""

    def __init__(self, first_type_value, second_type_value, third_type_value, union_final_value) -> None:
        """Initialize redefinition result.

        Args:
            first_type_value: TODO.
            second_type_value: TODO.
            third_type_value: TODO.
            union_final_value: TODO.
        """
        self.first_type_value = first_type_value
        self.second_type_value = second_type_value
        self.third_type_value = third_type_value
        self.union_final_value = union_final_value
````

</details>

<details><summary>ScopeResolutionResult — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: ScopeResolutionResult](../../../../fixtures/typed.py#L3576)**

````python
class ScopeResolutionResult(NamedTuple):
    """Result for same names in nested, class, and module scopes.

    Attributes:
        module_value (str): TODO.
        outer_value (int): TODO.
        inner_value (ListInt): TODO.
        class_value (str): TODO.
        method_and_nested_results (ListValue[float | str]): TODO.

    """
    module_value: str
    outer_value: int
    inner_value: ListInt
    class_value: str
    method_and_nested_results: ListValue[float | str]
````

**[Produced: ScopeResolutionResult](result.py#L2688)**

````python
class ScopeResolutionResult:
    """Result for same names in nested, class, and module scopes."""

    def __init__(self, module_value, outer_value, inner_value, class_value, method_and_nested_results) -> None:
        """Initialize scope resolution result.

        Args:
            module_value: TODO.
            outer_value: TODO.
            inner_value: TODO.
            class_value: TODO.
            method_and_nested_results: TODO.
        """
        self.module_value = module_value
        self.outer_value = outer_value
        self.inner_value = inner_value
        self.class_value = class_value
        self.method_and_nested_results = method_and_nested_results
````

</details>

<details><summary>function_with_scope_resolution.DuplicateScopeNameClass — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_scope_resolution.DuplicateScopeNameClass](../../../../fixtures/typed.py#L3741)**

````python
class DuplicateScopeNameClass:
    """Class with same conceptual name family as outer symbols.

        Attributes:
            duplicated_name (str): TODO.

        """
    duplicated_name: str = 'class'

    def method(self) -> float:
        """Return a method-local value with a reused variable name.

            Returns:
                float: TODO.

            """
        duplicated_name: float = 3.5
        return duplicated_name
````

**[Produced: function_with_scope_resolution.DuplicateScopeNameClass](result.py#L2843)**

````python
class DuplicateScopeNameClass:
    """Class with same conceptual name family as outer symbols."""
    duplicated_name = 'class'

    def method(self) -> float:
        """Return a method-local value with a reused variable name.

            Returns:
                float: TODO.
            """
        return 3.5
````

</details>

<details><summary>ExtendedResult — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: ExtendedResult](../../../../fixtures/typed.py#L3800)**

````python
class ExtendedResult[PayloadT]:
    """Tiny tuple-like result container preserving its payload type."""

    def __init__(self, name: str, payload: PayloadT, metadata: DictObjectOrNone=None) -> None:
        """Store a name, payload, and metadata mapping.

        Args:
            name (str): TODO.
            payload (PayloadT): TODO.
            metadata (DictObjectOrNone): TODO.

        """
        self.name: str = name
        self.payload: PayloadT = payload
        self.metadata: DictObject = {} if metadata is None else metadata

    def __iter__(self) -> Iterator[ValueOrOther[StrOrValue[PayloadT], DictObject]]:
        """Iterate over stored fields.

        Yields:
            ValueOrOther[StrOrValue[PayloadT], DictObject]: TODO.

        """
        yield self.name
        yield self.payload
        yield self.metadata

    def __len__(self) -> int:
        """Return tuple-like field count.

        Returns:
            int: TODO.

        """
        return 3

    @overload
    def __getitem__(self, index: Literal[0, 'name']) -> str:
        ...

    @overload
    def __getitem__(self, index: Literal[1, 'payload']) -> PayloadT:
        ...

    @overload
    def __getitem__(self, index: Literal[2, 'metadata']) -> DictObject:
        ...

    @overload
    def __getitem__(self, index: IntOrStr) -> ValueOrOther[StrOrValue[PayloadT], DictObject]:
        ...

    def __getitem__(self, index: IntOrStr) -> ValueOrOther[StrOrValue[PayloadT], DictObject]:
        """Return one field by index or name.

        Args:
            index (IntOrStr): TODO.

        Returns:
            ValueOrOther[StrOrValue[PayloadT], DictObject]: TODO.

        Raises:
            IndexError: TODO.

        """
        if index in {0, 'name'}:
            return self.name
        if index in {1, 'payload'}:
            return self.payload
        metadata_indexes: set[IntOrStr] = {2, 'metadata'}
        if index in metadata_indexes:
            return self.metadata
        raise I
````

Preview truncated; full content is in JSON.

**[Produced: ExtendedResult](result.py#L2914)**

````python
class ExtendedResult:
    """Tiny tuple-like result container intentionally left untyped."""

    def __init__(self, name: str, payload: list[int], metadata=None) -> None:
        """Store a name, payload, and metadata mapping.

        Args:
            name (str): TODO.
            payload (list[int]): TODO.
            metadata: TODO.
        """
        self.name = name
        self.payload = payload
        self.metadata = {} if metadata is None else metadata

    def __iter__(self):
        """Iterate over stored fields.

        Yields:
            TODO.
        """
        yield self.name
        yield self.payload
        yield self.metadata

    def __len__(self) -> int:
        """Return tuple-like field count.

        Returns:
            int: TODO.
        """
        return 3

    def __getitem__(self, index):
        """Return one field by index or name.

        Args:
            index: TODO.

        Returns:
            TODO.

        Raises:
            IndexError: TODO.
        """
        if index in {0, 'name'}:
            return self.name
        if index in {1, 'payload'}:
            return self.payload
        metadata_indexes: set[int | str] = {2, 'metadata'}
        if index in metadata_indexes:
            return self.metadata
        raise IndexError(index)
````

</details>

<details><summary>ExtendedDataclassStress — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: ExtendedDataclassStress](../../../../fixtures/typed.py#L3887)**

````python
class ExtendedDataclassStress:
    """Dataclass-like class with factory-style defaults."""

    def __init__(self, name: str='anonymous', values: ListInt | None=None, lookup: DictInt | None=None, flags: SetBool | None=None) -> None:
        """Initialize values without leaking mutable defaults.

        Args:
            name (str): TODO.
            values (ListInt | None): TODO.
            lookup (DictInt | None): TODO.
            flags (SetBool | None): TODO.

        """
        self.name: str = name
        self.values: ListInt = [] if values is None else values
        self.lookup: DictInt = {} if lookup is None else lookup
        self.flags: SetBool = set() if flags is None else flags
        _ = self.lookup.setdefault(self.name, len(self.values))
        self.flags.add(self.name in self.lookup)
        self.normalized: TupleValueVariadic[TupleStrInt] = tuple(sorted(self.lookup.items()))
````

**[Produced: ExtendedDataclassStress](result.py#L2969)**

````python
class ExtendedDataclassStress:
    """Dataclass-like class with factory-style defaults."""

    def __init__(self, name: str='anonymous', values=None, lookup=None, flags: set[bool]=None) -> None:
        """Initialize values without leaking mutable defaults.

        Args:
            name (str): TODO.
            values: TODO.
            lookup: TODO.
            flags (set[bool]): TODO.
        """
        self.name = name
        self.values = [] if values is None else values
        self.lookup = {} if lookup is None else lookup
        self.flags = set() if flags is None else flags
        self.lookup.setdefault(self.name, len(self.values))
        self.flags.add(self.name in self.lookup)
        self.normalized = tuple(sorted(self.lookup.items()))
````

</details>

<details><summary>DescriptorWithOwnerCache — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: DescriptorWithOwnerCache](../../../../fixtures/typed.py#L3917)**

````python
class DescriptorWithOwnerCache[ValueT]:
    """Weakly keyed descriptor that preserves its stored value type."""

    def __init__(self, default: ValueT) -> None:
        """Initialize descriptor storage.

        Args:
            default (ValueT): TODO.

        """
        self.default: ValueT = default
        self.storage: WeakKeyDictionary[object, ValueT] = WeakKeyDictionary()
        self.owner: TypeObjectOrNone = None
        self.name: str = ''

    def __set_name__(self, owner: TypeObject, name: str) -> None:
        """Store the owner/name pair.

        Args:
            owner (TypeObject): TODO.
            name (str): TODO.

        """
        self.owner = owner
        self.name = name

    @overload
    def __get__(self, instance: None, owner: TypeObjectOrNone=None) -> Self:
        ...

    @overload
    def __get__(self, instance: object, owner: TypeObjectOrNone=None) -> ValueT:
        ...

    def __get__(self, instance: ObjectOrNone, owner: TypeObjectOrNone=None) -> ValueT | Self:
        """Return descriptor or stored instance value.

        Args:
            instance (ObjectOrNone): TODO.
            owner (TypeObjectOrNone): TODO.

        Returns:
            ValueT | Self: TODO.

        """
        _ = owner
        if instance is None:
            return self
        return self.storage.get(instance, self.default)

    def __set__(self, instance: object, value: ValueT) -> None:
        """Set a value in weak storage.

        Args:
            instance (object): TODO.
            value (ValueT): TODO.

        """
        self.storage[instance] = value

    def __delete__(self, instance: object) -> None:
        """Delete value if present.

        Args:
            instance (object): TODO.

        """
        with suppress(KeyError):
            del self.storage[instance]
````

**[Produced: DescriptorWithOwnerCache](result.py#L2996)**

````python
class DescriptorWithOwnerCache:
    """Descriptor using WeakKeyDictionary to stress descriptor inference."""

    def __init__(self, default: int | str) -> None:
        """Initialize descriptor storage.

        Args:
            default (int | str): TODO.
        """
        self.default = default
        self.storage = WeakKeyDictionary()

    def __set_name__(self, owner, name: str) -> None:
        """Store the owner/name pair.

        Args:
            owner: TODO.
            name (str): TODO.
        """
        self.owner = owner
        self.name = name

    def __get__(self, instance, owner=None) -> Self:
        """Return descriptor or stored instance value.

        Args:
            instance: TODO.
            owner: TODO.

        Returns:
            Self: TODO.
        """
        if instance is None:
            return self
        return self.storage.get(instance, self.default)

    def __set__(self, instance, value) -> None:
        """Set a value in weak storage.

        Args:
            instance: TODO.
            value: TODO.
        """
        self.storage[instance] = value

    def __delete__(self, instance) -> None:
        """Delete value if present.

        Args:
            instance: TODO.
        """
        with suppress(KeyError):
            del self.storage[instance]
````

</details>

<details><summary>DescriptorSummary — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DescriptorSummary](../../../../fixtures/typed.py#L3998)**

````python
class DescriptorSummary(TypedDict):
    """Cached descriptor value snapshot."""
    score: int
    label: str
````

</details>

<details><summary>DescriptorStressOwner — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: DescriptorStressOwner](../../../../fixtures/typed.py#L4005)**

````python
class DescriptorStressOwner:
    """Owner class for descriptor stress.

    Attributes:
        score (DescriptorWithOwnerCacheInt): TODO.
        label (DescriptorWithOwnerCache[str]): TODO.

    """
    score: ClassVar[DescriptorWithOwnerCacheInt] = DescriptorWithOwnerCache(default=0)
    label: ClassVar[DescriptorWithOwnerCache[str]] = DescriptorWithOwnerCache(default='unset')

    def __init__(self, score: int, label: str) -> None:
        """Initialize descriptor-backed fields.

        Args:
            score (int): TODO.
            label (str): TODO.

        """
        self.score = score
        self.label = label

    @cached_property
    def summary(self) -> DescriptorSummary:
        """Return cached mixed summary.

        Returns:
            DescriptorSummary: TODO.

        """
        return {'score': self.score, 'label': self.label}
````

**[Produced: DescriptorStressOwner](result.py#L3051)**

````python
class DescriptorStressOwner:
    """Owner class for descriptor stress."""
    score = DescriptorWithOwnerCache(default=0)
    label = DescriptorWithOwnerCache(default='unset')

    def __init__(self, score: int, label: str) -> None:
        """Initialize descriptor-backed fields.

        Args:
            score (int): TODO.
            label (str): TODO.
        """
        self.score = score
        self.label = label

    @cached_property
    def summary(self):
        """Return cached mixed summary.

        Returns:
            TODO.
        """
        return {'score': self.score, 'label': self.label}
````

</details>

<details><summary>RegistryMeta — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: RegistryMeta](../../../../fixtures/typed.py#L4043)**

````python
class RegistryMeta(type):
    """Metaclass that registers subclasses and injects attributes.

    Attributes:
        registry (DictRegistryMeta): TODO.

    """
    registry: ClassVar[DictRegistryMeta] = {}

    def __new__(mcls: TypeValue[RegistryMeta], name: str, bases: TupleTypeObjectVariadic, namespace: DictObject, **_kwargs: object) -> RegistryMeta:
        """Create class and register it by lower-case name.

        Args:
            mcls (TypeValue[RegistryMeta]): TODO.
            name (str): TODO.
            bases (TupleTypeObjectVariadic): TODO.
            namespace (DictObject): TODO.
            _kwargs (object): TODO.

        Returns:
            RegistryMeta: TODO.

        """
        _ = namespace.setdefault('created_by_registry_meta', True)
        cls: RegistryMeta = super().__new__(mcls, name, bases, namespace)
        if not name.startswith('Abstract'):
            mcls.registry[name.lower()] = cls
        return cls

    @override
    def __call__[InstanceT: RegistryBase](cls: RegistryMeta | TypeValue[InstanceT], *args: object, **kwargs: object) -> InstanceT:
        """Create instance and mark it.

        Args:
            args (object): TODO.
            kwargs (object): TODO.

        Returns:
            InstanceT: TODO.

        """
        instance: InstanceT = super().__call__(*args, **kwargs)
        instance.registry_key = cls.__name__.lower()
        return instance
````

**[Produced: RegistryMeta](result.py#L3077)**

````python
class RegistryMeta(type):
    """Metaclass that registers subclasses and injects attributes."""
    registry = None

    def __new__(mcls, name: str, bases, namespace, **_kwargs):
        """Create class and register it by lower-case name.

        Args:
            mcls: TODO.
            name (str): TODO.
            bases: TODO.
            namespace: TODO.
            _kwargs: TODO.

        Returns:
            TODO.
        """
        namespace.setdefault('created_by_registry_meta', True)
        cls = super().__new__(mcls, name, bases, namespace)
        if mcls.registry is None:
            mcls.registry = {}
        if not name.startswith('Abstract'):
            mcls.registry[name.lower()] = cls
        return cls

    def __call__(cls, *args, **_kwargs):
        """Create instance and mark it.

        Args:
            args: TODO.
            _kwargs: TODO.

        Returns:
            TODO.
        """
        instance = super().__call__(*args, **_kwargs)
        instance.registry_key = cls.__name__.lower()
        return instance
````

</details>

<details><summary>RegistryBase — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: RegistryBase](../../../../fixtures/typed.py#L4100)**

````python
class RegistryBase(metaclass=RegistryMeta):
    """Base class using RegistryMeta."""
    registry_key: str = ''

    def clone(self, **overrides: object) -> Self:
        """Clone using the current instance dictionary.

        Args:
            overrides (object): TODO.

        Returns:
            Self: TODO.

        """
        data: DictObject = dict(self.__dict__)
        data.update(overrides)
        return self.__class__(**data)
````

**[Produced: RegistryBase](result.py#L3118)**

````python
class RegistryBase(metaclass=RegistryMeta):
    """Base class using RegistryMeta."""

    def clone(self, **overrides):
        """Clone using the current instance dictionary.

        Args:
            overrides: TODO.

        Returns:
            TODO.
        """
        data: DictInt = dict(self.__dict__)
        data.update(overrides)
        return self.__class__(**data)
````

</details>

<details><summary>RegistryItem — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: RegistryItem](../../../../fixtures/typed.py#L4120)**

````python
class RegistryItem(RegistryBase):
    """Concrete registry item."""

    def __init__(self, name: str, count: int=0, tags: ListStr | None=None, **extras: object) -> None:
        """Initialize with optional tags and arbitrary extras.

        Args:
            name (str): TODO.
            count (int): TODO.
            tags (ListStr | None): TODO.
            extras (object): TODO.

        """
        self.name: str = name
        self.count: int = count
        self.tags: ListStr = [] if tags is None else tags
        self.extras: DictObject = extras

    def bump(self, amount: int=1) -> Self:
        """Increment count and return self for chaining.

        Args:
            amount (int): TODO.

        Returns:
            Self: TODO.

        """
        self.count += amount
        return self
````

**[Produced: RegistryItem](result.py#L3135)**

````python
class RegistryItem(RegistryBase):
    """Concrete registry item."""

    def __init__(self, name: str, count: int=0, tags=None, **extras) -> None:
        """Initialize with optional tags and arbitrary extras.

        Args:
            name (str): TODO.
            count (int): TODO.
            tags: TODO.
            extras: TODO.
        """
        self.name = name
        self.count = count
        self.tags = [] if tags is None else tags
        self.extras = extras

    def bump(self, amount: int=1) -> Self:
        """Increment count and return self for chaining.

        Args:
            amount (int): TODO.

        Returns:
            Self: TODO.
        """
        self.count += amount
        return self
````

</details>

<details><summary>FluentBuilder — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: FluentBuilder](../../../../fixtures/typed.py#L4158)**

````python
class FluentBuilder:
    """Builder with fluent methods and conditional finalization."""

    def __init__(self) -> None:
        """Initialize builder state."""
        self.parts: ListStr = []
        self.options: DictObject = {}

    def add(self, part: str, *, repeat: int=1) -> Self:
        """Add repeated parts and return self.

        Args:
            part (str): TODO.
            repeat (int): TODO.

        Returns:
            Self: TODO.

        """
        for _ in range(repeat):
            self.parts.append(part)
        return self

    def configure(self, **options: object) -> Self:
        """Merge options and return self.

        Args:
            options (object): TODO.

        Returns:
            Self: TODO.

        """
        self.options.update(options)
        return self

    @overload
    def build(self, *, compact: Literal[True]) -> str:
        ...

    @overload
    def build(self, *, compact: Literal[False]=False) -> BuilderStructured:
        ...

    @overload
    def build(self, *, compact: bool) -> StrOrBuilderStructured:
        ...

    def build(self, *, compact: bool=False) -> StrOrBuilderStructured:
        """Return a compact string or a structured result.

        Args:
            compact (bool): TODO.

        Returns:
            StrOrBuilderStructured: TODO.

        """
        if compact:
            return ':'.join(self.parts)
        return {'parts': list(self.parts), 'options': dict(self.options)}
````

**[Produced: FluentBuilder](result.py#L3165)**

````python
class FluentBuilder:
    """Builder with fluent methods and conditional finalization."""

    def __init__(self) -> None:
        """Initialize builder state."""
        self.parts = []
        self.options = {}

    def add(self, part: str, *, repeat: int=1) -> Self:
        """Add repeated parts and return self.

        Args:
            part (str): TODO.
            repeat (int): TODO.

        Returns:
            Self: TODO.
        """
        for _ in range(repeat):
            self.parts.append(part)
        return self

    def configure(self, **options) -> Self:
        """Merge options and return self.

        Args:
            options: TODO.

        Returns:
            Self: TODO.
        """
        self.options.update(options)
        return self

    def build(self, *, compact: bool=False):
        """Return a compact string or a structured result.

        Args:
            compact (bool): TODO.

        Returns:
            TODO.
        """
        if compact:
            return ':'.join(self.parts)
        return {'parts': list(self.parts), 'options': dict(self.options)}
````

</details>

<details><summary>HybridContainer — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: HybridContainer](../../../../fixtures/typed.py#L4222)**

````python
class HybridContainer[ItemT, NamedT]:
    """Typed positional and named storage with distinct element types."""

    def __init__(self, *items: ItemT, **named: NamedT) -> None:
        """Initialize mixed storage.

        Args:
            items (ItemT): TODO.
            named (NamedT): TODO.

        """
        self.items: ListValue[ItemT] = list(items)
        self.named: dict[str, NamedT] = dict(named)

    def __iter__(self) -> Iterator[ItemT]:
        """Iterate over positional items.

        Returns:
            Iterator[ItemT]: TODO.

        """
        return iter(self.items)

    def __contains__(self, item: object) -> bool:
        """Check both positional and named storage.

        Args:
            item (object): TODO.

        Returns:
            bool: TODO.

        """
        return item in self.items or item in self.named

    @overload
    def __getitem__(self, key: int) -> ItemT:
        ...

    @overload
    def __getitem__(self, key: str) -> NamedT:
        ...

    def __getitem__(self, key: IntOrStr) -> ValueOrOther[ItemT, NamedT]:
        """Return item by int index or dict key.

        Args:
            key (IntOrStr): TODO.

        Returns:
            ValueOrOther[ItemT, NamedT]: TODO.

        """
        if isinstance(key, int):
            return self.items[key]
        return self.named[key]

    @overload
    def __setitem__(self, key: int, value: ItemT) -> None:
        ...

    @overload
    def __setitem__(self, key: str, value: NamedT) -> None:
        ...

    def __setitem__(self, key: IntOrStr, value: ValueOrOther[ItemT, NamedT]) -> None:
        """Set item by int index or dict key.

        Args:
            key (IntOrStr): TODO.
            value (ValueOrOther[ItemT, NamedT]): TODO.

        """
        if isinstance(key, int):
            self.items[key] = cast(typ='ItemT', val=value)
        else:
            self.named[key] = cast(typ='NamedT', val=value)

    def __or__(self, other: ValueOrOther[HybridContainer
````

Preview truncated; full content is in JSON.

**[Produced: HybridContainer](result.py#L3213)**

````python
class HybridContainer:
    """Container exposing list-like and dict-like operations."""

    def __init__(self, *items, **named) -> None:
        """Initialize mixed storage.

        Args:
            items: TODO.
            named: TODO.
        """
        self.items = list(items)
        self.named = dict(named)

    def __iter__(self):
        """Iterate over positional items.

        Returns:
            TODO.
        """
        return iter(self.items)

    def __contains__(self, item) -> bool:
        """Check both positional and named storage.

        Args:
            item: TODO.

        Returns:
            bool: TODO.
        """
        return item in self.items or item in self.named

    def __getitem__(self, key) -> int:
        """Return item by int index or dict key.

        Args:
            key: TODO.

        Returns:
            int: TODO.
        """
        if isinstance(key, int):
            return self.items[key]
        return self.named[key]

    def __setitem__(self, key, value) -> None:
        """Set item by int index or dict key.

        Args:
            key: TODO.
            value: TODO.
        """
        if isinstance(key, int):
            self.items[key] = value
        else:
            self.named[key] = value

    def __or__(self, other):
        """Merge with another container or mapping.

        Args:
            other: TODO.

        Returns:
            TODO.
        """
        merged: HybridContainer = HybridContainer(*self.items, **self.named)
        if isinstance(other, HybridContainer):
            merged.items.extend(other.items)
            merged.named.update(other.named)
        else:
            merged.named.update(other)
        return merged
````

</details>

<details><summary>CallableObject — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: CallableObject](../../../../fixtures/typed.py#L4322)**

````python
class CallableObject:
    """Callable object with state-dependent returns."""

    def __init__(self, mode: str) -> None:
        """Store call mode.

        Args:
            mode (str): TODO.

        """
        self.mode: str = mode

    def __call__[ValueT](self, value: ValueT, *, scale: int=1) -> IntOrStr | CallablePayload[ValueT]:
        """Return different types based on mode.

        Args:
            value (ValueT): TODO.
            scale (int): TODO.

        Returns:
            IntOrStr | CallablePayload[ValueT]: TODO.

        """
        if self.mode == 'number' and isinstance(value, int):
            return value * scale
        if self.mode == 'text':
            return str(object=value) * scale
        return {'value': value, 'scale': scale}
````

**[Produced: CallableObject](result.py#L3288)**

````python
class CallableObject:
    """Callable object with state-dependent returns."""

    def __init__(self, mode: str) -> None:
        """Store call mode.

        Args:
            mode (str): TODO.
        """
        self.mode = mode

    def __call__(self, value: int, *, scale: int=1) -> int | str | DictInt:
        """Return different types based on mode.

        Args:
            value (int): TODO.
            scale (int): TODO.

        Returns:
            int | str | dict[str, int]: TODO.
        """
        if self.mode == 'number':
            return value * scale
        if self.mode == 'text':
            return str(object=value) * scale
        return {'value': value, 'scale': scale}
````

</details>

<details><summary>AsyncResource — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: AsyncResource](../../../../fixtures/typed.py#L4357)**

````python
class AsyncResource:
    """Async resource with enter/exit methods."""

    def __init__(self, name: str) -> None:
        """Initialize resource.

        Args:
            name (str): TODO.

        """
        self.name: str = name
        self.events: ListStr = []

    async def __aenter__(self) -> Self:
        """Enter async context.

        Returns:
            Self: TODO.

        """
        self.events.append('enter')
        return self

    async def __aexit__(self, exc_type: TypeValue[BaseException] | None, exc: BaseException | None, tb: object) -> bool:
        """Exit async context.

        Args:
            exc_type (TypeValue[BaseException] | None): TODO.
            exc (BaseException | None): TODO.
            tb (object): TODO.

        Returns:
            bool: TODO.

        """
        _ = (exc, tb)
        self.events.append('exit')
        return exc_type is None

    async def fetch(self, value: int) -> AsyncPayload:
        """Return async payload.

        Args:
            value (int): TODO.

        Returns:
            AsyncPayload: TODO.

        """
        await sleep(delay=0)
        return {'resource': self.name, 'value': value}
````

**[Produced: AsyncResource](result.py#L3316)**

````python
class AsyncResource:
    """Async resource with enter/exit methods."""

    def __init__(self, name) -> None:
        """Initialize resource.

        Args:
            name: TODO.
        """
        self.name = name
        self.events = []

    async def __aenter__(self):
        """Enter async context.

        Returns:
            TODO.
        """
        self.events.append('enter')
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context.

        Args:
            exc_type: TODO.
            exc: TODO.
            tb: TODO.

        Returns:
            TODO.
        """
        self.events.append('exit')
        return exc_type is None

    async def fetch(self, value):
        """Return async payload.

        Args:
            value: TODO.

        Returns:
            TODO.
        """
        await asyncio.sleep(delay=0)
        return {'resource': self.name, 'value': value}
````

</details>

<details><summary>function_with_local_class_closure_stress.LocalMultiplier — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_local_class_closure_stress.LocalMultiplier](../../../../fixtures/typed.py#L5219)**

````python
class LocalMultiplier:
    """Local class closing over multiplier."""

    def __init__(self, offset: int=0) -> None:
        """TODO.

            Args:
                offset (int): TODO.

            """
        self.offset: int = offset

    def apply(self, value: int) -> int:
        """TODO.

            Args:
                value (int): TODO.

            Returns:
                int: TODO.

            """
        return value * multiplier + self.offset

    @classmethod
    def from_values(cls, values: SequenceInt) -> Self:
        """TODO.

            Args:
                values (SequenceInt): TODO.

            Returns:
                Self: TODO.

            """
        return cls(offset=sum(values))
````

**[Produced: function_with_local_class_closure_stress.LocalMultiplier](result.py#L3945)**

````python
class LocalMultiplier:
    """Local class closing over multiplier."""

    def __init__(self, offset: int=0) -> None:
        self.offset = offset

    def apply(self, value: SupportsMultiplication2) -> int:
        return value * multiplier + self.offset

    @classmethod
    def from_values(cls, values: Iterable):
        return cls(offset=sum(values))
````

</details>

<details><summary>function_with_deep_attribute_assignment.Node — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: function_with_deep_attribute_assignment.Node](../../../../fixtures/typed.py#L5375)**

````python
class Node:
    """TODO."""

    def __init__(self, name: str) -> None:
        """TODO.

            Args:
                name (str): TODO.

            """
        self.name: str = name
        self.children: ListValue[Node] = []
        self.metadata: NodeMetadata = {}
        self.parent: Node | None = None

    def add(self, child: Node) -> Node:
        """TODO.

            Args:
                child (Node): TODO.

            Returns:
                Node: TODO.

            """
        self.children.append(child)
        child.parent = self
        return child
````

**[Produced: function_with_deep_attribute_assignment.Node](result.py#L4045)**

````python
class Node:

    def __init__(self, name) -> None:
        self.name = name
        self.children = []
        self.metadata = {}

    def add(self, child):
        self.children.append(child)
        child.parent = self
        return child
````

</details>

<details><summary>SupportsUpdate — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsUpdate](result.py#L56)**

````python
class SupportsUpdate:
    """Protocol for observer-like objects."""

    def update(self, message) -> None:
        """Receive an update message.

        Args:
            message: TODO.
        """
````

</details>

<details><summary>SupportsExecuteInt — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsExecuteInt](result.py#L67)**

````python
class SupportsExecuteInt:
    """Protocol for integer strategies."""

    def execute(self, a, b) -> None:
        """Execute with two integer inputs.

        Args:
            a: TODO.
            b: TODO.
        """
````

</details>

<details><summary>SupportsAction — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsAction](result.py#L79)**

````python
class SupportsAction:
    """Protocol for receiver objects."""

    def action(self) -> None:
        """Perform the action."""
````

</details>

<details><summary>SupportsInitializedByMeta — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsInitializedByMeta](result.py#L86)**

````python
class SupportsInitializedByMeta:
    """Protocol for objects initialized by metaclass."""
    initialized_by_meta = None
````

</details>

<details><summary>SupportsNewMethod — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsNewMethod](result.py#L92)**

````python
class SupportsNewMethod:
    """Protocol for objects with new_method."""

    def new_method(self) -> None:
        """Return new method for testing."""
````

</details>

<details><summary>SupportsVector — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsVector](result.py#L99)**

````python
class SupportsVector:
    """Protocol for vector-like objects."""
    x = None
    y = None

    def __add__(self, other: int) -> int | Self:
        """Add vectors.

        Args:
            other (int): TODO.
        """
````

</details>

### Declaration uses

<details><summary>StrOrBufferOrSupportsIntOrSupportsIndex — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrBufferOrSupportsIntOrSupportsIndex](../../../../fixtures/typed.py#L89)**

````python
0 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListInt](../../../../fixtures/typed.py#L92)**

````python
75 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DictInt — changed</summary>

Compare the expected and produced contracts below; this comparison does not establish inference causes.

**[Reference: DictInt](../../../../fixtures/typed.py#L93)**

````python
23 resolved AST read references. Dynamic access and string forward references are not counted.
````

**[Produced: DictInt](result.py#L49)**

````python
40 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListIntOrDictIntOrStrOrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListIntOrDictIntOrStrOrInt](../../../../fixtures/typed.py#L94)**

````python
9 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableSequenceSequenceIntListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableSequenceSequenceIntListInt](../../../../fixtures/typed.py#L95)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DictObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictObject](../../../../fixtures/typed.py#L98)**

````python
18 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleExtendedResultListIntStrIntBool — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleExtendedResultListIntStrIntBool](../../../../fixtures/typed.py#L99)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>MappingStrObjectOrSequenceObjectOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MappingStrObjectOrSequenceObjectOrNone](../../../../fixtures/typed.py#L102)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleIntIntOrListObjectOrDictObjectOrStrOrObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntIntOrListObjectOrDictObjectOrStrOrObject](../../../../fixtures/typed.py#L105)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>MutableMappingStrObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MutableMappingStrObject](../../../../fixtures/typed.py#L108)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListStr](../../../../fixtures/typed.py#L112)**

````python
28 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListObject](../../../../fixtures/typed.py#L113)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SetInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SetInt](../../../../fixtures/typed.py#L114)**

````python
7 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SetBool — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SetBool](../../../../fixtures/typed.py#L115)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TypeObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeObject](../../../../fixtures/typed.py#L116)**

````python
28 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TypeObjectOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeObjectOrNone](../../../../fixtures/typed.py#L117)**

````python
4 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleTypeObjectVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleTypeObjectVariadic](../../../../fixtures/typed.py#L118)**

````python
11 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>IntOrStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrStr](../../../../fixtures/typed.py#L119)**

````python
17 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>IntOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrNone](../../../../fixtures/typed.py#L120)**

````python
13 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>StrOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrNone](../../../../fixtures/typed.py#L121)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>IntOrFloat — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrFloat](../../../../fixtures/typed.py#L122)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>IntOrStrOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrStrOrNone](../../../../fixtures/typed.py#L123)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>StrOrBoolOrListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrBoolOrListInt](../../../../fixtures/typed.py#L124)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntVariadic](../../../../fixtures/typed.py#L125)**

````python
22 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleIntStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntStr](../../../../fixtures/typed.py#L126)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleStrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleStrInt](../../../../fixtures/typed.py#L127)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleStrVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleStrVariadic](../../../../fixtures/typed.py#L128)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleIntVariadicStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntVariadicStr](../../../../fixtures/typed.py#L129)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleBoolVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleBoolVariadic](../../../../fixtures/typed.py#L130)**

````python
6 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleIntOrNoneVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntOrNoneVariadic](../../../../fixtures/typed.py#L131)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleIntOrNoneStrOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntOrNoneStrOrNone](../../../../fixtures/typed.py#L132)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListTupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListTupleIntVariadic](../../../../fixtures/typed.py#L133)**

````python
7 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListTupleIntStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListTupleIntStr](../../../../fixtures/typed.py#L134)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListTupleIntOrNoneStrOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListTupleIntOrNoneStrOrNone](../../../../fixtures/typed.py#L135)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleListIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListIntVariadic](../../../../fixtures/typed.py#L136)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleDictIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleDictIntVariadic](../../../../fixtures/typed.py#L137)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleListStrVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListStrVariadic](../../../../fixtures/typed.py#L138)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleSetIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleSetIntVariadic](../../../../fixtures/typed.py#L139)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DictListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictListInt](../../../../fixtures/typed.py#L140)**

````python
5 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DictIntInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictIntInt](../../../../fixtures/typed.py#L141)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DictStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictStr](../../../../fixtures/typed.py#L142)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DictTupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictTupleIntVariadic](../../../../fixtures/typed.py#L143)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DictDictTupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictDictTupleIntVariadic](../../../../fixtures/typed.py#L144)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>MappingStrObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MappingStrObject](../../../../fixtures/typed.py#L145)**

````python
4 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SequenceInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SequenceInt](../../../../fixtures/typed.py#L146)**

````python
12 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SequenceStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SequenceStr](../../../../fixtures/typed.py#L147)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SequenceSequenceInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SequenceSequenceInt](../../../../fixtures/typed.py#L148)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableIntInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableIntInt](../../../../fixtures/typed.py#L149)**

````python
6 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableIntIntInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableIntIntInt](../../../../fixtures/typed.py#L150)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableVariadicInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableVariadicInt](../../../../fixtures/typed.py#L151)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableStr](../../../../fixtures/typed.py#L152)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableNone](../../../../fixtures/typed.py#L153)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>AwaitableInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: AwaitableInt](../../../../fixtures/typed.py#L154)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>GeneratorInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: GeneratorInt](../../../../fixtures/typed.py#L155)**

````python
5 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>GeneratorIntIntOrStrOrNoneInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: GeneratorIntIntOrStrOrNoneInt](../../../../fixtures/typed.py#L156)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DequeInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DequeInt](../../../../fixtures/typed.py#L157)**

````python
4 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CounterInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CounterInt](../../../../fixtures/typed.py#L158)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>OrderedDictStrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: OrderedDictStrInt](../../../../fixtures/typed.py#L159)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DefaultdictStrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DefaultdictStrInt](../../../../fixtures/typed.py#L160)**

````python
6 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DefaultdictStrListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DefaultdictStrListInt](../../../../fixtures/typed.py#L161)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DefaultdictStrDefaultdictStrListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DefaultdictStrDefaultdictStrListInt](../../../../fixtures/typed.py#L162)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableParametersToResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableParametersToResult](../../../../fixtures/typed.py#L168)**

````python
16 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableValueToResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableValueToResult](../../../../fixtures/typed.py#L171)**

````python
5 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListValue](../../../../fixtures/typed.py#L172)**

````python
14 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SequenceValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SequenceValue](../../../../fixtures/typed.py#L173)**

````python
10 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>MappingValueToResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: MappingValueToResult](../../../../fixtures/typed.py#L174)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TypeValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeValue](../../../../fixtures/typed.py#L175)**

````python
8 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleValueVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleValueVariadic](../../../../fixtures/typed.py#L176)**

````python
8 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ValueOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrNone](../../../../fixtures/typed.py#L177)**

````python
8 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ValueOrInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrInt](../../../../fixtures/typed.py#L178)**

````python
7 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ValueOrIntOrStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrIntOrStr](../../../../fixtures/typed.py#L179)**

````python
0 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ValueOrListObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrListObject](../../../../fixtures/typed.py#L180)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>StrOrValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrValue](../../../../fixtures/typed.py#L181)**

````python
5 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>StrOrValueOrDictObject — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrValueOrDictObject](../../../../fixtures/typed.py#L182)**

````python
0 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ValueOrOther — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrOther](../../../../fixtures/typed.py#L183)**

````python
21 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ValueOrOtherOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ValueOrOtherOrNone](../../../../fixtures/typed.py#L184)**

````python
0 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleStrValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleStrValue](../../../../fixtures/typed.py#L185)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ObjectOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ObjectOrNone](../../../../fixtures/typed.py#L188)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DictObjectOrNone — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictObjectOrNone](../../../../fixtures/typed.py#L189)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DictRegistryMeta — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DictRegistryMeta](../../../../fixtures/typed.py#L190)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>StrOrBuilderStructured — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrBuilderStructured](../../../../fixtures/typed.py#L191)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>StrOrDictStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: StrOrDictStr](../../../../fixtures/typed.py#L192)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListRecursiveChild — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListRecursiveChild](../../../../fixtures/typed.py#L193)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListNormalizedRow — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListNormalizedRow](../../../../fixtures/typed.py#L194)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListException — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListException](../../../../fixtures/typed.py#L195)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>ListListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: ListListInt](../../../../fixtures/typed.py#L196)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>DescriptorWithOwnerCacheInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: DescriptorWithOwnerCacheInt](../../../../fixtures/typed.py#L197)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TypeAbstractBase — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeAbstractBase](../../../../fixtures/typed.py#L198)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TypeSupportsValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeSupportsValue](../../../../fixtures/typed.py#L199)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TypeSupportsClassMethods — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TypeSupportsClassMethods](../../../../fixtures/typed.py#L200)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableIntOrStrToIntOrStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableIntOrStrToIntOrStr](../../../../fixtures/typed.py#L203)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallablePayloadInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallablePayloadInt](../../../../fixtures/typed.py#L204)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallablePayloadStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallablePayloadStr](../../../../fixtures/typed.py#L205)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>IntOrStrOrCallablePayloadInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrStrOrCallablePayloadInt](../../../../fixtures/typed.py#L206)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>IntOrStrOrCallablePayloadStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: IntOrStrOrCallablePayloadStr](../../../../fixtures/typed.py#L207)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>HybridContainerIntOrFloatStrOrBoolOrListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: HybridContainerIntOrFloatStrOrBoolOrListInt](../../../../fixtures/typed.py#L208)**

````python
4 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleListTupleIntVariadicVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListTupleIntVariadicVariadic](../../../../fixtures/typed.py#L211)**

````python
4 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleAsyncPayloadListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleAsyncPayloadListInt](../../../../fixtures/typed.py#L212)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleListIntListStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListIntListStr](../../../../fixtures/typed.py#L213)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleListIntIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListIntIntVariadic](../../../../fixtures/typed.py#L214)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleDefaultdictStrIntListStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleDefaultdictStrIntListStr](../../../../fixtures/typed.py#L215)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleListIntDictIntIntGeneratorInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListIntDictIntIntGeneratorInt](../../../../fixtures/typed.py#L216)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic](../../../../fixtures/typed.py#L219)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleListNormalizedRowDictListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleListNormalizedRowDictListInt](../../../../fixtures/typed.py#L222)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleBuilderStructuredStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleBuilderStructuredStr](../../../../fixtures/typed.py#L223)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleDescriptorSummaryIntStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleDescriptorSummaryIntStr](../../../../fixtures/typed.py#L224)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleRegistryItemVariadicListStr — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleRegistryItemVariadicListStr](../../../../fixtures/typed.py#L225)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleIntFloatVariadicListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntFloatVariadicListInt](../../../../fixtures/typed.py#L228)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleIntVariadicGeneratorIntIntOrStrOrNoneInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntVariadicGeneratorIntIntOrStrOrNoneInt](../../../../fixtures/typed.py#L231)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt](../../../../fixtures/typed.py#L234)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleHybridContainerIntOrFloatStrOrBoolOrListIntBoolListInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleHybridContainerIntOrFloatStrOrBoolOrListIntBoolListInt](../../../../fixtures/typed.py#L237)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleIntOrStrOrCallablePayloadIntIntOrStrOrCallablePayloadStrVariadic — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleIntOrStrOrCallablePayloadIntIntOrStrOrCallablePayloadStrVariadic](../../../../fixtures/typed.py#L240)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleSupportsMetadataAndNameVariadicNodeMetadata — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleSupportsMetadataAndNameVariadicNodeMetadata](../../../../fixtures/typed.py#L246)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>TupleBytearrayMemoryviewBytesInt — missing</summary>

No generated artifact has this qualified identity.

**[Reference: TupleBytearrayMemoryviewBytesInt](../../../../fixtures/typed.py#L249)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>UnpackingStressResult — missing</summary>

No generated artifact has this qualified identity.

**[Reference: UnpackingStressResult](../../../../fixtures/typed.py#L252)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableExamples — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableExamples](../../../../fixtures/typed.py#L255)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsMetadataAndName — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsMetadataAndName](../../../../fixtures/typed.py#L265)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsUpdate — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsUpdate](../../../../fixtures/typed.py#L557)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsExecute — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsExecute](../../../../fixtures/typed.py#L570)**

````python
0 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsAction — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsAction](../../../../fixtures/typed.py#L587)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsClassMethodAndInstanceMethodAndStaticMethod — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsClassMethodAndInstanceMethodAndStaticMethod](../../../../fixtures/typed.py#L600)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsValue — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsValue](../../../../fixtures/typed.py#L618)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsMatrixMultiplicationAndData — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsMatrixMultiplicationAndData](../../../../fixtures/typed.py#L632)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsInstance — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsInstance](../../../../fixtures/typed.py#L642)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsJoin — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsJoin](../../../../fixtures/typed.py#L648)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsNameAndPath — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsNameAndPath](../../../../fixtures/typed.py#L656)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsCall — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall](../../../../fixtures/typed.py#L663)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsCall2 — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCall2](../../../../fixtures/typed.py#L675)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsInitializedByMeta — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsInitializedByMeta](../../../../fixtures/typed.py#L685)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsNewMethod — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsNewMethod](../../../../fixtures/typed.py#L696)**

````python
0 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsAdditionAndXAndY — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsAdditionAndXAndY](../../../../fixtures/typed.py#L709)**

````python
8 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>CallableIntIntSupportsAdditionAndXAndY — missing</summary>

No generated artifact has this qualified identity.

**[Reference: CallableIntIntSupportsAdditionAndXAndY](../../../../fixtures/typed.py#L736)**

````python
4 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsApplyAndOffset — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsApplyAndOffset](../../../../fixtures/typed.py#L5152)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsCallAndFromValues — missing</summary>

No generated artifact has this qualified identity.

**[Reference: SupportsCallAndFromValues](../../../../fixtures/typed.py#L5175)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsAddition — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsAddition](result.py#L168)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsAddition2 — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsAddition2](result.py#L343)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsRadd — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsRadd](result.py#L524)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsLeAndMultiplicationAndSub — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsLeAndMultiplicationAndSub](result.py#L604)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsMultiplication — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsMultiplication](result.py#L731)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsMultiplication2 — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsMultiplication2](result.py#L1452)**

````python
2 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsGtAndRmul — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsGtAndRmul](result.py#L1549)**

````python
3 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

<details><summary>SupportsUpper — extra</summary>

Generated artifact absent from the reference.

**[Produced: SupportsUpper](result.py#L3481)**

````python
1 resolved AST read references. Dynamic access and string forward references are not counted.
````

</details>

## Where the gap is, by the author's annotation

Compatible includes equivalent, narrower and looser types. Hard families are partly author choices or policy and bound the 90 % target.

| Author's annotation | Total | Exact | Compatible | Wrong | Missing | Share of gap | Hard | Tasks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | --- |
| Type alias | 381 | 12 | 145 | 9 | 108 | 35 % | yes | [S-03](../../../../docs/planning/TODO.md#s-03--use-type-x---for-type-aliases), [AL-14](../../../../docs/planning/TODO.md#al-14--finite-domain-values-to-literal-and-enum-suggestions) (author-defined names) |
| TypeVar | 75 | 0 | 3 | 2 | 50 | 19 % | yes | [M5-16](../../../../docs/planning/TODO.md#m5-16--multi-variable-relations), [I-18](../../../../docs/planning/TODO.md#i-18--typevar-solving-from-call-arguments), [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding) |
| Scalar | 331 | 207 | 5 | 0 | 31 | 16 % |  | [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [W-08](../../../../docs/planning/TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [I-10](../../../../docs/planning/TODO.md#i-10--numeric-tower-and-operator-result-rules), [F-37](../../../../docs/planning/TODO.md#f-37--default-literal-parameters-in-the-negotiator) |
| Module class | 101 | 29 | 3 | 8 | 38 | 14 % |  | [M2-02](../../../../docs/planning/TODO.md#m2-02--constructorattribute-resolution), [W-12](../../../../docs/planning/TODO.md#w-12--annotate-instance-attributes-from-negotiation), [I-11](../../../../docs/planning/TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-14](../../../../docs/planning/TODO.md#w-14--annotate-class-level-and-module-level-variables) |
| Top type (object) | 47 | 0 | 10 | 0 | 25 | 7 % | yes | policy: astart never writes object; [G-02](../../../../docs/planning/TODO.md#g-02--score-valid-narrowing-as-narrower-not-wrong) scores narrower |
| Library class | 8 | 1 | 0 | 0 | 6 | 2 % |  | [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [T-08](../../../../docs/planning/TODO.md#t-08--library-return-types-from-typeshed) |
| Self | 14 | 5 | 1 | 1 | 5 | 2 % | yes | [W-11](../../../../docs/planning/TODO.md#w-11--annotate-a-method-that-returns-its-own-class-self-or-quoted-name), [AF-02](../../../../docs/planning/TODO.md#af-02--annotate-selfcls-only-when-the-style-asks), [F-43](../../../../docs/planning/TODO.md#f-43--quote-instead-of-refusing) |
| Optional | 10 | 1 | 1 | 0 | 5 | 1 % |  | [I-01](../../../../docs/planning/TODO.md#i-01--narrow-the-else-branch-by-complement), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [AL-01](../../../../docs/planning/TODO.md#al-01--control-flow-graph-and-per-block-narrowing-replaces-ad-hoc-if-handling) |
| Generator/Iterator | 6 | 1 | 0 | 0 | 5 | 1 % | yes | [W-13](../../../../docs/planning/TODO.md#w-13--type-generators-as-iterator), [G-05](../../../../docs/planning/TODO.md#g-05--normalise-generator-defaults-and-subtype-spelling-in-the-scorer) |
| ClassVar/Final | 8 | 0 | 0 | 0 | 4 | 1 % | yes | [AF-05](../../../../docs/planning/TODO.md#af-05--classvar-and-final-inference), [G-06](../../../../docs/planning/TODO.md#g-06--never-type-a-descriptor-attribute-as-its-value) |
| Builtin container | 1 | 0 | 0 | 0 | 1 | 0 % |  | [I-05](../../../../docs/planning/TODO.md#i-05--type-for-targets-from-common-iterables), [I-09](../../../../docs/planning/TODO.md#i-09--defaultdict-counter-deque-element-types-from-mutation), [I-17](../../../../docs/planning/TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](../../../../docs/planning/TODO.md#f-40--comprehensions-as-derived-nodes), [AL-07](../../../../docs/planning/TODO.md#al-07--bidirectional-expected-type-inference) |
| Callable | 5 | 1 | 1 | 0 | 1 | 0 % | yes | [M4-17](../../../../docs/planning/TODO.md#m4-17--callable-r-params), [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding) |
| Union | 4 | 0 | 2 | 0 | 0 | 0 % |  | [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [I-19](../../../../docs/planning/TODO.md#i-19--join-and-simplify-unions-deterministically) |

## Wrong annotations (20), with code

The scorer found incompatible annotations. Each case separates the reference contract, observed input constraints, and the limits of the recorded tool diagnosis.

---

### Wrong annotation: `CallableObject.__call__->`

**Wrong** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| `DictInt \| int \| str` | `CallablePayload[ValueT] \| IntOrStr` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3299](result.py#L3299) · Reference: [typed.py:4339](../../../../fixtures/typed.py#L4339) · Input: [untyped.py:1997](../../../../fixtures/untyped.py#L1997)

```diff
@@ CallableObject.__call__-> · wrong · TypeVar @@
-    def __call__(self, value: int, *, scale: int = 1) -> int | str | DictInt:
+    ) -> IntOrStr | CallablePayload[ValueT]:
```

</details>

**1. Expected contract**

The reference declares `CallablePayload[ValueT] | IntOrStr` at [typed.py:4339](../../../../fixtures/typed.py#L4339). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `int`: The authored contract selects this type.
- `str`: The authored contract selects this type.
- `fixtures.typed.CallablePayload[ValueT]`: The authored contract selects this type.

Related operations in the reference:

- [reference:4354](../../../../fixtures/typed.py#L4354): `return {"value": value, "scale": scale}`. Source return/yield contributes a value.
- [reference:4351](../../../../fixtures/typed.py#L4351): `return value * scale`. Source return/yield contributes a value.
- [reference:4353](../../../../fixtures/typed.py#L4353): `return str(object=value) * scale`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2000](../../../../fixtures/untyped.py#L2000) | return: `value * scale` | Contributes a result; all paths and operands must be resolved. |
| [input:2002](../../../../fixtures/untyped.py#L2002) | return: `str(object=value) * scale` | Contributes a result; all paths and operands must be resolved. |
| [input:2003](../../../../fixtures/untyped.py#L2003) | return: `{'value': value, 'scale': scale}` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `DictInt | int | str`. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

---

### Wrong annotation: `function_with_mutable_default_like_pattern.store`

**Wrong** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| `int \| None` | `ValueOrNone[ListValue[ItemT]]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4127](result.py#L4127) · Reference: [typed.py:5511](../../../../fixtures/typed.py#L5511) · Input: [untyped.py:2544](../../../../fixtures/untyped.py#L2544)

```diff
@@ function_with_mutable_default_like_pattern.store · wrong · TypeVar @@
-def function_with_mutable_default_like_pattern(value: str, store: int | None = None):
+    store: ValueOrNone[ListValue[ItemT]] = None,
```

</details>

**1. Expected contract**

The reference declares `ValueOrNone[ListValue[ItemT]]` at [typed.py:5511](../../../../fixtures/typed.py#L5511). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ValueOrNone[fixtures.typed.ListValue[ItemT]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:5526](../../../../fixtures/typed.py#L5526): `return store, tuple(store), set(store)`. Source return/yield contributes a value.
- [reference:5525](../../../../fixtures/typed.py#L5525): `store.append`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

4 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2544](../../../../fixtures/untyped.py#L2544) | default value: `None` Observed type: `None`. | Shows one argument/default, not every accepted input. |
| [input:2546](../../../../fixtures/untyped.py#L2546) | body compares it with None: `store is None` | A constraint to combine with other operations and bindings. |
| [input:2548](../../../../fixtures/untyped.py#L2548) | body calls a method: `store.append(value)` Observed type: `is a list`. | Requires this member; its name alone does not prove a class. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `int | None`. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

### Wrong annotation: `function_with_optional_types->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `Callable[[None \| int], int \| str]` | `SupportsCall2` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1151](result.py#L1151) · Reference: [typed.py:1898](../../../../fixtures/typed.py#L1898) · Input: [untyped.py:645](../../../../fixtures/untyped.py#L645)

```diff
@@ function_with_optional_types-> · wrong · Module class @@
-def function_with_optional_types() -> Callable[[None | int], int | str]:
+def function_with_optional_types() -> SupportsCall2:
```

</details>

**1. Expected contract**

The reference declares `SupportsCall2` at [typed.py:1898](../../../../fixtures/typed.py#L1898). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.SupportsCall2`: Requires the declared protocol members `__call__`. Matching an unrelated method name does not establish these structural requirements.

Related operations in the reference:

- [reference:1926](../../../../fixtures/typed.py#L1926): `return optional_function`. Source return/yield contributes a value.
- [reference:1924](../../../../fixtures/typed.py#L1924): `return value`. Source return/yield contributes a value.
- [reference:1923](../../../../fixtures/typed.py#L1923): `return "default"`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

5 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:651](../../../../fixtures/untyped.py#L651) | return: `'default'` Observed type: `str`. | Contributes a result; all paths and operands must be resolved. |
| [input:652](../../../../fixtures/untyped.py#L652) | return: `value` | Contributes a result; all paths and operands must be resolved. |
| [input:654](../../../../fixtures/untyped.py#L654) | return: `optional_function` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `Callable[[None | int], int | str]`. A separate negotiator analysis reports **direct: unprovable Name**. Observation: `unprovable Name: optional_function`. Returns a name the prover cannot type (a wrapper, a decorated function, a class). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](../../../../docs/planning/TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls).

---

### Wrong annotation: `test_class_instantiations->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `dict[str, BaseClass \| DataClassExample \| DecoratedClass \| DerivedClass \| MetaDecoratedClass]` | `ClassInstantiationResults` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2481](result.py#L2481) · Reference: [typed.py:3412](../../../../fixtures/typed.py#L3412) · Input: [untyped.py:1490](../../../../fixtures/untyped.py#L1490)

```diff
@@ test_class_instantiations-> · wrong · Module class @@
-def test_class_instantiations() -> dict[str, BaseClass | DataClassExample | DecoratedClass | DerivedClass | MetaDecoratedClass]:
+def test_class_instantiations() -> ClassInstantiationResults:
```

</details>

**1. Expected contract**

The reference declares `ClassInstantiationResults` at [typed.py:3412](../../../../fixtures/typed.py#L3412). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ClassInstantiationResults`: The authored contract selects this type.

Related operations in the reference:

- [reference:3419](../../../../fixtures/typed.py#L3419): `return { "obj1": BaseClass(x=10), "obj2": BaseClass(x=10, y=20), "obj3": DerivedClass(x=10, y=20, z=30), "obj4": MetaDecoratedClass(value=100), "obj5": DataClas`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1492](../../../../fixtures/untyped.py#L1492) | return: `{'obj1': BaseClass(x=10), 'obj2': BaseClass(x=10, y=20), 'obj3': DerivedClass(x=10, y=20,…` Observed type: `dict[str, BaseClass \| DerivedClass \| MetaDecoratedClass \| DataClassExample \| DecoratedClass]`. | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `dict[str, BaseClass | DataClassExample | DecoratedClass | DerivedClass | MetaDecoratedClass]`. A separate negotiator analysis reports **direct: unprovable Dict**. Observation: `unprovable Dict: {'obj1': BaseClass(x=10), 'obj2': BaseClass(x=10, y=20), 'ob`. Returns a dict display with unpacking or untyped members. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [I-17](../../../../docs/planning/TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](../../../../docs/planning/TODO.md#f-40--comprehensions-as-derived-nodes).

---

### Wrong annotation: `test_extended_inference_edge_cases->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `DictInt` | `ExtendedTestResult` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4317](result.py#L4317) · Reference: [typed.py:5787](../../../../fixtures/typed.py#L5787) · Input: [untyped.py:2706](../../../../fixtures/untyped.py#L2706)

```diff
@@ test_extended_inference_edge_cases-> · wrong · Module class @@
-def test_extended_inference_edge_cases() -> DictInt:
+def test_extended_inference_edge_cases() -> ExtendedTestResult:
```

</details>

**1. Expected contract**

The reference declares `ExtendedTestResult` at [typed.py:5787](../../../../fixtures/typed.py#L5787). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ExtendedTestResult`: The authored contract selects this type.

Related operations in the reference:

- [reference:5794](../../../../fixtures/typed.py#L5794): `return { **test_extended_inference_edge_cases_part1(), **test_extended_inference_edge_cases_part2(), **test_extended_inference_edge_cases_part3(), }`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2708](../../../../fixtures/untyped.py#L2708) | return: `{**test_extended_inference_edge_cases_part1(), **test_extended_inference_edge_cases_part2…` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `DictInt`. A separate negotiator analysis reports **direct: unprovable Dict**. Observation: `unprovable Dict: {**test_extended_inference_edge_cases_part1(), **test_extend`. Returns a dict display with unpacking or untyped members. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [I-17](../../../../docs/planning/TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](../../../../docs/planning/TODO.md#f-40--comprehensions-as-derived-nodes).

---

### Wrong annotation: `test_extended_inference_edge_cases_part3->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `DictInt` | `ExtendedResultsPart3` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4264](result.py#L4264) · Reference: [typed.py:5725](../../../../fixtures/typed.py#L5725) · Input: [untyped.py:2657](../../../../fixtures/untyped.py#L2657)

```diff
@@ test_extended_inference_edge_cases_part3-> · wrong · Module class @@
-def test_extended_inference_edge_cases_part3() -> DictInt:
+def test_extended_inference_edge_cases_part3() -> ExtendedResultsPart3:
```

</details>

**1. Expected contract**

The reference declares `ExtendedResultsPart3` at [typed.py:5725](../../../../fixtures/typed.py#L5725). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ExtendedResultsPart3`: The authored contract selects this type.

Related operations in the reference:

- [reference:5747](../../../../fixtures/typed.py#L5747): `return { "local_class": local_instance.apply(value=5), "nested_defaultdict": function_with_nested_default_factories(), "partial_reduce": function_with_partial_r`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2665](../../../../fixtures/untyped.py#L2665) | return: `{'local_class': local_instance.apply(5), 'nested_defaultdict': function_with_nested_defau…` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `DictInt`. A separate negotiator analysis reports **direct: unprovable Dict**. Observation: `unprovable Dict: {'local_class': local_instance.apply(5), 'nested_defaultdict`. Returns a dict display with unpacking or untyped members. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [I-17](../../../../docs/planning/TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](../../../../docs/planning/TODO.md#f-40--comprehensions-as-derived-nodes).

---

### Wrong annotation: `test_new_inference_edge_cases->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `dict[str, ImportExampleResult \| RedefinitionResult \| ScopeResolutionResult \| SliceExampleResult \| list[int] \| tuple[BuiltinMethodList, BuiltinMethodDict, CustomAddSet, int]]` | `NewInferenceResults` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2882](result.py#L2882) · Reference: [typed.py:3773](../../../../fixtures/typed.py#L3773) · Input: [untyped.py:1757](../../../../fixtures/untyped.py#L1757)

```diff
@@ test_new_inference_edge_cases-> · wrong · Module class @@
-def test_new_inference_edge_cases() -> dict[str, ImportExampleResult | RedefinitionResult | ScopeResolutionResult | SliceExampleResult | list[int] | tuple[BuiltinMethodList, BuiltinMethodDict, CustomA…
+def test_new_inference_edge_cases() -> NewInferenceResults:
```

</details>

**1. Expected contract**

The reference declares `NewInferenceResults` at [typed.py:3773](../../../../fixtures/typed.py#L3773). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.NewInferenceResults`: The authored contract selects this type.

Related operations in the reference:

- [reference:3780](../../../../fixtures/typed.py#L3780): `return { "slices": function_with_list_and_dict_slices(), "builtin_name_collisions": function_with_builtin_name_collisions(), "imports": function_with_importlib_`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1759](../../../../fixtures/untyped.py#L1759) | return: `{'slices': function_with_list_and_dict_slices(), 'builtin_name_collisions': function_with…` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `dict[str, ImportExampleResult | RedefinitionResult | ScopeResolutionResult | SliceExampleResult | list[int] | tuple[BuiltinMethodList, BuiltinMethodDict, CustomAddSet, int]]`. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

---

### Wrong annotation: `test_other_operations->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `dict[str, EnumClass \| str]` | `OtherOperationResults` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2502](result.py#L2502) · Reference: [typed.py:3429](../../../../fixtures/typed.py#L3429) · Input: [untyped.py:1502](../../../../fixtures/untyped.py#L1502)

```diff
@@ test_other_operations-> · wrong · Module class @@
-def test_other_operations() -> dict[str, str | EnumClass]:
+def test_other_operations() -> OtherOperationResults:
```

</details>

**1. Expected contract**

The reference declares `OtherOperationResults` at [typed.py:3429](../../../../fixtures/typed.py#L3429). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.OtherOperationResults`: The authored contract selects this type.

Related operations in the reference:

- [reference:3447](../../../../fixtures/typed.py#L3447): `return { "enum_val": enum_val, "closure_result": closure_result, "context_result": context_result, "vec_sum": vec_sum, }`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

11 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1513](../../../../fixtures/untyped.py#L1513) | return: `{'enum_val': enum_val, 'closure_result': closure_result, 'context_result': context_result…` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `dict[str, EnumClass | str]`. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

---

### Wrong annotation: `HybridContainer.__or__.merged`

**Wrong** · Self

| Current tool output | Expected reference |
| --- | --- |
| `HybridContainer` | `Self` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3279](result.py#L3279) · Reference: [typed.py:4313](../../../../fixtures/typed.py#L4313) · Input: [untyped.py:1981](../../../../fixtures/untyped.py#L1981)

```diff
@@ HybridContainer.__or__.merged · wrong · Self @@
-        merged: HybridContainer = HybridContainer(*self.items, **self.named)
+        merged: Self = self.__class__(*self.items, **self.named)
```

</details>

**1. Expected contract**

The reference declares `Self` at [typed.py:4313](../../../../fixtures/typed.py#L4313). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `HybridContainer.Self`: Preserves the receiver's concrete subclass in the result.

Related operations in the reference:

- [reference:4319](../../../../fixtures/typed.py#L4319): `return merged`. Source return/yield contributes a value.
- [reference:4315](../../../../fixtures/typed.py#L4315): `merged.items`. The source requires this receiver member.
- [reference:4316](../../../../fixtures/typed.py#L4316): `merged.named`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

12 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1981](../../../../fixtures/untyped.py#L1981) | assignment: `merged = HybridContainer(*self.items, **self.named)` Observed type: `HybridContainer`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `HybridContainer`. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

### Wrong annotation: `function_with_extended_named_results.result`

**Wrong** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| `ExtendedResult` | `ExtendedResult[ListInt]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4192](result.py#L4192) · Reference: [typed.py:5638](../../../../fixtures/typed.py#L5638) · Input: [untyped.py:2581](../../../../fixtures/untyped.py#L2581)

```diff
@@ function_with_extended_named_results.result · wrong · Type alias @@
-    result: ExtendedResult = ExtendedResult(name='alpha', payload=[1, 2, 3], metadata={'ok': True})
+    result: ExtendedResult[ListInt] = ExtendedResult(
```

</details>

**1. Expected contract**

The reference declares `ExtendedResult[ListInt]` at [typed.py:5638](../../../../fixtures/typed.py#L5638). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ExtendedResult[list[int]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:5647](../../../../fixtures/typed.py#L5647): `return result, name, payload[-1], metadata["ok"]`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2581](../../../../fixtures/untyped.py#L2581) | assignment: `result = ExtendedResult(name='alpha', payload=[1, 2, 3], metadata={'ok': True})` Observed type: `ExtendedResult`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `ExtendedResult`. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

### Wrong annotation: `function_with_hybrid_container_stress.left`

**Wrong** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| `HybridContainer` | `HybridContainerIntOrFloatStrOrBoolOrListInt` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3890](result.py#L3890) · Reference: [typed.py:5087](../../../../fixtures/typed.py#L5087) · Input: [untyped.py:2372](../../../../fixtures/untyped.py#L2372)

```diff
@@ function_with_hybrid_container_stress.left · wrong · Type alias @@
-    left: HybridContainer = HybridContainer(1, 2, name='left')
+    left: HybridContainerIntOrFloatStrOrBoolOrListInt = HybridContainer(
```

</details>

**1. Expected contract**

The reference declares `HybridContainerIntOrFloatStrOrBoolOrListInt` at [typed.py:5087](../../../../fixtures/typed.py#L5087). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.HybridContainer[float | int, bool | list[int] | str]`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2372](../../../../fixtures/untyped.py#L2372) | assignment: `left = HybridContainer(1, 2, name='left')` Observed type: `HybridContainer`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `HybridContainer`. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

### Wrong annotation: `function_with_hybrid_container_stress.merged`

**Wrong** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| `int` | `HybridContainerIntOrFloatStrOrBoolOrListInt` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3892](result.py#L3892) · Reference: [typed.py:5098](../../../../fixtures/typed.py#L5098) · Input: [untyped.py:2374](../../../../fixtures/untyped.py#L2374)

```diff
@@ function_with_hybrid_container_stress.merged · wrong · Type alias @@
-    merged: int = left | right
+    merged: HybridContainerIntOrFloatStrOrBoolOrListInt = left | right
```

</details>

**1. Expected contract**

The reference declares `HybridContainerIntOrFloatStrOrBoolOrListInt` at [typed.py:5098](../../../../fixtures/typed.py#L5098). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.HybridContainer[float | int, bool | list[int] | str]`: The authored contract selects this type.

Related operations in the reference:

- [reference:5102](../../../../fixtures/typed.py#L5102): `return merged, "name" in merged, cast(typ="ListInt", val=merged["extra"])`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2374](../../../../fixtures/untyped.py#L2374) | assignment: `merged = left \| right` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `int`. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

---

### Wrong annotation: `function_with_hybrid_container_stress.right`

**Wrong** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| `HybridContainer` | `HybridContainerIntOrFloatStrOrBoolOrListInt` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3891](result.py#L3891) · Reference: [typed.py:5092](../../../../fixtures/typed.py#L5092) · Input: [untyped.py:2373](../../../../fixtures/untyped.py#L2373)

```diff
@@ function_with_hybrid_container_stress.right · wrong · Type alias @@
-    right: HybridContainer = HybridContainer(3, 4, name='right', enabled=True)
+    right: HybridContainerIntOrFloatStrOrBoolOrListInt = HybridContainer(
```

</details>

**1. Expected contract**

The reference declares `HybridContainerIntOrFloatStrOrBoolOrListInt` at [typed.py:5092](../../../../fixtures/typed.py#L5092). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.HybridContainer[float | int, bool | list[int] | str]`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2373](../../../../fixtures/untyped.py#L2373) | assignment: `right = HybridContainer(3, 4, name='right', enabled=True)` Observed type: `HybridContainer`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `HybridContainer`. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

### Wrong annotation: `function_with_json_uuid_and_path_stress.payload`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `dict[str, str]` | `JSONRoundtrip` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3768](result.py#L3768) · Reference: [typed.py:4925](../../../../fixtures/typed.py#L4925) · Input: [untyped.py:2283](../../../../fixtures/untyped.py#L2283)

```diff
@@ function_with_json_uuid_and_path_stress.payload · wrong · Module class @@
-    payload: dict[str, str] = {'id': str(object=identifier), 'parts': path.stem.split(sep='-'), 'exists': path.exists()}
+    payload: JSONRoundtrip = {
```

</details>

**1. Expected contract**

The reference declares `JSONRoundtrip` at [typed.py:4925](../../../../fixtures/typed.py#L4925). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.JSONRoundtrip`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

11 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2283](../../../../fixtures/untyped.py#L2283) | assignment: `payload = {'id': str(object=identifier), 'parts': path.stem.split(sep='-'), 'exists': path.exists()}` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `dict[str, str]`. A separate negotiator analysis reports **direct: container literal mutated or not provable**. Observation: `container literal mutated or not provable`. Not described yet: add it to the table in scripts/compare/conversion_report.py. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner).

---

### Wrong annotation: `function_with_metaclass_registry_stress.registry`

**Wrong** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| `None` | `DictRegistryMeta` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3865](result.py#L3865) · Reference: [typed.py:5055](../../../../fixtures/typed.py#L5055) · Input: [untyped.py:2355](../../../../fixtures/untyped.py#L2355)

```diff
@@ function_with_metaclass_registry_stress.registry · wrong · Type alias @@
-    registry: None = RegistryMeta.registry
+    registry: DictRegistryMeta = RegistryMeta.registry or {}
```

</details>

**1. Expected contract**

The reference declares `DictRegistryMeta` at [typed.py:5055](../../../../fixtures/typed.py#L5055). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `dict[str, fixtures.typed.RegistryMeta]`: Preserves key/value types (str, fixtures.typed.RegistryMeta). Mapping operations and the types flowing through keys and values must agree.

Related operations in the reference:

- [reference:5057](../../../../fixtures/typed.py#L5057): `return item, clone, registry_names`. Source return/yield contributes a value.
- [reference:5055](../../../../fixtures/typed.py#L5055): `RegistryMeta.registry`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2355](../../../../fixtures/untyped.py#L2355) | assignment: `registry = RegistryMeta.registry` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `None`. A separate negotiator analysis reports **direct: unprovable Attribute**. Observation: `unprovable Attribute: RegistryMeta.registry`. Returns an attribute the class table does not type. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [I-11](../../../../docs/planning/TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-12](../../../../docs/planning/TODO.md#w-12--annotate-instance-attributes-from-negotiation), [M2-06](../../../../docs/planning/TODO.md#m2-06--r9-attribute-types).

---

### Wrong annotation: `function_with_nested_default_factories.tree`

**Wrong** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| `defaultdict[str, int]` | `DefaultdictStrDefaultdictStrListInt` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3967](result.py#L3967) · Reference: [typed.py:5268](../../../../fixtures/typed.py#L5268) · Input: [untyped.py:2427](../../../../fixtures/untyped.py#L2427)

```diff
@@ function_with_nested_default_factories.tree · wrong · Type alias @@
-    tree: defaultdict[str, int] = defaultdict(lambda: defaultdict(list))
+    tree: DefaultdictStrDefaultdictStrListInt = defaultdict(
```

</details>

**1. Expected contract**

The reference declares `DefaultdictStrDefaultdictStrListInt` at [typed.py:5268](../../../../fixtures/typed.py#L5268). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `collections.defaultdict[str, collections.defaultdict[str, list[int]]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:5282](../../../../fixtures/typed.py#L5282): `return tree, frozen`. Source return/yield contributes a value.
- [reference:5280](../../../../fixtures/typed.py#L5280): `tree.items`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2427](../../../../fixtures/untyped.py#L2427) | assignment: `tree = defaultdict(lambda: defaultdict(list))` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `defaultdict[str, int]`. A separate negotiator analysis reports **direct: unprovable Call**. Observation: `unprovable Call: defaultdict(lambda: defaultdict(list))`. Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers).

---

### Wrong annotation: `function_with_sort_key_and_grouping_stress.normalized`

**Wrong** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| `list[DictInt]` | `ListNormalizedRow` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3991](result.py#L3991) · Reference: [typed.py:5297](../../../../fixtures/typed.py#L5297) · Input: [untyped.py:2444](../../../../fixtures/untyped.py#L2444)

```diff
@@ function_with_sort_key_and_grouping_stress.normalized · wrong · Type alias @@
-    normalized: list[DictInt] = [{'name': row['name'].strip().lower(), 'score': int(row['score'])} for row in rows]
+    normalized: ListNormalizedRow = [
```

</details>

**1. Expected contract**

The reference declares `ListNormalizedRow` at [typed.py:5297](../../../../fixtures/typed.py#L5297). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `list[fixtures.typed.NormalizedRow]`: The authored contract selects this type.

Related operations in the reference:

- [reference:5317](../../../../fixtures/typed.py#L5317): `return normalized, grouped`. Source return/yield contributes a value.
- [reference:5304](../../../../fixtures/typed.py#L5304): `normalized.sort`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

5 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2444](../../../../fixtures/untyped.py#L2444) | assignment: `normalized = [{'name': row['name'].strip().lower(), 'score': int(row['score'])} for row in rows]` Observed type: `list[?]`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `list[DictInt]`. A separate negotiator analysis reports **direct: container literal mutated or not provable**. Observation: `container literal mutated or not provable`. Not described yet: add it to the table in scripts/compare/conversion_report.py. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner).

---

### Wrong annotation: `test_extended_inference_edge_cases_part1.records`

**Wrong** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| `list[dict[str, int \| str \| None]]` | `ListValue[AmountRecord]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4205](result.py#L4205) · Reference: [typed.py:5657](../../../../fixtures/typed.py#L5657) · Input: [untyped.py:2594](../../../../fixtures/untyped.py#L2594)

```diff
@@ test_extended_inference_edge_cases_part1.records · wrong · Type alias @@
-    records: list[dict[str, None | int | str]] = [{'name': ' Alpha ', 'amount': '10'}, {'name': 'beta', 'amount': 5}, {'name': None, 'amount': None}]
+    records: ListValue[AmountRecord] = [
```

</details>

**1. Expected contract**

The reference declares `ListValue[AmountRecord]` at [typed.py:5657](../../../../fixtures/typed.py#L5657). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ListValue[fixtures.typed.AmountRecord]`: The authored contract selects this type.

Related operations in the reference:

- [reference:5662](../../../../fixtures/typed.py#L5662): `return { "pattern_point": function_with_pattern_matching_stress( value={"kind": "point", "x": 1, "y": 2}, ), "pattern_line": function_with_pattern_matching_stre`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2594](../../../../fixtures/untyped.py#L2594) | assignment: `records = [{'name': ' Alpha ', 'amount': '10'}, {'name': 'beta', 'amount': 5}, {'name': None, 'amou…` Observed type: `list[dict[str, str] \| dict[str, str \| int] \| dict[str, None]]`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `list[dict[str, int | str | None]]`. A separate negotiator analysis reports **direct: container literal mutated or not provable**. Observation: `container literal mutated or not provable`. Not described yet: add it to the table in scripts/compare/conversion_report.py. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner).

---

### Wrong annotation: `test_extended_inference_edge_cases_part2.rows`

**Wrong** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| `list[dict[str, int \| str]]` | `ListValue[GroupInput]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4241](result.py#L4241) · Reference: [typed.py:5698](../../../../fixtures/typed.py#L5698) · Input: [untyped.py:2630](../../../../fixtures/untyped.py#L2630)

```diff
@@ test_extended_inference_edge_cases_part2.rows · wrong · Type alias @@
-    rows: list[dict[str, int | str]] = [{'name': ' Alpha', 'score': '10'}, {'name': 'alpha', 'score': 7}, {'name': 'Beta', 'score': 3}]
+    rows: ListValue[GroupInput] = [
```

</details>

**1. Expected contract**

The reference declares `ListValue[GroupInput]` at [typed.py:5698](../../../../fixtures/typed.py#L5698). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ListValue[fixtures.typed.GroupInput]`: The authored contract selects this type.

Related operations in the reference:

- [reference:5703](../../../../fixtures/typed.py#L5703): `return { "json_uuid_path": function_with_json_uuid_and_path_stress( tmp_name="demo", ), "contextvars": function_with_contextvars_and_chainmap( configs=[{"fallba`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2630](../../../../fixtures/untyped.py#L2630) | assignment: `rows = [{'name': ' Alpha', 'score': '10'}, {'name': 'alpha', 'score': 7}, {'name': 'Beta', 'scor…` Observed type: `list[dict[str, str] \| dict[str, str \| int]]`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `list[dict[str, int | str]]`. A separate negotiator analysis reports **direct: container literal mutated or not provable**. Observation: `container literal mutated or not provable`. Not described yet: add it to the table in scripts/compare/conversion_report.py. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner).

---

### Wrong annotation: `test_function_calls_part1.result22`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `Callable[[None \| int], int \| str]` | `SupportsCall2` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2332](result.py#L2332) · Reference: [typed.py:3244](../../../../fixtures/typed.py#L3244) · Input: [untyped.py:1353](../../../../fixtures/untyped.py#L1353)

```diff
@@ test_function_calls_part1.result22 · wrong · Module class @@
-    result22: Callable[[None | int], int | str] = function_with_optional_types()
+    result22: SupportsCall2 = function_with_optional_types()
```

</details>

**1. Expected contract**

The reference declares `SupportsCall2` at [typed.py:3244](../../../../fixtures/typed.py#L3244). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.SupportsCall2`: Requires the declared protocol members `__call__`. Matching an unrelated method name does not establish these structural requirements.

Related operations in the reference:

- [reference:3245](../../../../fixtures/typed.py#L3245): `return { "result1": result1, "result2": result2, "result3": result3, "result4": result4, "result5": result5, "result6": result6, "result7": result7, "result8": `. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

24 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1353](../../../../fixtures/untyped.py#L1353) | assignment: `result22 = function_with_optional_types()` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `Callable[[None | int], int | str]`. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

## Gap by owner (most missing or wrong first)

| Owner | Gap |
| --- | ---: |
| `test_function_calls_part1` ([untyped.py:1325](../../../../fixtures/untyped.py#L1325)) | 10 |
| `test_function_calls_part2` ([untyped.py:1380](../../../../fixtures/untyped.py#L1380)) | 9 |
| `test_function_calls_part3` ([untyped.py:1431](../../../../fixtures/untyped.py#L1431)) | 8 |
| `RegistryMeta.__new__` ([untyped.py:1881](../../../../fixtures/untyped.py#L1881)) | 6 |
| `MetaClass.__new__` ([untyped.py:101](../../../../fixtures/untyped.py#L101)) | 5 |
| `test_other_operations` ([untyped.py:1502](../../../../fixtures/untyped.py#L1502)) | 5 |
| `MetaClass.__call__` ([untyped.py:106](../../../../fixtures/untyped.py#L106)) | 4 |
| `decorator.wrapper` ([untyped.py:196](../../../../fixtures/untyped.py#L196)) | 4 |
| `decorator_with_args.actual_decorator.wrapper` ([untyped.py:208](../../../../fixtures/untyped.py#L208)) | 4 |
| `RegistryMeta.__call__` ([untyped.py:1891](../../../../fixtures/untyped.py#L1891)) | 4 |
| `AsyncResource.__aexit__` ([untyped.py:2019](../../../../fixtures/untyped.py#L2019)) | 4 |
| `preserve_signature_decorator.wrapper` ([untyped.py:2053](../../../../fixtures/untyped.py#L2053)) | 4 |
| `function_with_recursive_containers` ([untyped.py:2154](../../../../fixtures/untyped.py#L2154)) | 4 |
| `function_with_exception_group_stress` ([untyped.py:2240](../../../../fixtures/untyped.py#L2240)) | 4 |
| `function_with_json_uuid_and_path_stress` ([untyped.py:2279](../../../../fixtures/untyped.py#L2279)) | 4 |

## Missing annotations by family, with code

### Type alias: 108 missing

Tasks: [S-03](../../../../docs/planning/TODO.md#s-03--use-type-x---for-type-aliases), [AL-14](../../../../docs/planning/TODO.md#al-14--finite-domain-values-to-literal-and-enum-suggestions) (author-defined names)

---

#### Missing annotation: `MetaClass.__new__.mcs`

**Missing** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `TypeValue[MetaClass]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:116](result.py#L116) · Reference: [typed.py:745](../../../../fixtures/typed.py#L745) · Input: [untyped.py:101](../../../../fixtures/untyped.py#L101)

```diff
@@ MetaClass.__new__.mcs · missing · Type alias @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        mcs: TypeValue[MetaClass],
```

</details>

**1. Expected contract**

The reference declares `TypeValue[MetaClass]` at [typed.py:745](../../../../fixtures/typed.py#L745). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.TypeValue[fixtures.typed.MetaClass]`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:991](../../../../fixtures/untyped.py#L991) | same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` | Name-only match; binding to this target is unverified. |
| [input:1881](../../../../fixtures/untyped.py#L1881) | same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: no evidence reaches it**. Observation: `no evidence reaches it`. A parameter with no call site, default or use that proves a type. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-08](../../../../docs/planning/TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-09](../../../../docs/planning/TODO.md#al-09--name-and-usage-language-model-as-calibrated-prior).

---

#### Missing annotation: `MetaClass.__new__.bases`

**Missing** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `TupleTypeObjectVariadic` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:116](result.py#L116) · Reference: [typed.py:747](../../../../fixtures/typed.py#L747) · Input: [untyped.py:101](../../../../fixtures/untyped.py#L101)

```diff
@@ MetaClass.__new__.bases · missing · Type alias @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        bases: TupleTypeObjectVariadic,
```

</details>

**1. Expected contract**

The reference declares `TupleTypeObjectVariadic` at [typed.py:747](../../../../fixtures/typed.py#L747). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `tuple[type[object], ...]`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:104](../../../../fixtures/untyped.py#L104) | call site passes: `super().__new__(mcs, name, bases, namespace)  ->  name` | Name-only match; binding to this target is unverified. |
| [input:991](../../../../fixtures/untyped.py#L991) | same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` | Name-only match; binding to this target is unverified. |
| [input:1881](../../../../fixtures/untyped.py#L1881) | same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` | Name-only match; binding to this target is unverified. |
| [input:1884](../../../../fixtures/untyped.py#L1884) | call site passes: `super().__new__(mcls, name, bases, namespace)  ->  name` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: no evidence reaches it**. Observation: `no evidence reaches it`. A parameter with no call site, default or use that proves a type. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-08](../../../../docs/planning/TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-09](../../../../docs/planning/TODO.md#al-09--name-and-usage-language-model-as-calibrated-prior).

---

#### Missing annotation: `MetaClass.__new__.namespace`

**Missing** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `DictObject` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:116](result.py#L116) · Reference: [typed.py:748](../../../../fixtures/typed.py#L748) · Input: [untyped.py:101](../../../../fixtures/untyped.py#L101)

```diff
@@ MetaClass.__new__.namespace · missing · Type alias @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        namespace: DictObject,
```

</details>

**1. Expected contract**

The reference declares `DictObject` at [typed.py:748](../../../../fixtures/typed.py#L748). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `dict[str, object]`: Preserves key/value types (str, object). Mapping operations and the types flowing through keys and values must agree.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:103](../../../../fixtures/untyped.py#L103) | body indexes it: `namespace['meta_added']` | Requires subscription; this alone does not identify a class. |
| [input:104](../../../../fixtures/untyped.py#L104) | call site passes: `super().__new__(mcs, name, bases, namespace)  ->  bases` | Name-only match; binding to this target is unverified. |
| [input:991](../../../../fixtures/untyped.py#L991) | same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` | Name-only match; binding to this target is unverified. |
| [input:1881](../../../../fixtures/untyped.py#L1881) | same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` | Name-only match; binding to this target is unverified. |
| [input:1884](../../../../fixtures/untyped.py#L1884) | call site passes: `super().__new__(mcls, name, bases, namespace)  ->  bases` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: no evidence reaches it**. Observation: `no evidence reaches it`. A parameter with no call site, default or use that proves a type. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-08](../../../../docs/planning/TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-09](../../../../docs/planning/TODO.md#al-09--name-and-usage-language-model-as-calibrated-prior).

---

#### Missing annotation: `function_with_generators->`

**Missing** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ListInt` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:715](result.py#L715) · Reference: [typed.py:1418](../../../../fixtures/typed.py#L1418) · Input: [untyped.py:403](../../../../fixtures/untyped.py#L403)

```diff
@@ function_with_generators-> · missing · Type alias @@
-def function_with_generators():
+def function_with_generators() -> ListInt:
```

</details>

**1. Expected contract**

The reference declares `ListInt` at [typed.py:1418](../../../../fixtures/typed.py#L1418). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `list[int]`: The authored contract selects this type.

Related operations in the reference:

- [reference:1435](../../../../fixtures/typed.py#L1435): `return list(generator())`. Source return/yield contributes a value.
- [reference:1433](../../../../fixtures/typed.py#L1433): `yield from range(10)`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:403](../../../../fixtures/untyped.py#L403) | generator: `the body contains 'yield'` | A constraint to combine with other operations and bindings. |
| [input:410](../../../../fixtures/untyped.py#L410) | return: `list(generator())` Observed type: `list[?]`. | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Call**. Observation: `unprovable Call: list(generator())`. Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers).

---

#### Missing annotation: `function_with_class_methods->`

**Missing** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `TypeSupportsClassMethods` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:765](result.py#L765) · Reference: [typed.py:1462](../../../../fixtures/typed.py#L1462) · Input: [untyped.py:424](../../../../fixtures/untyped.py#L424)

```diff
@@ function_with_class_methods-> · missing · Type alias @@
-def function_with_class_methods():
+def function_with_class_methods() -> TypeSupportsClassMethods:
```

</details>

**1. Expected contract**

The reference declares `TypeSupportsClassMethods` at [typed.py:1462](../../../../fixtures/typed.py#L1462). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `type[fixtures.typed.SupportsClassMethodAndInstanceMethodAndStaticMethod]`: The authored contract selects this type.

Related operations in the reference:

- [reference:1502](../../../../fixtures/typed.py#L1502): `return InnerClass`. Source return/yield contributes a value.
- [reference:1481](../../../../fixtures/typed.py#L1481): `return cls.__name__`. Source return/yield contributes a value.
- [reference:1491](../../../../fixtures/typed.py#L1491): `return "static"`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:444](../../../../fixtures/untyped.py#L444) | return: `InnerClass` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Name**. Observation: `unprovable Name: InnerClass`. Returns a name the prover cannot type (a wrapper, a decorated function, a class). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](../../../../docs/planning/TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls).

<details><summary>All 108 (first 30, with links to the author's line)</summary>

- `MetaClass.__new__.mcs` ([typed.py:745](../../../../fixtures/typed.py#L745)): `TypeValue[MetaClass]`
- `MetaClass.__new__.bases` ([typed.py:747](../../../../fixtures/typed.py#L747)): `TupleTypeObjectVariadic`
- `MetaClass.__new__.namespace` ([typed.py:748](../../../../fixtures/typed.py#L748)): `DictObject`
- `function_with_generators->` ([typed.py:1418](../../../../fixtures/typed.py#L1418)): `ListInt`
- `function_with_class_methods->` ([typed.py:1462](../../../../fixtures/typed.py#L1462)): `TypeSupportsClassMethods`
- `function_with_property->` ([typed.py:1505](../../../../fixtures/typed.py#L1505)): `TypeSupportsValue`
- `function_with_descriptor->` ([typed.py:1548](../../../../fixtures/typed.py#L1548)): `TypeObject`
- `function_with_descriptor.Descriptor.__get__.objtype` ([typed.py:1563](../../../../fixtures/typed.py#L1563)): `TypeObject`
- `function_with_operator_overloading->` ([typed.py:1602](../../../../fixtures/typed.py#L1602)): `CallableIntIntSupportsAdditionAndXAndY`
- `function_with_multiple_inheritance->` ([typed.py:1725](../../../../fixtures/typed.py#L1725)): `TypeObject`
- `function_with_protocol->` ([typed.py:1809](../../../../fixtures/typed.py#L1809)): `TypeObject`
- `function_with_union_types->` ([typed.py:1871](../../../../fixtures/typed.py#L1871)): `CallableIntOrStrToIntOrStr`
- `function_with_union_types.union_function.value` ([typed.py:1879](../../../../fixtures/typed.py#L1879)): `IntOrStr`
- `function_with_matrix_multiplication->` ([typed.py:2166](../../../../fixtures/typed.py#L2166)): `TypeValue[SupportsMatrixMultiplicationAndData]`
- `function_with_slots->` ([typed.py:2459](../../../../fixtures/typed.py#L2459)): `TypeObject`
- `function_with_class_decorator->` ([typed.py:2491](../../../../fixtures/typed.py#L2491)): `TypeObject`
- `function_with_singleton->` ([typed.py:2534](../../../../fixtures/typed.py#L2534)): `TypeObject`
- `function_with_factory->` ([typed.py:2566](../../../../fixtures/typed.py#L2566)): `TypeObject`
- `function_with_builder->` ([typed.py:2603](../../../../fixtures/typed.py#L2603)): `TypeObject`
- `function_with_builder.Product.__init__.parts` ([typed.py:2614](../../../../fixtures/typed.py#L2614)): `SequenceStr`
- `function_with_observer->` ([typed.py:2655](../../../../fixtures/typed.py#L2655)): `TupleTypeObjectVariadic`
- `function_with_strategy->` ([typed.py:2704](../../../../fixtures/typed.py#L2704)): `TupleTypeObjectVariadic`
- `function_with_command->` ([typed.py:2766](../../../../fixtures/typed.py#L2766)): `TupleTypeObjectVariadic`
- `function_with_chain_of_responsibility->` ([typed.py:2812](../../../../fixtures/typed.py#L2812)): `TypeObject`
- `function_with_groupby->` ([typed.py:2972](../../../../fixtures/typed.py#L2972)): `DictListInt`
- `function_with_permutations_combinations->` ([typed.py:2987](../../../../fixtures/typed.py#L2987)): `TupleListTupleIntVariadicVariadic`
- `function_with_zip_longest->` ([typed.py:3110](../../../../fixtures/typed.py#L3110)): `ListTupleIntOrNoneStrOrNone`
- `function_with_compress->` ([typed.py:3155](../../../../fixtures/typed.py#L3155)): `ListInt`
- `function_with_accumulate->` ([typed.py:3167](../../../../fixtures/typed.py#L3167)): `ListInt`
- `function_with_scope_resolution.duplicate_scope_name.deepest->` ([typed.py:3730](../../../../fixtures/typed.py#L3730)): `ListInt`

</details>

### TypeVar: 50 missing

Tasks: [M5-16](../../../../docs/planning/TODO.md#m5-16--multi-variable-relations), [I-18](../../../../docs/planning/TODO.md#i-18--typevar-solving-from-call-arguments), [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding)

---

#### Missing annotation: `decorator->`

**Missing** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `CallableParametersToResult[P, ValueOrInt[R]]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:287](result.py#L287) · Reference: [typed.py:936](../../../../fixtures/typed.py#L936) · Input: [untyped.py:192](../../../../fixtures/untyped.py#L192)

```diff
@@ decorator-> · missing · TypeVar @@
-def decorator(func):
+) -> CallableParametersToResult[P, ValueOrInt[R]]:
```

</details>

**1. Expected contract**

The reference declares `CallableParametersToResult[P, ValueOrInt[R]]` at [typed.py:936](../../../../fixtures/typed.py#L936). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.CallableParametersToResult[P, fixtures.typed.ValueOrInt[R]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:964](../../../../fixtures/typed.py#L964): `return wrapper`. Source return/yield contributes a value.
- [reference:962](../../../../fixtures/typed.py#L962): `return result`. Source return/yield contributes a value.
- [reference:961](../../../../fixtures/typed.py#L961): `return result * 2`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:198](../../../../fixtures/untyped.py#L198) | return: `result * 2` | Contributes a result; all paths and operands must be resolved. |
| [input:200](../../../../fixtures/untyped.py#L200) | return: `wrapper` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Name**. Observation: `unprovable Name: wrapper`. Returns a name the prover cannot type (a wrapper, a decorated function, a class). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](../../../../docs/planning/TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls).

---

#### Missing annotation: `decorator.func`

**Missing** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `CallableParametersToResult[P, R]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:287](result.py#L287) · Reference: [typed.py:935](../../../../fixtures/typed.py#L935) · Input: [untyped.py:192](../../../../fixtures/untyped.py#L192)

```diff
@@ decorator.func · missing · TypeVar @@
-def decorator(func):
+    func: CallableParametersToResult[P, R],
```

</details>

**1. Expected contract**

The reference declares `CallableParametersToResult[P, R]` at [typed.py:935](../../../../fixtures/typed.py#L935). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.CallableParametersToResult[P, R]`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

The collector did not resolve direct evidence for this target. This is a limit of the collector, not proof that the type cannot be inferred from the source.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: function escapes as a value**. Observation: `function escapes as a value`. The function is passed around as a value, so its callers are unknown. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-07](../../../../docs/planning/TODO.md#w-07--burn-down-unbindable-calls-and-escaping-functions), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

---

#### Missing annotation: `decorator.wrapper.args`

**Missing** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `args` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:298](result.py#L298) · Reference: [typed.py:948](../../../../fixtures/typed.py#L948) · Input: [untyped.py:196](../../../../fixtures/untyped.py#L196)

```diff
@@ decorator.wrapper.args · missing · TypeVar @@
-    def wrapper(*args, **kwargs) -> int:
+    def wrapper(*args: P.args, **kwargs: P.kwargs) -> ValueOrInt[R]:
```

</details>

**1. Expected contract**

The reference declares `args` at [typed.py:948](../../../../fixtures/typed.py#L948). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `P.args`: The authored contract selects this type.

Related operations in the reference:

- [reference:948](../../../../fixtures/typed.py#L948): `P.args`. The source requires this receiver member.
- [reference:948](../../../../fixtures/typed.py#L948): `P.kwargs`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

7 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

The collector did not resolve direct evidence for this target. This is a limit of the collector, not proof that the type cannot be inferred from the source.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `decorator.wrapper.kwargs`

**Missing** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `kwargs` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:298](result.py#L298) · Reference: [typed.py:948](../../../../fixtures/typed.py#L948) · Input: [untyped.py:196](../../../../fixtures/untyped.py#L196)

```diff
@@ decorator.wrapper.kwargs · missing · TypeVar @@
-    def wrapper(*args, **kwargs) -> int:
+    def wrapper(*args: P.args, **kwargs: P.kwargs) -> ValueOrInt[R]:
```

</details>

**1. Expected contract**

The reference declares `kwargs` at [typed.py:948](../../../../fixtures/typed.py#L948). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `P.kwargs`: The authored contract selects this type.

Related operations in the reference:

- [reference:948](../../../../fixtures/typed.py#L948): `P.kwargs`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

7 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

The collector did not resolve direct evidence for this target. This is a limit of the collector, not proof that the type cannot be inferred from the source.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `decorator_with_args->`

**Missing** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `CallableValueToResult[CallableParametersToResult[P, R], CallableParametersToResult[P, ValueOrInt[R]]]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:305](result.py#L305) · Reference: [typed.py:969](../../../../fixtures/typed.py#L969) · Input: [untyped.py:203](../../../../fixtures/untyped.py#L203)

```diff
@@ decorator_with_args-> · missing · TypeVar @@
-def decorator_with_args(multiplier: int = 2):
+) -> CallableValueToResult[
```

</details>

**1. Expected contract**

The reference declares `CallableValueToResult[CallableParametersToResult[P, R], CallableParametersToResult[P, ValueOrInt[R]]]` at [typed.py:969](../../../../fixtures/typed.py#L969). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.CallableValueToResult[fixtures.typed.CallableParametersToResult[P, R], fixtures.typed.CallableParametersToResult[P, fixtures.typed.ValueOrInt[R]]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:1015](../../../../fixtures/typed.py#L1015): `return actual_decorator`. Source return/yield contributes a value.
- [reference:1013](../../../../fixtures/typed.py#L1013): `return wrapper`. Source return/yield contributes a value.
- [reference:1011](../../../../fixtures/typed.py#L1011): `return result`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

9 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:212](../../../../fixtures/untyped.py#L212) | return: `wrapper` | Contributes a result; all paths and operands must be resolved. |
| [input:214](../../../../fixtures/untyped.py#L214) | return: `actual_decorator` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Name**. Observation: `unprovable Name: actual_decorator`. Returns a name the prover cannot type (a wrapper, a decorated function, a class). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](../../../../docs/planning/TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls).

<details><summary>All 50 (first 30, with links to the author's line)</summary>

- `decorator->` ([typed.py:936](../../../../fixtures/typed.py#L936)): `CallableParametersToResult[P, ValueOrInt[R]]`
- `decorator.func` ([typed.py:935](../../../../fixtures/typed.py#L935)): `CallableParametersToResult[P, R]`
- `decorator.wrapper.args` ([typed.py:948](../../../../fixtures/typed.py#L948)): `args`
- `decorator.wrapper.kwargs` ([typed.py:948](../../../../fixtures/typed.py#L948)): `kwargs`
- `decorator_with_args->` ([typed.py:969](../../../../fixtures/typed.py#L969)): `CallableValueToResult[CallableParametersToResult[P, R], CallableParametersToResult[P, ValueOrInt[R]]]`
- `decorator_with_args.actual_decorator->` ([typed.py:985](../../../../fixtures/typed.py#L985)): `CallableParametersToResult[P, ValueOrInt[R]]`
- `decorator_with_args.actual_decorator.func` ([typed.py:984](../../../../fixtures/typed.py#L984)): `CallableParametersToResult[P, R]`
- `decorator_with_args.actual_decorator.wrapper->` ([typed.py:997](../../../../fixtures/typed.py#L997)): `ValueOrInt[R]`
- `decorator_with_args.actual_decorator.wrapper.args` ([typed.py:997](../../../../fixtures/typed.py#L997)): `args`
- `decorator_with_args.actual_decorator.wrapper.kwargs` ([typed.py:997](../../../../fixtures/typed.py#L997)): `kwargs`
- `decorator_with_class.cls` ([typed.py:1019](../../../../fixtures/typed.py#L1019)): `TypeValue[T]`
- `function_with_callable.callable_function->` ([typed.py:1940](../../../../fixtures/typed.py#L1940)): `OutputT`
- `function_with_callable.callable_function.arg` ([typed.py:1939](../../../../fixtures/typed.py#L1939)): `InputT`
- `function_with_class_decorator.add_method->` ([typed.py:2499](../../../../fixtures/typed.py#L2499)): `TypeValue[T]`
- `function_with_class_decorator.add_method.cls` ([typed.py:2499](../../../../fixtures/typed.py#L2499)): `TypeValue[T]`
- `function_with_class_decorator.add_method.new_method.self` ([typed.py:2510](../../../../fixtures/typed.py#L2510)): `T`
- `function_with_decorator_stack.decorator1->` ([typed.py:2867](../../../../fixtures/typed.py#L2867)): `CallableParametersToResult[P, R]`
- `function_with_decorator_stack.decorator1.func` ([typed.py:2866](../../../../fixtures/typed.py#L2866)): `CallableParametersToResult[P, R]`
- `function_with_decorator_stack.decorator1.wrapper->` ([typed.py:2879](../../../../fixtures/typed.py#L2879)): `R`
- `function_with_decorator_stack.decorator1.wrapper.args` ([typed.py:2879](../../../../fixtures/typed.py#L2879)): `args`
- `function_with_decorator_stack.decorator1.wrapper.kwargs` ([typed.py:2879](../../../../fixtures/typed.py#L2879)): `kwargs`
- `function_with_decorator_stack.decorator2->` ([typed.py:2896](../../../../fixtures/typed.py#L2896)): `CallableParametersToResult[P, R]`
- `function_with_decorator_stack.decorator2.func` ([typed.py:2895](../../../../fixtures/typed.py#L2895)): `CallableParametersToResult[P, R]`
- `function_with_decorator_stack.decorator2.wrapper->` ([typed.py:2908](../../../../fixtures/typed.py#L2908)): `R`
- `function_with_decorator_stack.decorator2.wrapper.args` ([typed.py:2908](../../../../fixtures/typed.py#L2908)): `args`
- `function_with_decorator_stack.decorator2.wrapper.kwargs` ([typed.py:2908](../../../../fixtures/typed.py#L2908)): `kwargs`
- `ExtendedResult.__getitem__->` ([typed.py:3864](../../../../fixtures/typed.py#L3864)): `ValueOrOther[StrOrValue[PayloadT], DictObject]`
- `DescriptorWithOwnerCache.__set__.value` ([typed.py:3977](../../../../fixtures/typed.py#L3977)): `ValueT`
- `RegistryMeta.__call__->` ([typed.py:4084](../../../../fixtures/typed.py#L4084)): `InstanceT`
- `RegistryMeta.__call__.cls` ([typed.py:4081](../../../../fixtures/typed.py#L4081)): `RegistryMeta | TypeValue[InstanceT]`

</details>

### Scalar: 31 missing

Tasks: [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [W-08](../../../../docs/planning/TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [I-10](../../../../docs/planning/TODO.md#i-10--numeric-tower-and-operator-result-rules), [F-37](../../../../docs/planning/TODO.md#f-37--default-literal-parameters-in-the-negotiator)

---

#### Missing annotation: `SupportsUpdate.update.message`

**Missing** · Scalar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `str` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:59](result.py#L59) · Reference: [typed.py:560](../../../../fixtures/typed.py#L560) · Input: [untyped.py:57](../../../../fixtures/untyped.py#L57)

```diff
@@ SupportsUpdate.update.message · missing · Scalar @@
-    def update(self, message) -> None:
+    def update(self, message: str) -> None:
```

</details>

**1. Expected contract**

The reference declares `str` at [typed.py:560](../../../../fixtures/typed.py#L560). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `str`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1056](../../../../fixtures/untyped.py#L1056) | same-named method in Observer: `function_with_observer.Observer.update(self, message)` | Name-only match; binding to this target is unverified. |
| [input:1560](../../../../fixtures/untyped.py#L1560) | same-named method in BuiltinMethodDict: `BuiltinMethodDict.update(self, other=(), *values, **kwargs)` | Name-only match; binding to this target is unverified. |
| [input:1674](../../../../fixtures/untyped.py#L1674) | call site passes: `custom_dict.update({'b': 2}, 3)  ->  {'b': 2}` | Name-only match; binding to this target is unverified. |
| [input:1675](../../../../fixtures/untyped.py#L1675) | call site passes: `builtin_dict.update({'b': 2})  ->  {'b': 2}` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **unsettled (no evidence)**. Nothing proves a type and no evidence reaches the node. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](../../../../docs/planning/TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source).

---

#### Missing annotation: `BaseClass.base_property.value`

**Missing** · Scalar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `int` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:214](result.py#L214) · Reference: [typed.py:853](../../../../fixtures/typed.py#L853) · Input: [untyped.py:150](../../../../fixtures/untyped.py#L150)

```diff
@@ BaseClass.base_property.value · missing · Scalar @@
-    def base_property(self, value) -> None:
+    def base_property(self, value: int) -> None:
```

</details>

**1. Expected contract**

The reference declares `int` at [typed.py:853](../../../../fixtures/typed.py#L853). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `int`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

The collector did not resolve direct evidence for this target. This is a limit of the collector, not proof that the type cannot be inferred from the source.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `MetaDecoratedClass.__init__.value`

**Missing** · Scalar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `int` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:278](result.py#L278) · Reference: [typed.py:924](../../../../fixtures/typed.py#L924) · Input: [untyped.py:187](../../../../fixtures/untyped.py#L187)

```diff
@@ MetaDecoratedClass.__init__.value · missing · Scalar @@
-    def __init__(self, value) -> None:
+    def __init__(self, value: int) -> None:
```

</details>

**1. Expected contract**

The reference declares `int` at [typed.py:924](../../../../fixtures/typed.py#L924). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `int`: The authored contract selects this type.

Related operations in the reference:

- [reference:931](../../../../fixtures/typed.py#L931): `self.value`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:135](../../../../fixtures/untyped.py#L135) | same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` | Name-only match; binding to this target is unverified. |
| [input:158](../../../../fixtures/untyped.py#L158) | same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` | Name-only match; binding to this target is unverified. |
| [input:223](../../../../fixtures/untyped.py#L223) | same-named method in Wrapper: `decorator_with_class.Wrapper.__init__(self, *args, **kwargs)` | Name-only match; binding to this target is unverified. |
| [input:1496](../../../../fixtures/untyped.py#L1496) | call site passes: `MetaDecoratedClass(value=100)  ->  100` Observed type: `int`. | Shows one argument/default, not every accepted input. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **unsettled (no evidence)**. Nothing proves a type and no evidence reaches the node. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](../../../../docs/planning/TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source).

---

#### Missing annotation: `function_with_property.PropertyClass.value.val`

**Missing** · Scalar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `int` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:828](result.py#L828) · Reference: [typed.py:1531](../../../../fixtures/typed.py#L1531) · Input: [untyped.py:463](../../../../fixtures/untyped.py#L463)

```diff
@@ function_with_property.PropertyClass.value.val · missing · Scalar @@
-        def value(self, val) -> None:
+        def value(self, val: int) -> None:
```

</details>

**1. Expected contract**

The reference declares `int` at [typed.py:1531](../../../../fixtures/typed.py#L1531). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `int`: The authored contract selects this type.

Related operations in the reference:

- [reference:1538](../../../../fixtures/typed.py#L1538): `self._value`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

The collector did not resolve direct evidence for this target. This is a limit of the collector, not proof that the type cannot be inferred from the source.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `function_with_slots.SlottedClass.__init__.x`

**Missing** · Scalar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `int` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1701](result.py#L1701) · Reference: [typed.py:2477](../../../../fixtures/typed.py#L2477) · Input: [untyped.py:954](../../../../fixtures/untyped.py#L954)

```diff
@@ function_with_slots.SlottedClass.__init__.x · missing · Scalar @@
-        def __init__(self, x, y) -> None:
+        def __init__(self, x: int, y: int) -> None:
```

</details>

**1. Expected contract**

The reference declares `int` at [typed.py:2477](../../../../fixtures/typed.py#L2477). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `int`: The authored contract selects this type.

Related operations in the reference:

- [reference:2485](../../../../fixtures/typed.py#L2485): `self.x`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

5 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:135](../../../../fixtures/untyped.py#L135) | same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` | Name-only match; binding to this target is unverified. |
| [input:158](../../../../fixtures/untyped.py#L158) | same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` | Name-only match; binding to this target is unverified. |
| [input:187](../../../../fixtures/untyped.py#L187) | same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **unsettled (no evidence)**. Nothing proves a type and no evidence reaches the node. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](../../../../docs/planning/TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source).

<details><summary>All 31 (first 30, with links to the author's line)</summary>

- `SupportsUpdate.update.message` ([typed.py:560](../../../../fixtures/typed.py#L560)): `str`
- `BaseClass.base_property.value` ([typed.py:853](../../../../fixtures/typed.py#L853)): `int`
- `MetaDecoratedClass.__init__.value` ([typed.py:924](../../../../fixtures/typed.py#L924)): `int`
- `function_with_property.PropertyClass.value.val` ([typed.py:1531](../../../../fixtures/typed.py#L1531)): `int`
- `function_with_slots.SlottedClass.__init__.x` ([typed.py:2477](../../../../fixtures/typed.py#L2477)): `int`
- `function_with_slots.SlottedClass.__init__.y` ([typed.py:2477](../../../../fixtures/typed.py#L2477)): `int`
- `function_with_factory.Factory.create.type_name` ([typed.py:2584](../../../../fixtures/typed.py#L2584)): `str`
- `function_with_builder.Builder.add_part.part` ([typed.py:2630](../../../../fixtures/typed.py#L2630)): `str`
- `function_with_observer.Observer.update.message` ([typed.py:2666](../../../../fixtures/typed.py#L2666)): `str`
- `function_with_observer.Subject.notify.message` ([typed.py:2691](../../../../fixtures/typed.py#L2691)): `str`
- `function_with_chain_of_responsibility.Handler.handle.request` ([typed.py:2840](../../../../fixtures/typed.py#L2840)): `str`
- `duplicate_scope_name.value` ([typed.py:3595](../../../../fixtures/typed.py#L3595)): `str`
- `AsyncResource.__init__.name` ([typed.py:4360](../../../../fixtures/typed.py#L4360)): `str`
- `AsyncResource.__aexit__->` ([typed.py:4385](../../../../fixtures/typed.py#L4385)): `bool`
- `AsyncResource.fetch.value` ([typed.py:4401](../../../../fixtures/typed.py#L4401)): `int`
- `extended_sync_context.seed` ([typed.py:4416](../../../../fixtures/typed.py#L4416)): `int`
- `extended_async_context.seed` ([typed.py:4436](../../../../fixtures/typed.py#L4436)): `int`
- `decorator_factory.prefix` ([typed.py:4491](../../../../fixtures/typed.py#L4491)): `str`
- `decorated_pipeline_value.value` ([typed.py:4546](../../../../fixtures/typed.py#L4546)): `str`
- `_->` ([typed.py:4589](../../../../fixtures/typed.py#L4589)): `str`
- `function_with_deep_attribute_assignment.Node.__init__.name` ([typed.py:5378](../../../../fixtures/typed.py#L5378)): `str`
- `SupportsInitializedByMeta.initialized_by_meta` ([typed.py:693](../../../../fixtures/typed.py#L693)): `bool`
- `DataClassExample.x` ([typed.py:1122](../../../../fixtures/typed.py#L1122)): `int`
- `DataClassExample.y` ([typed.py:1123](../../../../fixtures/typed.py#L1123)): `str`
- `function_with_chained_comparisons.x` ([typed.py:2067](../../../../fixtures/typed.py#L2067)): `int`
- `function_with_scope_resolution.DuplicateScopeNameClass.duplicated_name` ([typed.py:3749](../../../../fixtures/typed.py#L3749)): `str`
- `function_with_scope_resolution.nested_function_result` ([typed.py:3762](../../../../fixtures/typed.py#L3762)): `str`
- `function_with_scope_resolution.module_value` ([typed.py:3763](../../../../fixtures/typed.py#L3763)): `str`
- `function_with_numeric_tower.magnitude` ([typed.py:4790](../../../../fixtures/typed.py#L4790)): `float`
- `function_with_generator_send_throw_close.second` ([typed.py:5013](../../../../fixtures/typed.py#L5013)): `int`

</details>

### Module class: 38 missing

Tasks: [M2-02](../../../../docs/planning/TODO.md#m2-02--constructorattribute-resolution), [W-12](../../../../docs/planning/TODO.md#w-12--annotate-instance-attributes-from-negotiation), [I-11](../../../../docs/planning/TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-14](../../../../docs/planning/TODO.md#w-14--annotate-class-level-and-module-level-variables)

---

#### Missing annotation: `MetaClass.__new__->`

**Missing** · Module class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `MetaClass` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:116](result.py#L116) · Reference: [typed.py:750](../../../../fixtures/typed.py#L750) · Input: [untyped.py:101](../../../../fixtures/untyped.py#L101)

```diff
@@ MetaClass.__new__-> · missing · Module class @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+    ) -> MetaClass:
```

</details>

**1. Expected contract**

The reference declares `MetaClass` at [typed.py:750](../../../../fixtures/typed.py#L750). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.MetaClass`: The authored contract selects this type.

Related operations in the reference:

- [reference:766](../../../../fixtures/typed.py#L766): `return created`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:104](../../../../fixtures/untyped.py#L104) | return: `super().__new__(mcs, name, bases, namespace)` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

---

#### Missing annotation: `function_with_callable->`

**Missing** · Module class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `SupportsCall` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1174](result.py#L1174) · Reference: [typed.py:1929](../../../../fixtures/typed.py#L1929) · Input: [untyped.py:657](../../../../fixtures/untyped.py#L657)

```diff
@@ function_with_callable-> · missing · Module class @@
-def function_with_callable():
+def function_with_callable() -> SupportsCall:
```

</details>

**1. Expected contract**

The reference declares `SupportsCall` at [typed.py:1929](../../../../fixtures/typed.py#L1929). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.SupportsCall`: Requires the declared protocol members `__call__`. Matching an unrelated method name does not establish these structural requirements.

Related operations in the reference:

- [reference:1953](../../../../fixtures/typed.py#L1953): `return callable_function`. Source return/yield contributes a value.
- [reference:1951](../../../../fixtures/typed.py#L1951): `return func(arg)`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:662](../../../../fixtures/untyped.py#L662) | return: `func(arg)` | Contributes a result; all paths and operands must be resolved. |
| [input:664](../../../../fixtures/untyped.py#L664) | return: `callable_function` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Name**. Observation: `unprovable Name: callable_function`. Returns a name the prover cannot type (a wrapper, a decorated function, a class). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](../../../../docs/planning/TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls).

---

#### Missing annotation: `function_with_observer.Subject.attach.observer`

**Missing** · Module class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `SupportsUpdate` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1861](result.py#L1861) · Reference: [typed.py:2682](../../../../fixtures/typed.py#L2682) · Input: [untyped.py:1067](../../../../fixtures/untyped.py#L1067)

```diff
@@ function_with_observer.Subject.attach.observer · missing · Module class @@
-        def attach(self, observer) -> None:
+        def attach(self, observer: SupportsUpdate) -> None:
```

</details>

**1. Expected contract**

The reference declares `SupportsUpdate` at [typed.py:2682](../../../../fixtures/typed.py#L2682). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.SupportsUpdate`: Requires the declared protocol members `update`. Matching an unrelated method name does not establish these structural requirements.

Related operations in the reference:

- [reference:2689](../../../../fixtures/typed.py#L2689): `self.observers`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

The collector did not resolve direct evidence for this target. This is a limit of the collector, not proof that the type cannot be inferred from the source.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **unsettled (no evidence)**. Nothing proves a type and no evidence reaches the node. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](../../../../docs/planning/TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source).

---

#### Missing annotation: `function_with_command.ConcreteCommand.__init__.receiver`

**Missing** · Module class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `SupportsAction` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1964](result.py#L1964) · Reference: [typed.py:2795](../../../../fixtures/typed.py#L2795) · Input: [untyped.py:1126](../../../../fixtures/untyped.py#L1126)

```diff
@@ function_with_command.ConcreteCommand.__init__.receiver · missing · Module class @@
-        def __init__(self, receiver) -> None:
+        def __init__(self, receiver: SupportsAction) -> None:
```

</details>

**1. Expected contract**

The reference declares `SupportsAction` at [typed.py:2795](../../../../fixtures/typed.py#L2795). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.SupportsAction`: Requires the declared protocol members `action`. Matching an unrelated method name does not establish these structural requirements.

Related operations in the reference:

- [reference:2802](../../../../fixtures/typed.py#L2802): `self.receiver`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:135](../../../../fixtures/untyped.py#L135) | same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` | Name-only match; binding to this target is unverified. |
| [input:158](../../../../fixtures/untyped.py#L158) | same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` | Name-only match; binding to this target is unverified. |
| [input:187](../../../../fixtures/untyped.py#L187) | same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **unsettled (no evidence)**. Nothing proves a type and no evidence reaches the node. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](../../../../docs/planning/TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source).

---

#### Missing annotation: `function_with_chain_of_responsibility.Handler.set_next->`

**Missing** · Module class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `Handler` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1987](result.py#L1987) · Reference: [typed.py:2827](../../../../fixtures/typed.py#L2827) · Input: [untyped.py:1145](../../../../fixtures/untyped.py#L1145)

```diff
@@ function_with_chain_of_responsibility.Handler.set_next-> · missing · Module class @@
-        def set_next(self, handler):
+        def set_next(self, handler: Handler) -> Handler:
```

</details>

**1. Expected contract**

The reference declares `Handler` at [typed.py:2827](../../../../fixtures/typed.py#L2827). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.function_with_chain_of_responsibility.Handler`: The authored contract selects this type.

Related operations in the reference:

- [reference:2838](../../../../fixtures/typed.py#L2838): `return handler`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1148](../../../../fixtures/untyped.py#L1148) | return: `handler` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

<details><summary>All 38 (first 30, with links to the author's line)</summary>

- `MetaClass.__new__->` ([typed.py:750](../../../../fixtures/typed.py#L750)): `MetaClass`
- `function_with_callable->` ([typed.py:1929](../../../../fixtures/typed.py#L1929)): `SupportsCall`
- `function_with_observer.Subject.attach.observer` ([typed.py:2682](../../../../fixtures/typed.py#L2682)): `SupportsUpdate`
- `function_with_command.ConcreteCommand.__init__.receiver` ([typed.py:2795](../../../../fixtures/typed.py#L2795)): `SupportsAction`
- `function_with_chain_of_responsibility.Handler.set_next->` ([typed.py:2827](../../../../fixtures/typed.py#L2827)): `Handler`
- `function_with_chain_of_responsibility.Handler.set_next.handler` ([typed.py:2827](../../../../fixtures/typed.py#L2827)): `Handler`
- `function_with_namedtuple->` ([typed.py:3049](../../../../fixtures/typed.py#L3049)): `Point`
- `test_function_calls_part1->` ([typed.py:3201](../../../../fixtures/typed.py#L3201)): `TestCallsPart1`
- `test_function_calls_part2->` ([typed.py:3271](../../../../fixtures/typed.py#L3271)): `TestCallsPart2`
- `test_function_calls_part3->` ([typed.py:3329](../../../../fixtures/typed.py#L3329)): `TestCallsPart3`
- `test_function_calls->` ([typed.py:3398](../../../../fixtures/typed.py#L3398)): `TestCallsResult`
- `DescriptorStressOwner.summary->` ([typed.py:4033](../../../../fixtures/typed.py#L4033)): `DescriptorSummary`
- `RegistryMeta.__new__->` ([typed.py:4059](../../../../fixtures/typed.py#L4059)): `RegistryMeta`
- `AsyncResource.fetch->` ([typed.py:4401](../../../../fixtures/typed.py#L4401)): `AsyncPayload`
- `function_with_recursive_containers->` ([typed.py:4751](../../../../fixtures/typed.py#L4751)): `RecursiveRoot`
- `function_with_json_uuid_and_path_stress->` ([typed.py:4913](../../../../fixtures/typed.py#L4913)): `JSONRoundtrip`
- `function_with_local_class_closure_stress->` ([typed.py:5208](../../../../fixtures/typed.py#L5208)): `SupportsCallAndFromValues`
- `function_with_deep_attribute_assignment.Node.add->` ([typed.py:5390](../../../../fixtures/typed.py#L5390)): `Node`
- `function_with_deep_attribute_assignment.Node.add.child` ([typed.py:5390](../../../../fixtures/typed.py#L5390)): `Node`
- `test_extended_inference_edge_cases_part1->` ([typed.py:5650](../../../../fixtures/typed.py#L5650)): `ExtendedResultsPart1`
- `test_extended_inference_edge_cases_part2->` ([typed.py:5691](../../../../fixtures/typed.py#L5691)): `ExtendedResultsPart2`
- `MetaClass.__call__.instance` ([typed.py:784](../../../../fixtures/typed.py#L784)): `SupportsInitializedByMeta`
- `test_other_operations.vec` ([typed.py:3444](../../../../fixtures/typed.py#L3444)): `SupportsAdditionAndXAndY`
- `test_other_operations.vec2` ([typed.py:3445](../../../../fixtures/typed.py#L3445)): `SupportsAdditionAndXAndY`
- `test_other_operations.vec_sum` ([typed.py:3446](../../../../fixtures/typed.py#L3446)): `SupportsAdditionAndXAndY`
- `function_with_importlib_and_dunder_import.os_path_module` ([typed.py:3676](../../../../fixtures/typed.py#L3676)): `SupportsNameAndPath`
- `RegistryMeta.__new__.cls` ([typed.py:4074](../../../../fixtures/typed.py#L4074)): `RegistryMeta`
- `extended_sync_context.context` ([typed.py:4427](../../../../fixtures/typed.py#L4427)): `SyncContext`
- `function_with_recursive_containers.root` ([typed.py:4761](../../../../fixtures/typed.py#L4761)): `RecursiveRoot`
- `function_with_recursive_containers.child` ([typed.py:4762](../../../../fixtures/typed.py#L4762)): `RecursiveChild`

</details>

### Top type (object): 25 missing

Tasks: policy: astart never writes object; [G-02](../../../../docs/planning/TODO.md#g-02--score-valid-narrowing-as-narrower-not-wrong) scores narrower

---

#### Missing annotation: `MetaClass.__new__._kwargs`

**Missing** · Top type (object)

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `object` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:116](result.py#L116) · Reference: [typed.py:749](../../../../fixtures/typed.py#L749) · Input: [untyped.py:101](../../../../fixtures/untyped.py#L101)

```diff
@@ MetaClass.__new__._kwargs · missing · Top type (object) @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        **_kwargs: object,
```

</details>

**1. Expected contract**

The reference declares `object` at [typed.py:749](../../../../fixtures/typed.py#L749). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `object`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:991](../../../../fixtures/untyped.py#L991) | same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` | Name-only match; binding to this target is unverified. |
| [input:1881](../../../../fixtures/untyped.py#L1881) | same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `MetaClass.__call__->`

**Missing** · Top type (object)

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `object` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:132](result.py#L132) · Reference: [typed.py:773](../../../../fixtures/typed.py#L773) · Input: [untyped.py:106](../../../../fixtures/untyped.py#L106)

```diff
@@ MetaClass.__call__-> · missing · Top type (object) @@
-    def __call__(cls, *args, **kwargs):
+    ) -> object:
```

</details>

**1. Expected contract**

The reference declares `object` at [typed.py:773](../../../../fixtures/typed.py#L773). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `object`: The authored contract selects this type.

Related operations in the reference:

- [reference:786](../../../../fixtures/typed.py#L786): `return instance`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

4 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:111](../../../../fixtures/untyped.py#L111) | return: `initialized` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

---

#### Missing annotation: `MetaClass.__call__.args`

**Missing** · Top type (object)

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `object` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:132](result.py#L132) · Reference: [typed.py:771](../../../../fixtures/typed.py#L771) · Input: [untyped.py:106](../../../../fixtures/untyped.py#L106)

```diff
@@ MetaClass.__call__.args · missing · Top type (object) @@
-    def __call__(cls, *args, **kwargs):
+        *args: object,
```

</details>

**1. Expected contract**

The reference declares `object` at [typed.py:771](../../../../fixtures/typed.py#L771). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `object`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

4 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1891](../../../../fixtures/untyped.py#L1891) | same-named method in RegistryMeta: `RegistryMeta.__call__(cls, *args, **_kwargs)` | Name-only match; binding to this target is unverified. |
| [input:1997](../../../../fixtures/untyped.py#L1997) | same-named method in CallableObject: `CallableObject.__call__(self, value, *, scale=1)` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `MetaClass.__call__.kwargs`

**Missing** · Top type (object)

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `object` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:132](result.py#L132) · Reference: [typed.py:772](../../../../fixtures/typed.py#L772) · Input: [untyped.py:106](../../../../fixtures/untyped.py#L106)

```diff
@@ MetaClass.__call__.kwargs · missing · Top type (object) @@
-    def __call__(cls, *args, **kwargs):
+        **kwargs: object,
```

</details>

**1. Expected contract**

The reference declares `object` at [typed.py:772](../../../../fixtures/typed.py#L772). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `object`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

4 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1891](../../../../fixtures/untyped.py#L1891) | same-named method in RegistryMeta: `RegistryMeta.__call__(cls, *args, **_kwargs)` | Name-only match; binding to this target is unverified. |
| [input:1997](../../../../fixtures/untyped.py#L1997) | same-named method in CallableObject: `CallableObject.__call__(self, value, *, scale=1)` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `decorator_with_class.Wrapper.__init__.args`

**Missing** · Top type (object)

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `object` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:336](result.py#L336) · Reference: [typed.py:1034](../../../../fixtures/typed.py#L1034) · Input: [untyped.py:223](../../../../fixtures/untyped.py#L223)

```diff
@@ decorator_with_class.Wrapper.__init__.args · missing · Top type (object) @@
-        def __init__(self, *args, **kwargs) -> None:
+        def __init__(self, *args: object, **_kwargs: object) -> None:
```

</details>

**1. Expected contract**

The reference declares `object` at [typed.py:1034](../../../../fixtures/typed.py#L1034). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `object`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:135](../../../../fixtures/untyped.py#L135) | same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` | Name-only match; binding to this target is unverified. |
| [input:158](../../../../fixtures/untyped.py#L158) | same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` | Name-only match; binding to this target is unverified. |
| [input:187](../../../../fixtures/untyped.py#L187) | same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

<details><summary>All 25 (first 30, with links to the author's line)</summary>

- `MetaClass.__new__._kwargs` ([typed.py:749](../../../../fixtures/typed.py#L749)): `object`
- `MetaClass.__call__->` ([typed.py:773](../../../../fixtures/typed.py#L773)): `object`
- `MetaClass.__call__.args` ([typed.py:771](../../../../fixtures/typed.py#L771)): `object`
- `MetaClass.__call__.kwargs` ([typed.py:772](../../../../fixtures/typed.py#L772)): `object`
- `decorator_with_class.Wrapper.__init__.args` ([typed.py:1034](../../../../fixtures/typed.py#L1034)): `object`
- `decorator_with_class.Wrapper.__getattr__->` ([typed.py:1044](../../../../fixtures/typed.py#L1044)): `object`
- `function_with_descriptor.Descriptor.__get__.obj` ([typed.py:1563](../../../../fixtures/typed.py#L1563)): `object`
- `function_with_descriptor.Descriptor.__set__.obj` ([typed.py:1577](../../../../fixtures/typed.py#L1577)): `object`
- `function_with_descriptor.Descriptor.__delete__.obj` ([typed.py:1588](../../../../fixtures/typed.py#L1588)): `object`
- `function_with_operator_overloading.Vector.__eq__.other` ([typed.py:1662](../../../../fixtures/typed.py#L1662)): `object`
- `function_with_metaclass_usage->` ([typed.py:1711](../../../../fixtures/typed.py#L1711)): `object`
- `function_with_weak_refs->` ([typed.py:2444](../../../../fixtures/typed.py#L2444)): `ReferenceType[object]`
- `DescriptorWithOwnerCache.__set__.instance` ([typed.py:3977](../../../../fixtures/typed.py#L3977)): `object`
- `DescriptorWithOwnerCache.__delete__.instance` ([typed.py:3987](../../../../fixtures/typed.py#L3987)): `object`
- `RegistryMeta.__new__._kwargs` ([typed.py:4058](../../../../fixtures/typed.py#L4058)): `object`
- `RegistryMeta.__call__.args` ([typed.py:4082](../../../../fixtures/typed.py#L4082)): `object`
- `RegistryBase.clone.overrides` ([typed.py:4105](../../../../fixtures/typed.py#L4105)): `object`
- `RegistryItem.__init__.extras` ([typed.py:4128](../../../../fixtures/typed.py#L4128)): `object`
- `FluentBuilder.configure.options` ([typed.py:4181](../../../../fixtures/typed.py#L4181)): `object`
- `HybridContainer.__contains__.item` ([typed.py:4245](../../../../fixtures/typed.py#L4245)): `object`
- `AsyncResource.__aexit__.tb` ([typed.py:4384](../../../../fixtures/typed.py#L4384)): `object`
- `test_function_calls_part1.result17` ([typed.py:3239](../../../../fixtures/typed.py#L3239)): `object`
- `decorator_factory.decorate.wrapper.result` ([typed.py:4533](../../../../fixtures/typed.py#L4533)): `object`
- `function_with_import_and_reflection_stress.attr` ([typed.py:4903](../../../../fixtures/typed.py#L4903)): `object`
- `function_with_contextvars_and_chainmap.chain_map` ([typed.py:4953](../../../../fixtures/typed.py#L4953)): `ChainMap[str, object]`

</details>

### Library class: 6 missing

Tasks: [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [T-08](../../../../docs/planning/TODO.md#t-08--library-return-types-from-typeshed)

---

#### Missing annotation: `function_with_exception_chaining.exception_chain_func.raise_second_error.original_error`

**Missing** · Library class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ValueError` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1638](result.py#L1638) · Reference: [typed.py:2396](../../../../fixtures/typed.py#L2396) · Input: [untyped.py:907](../../../../fixtures/untyped.py#L907)

```diff
@@ function_with_exception_chaining.exception_chain_func.raise_second_error.original_error · missing · Library class @@
-        def raise_second_error(original_error) -> Never:
+        def raise_second_error(original_error: ValueError) -> None:
```

</details>

**1. Expected contract**

The reference declares `ValueError` at [typed.py:2396](../../../../fixtures/typed.py#L2396). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `ValueError`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:914](../../../../fixtures/untyped.py#L914) | call site passes: `raise_second_error(original_error=e)  ->  e` | Shows one argument/default, not every accepted input. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: a call to it cannot be bound**. Observation: `a call to it cannot be bound`. Some call to the function cannot be matched to its parameters. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-07](../../../../docs/planning/TODO.md#w-07--burn-down-unbindable-calls-and-escaping-functions), [M2-02](../../../../docs/planning/TODO.md#m2-02--constructorattribute-resolution), [M2-11](../../../../docs/planning/TODO.md#m2-11--kwargs-for-method-calls).

---

#### Missing annotation: `function_with_islice.data`

**Missing** · Library class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `range` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2227](result.py#L2227) · Reference: [typed.py:3091](../../../../fixtures/typed.py#L3091) · Input: [untyped.py:1275](../../../../fixtures/untyped.py#L1275)

```diff
@@ function_with_islice.data · missing · Library class @@
-    data = range(10)
+    data: range = range(10)
```

</details>

**1. Expected contract**

The reference declares `range` at [typed.py:3091](../../../../fixtures/typed.py#L3091). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `range`: The authored contract selects this type.

Related operations in the reference:

- [reference:3092](../../../../fixtures/typed.py#L3092): `return list(islice(data, 2, 8, 2))`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1275](../../../../fixtures/untyped.py#L1275) | assignment: `data = range(10)` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Call**. Observation: `unprovable Call: range(10)`. Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers).

---

#### Missing annotation: `function_with_importlib_and_dunder_import.pathlib_module`

**Missing** · Library class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ModuleType` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2781](result.py#L2781) · Reference: [typed.py:3675](../../../../fixtures/typed.py#L3675) · Input: [untyped.py:1688](../../../../fixtures/untyped.py#L1688)

```diff
@@ function_with_importlib_and_dunder_import.pathlib_module · missing · Library class @@
-    pathlib_module = importlib.import_module(name="pathlib")
+    pathlib_module: ModuleType = import_module(name="pathlib")
```

</details>

**1. Expected contract**

The reference declares `ModuleType` at [typed.py:3675](../../../../fixtures/typed.py#L3675). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `types.ModuleType`: The authored contract selects this type.

Related operations in the reference:

- [reference:3678](../../../../fixtures/typed.py#L3678): `return ImportExampleResult( importlib_module_name=pathlib_module.__name__, dunder_module_name=os_path_module.__name__, imported_join_result=imported_join_result`. Source return/yield contributes a value.
- [reference:3679](../../../../fixtures/typed.py#L3679): `pathlib_module.__name__`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1688](../../../../fixtures/untyped.py#L1688) | assignment: `pathlib_module = importlib.import_module(name='pathlib')` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Call**. Observation: `unprovable Call: importlib.import_module(name='pathlib')`. Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers).

---

#### Missing annotation: `function_with_import_and_reflection_stress.module`

**Missing** · Library class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ModuleType` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3746](result.py#L3746) · Reference: [typed.py:4902](../../../../fixtures/typed.py#L4902) · Input: [untyped.py:2268](../../../../fixtures/untyped.py#L2268)

```diff
@@ function_with_import_and_reflection_stress.module · missing · Library class @@
-    module = importlib.import_module(name=module_name)
+    module: ModuleType = import_module(name=module_name)
```

</details>

**1. Expected contract**

The reference declares `ModuleType` at [typed.py:4902](../../../../fixtures/typed.py#L4902). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `types.ModuleType`: The authored contract selects this type.

Related operations in the reference:

- [reference:4905](../../../../fixtures/typed.py#L4905): `return { "module": module.__name__, "attr": attr, "attr_type": attr_type.__name__, "has_doc": bool(getattr(attr, "__doc__", None)), }`. Source return/yield contributes a value.
- [reference:4906](../../../../fixtures/typed.py#L4906): `module.__name__`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

7 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2268](../../../../fixtures/untyped.py#L2268) | assignment: `module = importlib.import_module(name=module_name)` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Call**. Observation: `unprovable Call: importlib.import_module(name=module_name)`. Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers).

---

#### Missing annotation: `function_with_bytes_memoryview_and_slices.raw`

**Missing** · Library class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `bytearray` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4072](result.py#L4072) · Reference: [typed.py:5423](../../../../fixtures/typed.py#L5423) · Input: [untyped.py:2503](../../../../fixtures/untyped.py#L2503)

```diff
@@ function_with_bytes_memoryview_and_slices.raw · missing · Library class @@
-    raw = bytearray(data)
+    raw: bytearray = bytearray(data)
```

</details>

**1. Expected contract**

The reference declares `bytearray` at [typed.py:5423](../../../../fixtures/typed.py#L5423). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `bytearray`: The authored contract selects this type.

Related operations in the reference:

- [reference:5428](../../../../fixtures/typed.py#L5428): `return raw, view, prefix, ordinal_sum`. Source return/yield contributes a value.
- [reference:5424](../../../../fixtures/typed.py#L5424): `raw.extend`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

7 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2503](../../../../fixtures/untyped.py#L2503) | assignment: `raw = bytearray(data)` | Constrains stored values; later writes and aliases also matter. |
| [input:2504](../../../../fixtures/untyped.py#L2504) | adds elements: `raw.extend(b'!')` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

<details><summary>All 6 (first 30, with links to the author's line)</summary>

- `function_with_exception_chaining.exception_chain_func.raise_second_error.original_error` ([typed.py:2396](../../../../fixtures/typed.py#L2396)): `ValueError`
- `function_with_islice.data` ([typed.py:3091](../../../../fixtures/typed.py#L3091)): `range`
- `function_with_importlib_and_dunder_import.pathlib_module` ([typed.py:3675](../../../../fixtures/typed.py#L3675)): `ModuleType`
- `function_with_import_and_reflection_stress.module` ([typed.py:4902](../../../../fixtures/typed.py#L4902)): `ModuleType`
- `function_with_bytes_memoryview_and_slices.raw` ([typed.py:5423](../../../../fixtures/typed.py#L5423)): `bytearray`
- `function_with_bytes_memoryview_and_slices.view` ([typed.py:5425](../../../../fixtures/typed.py#L5425)): `memoryview[int]`

</details>

### Self: 5 missing

Tasks: [W-11](../../../../docs/planning/TODO.md#w-11--annotate-a-method-that-returns-its-own-class-self-or-quoted-name), [AF-02](../../../../docs/planning/TODO.md#af-02--annotate-selfcls-only-when-the-style-asks), [F-43](../../../../docs/planning/TODO.md#f-43--quote-instead-of-refusing)

---

#### Missing annotation: `RegistryBase.clone->`

**Missing** · Self

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `Self` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3121](result.py#L3121) · Reference: [typed.py:4105](../../../../fixtures/typed.py#L4105) · Input: [untyped.py:1901](../../../../fixtures/untyped.py#L1901)

```diff
@@ RegistryBase.clone-> · missing · Self @@
-    def clone(self, **overrides):
+    def clone(self, **overrides: object) -> Self:
```

</details>

**1. Expected contract**

The reference declares `Self` at [typed.py:4105](../../../../fixtures/typed.py#L4105). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `RegistryBase.Self`: Preserves the receiver's concrete subclass in the result.

Related operations in the reference:

- [reference:4117](../../../../fixtures/typed.py#L4117): `return self.__class__(**data)`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1905](../../../../fixtures/untyped.py#L1905) | return: `self.__class__(**data)` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Call**. Observation: `unprovable Call: self.__class__(**data)`. Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers).

---

#### Missing annotation: `HybridContainer.__or__->`

**Missing** · Self

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `Self` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3270](result.py#L3270) · Reference: [typed.py:4303](../../../../fixtures/typed.py#L4303) · Input: [untyped.py:1979](../../../../fixtures/untyped.py#L1979)

```diff
@@ HybridContainer.__or__-> · missing · Self @@
-    def __or__(self, other):
+    ) -> Self:
```

</details>

**1. Expected contract**

The reference declares `Self` at [typed.py:4303](../../../../fixtures/typed.py#L4303). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `HybridContainer.Self`: Preserves the receiver's concrete subclass in the result.

Related operations in the reference:

- [reference:4319](../../../../fixtures/typed.py#L4319): `return merged`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

12 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1987](../../../../fixtures/untyped.py#L1987) | return: `merged` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

#### Missing annotation: `AsyncResource.__aenter__->`

**Missing** · Self

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `Self` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3328](result.py#L3328) · Reference: [typed.py:4370](../../../../fixtures/typed.py#L4370) · Input: [untyped.py:2014](../../../../fixtures/untyped.py#L2014)

```diff
@@ AsyncResource.__aenter__-> · missing · Self @@
-    async def __aenter__(self):
+    async def __aenter__(self) -> Self:
```

</details>

**1. Expected contract**

The reference declares `Self` at [typed.py:4370](../../../../fixtures/typed.py#L4370). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `AsyncResource.Self`: Preserves the receiver's concrete subclass in the result.

Related operations in the reference:

- [reference:4378](../../../../fixtures/typed.py#L4378): `return self`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2017](../../../../fixtures/untyped.py#L2017) | return: `self` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Name**. Observation: `unprovable Name: self`. Returns a name the prover cannot type (a wrapper, a decorated function, a class). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](../../../../docs/planning/TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls).

---

#### Missing annotation: `function_with_local_class_closure_stress.LocalMultiplier.from_values->`

**Missing** · Self

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `Self` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3955](result.py#L3955) · Reference: [typed.py:5244](../../../../fixtures/typed.py#L5244) · Input: [untyped.py:2419](../../../../fixtures/untyped.py#L2419)

```diff
@@ function_with_local_class_closure_stress.LocalMultiplier.from_values-> · missing · Self @@
-        def from_values(cls, values: Iterable):
+        def from_values(cls, values: SequenceInt) -> Self:
```

</details>

**1. Expected contract**

The reference declares `Self` at [typed.py:5244](../../../../fixtures/typed.py#L5244). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `function_with_local_class_closure_stress.LocalMultiplier.Self`: Preserves the receiver's concrete subclass in the result.

Related operations in the reference:

- [reference:5254](../../../../fixtures/typed.py#L5254): `return cls(offset=sum(values))`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2420](../../../../fixtures/untyped.py#L2420) | return: `cls(offset=sum(values))` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Call**. Observation: `unprovable Call: cls(offset=sum(values))`. Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers).

---

#### Missing annotation: `function_with_singleton.Singleton._instance`

**Missing** · Self

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ClassVar[Self \| None]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1752](result.py#L1752) · Reference: [typed.py:2550](../../../../fixtures/typed.py#L2550) · Input: [untyped.py:989](../../../../fixtures/untyped.py#L989)

```diff
@@ function_with_singleton.Singleton._instance · missing · Self @@
-        _instance = None
+        _instance: ClassVar[Self | None] = None
```

</details>

**1. Expected contract**

The reference declares `ClassVar[Self | None]` at [typed.py:2550](../../../../fixtures/typed.py#L2550). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `typing.ClassVar[function_with_singleton.Singleton.Self | None]`: The authored contract selects this type.

Related operations in the reference:

- [reference:2561](../../../../fixtures/typed.py#L2561): `return cls._instance`. Source return/yield contributes a value.
- [reference:2561](../../../../fixtures/typed.py#L2561): `cls._instance`. The source requires this receiver member.
- [reference:2559](../../../../fixtures/typed.py#L2559): `cls._instance`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

7 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:989](../../../../fixtures/untyped.py#L989) | assignment: `_instance = None` Observed type: `None`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

<details><summary>All 5 (first 30, with links to the author's line)</summary>

- `RegistryBase.clone->` ([typed.py:4105](../../../../fixtures/typed.py#L4105)): `Self`
- `HybridContainer.__or__->` ([typed.py:4303](../../../../fixtures/typed.py#L4303)): `Self`
- `AsyncResource.__aenter__->` ([typed.py:4370](../../../../fixtures/typed.py#L4370)): `Self`
- `function_with_local_class_closure_stress.LocalMultiplier.from_values->` ([typed.py:5244](../../../../fixtures/typed.py#L5244)): `Self`
- `function_with_singleton.Singleton._instance` ([typed.py:2550](../../../../fixtures/typed.py#L2550)): `ClassVar[Self | None]`

</details>

### Optional: 5 missing

Tasks: [I-01](../../../../docs/planning/TODO.md#i-01--narrow-the-else-branch-by-complement), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [AL-01](../../../../docs/planning/TODO.md#al-01--control-flow-graph-and-per-block-narrowing-replaces-ad-hoc-if-handling)

---

#### Missing annotation: `ExtendedDataclassStress.__init__.values`

**Missing** · Optional

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ListInt \| None` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2975](result.py#L2975) · Reference: [typed.py:3893](../../../../fixtures/typed.py#L3893) · Input: [untyped.py:1816](../../../../fixtures/untyped.py#L1816)

```diff
@@ ExtendedDataclassStress.__init__.values · missing · Optional @@
-        values=None,
+        values: ListInt | None = None,
```

</details>

**1. Expected contract**

The reference declares `ListInt | None` at [typed.py:3893](../../../../fixtures/typed.py#L3893). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `list[int]`: The authored contract selects this type.
- `None`: The authored contract selects this type.

Related operations in the reference:

- [reference:3907](../../../../fixtures/typed.py#L3907): `self.values`. The source requires this receiver member.
- [reference:3910](../../../../fixtures/typed.py#L3910): `self.values`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

18 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:135](../../../../fixtures/untyped.py#L135) | same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` | Name-only match; binding to this target is unverified. |
| [input:158](../../../../fixtures/untyped.py#L158) | same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` | Name-only match; binding to this target is unverified. |
| [input:187](../../../../fixtures/untyped.py#L187) | same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` | Name-only match; binding to this target is unverified. |
| [input:1816](../../../../fixtures/untyped.py#L1816) | default value: `None` Observed type: `None`. | Shows one argument/default, not every accepted input. |
| [input:1822](../../../../fixtures/untyped.py#L1822) | body compares it with None: `values is None` | A constraint to combine with other operations and bindings. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

#### Missing annotation: `ExtendedDataclassStress.__init__.lookup`

**Missing** · Optional

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `DictInt \| None` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2976](result.py#L2976) · Reference: [typed.py:3894](../../../../fixtures/typed.py#L3894) · Input: [untyped.py:1817](../../../../fixtures/untyped.py#L1817)

```diff
@@ ExtendedDataclassStress.__init__.lookup · missing · Optional @@
-        lookup=None,
+        lookup: DictInt | None = None,
```

</details>

**1. Expected contract**

The reference declares `DictInt | None` at [typed.py:3894](../../../../fixtures/typed.py#L3894). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `dict[str, int]`: Preserves key/value types (str, int). Mapping operations and the types flowing through keys and values must agree.
- `None`: The authored contract selects this type.

Related operations in the reference:

- [reference:3908](../../../../fixtures/typed.py#L3908): `self.lookup`. The source requires this receiver member.
- [reference:3910](../../../../fixtures/typed.py#L3910): `self.lookup`. The source requires this receiver member.
- [reference:3911](../../../../fixtures/typed.py#L3911): `self.lookup`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

18 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:135](../../../../fixtures/untyped.py#L135) | same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` | Name-only match; binding to this target is unverified. |
| [input:158](../../../../fixtures/untyped.py#L158) | same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` | Name-only match; binding to this target is unverified. |
| [input:187](../../../../fixtures/untyped.py#L187) | same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` | Name-only match; binding to this target is unverified. |
| [input:1817](../../../../fixtures/untyped.py#L1817) | default value: `None` Observed type: `None`. | Shows one argument/default, not every accepted input. |
| [input:1823](../../../../fixtures/untyped.py#L1823) | body compares it with None: `lookup is None` | A constraint to combine with other operations and bindings. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

#### Missing annotation: `RegistryItem.__init__.tags`

**Missing** · Optional

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ListStr \| None` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3138](result.py#L3138) · Reference: [typed.py:4127](../../../../fixtures/typed.py#L4127) · Input: [untyped.py:1911](../../../../fixtures/untyped.py#L1911)

```diff
@@ RegistryItem.__init__.tags · missing · Optional @@
-    def __init__(self, name: str, count: int = 0, tags=None, **extras) -> None:
+        tags: ListStr | None = None,
```

</details>

**1. Expected contract**

The reference declares `ListStr | None` at [typed.py:4127](../../../../fixtures/typed.py#L4127). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `list[str]`: The authored contract selects this type.
- `None`: The authored contract selects this type.

Related operations in the reference:

- [reference:4141](../../../../fixtures/typed.py#L4141): `self.tags`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

9 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:135](../../../../fixtures/untyped.py#L135) | same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` | Name-only match; binding to this target is unverified. |
| [input:158](../../../../fixtures/untyped.py#L158) | same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` | Name-only match; binding to this target is unverified. |
| [input:187](../../../../fixtures/untyped.py#L187) | same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` | Name-only match; binding to this target is unverified. |
| [input:1911](../../../../fixtures/untyped.py#L1911) | default value: `None` Observed type: `None`. | Shows one argument/default, not every accepted input. |
| [input:1915](../../../../fixtures/untyped.py#L1915) | body compares it with None: `tags is None` | A constraint to combine with other operations and bindings. |
| [input:2353](../../../../fixtures/untyped.py#L2353) | call site passes: `RegistryItem(name='alpha', count=1, tags=['x'], extra=True)  ->  ['x']` Observed type: `list[str]`. | Shows one argument/default, not every accepted input. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

#### Missing annotation: `AsyncResource.__aexit__.exc_type`

**Missing** · Optional

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `TypeValue[BaseException] \| None` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3337](result.py#L3337) · Reference: [typed.py:4382](../../../../fixtures/typed.py#L4382) · Input: [untyped.py:2019](../../../../fixtures/untyped.py#L2019)

```diff
@@ AsyncResource.__aexit__.exc_type · missing · Optional @@
-    async def __aexit__(self, exc_type, exc, tb):
+        exc_type: TypeValue[BaseException] | None,
```

</details>

**1. Expected contract**

The reference declares `TypeValue[BaseException] | None` at [typed.py:4382](../../../../fixtures/typed.py#L4382). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.TypeValue[BaseException]`: The authored contract selects this type.
- `None`: The authored contract selects this type.

Related operations in the reference:

- [reference:4399](../../../../fixtures/typed.py#L4399): `return exc_type is None`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2022](../../../../fixtures/untyped.py#L2022) | body compares it with None: `exc_type is None` | A constraint to combine with other operations and bindings. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **unsettled (no evidence)**. Nothing proves a type and no evidence reaches the node. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](../../../../docs/planning/TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source).

---

#### Missing annotation: `AsyncResource.__aexit__.exc`

**Missing** · Optional

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `BaseException \| None` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3337](result.py#L3337) · Reference: [typed.py:4383](../../../../fixtures/typed.py#L4383) · Input: [untyped.py:2019](../../../../fixtures/untyped.py#L2019)

```diff
@@ AsyncResource.__aexit__.exc · missing · Optional @@
-    async def __aexit__(self, exc_type, exc, tb):
+        exc: BaseException | None,
```

</details>

**1. Expected contract**

The reference declares `BaseException | None` at [typed.py:4383](../../../../fixtures/typed.py#L4383). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `BaseException`: The authored contract selects this type.
- `None`: The authored contract selects this type.

Related operations in the reference:

- [reference:4399](../../../../fixtures/typed.py#L4399): `return exc_type is None`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

The collector did not resolve direct evidence for this target. This is a limit of the collector, not proof that the type cannot be inferred from the source.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **unsettled (no evidence)**. Nothing proves a type and no evidence reaches the node. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](../../../../docs/planning/TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source).

<details><summary>All 5 (first 30, with links to the author's line)</summary>

- `ExtendedDataclassStress.__init__.values` ([typed.py:3893](../../../../fixtures/typed.py#L3893)): `ListInt | None`
- `ExtendedDataclassStress.__init__.lookup` ([typed.py:3894](../../../../fixtures/typed.py#L3894)): `DictInt | None`
- `RegistryItem.__init__.tags` ([typed.py:4127](../../../../fixtures/typed.py#L4127)): `ListStr | None`
- `AsyncResource.__aexit__.exc_type` ([typed.py:4382](../../../../fixtures/typed.py#L4382)): `TypeValue[BaseException] | None`
- `AsyncResource.__aexit__.exc` ([typed.py:4383](../../../../fixtures/typed.py#L4383)): `BaseException | None`

</details>

### Generator/Iterator: 5 missing

Tasks: [W-13](../../../../docs/planning/TODO.md#w-13--type-generators-as-iterator), [G-05](../../../../docs/planning/TODO.md#g-05--normalise-generator-defaults-and-subtype-spelling-in-the-scorer)

---

#### Missing annotation: `ExtendedResult.__iter__->`

**Missing** · Generator/Iterator

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `Iterator[ValueOrOther[StrOrValue[PayloadT], DictObject]]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2929](result.py#L2929) · Reference: [typed.py:3823](../../../../fixtures/typed.py#L3823) · Input: [untyped.py:1788](../../../../fixtures/untyped.py#L1788)

```diff
@@ ExtendedResult.__iter__-> · missing · Generator/Iterator @@
-    def __iter__(self):
+    ) -> Iterator[ValueOrOther[StrOrValue[PayloadT], DictObject]]:
```

</details>

**1. Expected contract**

The reference declares `Iterator[ValueOrOther[StrOrValue[PayloadT], DictObject]]` at [typed.py:3823](../../../../fixtures/typed.py#L3823). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `collections.abc.Iterator[fixtures.typed.ValueOrOther[fixtures.typed.StrOrValue[fixtures.typed.ExtendedResult], dict[str, object]]]`: Preserves iteration/yield types (fixtures.typed.ValueOrOther[fixtures.typed.StrOrValue[fixtures.typed.ExtendedResult], dict[str, object]]); iteration does not by itself establish sequence indexing.

Related operations in the reference:

- [reference:3830](../../../../fixtures/typed.py#L3830): `yield self.name`. Source return/yield contributes a value.
- [reference:3831](../../../../fixtures/typed.py#L3831): `yield self.payload`. Source return/yield contributes a value.
- [reference:3832](../../../../fixtures/typed.py#L3832): `yield self.metadata`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

7 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1788](../../../../fixtures/untyped.py#L1788) | generator: `the body contains 'yield'` | A constraint to combine with other operations and bindings. |
| [input:1792](../../../../fixtures/untyped.py#L1792) | falls off the end: `some path ends without 'return', so it returns None` Observed type: `None`. | A constraint to combine with other operations and bindings. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: generator**. Observation: `generator`. Generator functions: the return type needs the yield types. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-13](../../../../docs/planning/TODO.md#w-13--type-generators-as-iterator), [M4-06](../../../../docs/planning/TODO.md#m4-06--r3-generatorasync).

---

#### Missing annotation: `HybridContainer.__iter__->`

**Missing** · Generator/Iterator

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `Iterator[ItemT]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3226](result.py#L3226) · Reference: [typed.py:4236](../../../../fixtures/typed.py#L4236) · Input: [untyped.py:1958](../../../../fixtures/untyped.py#L1958)

```diff
@@ HybridContainer.__iter__-> · missing · Generator/Iterator @@
-    def __iter__(self):
+    def __iter__(self) -> Iterator[ItemT]:
```

</details>

**1. Expected contract**

The reference declares `Iterator[ItemT]` at [typed.py:4236](../../../../fixtures/typed.py#L4236). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `collections.abc.Iterator[fixtures.typed.HybridContainer]`: Preserves iteration/yield types (fixtures.typed.HybridContainer); iteration does not by itself establish sequence indexing.

Related operations in the reference:

- [reference:4243](../../../../fixtures/typed.py#L4243): `return iter(self.items)`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1960](../../../../fixtures/untyped.py#L1960) | return: `iter(self.items)` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Call**. Observation: `unprovable Call: iter(self.items)`. Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers).

---

#### Missing annotation: `extended_sync_context->`

**Missing** · Generator/Iterator

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `Generator[SyncContext]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3365](result.py#L3365) · Reference: [typed.py:4416](../../../../fixtures/typed.py#L4416) · Input: [untyped.py:2031](../../../../fixtures/untyped.py#L2031)

```diff
@@ extended_sync_context-> · missing · Generator/Iterator @@
-def extended_sync_context(seed):
+def extended_sync_context(seed: int) -> Generator[SyncContext]:
```

</details>

**1. Expected contract**

The reference declares `Generator[SyncContext]` at [typed.py:4416](../../../../fixtures/typed.py#L4416). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `collections.abc.Generator[fixtures.typed.SyncContext]`: Preserves iteration/yield types (fixtures.typed.SyncContext); iteration does not by itself establish sequence indexing.

Related operations in the reference:

- [reference:4430](../../../../fixtures/typed.py#L4430): `yield context`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2031](../../../../fixtures/untyped.py#L2031) | generator: `the body contains 'yield'` | A constraint to combine with other operations and bindings. |
| [input:2038](../../../../fixtures/untyped.py#L2038) | falls off the end: `some path ends without 'return', so it returns None` Observed type: `None`. | A constraint to combine with other operations and bindings. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: generator**. Observation: `generator`. Generator functions: the return type needs the yield types. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-13](../../../../docs/planning/TODO.md#w-13--type-generators-as-iterator), [M4-06](../../../../docs/planning/TODO.md#m4-06--r3-generatorasync).

---

#### Missing annotation: `extended_async_context->`

**Missing** · Generator/Iterator

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `AsyncGenerator[AsyncResource]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3383](result.py#L3383) · Reference: [typed.py:4436](../../../../fixtures/typed.py#L4436) · Input: [untyped.py:2042](../../../../fixtures/untyped.py#L2042)

```diff
@@ extended_async_context-> · missing · Generator/Iterator @@
-async def extended_async_context(seed):
+async def extended_async_context(seed: int) -> AsyncGenerator[AsyncResource]:
```

</details>

**1. Expected contract**

The reference declares `AsyncGenerator[AsyncResource]` at [typed.py:4436](../../../../fixtures/typed.py#L4436). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `collections.abc.AsyncGenerator[fixtures.typed.AsyncResource]`: The authored contract selects this type.

Related operations in the reference:

- [reference:4448](../../../../fixtures/typed.py#L4448): `yield opened`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2042](../../../../fixtures/untyped.py#L2042) | generator: `the body contains 'yield'` | A constraint to combine with other operations and bindings. |
| [input:2046](../../../../fixtures/untyped.py#L2046) | falls off the end: `some path ends without 'return', so it returns None` Observed type: `None`. | A constraint to combine with other operations and bindings. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: generator**. Observation: `generator`. Generator functions: the return type needs the yield types. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-13](../../../../docs/planning/TODO.md#w-13--type-generators-as-iterator), [M4-06](../../../../docs/planning/TODO.md#m4-06--r3-generatorasync).

---

#### Missing annotation: `function_with_async_comprehension_stress.produce->`

**Missing** · Generator/Iterator

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `AsyncIterator[int]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3924](result.py#L3924) · Reference: [typed.py:5135](../../../../fixtures/typed.py#L5135) · Input: [untyped.py:2395](../../../../fixtures/untyped.py#L2395)

```diff
@@ function_with_async_comprehension_stress.produce-> · missing · Generator/Iterator @@
-    async def produce():
+    async def produce() -> AsyncIterator[int]:
```

</details>

**1. Expected contract**

The reference declares `AsyncIterator[int]` at [typed.py:5135](../../../../fixtures/typed.py#L5135). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `collections.abc.AsyncIterator[int]`: The authored contract selects this type.

Related operations in the reference:

- [reference:5144](../../../../fixtures/typed.py#L5144): `yield value * 2`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2395](../../../../fixtures/untyped.py#L2395) | generator: `the body contains 'yield'` | A constraint to combine with other operations and bindings. |
| [input:2398](../../../../fixtures/untyped.py#L2398) | falls off the end: `some path ends without 'return', so it returns None` Observed type: `None`. | A constraint to combine with other operations and bindings. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: generator**. Observation: `generator`. Generator functions: the return type needs the yield types. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-13](../../../../docs/planning/TODO.md#w-13--type-generators-as-iterator), [M4-06](../../../../docs/planning/TODO.md#m4-06--r3-generatorasync).

<details><summary>All 5 (first 30, with links to the author's line)</summary>

- `ExtendedResult.__iter__->` ([typed.py:3823](../../../../fixtures/typed.py#L3823)): `Iterator[ValueOrOther[StrOrValue[PayloadT], DictObject]]`
- `HybridContainer.__iter__->` ([typed.py:4236](../../../../fixtures/typed.py#L4236)): `Iterator[ItemT]`
- `extended_sync_context->` ([typed.py:4416](../../../../fixtures/typed.py#L4416)): `Generator[SyncContext]`
- `extended_async_context->` ([typed.py:4436](../../../../fixtures/typed.py#L4436)): `AsyncGenerator[AsyncResource]`
- `function_with_async_comprehension_stress.produce->` ([typed.py:5135](../../../../fixtures/typed.py#L5135)): `AsyncIterator[int]`

</details>

### ClassVar/Final: 4 missing

Tasks: [AF-05](../../../../docs/planning/TODO.md#af-05--classvar-and-final-inference), [G-06](../../../../docs/planning/TODO.md#g-06--never-type-a-descriptor-attribute-as-its-value)

---

#### Missing annotation: `function_with_slots.SlottedClass.__slots__`

**Missing** · ClassVar/Final

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ClassVar[TupleStrVariadic]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1699](result.py#L1699) · Reference: [typed.py:2475](../../../../fixtures/typed.py#L2475) · Input: [untyped.py:952](../../../../fixtures/untyped.py#L952)

```diff
@@ function_with_slots.SlottedClass.__slots__ · missing · ClassVar/Final @@
-        __slots__ = ("x", "y")
+        __slots__: ClassVar[TupleStrVariadic] = ("x", "y")
```

</details>

**1. Expected contract**

The reference declares `ClassVar[TupleStrVariadic]` at [typed.py:2475](../../../../fixtures/typed.py#L2475). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `typing.ClassVar[tuple[str, ...]]`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:952](../../../../fixtures/untyped.py#L952) | assignment: `__slots__ = ('x', 'y')` Observed type: `tuple[str, str]`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `DescriptorStressOwner.score`

**Missing** · ClassVar/Final

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ClassVar[DescriptorWithOwnerCacheInt]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3054](result.py#L3054) · Reference: [typed.py:4014](../../../../fixtures/typed.py#L4014) · Input: [untyped.py:1862](../../../../fixtures/untyped.py#L1862)

```diff
@@ DescriptorStressOwner.score · missing · ClassVar/Final @@
-    score = DescriptorWithOwnerCache(default=0)
+    score: ClassVar[DescriptorWithOwnerCacheInt] = DescriptorWithOwnerCache(
```

</details>

**1. Expected contract**

The reference declares `ClassVar[DescriptorWithOwnerCacheInt]` at [typed.py:4014](../../../../fixtures/typed.py#L4014). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `typing.ClassVar[fixtures.typed.DescriptorWithOwnerCache[int]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:4040](../../../../fixtures/typed.py#L4040): `return {"score": self.score, "label": self.label}`. Source return/yield contributes a value.
- [reference:4029](../../../../fixtures/typed.py#L4029): `self.score`. The source requires this receiver member.
- [reference:4040](../../../../fixtures/typed.py#L4040): `self.score`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1862](../../../../fixtures/untyped.py#L1862) | assignment: `score = DescriptorWithOwnerCache(default=0)` Observed type: `DescriptorWithOwnerCache`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `DescriptorStressOwner.label`

**Missing** · ClassVar/Final

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ClassVar[DescriptorWithOwnerCache[str]]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3055](result.py#L3055) · Reference: [typed.py:4017](../../../../fixtures/typed.py#L4017) · Input: [untyped.py:1863](../../../../fixtures/untyped.py#L1863)

```diff
@@ DescriptorStressOwner.label · missing · ClassVar/Final @@
-    label = DescriptorWithOwnerCache(default="unset")
+    label: ClassVar[DescriptorWithOwnerCache[str]] = DescriptorWithOwnerCache(
```

</details>

**1. Expected contract**

The reference declares `ClassVar[DescriptorWithOwnerCache[str]]` at [typed.py:4017](../../../../fixtures/typed.py#L4017). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `typing.ClassVar[fixtures.typed.DescriptorWithOwnerCache[str]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:4040](../../../../fixtures/typed.py#L4040): `return {"score": self.score, "label": self.label}`. Source return/yield contributes a value.
- [reference:4030](../../../../fixtures/typed.py#L4030): `self.label`. The source requires this receiver member.
- [reference:4040](../../../../fixtures/typed.py#L4040): `self.label`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1863](../../../../fixtures/untyped.py#L1863) | assignment: `label = DescriptorWithOwnerCache(default='unset')` Observed type: `DescriptorWithOwnerCache`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

---

#### Missing annotation: `RegistryMeta.registry`

**Missing** · ClassVar/Final

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ClassVar[DictRegistryMeta]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3080](result.py#L3080) · Reference: [typed.py:4051](../../../../fixtures/typed.py#L4051) · Input: [untyped.py:1879](../../../../fixtures/untyped.py#L1879)

```diff
@@ RegistryMeta.registry · missing · ClassVar/Final @@
-    registry = None
+    registry: ClassVar[DictRegistryMeta] = {}
```

</details>

**1. Expected contract**

The reference declares `ClassVar[DictRegistryMeta]` at [typed.py:4051](../../../../fixtures/typed.py#L4051). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `typing.ClassVar[dict[str, fixtures.typed.RegistryMeta]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:4096](../../../../fixtures/typed.py#L4096): `instance.registry_key`. The source requires this receiver member.
- [reference:4076](../../../../fixtures/typed.py#L4076): `mcls.registry`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

13 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1879](../../../../fixtures/untyped.py#L1879) | assignment: `registry = None` Observed type: `None`. | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

<details><summary>All 4 (first 30, with links to the author's line)</summary>

- `function_with_slots.SlottedClass.__slots__` ([typed.py:2475](../../../../fixtures/typed.py#L2475)): `ClassVar[TupleStrVariadic]`
- `DescriptorStressOwner.score` ([typed.py:4014](../../../../fixtures/typed.py#L4014)): `ClassVar[DescriptorWithOwnerCacheInt]`
- `DescriptorStressOwner.label` ([typed.py:4017](../../../../fixtures/typed.py#L4017)): `ClassVar[DescriptorWithOwnerCache[str]]`
- `RegistryMeta.registry` ([typed.py:4051](../../../../fixtures/typed.py#L4051)): `ClassVar[DictRegistryMeta]`

</details>

### Builtin container: 1 missing

Tasks: [I-05](../../../../docs/planning/TODO.md#i-05--type-for-targets-from-common-iterables), [I-09](../../../../docs/planning/TODO.md#i-09--defaultdict-counter-deque-element-types-from-mutation), [I-17](../../../../docs/planning/TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](../../../../docs/planning/TODO.md#f-40--comprehensions-as-derived-nodes), [AL-07](../../../../docs/planning/TODO.md#al-07--bidirectional-expected-type-inference)

---

#### Missing annotation: `function_with_extended_named_results.metadata`

**Missing** · Builtin container

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `dict[str, bool]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4195](result.py#L4195) · Reference: [typed.py:5646](../../../../fixtures/typed.py#L5646) · Input: [untyped.py:2588](../../../../fixtures/untyped.py#L2588)

```diff
@@ function_with_extended_named_results.metadata · missing · Builtin container @@
-    metadata = result.metadata
+    metadata: dict[str, bool] = cast(typ="dict[str, bool]", val=metadata_obj)
```

</details>

**1. Expected contract**

The reference declares `dict[str, bool]` at [typed.py:5646](../../../../fixtures/typed.py#L5646). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `dict[str, bool]`: Preserves key/value types (str, bool). Mapping operations and the types flowing through keys and values must agree.

Related operations in the reference:

- [reference:5647](../../../../fixtures/typed.py#L5647): `return result, name, payload[-1], metadata["ok"]`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2588](../../../../fixtures/untyped.py#L2588) | assignment: `metadata = result.metadata` | Constrains stored values; later writes and aliases also matter. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers).

<details><summary>All 1 (first 30, with links to the author's line)</summary>

- `function_with_extended_named_results.metadata` ([typed.py:5646](../../../../fixtures/typed.py#L5646)): `dict[str, bool]`

</details>

### Callable: 1 missing

Tasks: [M4-17](../../../../docs/planning/TODO.md#m4-17--callable-r-params), [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding)

---

#### Missing annotation: `decorator_with_class->`

**Missing** · Callable

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `Callable[Ellipsis, SupportsInstance[T]]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:326](result.py#L326) · Reference: [typed.py:1020](../../../../fixtures/typed.py#L1020) · Input: [untyped.py:217](../../../../fixtures/untyped.py#L217)

```diff
@@ decorator_with_class-> · missing · Callable @@
-def decorator_with_class(cls):
+) -> Callable[..., SupportsInstance[T]]:
```

</details>

**1. Expected contract**

The reference declares `Callable[Ellipsis, SupportsInstance[T]]` at [typed.py:1020](../../../../fixtures/typed.py#L1020). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `collections.abc.Callable[fixtures.typed.SupportsInstance[T], ...]`: Preserves the callable's parameter/result relation (fixtures.typed.SupportsInstance[T]). A bare Callable omits that relationship.

Related operations in the reference:

- [reference:1056](../../../../fixtures/typed.py#L1056): `return Wrapper`. Source return/yield contributes a value.
- [reference:1054](../../../../fixtures/typed.py#L1054): `return getattr(self.instance, name)`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

6 linked records are retained in [conversion-report.json](conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:229](../../../../fixtures/untyped.py#L229) | return: `Wrapper` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Name**. Observation: `unprovable Name: Wrapper`. Returns a name the prover cannot type (a wrapper, a decorated function, a class). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](../../../../docs/planning/TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls).

<details><summary>All 1 (first 30, with links to the author's line)</summary>

- `decorator_with_class->` ([typed.py:1020](../../../../fixtures/typed.py#L1020)): `Callable[Ellipsis, SupportsInstance[T]]`

</details>

## Why nodes stay unannotated

From [`opacity_report.py`](../../opacity_report.py) on the untyped input. A node is something that has a type: a parameter, a return value or a local variable. A *direct* reason blocks a node by itself; the other labels describe nodes that are typed, declared, or blocked only because of another node.

### Parameters and returns: 546 nodes

| Reason | Nodes | Share | | What it means | Tasks |
| --- | ---: | ---: | --- | --- | --- |
| settled | 92 | 16.8 % | `███░░░░░░░░░░░░░░░░░` | Typed by negotiation: these are the nodes astart can write |  |
| unsettled (no evidence) | 87 | 15.9 % | `███░░░░░░░░░░░░░░░░░` | Nothing proves a type and no evidence reaches the node | [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](../../../../docs/planning/TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source) |
| downstream of a blocked node | 76 | 13.9 % | `███░░░░░░░░░░░░░░░░░` | Opacity spreads: the node depends on a blocked one. Fix the direct reasons first | [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers) |
| declared | 63 | 11.5 % | `██░░░░░░░░░░░░░░░░░░` | Already annotated in the input, or guaranteed by the language |  |
| direct: unprovable Name | 46 | 8.4 % | `██░░░░░░░░░░░░░░░░░░` | Returns a name the prover cannot type (a wrapper, a decorated function, a class) | [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](../../../../docs/planning/TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls) |
| direct: no evidence reaches it | 34 | 6.2 % | `█░░░░░░░░░░░░░░░░░░░` | A parameter with no call site, default or use that proves a type | [W-08](../../../../docs/planning/TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-09](../../../../docs/planning/TODO.md#al-09--name-and-usage-language-model-as-calibrated-prior) |
| direct: unprovable Call | 32 | 5.9 % | `█░░░░░░░░░░░░░░░░░░░` | Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`) | [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers) |
| direct: function escapes as a value | 28 | 5.1 % | `█░░░░░░░░░░░░░░░░░░░` | The function is passed around as a value, so its callers are unknown | [W-07](../../../../docs/planning/TODO.md#w-07--burn-down-unbindable-calls-and-escaping-functions), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers) |
| direct: stub, abstract or never returns | 20 | 3.7 % | `█░░░░░░░░░░░░░░░░░░░` | Protocol stubs, abstract methods and functions that never return | [AF-03](../../../../docs/planning/TODO.md#af-03--dunder-method-annotations-from-the-language), [I-16](../../../../docs/planning/TODO.md#i-16--abstract-methods-and-subclass-joins), [M5-04](../../../../docs/planning/TODO.md#m5-04--generatorcmindexingoperatortruthinesslen-members) |
| direct: a call to it cannot be bound | 16 | 2.9 % | `█░░░░░░░░░░░░░░░░░░░` | Some call to the function cannot be matched to its parameters | [W-07](../../../../docs/planning/TODO.md#w-07--burn-down-unbindable-calls-and-escaping-functions), [M2-02](../../../../docs/planning/TODO.md#m2-02--constructorattribute-resolution), [M2-11](../../../../docs/planning/TODO.md#m2-11--kwargs-for-method-calls) |
| direct: unprovable Tuple | 11 | 2.0 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a tuple whose members are not all typed | [I-17](../../../../docs/planning/TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](../../../../docs/planning/TODO.md#f-40--comprehensions-as-derived-nodes) |
| direct: unprovable Dict | 9 | 1.6 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a dict display with unpacking or untyped members | [I-17](../../../../docs/planning/TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](../../../../docs/planning/TODO.md#f-40--comprehensions-as-derived-nodes) |
| direct: unprovable BinOp | 8 | 1.5 % | `░░░░░░░░░░░░░░░░░░░░` | Arithmetic over operands that are not typed | [I-10](../../../../docs/planning/TODO.md#i-10--numeric-tower-and-operator-result-rules), [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator) |
| direct: generator | 7 | 1.3 % | `░░░░░░░░░░░░░░░░░░░░` | Generator functions: the return type needs the yield types | [W-13](../../../../docs/planning/TODO.md#w-13--type-generators-as-iterator), [M4-06](../../../../docs/planning/TODO.md#m4-06--r3-generatorasync) |
| direct: unprovable Attribute | 5 | 0.9 % | `░░░░░░░░░░░░░░░░░░░░` | Returns an attribute the class table does not type | [I-11](../../../../docs/planning/TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-12](../../../../docs/planning/TODO.md#w-12--annotate-instance-attributes-from-negotiation), [M2-06](../../../../docs/planning/TODO.md#m2-06--r9-attribute-types) |
| direct: unprovable List | 4 | 0.7 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a List expression the prover cannot type | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |
| direct: unprovable Subscript | 2 | 0.4 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a Subscript expression the prover cannot type | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |
| direct: unprovable DictComp | 2 | 0.4 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a DictComp expression the prover cannot type | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |
| direct: protocol result does not fit | 2 | 0.4 % | `░░░░░░░░░░░░░░░░░░░░` | Not described yet: add it to the table in scripts/compare/conversion_report.py | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |
| direct: default or value not provable | 1 | 0.2 % | `░░░░░░░░░░░░░░░░░░░░` | Not described yet: add it to the table in scripts/compare/conversion_report.py | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |
| direct: unprovable ListComp | 1 | 0.2 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a ListComp expression the prover cannot type | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |

<details><summary>Examples: direct: unprovable Name (46 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `decorator->` | [untyped.py:192](../../../../fixtures/untyped.py#L192) | `def decorator(func):` | `unprovable Name: wrapper` |
| `decorator_with_args->` | [untyped.py:203](../../../../fixtures/untyped.py#L203) | `def decorator_with_args(multiplier=2):` | `unprovable Name: actual_decorator` |
| `decorator_with_args.actual_decorator->` | [untyped.py:206](../../../../fixtures/untyped.py#L206) | `def actual_decorator(func):` | `unprovable Name: wrapper` |
| `decorator_with_class->` | [untyped.py:217](../../../../fixtures/untyped.py#L217) | `def decorator_with_class(cls):` | `unprovable Name: Wrapper` |
| `function_with_kwargs->` | [untyped.py:286](../../../../fixtures/untyped.py#L286) | `def function_with_kwargs(a, b=5, *args, **kwargs):` | `unprovable Name: result` |
| `function_with_args_kwargs->` | [untyped.py:296](../../../../fixtures/untyped.py#L296) | `def function_with_args_kwargs(*args, **kwargs):` | `unprovable Name: total` |

</details>

<details><summary>Examples: direct: no evidence reaches it (34 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `MetaClass.__new__.mcs` | [untyped.py:101](../../../../fixtures/untyped.py#L101) | `def __new__(mcs, name, bases, namespace, **_kwargs):` | `no evidence reaches it` |
| `MetaClass.__new__.name` | [untyped.py:101](../../../../fixtures/untyped.py#L101) | `def __new__(mcs, name, bases, namespace, **_kwargs):` | `no evidence reaches it` |
| `MetaClass.__new__.bases` | [untyped.py:101](../../../../fixtures/untyped.py#L101) | `def __new__(mcs, name, bases, namespace, **_kwargs):` | `no evidence reaches it` |
| `MetaClass.__new__.namespace` | [untyped.py:101](../../../../fixtures/untyped.py#L101) | `def __new__(mcs, name, bases, namespace, **_kwargs):` | `no evidence reaches it` |
| `BaseClass.base_method.a` | [untyped.py:140](../../../../fixtures/untyped.py#L140) | `def base_method(self, a, b=10):` | `no evidence reaches it` |
| `DerivedClass.abstract_method.value` | [untyped.py:163](../../../../fixtures/untyped.py#L163) | `def abstract_method(self, value):` | `no evidence reaches it` |

</details>

<details><summary>Examples: direct: unprovable Call (32 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `decorator_with_class.Wrapper.__getattr__->` | [untyped.py:226](../../../../fixtures/untyped.py#L226) | `def __getattr__(self, name):` | `unprovable Call: getattr(self.instance, name)` |
| `function_with_generators->` | [untyped.py:403](../../../../fixtures/untyped.py#L403) | `def function_with_generators():` | `unprovable Call: list(generator())` |
| `function_with_operator_overloading.Vector.__add__->` | [untyped.py:513](../../../../fixtures/untyped.py#L513) | `def __add__(self, other):` | `unprovable Call: Vector(x=self.x + other.x, y=self.y + other.y)` |
| `function_with_operator_overloading.Vector.__sub__->` | [untyped.py:517](../../../../fixtures/untyped.py#L517) | `def __sub__(self, other):` | `unprovable Call: Vector(x=self.x - other.x, y=self.y - other.y)` |
| `function_with_operator_overloading.Vector.__mul__->` | [untyped.py:521](../../../../fixtures/untyped.py#L521) | `def __mul__(self, scalar):` | `unprovable Call: Vector(x=self.x * scalar, y=self.y * scalar)` |
| `function_with_metaclass_usage->` | [untyped.py:546](../../../../fixtures/untyped.py#L546) | `def function_with_metaclass_usage():` | `unprovable Call: MetaInstance()` |

</details>

<details><summary>Examples: direct: function escapes as a value (28 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `decorator.func` | [untyped.py:192](../../../../fixtures/untyped.py#L192) | `def decorator(func):` | `function escapes as a value` |
| `decorator_with_args.actual_decorator.func` | [untyped.py:206](../../../../fixtures/untyped.py#L206) | `def actual_decorator(func):` | `function escapes as a value` |
| `decorator_with_class.cls` | [untyped.py:217](../../../../fixtures/untyped.py#L217) | `def decorator_with_class(cls):` | `function escapes as a value` |
| `function_with_coroutines.async_function.x` | [untyped.py:416](../../../../fixtures/untyped.py#L416) | `async def async_function(x):` | `function escapes as a value` |
| `function_with_union_types.union_function.value` | [untyped.py:634](../../../../fixtures/untyped.py#L634) | `def union_function(value):` | `function escapes as a value` |
| `function_with_optional_types.optional_function.value` | [untyped.py:648](../../../../fixtures/untyped.py#L648) | `def optional_function(value=None):` | `function escapes as a value` |

</details>

<details><summary>Examples: direct: stub, abstract or never returns (20 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `SupportsUpdate.update->` | [untyped.py:57](../../../../fixtures/untyped.py#L57) | `def update(self, message) -> None:` | `stub, abstract or never returns` |
| `SupportsExecuteInt.execute->` | [untyped.py:64](../../../../fixtures/untyped.py#L64) | `def execute(self, a, b) -> None:` | `stub, abstract or never returns` |
| `SupportsAction.action->` | [untyped.py:71](../../../../fixtures/untyped.py#L71) | `def action(self) -> None:` | `stub, abstract or never returns` |
| `SupportsNewMethod.new_method->` | [untyped.py:84](../../../../fixtures/untyped.py#L84) | `def new_method(self) -> None:` | `stub, abstract or never returns` |
| `SupportsVector.__add__->` | [untyped.py:94](../../../../fixtures/untyped.py#L94) | `def __add__(self, other):` | `stub, abstract or never returns` |
| `AbstractBase.abstract_method->` | [untyped.py:118](../../../../fixtures/untyped.py#L118) | `def abstract_method(self, value):` | `stub, abstract or never returns` |

</details>

<details><summary>Examples: direct: a call to it cannot be bound (16 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `decorator_with_args.multiplier` | [untyped.py:203](../../../../fixtures/untyped.py#L203) | `def decorator_with_args(multiplier=2):` | `a call to it cannot be bound` |
| `nested_function.inner.deeper.c` | [untyped.py:310](../../../../fixtures/untyped.py#L310) | `def deeper(c, d):` | `a call to it cannot be bound` |
| `nested_function.inner.deeper.d` | [untyped.py:310](../../../../fixtures/untyped.py#L310) | `def deeper(c, d):` | `a call to it cannot be bound` |
| `release_resource.resource` | [untyped.py:398](../../../../fixtures/untyped.py#L398) | `def release_resource(resource) -> None:` | `a call to it cannot be bound` |
| `function_with_generic_types.generic_function.container` | [untyped.py:619](../../../../fixtures/untyped.py#L619) | `def generic_function(container):` | `a call to it cannot be bound` |
| `function_with_none_handling.maybe_none.value` | [untyped.py:766](../../../../fixtures/untyped.py#L766) | `def maybe_none(value):` | `a call to it cannot be bound` |

</details>

<details><summary>Examples: direct: unprovable Tuple (11 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_tuple_unpacking->` | [untyped.py:667](../../../../fixtures/untyped.py#L667) | `def function_with_tuple_unpacking():` | `unprovable Tuple: (a, b, c, d, e)` |
| `function_with_type_annotations_missing->` | [untyped.py:838](../../../../fixtures/untyped.py#L838) | `def function_with_type_annotations_missing():` | `unprovable Tuple: (func1, func2, func3, func4, func5, func6)` |
| `function_with_observer->` | [untyped.py:1050](../../../../fixtures/untyped.py#L1050) | `def function_with_observer():` | `unprovable Tuple: (Subject, Observer)` |
| `function_with_strategy->` | [untyped.py:1079](../../../../fixtures/untyped.py#L1079) | `def function_with_strategy():` | `unprovable Tuple: (AddStrategy, MultiplyStrategy)` |
| `function_with_command->` | [untyped.py:1107](../../../../fixtures/untyped.py#L1107) | `def function_with_command():` | `unprovable Tuple: (ConcreteCommand, Receiver)` |
| `function_with_pattern_matching_stress->` | [untyped.py:2114](../../../../fixtures/untyped.py#L2114) | `def function_with_pattern_matching_stress(value):` | `unprovable Tuple: (x, y)` |

</details>

<details><summary>Examples: direct: unprovable Dict (9 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_double_star_expressions->` | [untyped.py:793](../../../../fixtures/untyped.py#L793) | `def function_with_double_star_expressions():` | `unprovable Dict: {**d1, **d2, 'c': 3}` |
| `test_function_calls->` | [untyped.py:1481](../../../../fixtures/untyped.py#L1481) | `def test_function_calls():` | `unprovable Dict: {**test_function_calls_part1(), **test_function_calls_part2(` |
| `test_class_instantiations->` | [untyped.py:1490](../../../../fixtures/untyped.py#L1490) | `def test_class_instantiations():` | `unprovable Dict: {'obj1': BaseClass(x=10), 'obj2': BaseClass(x=10, y=20), 'ob` |
| `DescriptorStressOwner.summary->` | [untyped.py:1871](../../../../fixtures/untyped.py#L1871) | `def summary(self):` | `unprovable Dict: {'score': self.score, 'label': self.label}` |
| `FluentBuilder.build->` | [untyped.py:1943](../../../../fixtures/untyped.py#L1943) | `def build(self, *, compact=False):` | `unprovable Dict: {'parts': list(self.parts), 'options': dict(self.options)}` |
| `AsyncResource.fetch->` | [untyped.py:2024](../../../../fixtures/untyped.py#L2024) | `async def fetch(self, value):` | `unprovable Dict: {'resource': self.name, 'value': value}` |

</details>

<details><summary>Examples: direct: unprovable BinOp (8 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `decorator_with_args.actual_decorator.wrapper->` | [untyped.py:208](../../../../fixtures/untyped.py#L208) | `def wrapper(*args, **kwargs):` | `unprovable BinOp: result * multiplier` |
| `nested_function->` | [untyped.py:304](../../../../fixtures/untyped.py#L304) | `def nested_function(x, y, z):` | `unprovable BinOp: inner(a=x, b=y) + z` |
| `nested_function.inner->` | [untyped.py:307](../../../../fixtures/untyped.py#L307) | `def inner(a, b):` | `unprovable BinOp: deeper(c=a, d=b) + a` |
| `closure_function.inner->` | [untyped.py:322](../../../../fixtures/untyped.py#L322) | `def inner(y):` | `unprovable BinOp: x + y` |
| `function_with_multiple_inheritance.Combined.combined_method->` | [untyped.py:575](../../../../fixtures/untyped.py#L575) | `def combined_method(self):` | `unprovable BinOp: self.method_a() + self.method_b()` |
| `function_with_type_annotations_missing.func6->` | [untyped.py:861](../../../../fixtures/untyped.py#L861) | `def func6(*args, **kwargs):` | `unprovable BinOp: sum(args) + sum(kwargs.values())` |

</details>

<details><summary>Examples: direct: generator (7 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `custom_context->` | [untyped.py:384](../../../../fixtures/untyped.py#L384) | `def custom_context():` | `generator` |
| `function_with_generators.generator->` | [untyped.py:406](../../../../fixtures/untyped.py#L406) | `def generator():` | `generator` |
| `ExtendedResult.__iter__->` | [untyped.py:1788](../../../../fixtures/untyped.py#L1788) | `def __iter__(self):` | `generator` |
| `extended_sync_context->` | [untyped.py:2031](../../../../fixtures/untyped.py#L2031) | `def extended_sync_context(seed):` | `generator` |
| `extended_async_context->` | [untyped.py:2042](../../../../fixtures/untyped.py#L2042) | `async def extended_async_context(seed):` | `generator` |
| `function_with_generator_send_throw_close.controlled_generator->` | [untyped.py:2317](../../../../fixtures/untyped.py#L2317) | `def controlled_generator():` | `generator` |

</details>

<details><summary>Examples: direct: unprovable Attribute (5 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `DecoratedClass.method->` | [untyped.py:252](../../../../fixtures/untyped.py#L252) | `def method(self):` | `unprovable Attribute: self.value` |
| `function_with_class_methods.InnerClass.class_method->` | [untyped.py:431](../../../../fixtures/untyped.py#L431) | `def class_method(cls):` | `unprovable Attribute: cls.__name__` |
| `function_with_descriptor.Descriptor.__get__->` | [untyped.py:484](../../../../fixtures/untyped.py#L484) | `def __get__(self, obj, objtype):` | `unprovable Attribute: self._value` |
| `function_with_singleton.Singleton.__new__->` | [untyped.py:991](../../../../fixtures/untyped.py#L991) | `def __new__(cls):` | `unprovable Attribute: cls._instance` |
| `ExtendedResult.__getitem__->` | [untyped.py:1798](../../../../fixtures/untyped.py#L1798) | `def __getitem__(self, index):` | `unprovable Attribute: self.name` |

</details>

<details><summary>Examples: direct: unprovable List (4 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_star_expressions->` | [untyped.py:787](../../../../fixtures/untyped.py#L787) | `def function_with_star_expressions():` | `unprovable List: [*data, 4, 5]` |
| `function_with_numeric_tower.values` | [untyped.py:2164](../../../../fixtures/untyped.py#L2164) | `def function_with_numeric_tower(values):` | `unprovable List: [1, 2.5, 3]` |
| `function_with_type_reassignment_maze->` | [untyped.py:2177](../../../../fixtures/untyped.py#L2177) | `def function_with_type_reassignment_maze(flag, payload):` | `unprovable List: [*value, 'extra']` |
| `function_with_exception_group_stress.values` | [untyped.py:2240](../../../../fixtures/untyped.py#L2240) | `def function_with_exception_group_stress(values):` | `unprovable List: [-1, None, 2]` |

</details>

<details><summary>Examples: direct: unprovable Subscript (2 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_slices->` | [untyped.py:329](../../../../fixtures/untyped.py#L329) | `def function_with_slices(data, start, end, step=None):` | `unprovable Subscript: data[start:end]` |
| `HybridContainer.__getitem__->` | [untyped.py:1966](../../../../fixtures/untyped.py#L1966) | `def __getitem__(self, key):` | `unprovable Subscript: self.items[key]` |

</details>

<details><summary>Examples: direct: unprovable DictComp (2 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_groupby->` | [untyped.py:1207](../../../../fixtures/untyped.py#L1207) | `def function_with_groupby():` | `unprovable DictComp: {k: [v for _, v in g] for k, g in groupby(iterable=sorted(da` |
| `function_with_composed_inner_functions.score->` | [untyped.py:2536](../../../../fixtures/untyped.py#L2536) | `def score(tokens):` | `unprovable DictComp: {token: index + seed for index, token in enumerate(iterable=` |

</details>

<details><summary>Examples: direct: protocol result does not fit (2 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `HybridContainer.__contains__->` | [untyped.py:1962](../../../../fixtures/untyped.py#L1962) | `def __contains__(self, item) -> bool:` | `protocol result does not fit` |
| `AsyncResource.__aexit__->` | [untyped.py:2019](../../../../fixtures/untyped.py#L2019) | `async def __aexit__(self, exc_type, exc, tb):` | `protocol result does not fit` |

</details>

<details><summary>Examples: direct: default or value not provable (1 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `BuiltinMethodDict.update.other` | [untyped.py:1560](../../../../fixtures/untyped.py#L1560) | `def update(self, other=(), *values, **kwargs) -> None:` | `default or value not provable` |

</details>

<details><summary>Examples: direct: unprovable ListComp (1 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_composed_inner_functions.tokenize->` | [untyped.py:2529](../../../../fixtures/untyped.py#L2529) | `def tokenize(value):` | `unprovable ListComp: [part for part in re.split(pattern='\\W+', string=normalize(` |

</details>

### Local variables: 292 nodes

| Reason | Nodes | Share | | What it means | Tasks |
| --- | ---: | ---: | --- | --- | --- |
| downstream of a blocked node | 99 | 33.9 % | `███████░░░░░░░░░░░░░` | Opacity spreads: the node depends on a blocked one. Fix the direct reasons first | [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](../../../../docs/planning/TODO.md#al-04--alias-and-escape-analysis-for-containers) |
| settled | 84 | 28.8 % | `██████░░░░░░░░░░░░░░` | Typed by negotiation: these are the nodes astart can write |  |
| direct: unprovable Call | 56 | 19.2 % | `████░░░░░░░░░░░░░░░░` | Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`) | [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](../../../../docs/planning/TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](../../../../docs/planning/TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](../../../../docs/planning/TODO.md#f-41--calls-on-builtin-typed-receivers) |
| direct: container literal mutated or not provable | 32 | 11.0 % | `██░░░░░░░░░░░░░░░░░░` | Not described yet: add it to the table in scripts/compare/conversion_report.py | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |
| direct: unprovable Name | 6 | 2.1 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a name the prover cannot type (a wrapper, a decorated function, a class) | [M5-19](../../../../docs/planning/TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](../../../../docs/planning/TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](../../../../docs/planning/TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls) |
| unsettled (no evidence) | 4 | 1.4 % | `░░░░░░░░░░░░░░░░░░░░` | Nothing proves a type and no evidence reaches the node | [P-05](../../../../docs/planning/TODO.md#p-05--no-candidate-72), [AL-05](../../../../docs/planning/TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](../../../../docs/planning/TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source) |
| direct: unprovable Attribute | 3 | 1.0 % | `░░░░░░░░░░░░░░░░░░░░` | Returns an attribute the class table does not type | [I-11](../../../../docs/planning/TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-12](../../../../docs/planning/TODO.md#w-12--annotate-instance-attributes-from-negotiation), [M2-06](../../../../docs/planning/TODO.md#m2-06--r9-attribute-types) |
| direct: unprovable Tuple | 2 | 0.7 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a tuple whose members are not all typed | [I-17](../../../../docs/planning/TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](../../../../docs/planning/TODO.md#f-40--comprehensions-as-derived-nodes) |
| direct: unprovable BinOp | 2 | 0.7 % | `░░░░░░░░░░░░░░░░░░░░` | Arithmetic over operands that are not typed | [I-10](../../../../docs/planning/TODO.md#i-10--numeric-tower-and-operator-result-rules), [W-06](../../../../docs/planning/TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator) |
| direct: container used in an unknown way | 1 | 0.3 % | `░░░░░░░░░░░░░░░░░░░░` | Not described yet: add it to the table in scripts/compare/conversion_report.py | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |
| direct: unprovable Yield | 1 | 0.3 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a Yield expression the prover cannot type | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |
| direct: unprovable List | 1 | 0.3 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a List expression the prover cannot type | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |
| direct: unprovable Await | 1 | 0.3 % | `░░░░░░░░░░░░░░░░░░░░` | Returns a Await expression the prover cannot type | [G-03](../../../../docs/planning/TODO.md#g-03--give-every-missed-annotation-an-owner) |

<details><summary>Examples: direct: unprovable Call (56 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `MetaClass.__call__.instance` | [untyped.py:108](../../../../fixtures/untyped.py#L108) | `instance = super().__call__(*args, **kwargs)` | `unprovable Call: super().__call__(*args, **kwargs)` |
| `decorator.wrapper.result` | [untyped.py:197](../../../../fixtures/untyped.py#L197) | `result = func(*args, **kwargs)` | `unprovable Call: func(*args, **kwargs)` |
| `decorator_with_args.actual_decorator.wrapper.result` | [untyped.py:209](../../../../fixtures/untyped.py#L209) | `result = func(*args, **kwargs)` | `unprovable Call: func(*args, **kwargs)` |
| `function_with_lambdas.sorted_items` | [untyped.py:346](../../../../fixtures/untyped.py#L346) | `sorted_items = sorted(items, key=lambda x: x.lower())` | `unprovable Call: sorted(items, key=lambda x: x.lower())` |
| `function_with_context._` | [untyped.py:377](../../../../fixtures/untyped.py#L377) | `_ = f.write("test")` | `unprovable Call: f.write('test')` |
| `function_with_generic_types.result1` | [untyped.py:625](../../../../fixtures/untyped.py#L625) | `result1 = generic_function(container=[1, 2, 3])` | `unprovable Call: generic_function(container=[1, 2, 3])` |

</details>

<details><summary>Examples: direct: container literal mutated or not provable (32 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_dict_operations.merged` | [untyped.py:679](../../../../fixtures/untyped.py#L679) | `merged = {**d1, **d2}` | `container literal mutated or not provable` |
| `function_with_set_operations.s1` | [untyped.py:686](../../../../fixtures/untyped.py#L686) | `s1 = {1, 2, 3, 4}` | `container literal mutated or not provable` |
| `function_with_set_operations.s2` | [untyped.py:687](../../../../fixtures/untyped.py#L687) | `s2 = {3, 4, 5, 6}` | `container literal mutated or not provable` |
| `function_with_reduce.numbers` | [untyped.py:1203](../../../../fixtures/untyped.py#L1203) | `numbers = [1, 2, 3, 4, 5]` | `container literal mutated or not provable` |
| `function_with_permutations_combinations.items` | [untyped.py:1218](../../../../fixtures/untyped.py#L1218) | `items = [1, 2, 3]` | `container literal mutated or not provable` |
| `function_with_chain.list1` | [untyped.py:1268](../../../../fixtures/untyped.py#L1268) | `list1 = [1, 2, 3]` | `container literal mutated or not provable` |

</details>

<details><summary>Examples: direct: unprovable Name (6 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `test_other_operations.context_result` | [untyped.py:1508](../../../../fixtures/untyped.py#L1508) | `context_result = resource` | `unprovable Name: resource` |
| `function_with_variable_type_redefinition.first_type_value` | [untyped.py:1702](../../../../fixtures/untyped.py#L1702) | `first_type_value = evolving_value` | `unprovable Name: evolving_value` |
| `function_with_variable_type_redefinition.second_type_value` | [untyped.py:1704](../../../../fixtures/untyped.py#L1704) | `second_type_value = evolving_value` | `unprovable Name: evolving_value` |
| `function_with_variable_type_redefinition.third_type_value` | [untyped.py:1706](../../../../fixtures/untyped.py#L1706) | `third_type_value = evolving_value` | `unprovable Name: evolving_value` |
| `function_with_variable_type_redefinition.union_final_value` | [untyped.py:1708](../../../../fixtures/untyped.py#L1708) | `union_final_value = evolving_value` | `unprovable Name: evolving_value` |
| `function_with_numeric_tower.adjusted` | [untyped.py:2169](../../../../fixtures/untyped.py#L2169) | `adjusted = index if isinstance(value, str) else int(value) + index` | `unprovable Name: index` |

</details>

<details><summary>Examples: direct: unprovable Attribute (3 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_context.temp_path` | [untyped.py:378](../../../../fixtures/untyped.py#L378) | `temp_path = f.name` | `unprovable Attribute: f.name` |
| `test_other_operations.enum_val` | [untyped.py:1504](../../../../fixtures/untyped.py#L1504) | `enum_val = EnumClass.VALUE_A` | `unprovable Attribute: EnumClass.VALUE_A` |
| `function_with_metaclass_registry_stress.registry` | [untyped.py:2355](../../../../fixtures/untyped.py#L2355) | `registry = RegistryMeta.registry` | `unprovable Attribute: RegistryMeta.registry` |

</details>

<details><summary>Examples: direct: unprovable Tuple (2 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_observer.Observer.update._` | [untyped.py:1058](../../../../fixtures/untyped.py#L1058) | `_ = (self, message)` | `unprovable Tuple: (self, message)` |
| `function_with_strategy.Strategy.execute._` | [untyped.py:1087](../../../../fixtures/untyped.py#L1087) | `_ = (self, a, b)` | `unprovable Tuple: (self, a, b)` |

</details>

<details><summary>Examples: direct: unprovable BinOp (2 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_numeric_tower.mean` | [untyped.py:2172](../../../../fixtures/untyped.py#L2172) | `mean = total / len(values) if values else math.nan` | `unprovable BinOp: total / len(values)` |
| `function_with_json_uuid_and_path_stress.path` | [untyped.py:2282](../../../../fixtures/untyped.py#L2282) | `path = Path(tempfile.gettempdir()) / f"{identifier}.json"` | `unprovable BinOp: Path(tempfile.gettempdir()) / f'{identifier}.json'` |

</details>

<details><summary>Examples: direct: container used in an unknown way (1 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_exception_group_stress.errors` | [untyped.py:2247](../../../../fixtures/untyped.py#L2247) | `errors = []` | `container used in an unknown way` |

</details>

<details><summary>Examples: direct: unprovable Yield (1 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_generator_send_throw_close.controlled_generator.received` | [untyped.py:2320](../../../../fixtures/untyped.py#L2320) | `received = yield current` | `unprovable Yield: (yield current)` |

</details>

<details><summary>Examples: direct: unprovable List (1 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_metaclass_registry_stress.registry_names` | [untyped.py:2356](../../../../fixtures/untyped.py#L2356) | `registry_names = sorted(registry) if registry else []` | `unprovable List: []` |

</details>

<details><summary>Examples: direct: unprovable Await (1 nodes)</summary>

| Node | Line | Code | Evidence |
| --- | ---: | --- | --- |
| `function_with_async_comprehension_stress.fetched` | [untyped.py:2401](../../../../fixtures/untyped.py#L2401) | `fetched = await resource.fetch(sum(values))` | `unprovable Await: await resource.fetch(sum(values))` |

</details>

## Reproduce

`python scripts/compare --min-confidence 0.5`
