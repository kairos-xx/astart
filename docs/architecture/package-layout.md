# Package ownership decision

The former flat implementation modules mixed documentation, source machinery
and transformations. Documentation rules were also separated from their
model, renderer and synthesis helpers.

The implementation is grouped by ownership:

| Package | Responsibility |
| --- | --- |
| `astart.docstrings` | Model, parsing, rendering, generation, wrapping and documentation rules/data. |
| `astart.source` | Extended AST, comments, tokens, indexing, transactions and lexical emission. |
| `astart.transforms` | Native insertion, constant extraction and alias optimization. |
| `astart.rules` | Generic rule execution and remaining rule domains. |
| `astart.semantic`, `project`, `stubs`, `cli`, `graph` | Existing cohesive subsystem boundaries. |

The supported `from astart import ...` API remains unchanged. The
`astart.docstrings` module becomes a package exporting the same model/parser
objects. Internal flat implementation paths move to their owning packages;
they have no duplicate compatibility implementations. Internal consumers,
tests, source links and diagnostic allowlists migrate together.

Keeping the flat files as forwarding modules was rejected because it would
leave two apparent ownership locations. Broad changes to inference behavior
were also rejected: this migration changes ownership and resource lookup,
not typing decisions, parsing policy or runtime behavior. Documentation's
catalog remains loaded in its previous merge position and is explicitly
included in wheel package data.

The source module retains documentation attachment/index lifecycle because
it owns the authoritative tree. Documentation model and content-editing
logic live in the documentation package. Its facade imports only the model,
avoiding a source-parser → rule-engine → source-parser dependency cycle.
The source-preservation error is independent of both formatting and document
layout, preventing a new cycle between those packages.

There are no new dependencies, code execution paths, persistence schema
changes or concurrency changes. Rollback requires restoring the moved modules,
import mapping and package-data/catalog registration together; reverting only
one side would leave broken imports or missing documentation rules. Regression
and extracted-wheel checks cover the supported facade and catalog resources.
