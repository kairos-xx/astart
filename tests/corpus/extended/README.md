# External annotation-recovery corpus

Real, already fully annotated library and application code, to complement the
stdlib corpus in `tests/corpus/base` (which is mostly untyped). The recovery
benchmark strips every annotation, runs the fixer, and scores what comes back
against the original, so the original annotations are the ground truth.

* **Source of truth:** `scripts/benchmark/artifacts/resources/external_corpus.json` pins each
  distribution by version and wheel SHA-256. `MANIFEST.json` records, per file,
  where it came from (`distribution`, `version`, `origin` path inside the
  wheel), its SHA-256, size, function count and annotation density.
* **Files are unmodified** copies of the wheel's modules with a `.py`
  suffix. They are test data; project lint and Exactus checks exclude
  `tests/corpus/`.
* **Selection:** pure-Python modules of 60–1500 lines with at least 6
  functions and at least 90 % of parameters and returns annotated; at most 8
  per distribution (the ones with most functions); tests, vendored code and
  `__init__.py` are skipped.
* **Licenses:** each distribution's license text is in `LICENSES/`. All
  distributions are permissively licensed (MIT, BSD, Apache-2.0, PSF); the
  copies are kept for benchmarking only and are not part of the astart
  package.

Rebuild (needs network):

```console
python -m scripts.benchmark.build_corpus build   # verifies every wheel hash
python -m scripts.benchmark recovery --corpus tests/corpus/extended --json report.json
```

Refresh the pins deliberately with `python -m scripts.benchmark.build_corpus pin`
and review the diff of `MANIFEST.json`.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`MANIFEST.json`](MANIFEST.json) — Provide MANIFEST json content.
- [`anyio__anyio___backends___trio.py`](anyio__anyio___backends___trio.py) — Provide anyio  anyio   backends   trio.py content.
- [`anyio__anyio___core___fileio.py`](anyio__anyio___core___fileio.py) — Provide anyio  anyio   core   fileio.py content.
- [`anyio__anyio___core___sockets.py`](anyio__anyio___core___sockets.py) — Provide anyio  anyio   core   sockets.py content.
- [`anyio__anyio___core___synchronization.py`](anyio__anyio___core___synchronization.py) — Provide anyio  anyio   core   synchronization.py content.
- [`anyio__anyio___core___tempfile.py`](anyio__anyio___core___tempfile.py) — Provide anyio  anyio   core   tempfile.py content.
- [`anyio__anyio__abc___eventloop.py`](anyio__anyio__abc___eventloop.py) — Provide anyio  anyio  abc   eventloop.py content.
- [`anyio__anyio__from_thread.py`](anyio__anyio__from_thread.py) — Provide anyio  anyio  from thread.py content.
- [`anyio__anyio__itertools.py`](anyio__anyio__itertools.py) — Provide anyio  anyio  itertools.py content.
- [`arrow__arrow__api.py`](arrow__arrow__api.py) — Provide arrow  arrow  api.py content.
- [`arrow__arrow__factory.py`](arrow__arrow__factory.py) — Provide arrow  arrow  factory.py content.
- [`arrow__arrow__parser.py`](arrow__arrow__parser.py) — Provide arrow  arrow  parser.py content.
- [`arrow__arrow__util.py`](arrow__arrow__util.py) — Provide arrow  arrow  util.py content.
- [`cattrs__cattrs__disambiguators.py`](cattrs__cattrs__disambiguators.py) — Provide cattrs  cattrs  disambiguators.py content.
- [`cattrs__cattrs__errors.py`](cattrs__cattrs__errors.py) — Provide cattrs  cattrs  errors.py content.
- [`cattrs__cattrs__gen__typeddicts.py`](cattrs__cattrs__gen__typeddicts.py) — Provide cattrs  cattrs  gen  typeddicts.py content.
- [`cattrs__cattrs__preconf__msgspec.py`](cattrs__cattrs__preconf__msgspec.py) — Provide cattrs  cattrs  preconf  msgspec.py content.
- [`click__click___compat.py`](click__click___compat.py) — Provide click  click   compat.py content.
- [`click__click___termui_impl.py`](click__click___termui_impl.py) — Provide click  click   termui impl.py content.
- [`click__click__decorators.py`](click__click__decorators.py) — Provide click  click  decorators.py content.
- [`click__click__shell_completion.py`](click__click__shell_completion.py) — Provide click  click  shell completion.py content.
- [`click__click__termui.py`](click__click__termui.py) — Provide click  click  termui.py content.
- [`click__click__testing.py`](click__click__testing.py) — Provide click  click  testing.py content.
- [`click__click__types.py`](click__click__types.py) — Provide click  click  types.py content.
- [`click__click__utils.py`](click__click__utils.py) — Provide click  click  utils.py content.
- [`fastapi__fastapi___compat__shared.py`](fastapi__fastapi___compat__shared.py) — Provide fastapi  fastapi   compat  shared.py content.
- [`fastapi__fastapi___compat__v2.py`](fastapi__fastapi___compat__v2.py) — Provide fastapi  fastapi   compat  v2.py content.
- [`fastapi__fastapi__datastructures.py`](fastapi__fastapi__datastructures.py) — Provide fastapi  fastapi  datastructures.py content.
- [`fastapi__fastapi__dependencies__models.py`](fastapi__fastapi__dependencies__models.py) — Provide fastapi  fastapi  dependencies  models.py content.
- [`fastapi__fastapi__dependencies__utils.py`](fastapi__fastapi__dependencies__utils.py) — Provide fastapi  fastapi  dependencies  utils.py content.
- [`fastapi__fastapi__openapi__utils.py`](fastapi__fastapi__openapi__utils.py) — Provide fastapi  fastapi  openapi  utils.py content.
- [`fastapi__fastapi__params.py`](fastapi__fastapi__params.py) — Provide fastapi  fastapi  params.py content.
- [`fastapi__fastapi__telemetry___asgi.py`](fastapi__fastapi__telemetry___asgi.py) — Provide fastapi  fastapi  telemetry   asgi.py content.
- [`filelock__filelock___async.py`](filelock__filelock___async.py) — Provide filelock  filelock   async.py content.
- [`filelock__filelock___async_read_write.py`](filelock__filelock___async_read_write.py) — Provide filelock  filelock   async read write.py content.
- [`filelock__filelock___soft.py`](filelock__filelock___soft.py) — Provide filelock  filelock   soft.py content.
- [`filelock__filelock___soft_rw___protocol.py`](filelock__filelock___soft_rw___protocol.py) — Provide filelock  filelock   soft rw   protocol.py content.
- [`filelock__filelock___soft_rw___sync.py`](filelock__filelock___soft_rw___sync.py) — Provide filelock  filelock   soft rw   sync.py content.
- [`filelock__filelock___strict.py`](filelock__filelock___strict.py) — Provide filelock  filelock   strict.py content.
- [`filelock__filelock___windows.py`](filelock__filelock___windows.py) — Provide filelock  filelock   windows.py content.
- [`filelock__filelock__asyncio.py`](filelock__filelock__asyncio.py) — Provide filelock  filelock  asyncio.py content.
- [`flask__flask__cli.py`](flask__flask__cli.py) — Provide flask  flask  cli.py content.
- [`flask__flask__ctx.py`](flask__flask__ctx.py) — Provide flask  flask  ctx.py content.
- [`flask__flask__helpers.py`](flask__flask__helpers.py) — Provide flask  flask  helpers.py content.
- [`flask__flask__json__tag.py`](flask__flask__json__tag.py) — Provide flask  flask  json  tag.py content.
- [`flask__flask__sansio__app.py`](flask__flask__sansio__app.py) — Provide flask  flask  sansio  app.py content.
- [`flask__flask__sansio__blueprints.py`](flask__flask__sansio__blueprints.py) — Provide flask  flask  sansio  blueprints.py content.
- [`flask__flask__sansio__scaffold.py`](flask__flask__sansio__scaffold.py) — Provide flask  flask  sansio  scaffold.py content.
- [`flask__flask__sessions.py`](flask__flask__sessions.py) — Provide flask  flask  sessions.py content.
- [`h11__h11___connection.py`](h11__h11___connection.py) — Provide h11  h11   connection.py content.
- [`h11__h11___events.py`](h11__h11___events.py) — Provide h11  h11   events.py content.
- [`h11__h11___headers.py`](h11__h11___headers.py) — Provide h11  h11   headers.py content.
- [`h11__h11___readers.py`](h11__h11___readers.py) — Provide h11  h11   readers.py content.
- [`h11__h11___receivebuffer.py`](h11__h11___receivebuffer.py) — Provide h11  h11   receivebuffer.py content.
- [`h11__h11___state.py`](h11__h11___state.py) — Provide h11  h11   state.py content.
- [`h11__h11___util.py`](h11__h11___util.py) — Provide h11  h11   util.py content.
- [`h11__h11___writers.py`](h11__h11___writers.py) — Provide h11  h11   writers.py content.
- [`httpcore__httpcore___async__http11.py`](httpcore__httpcore___async__http11.py) — Provide httpcore  httpcore   async  http11.py content.
- [`httpcore__httpcore___async__http2.py`](httpcore__httpcore___async__http2.py) — Provide httpcore  httpcore   async  http2.py content.
- [`httpcore__httpcore___async__http_proxy.py`](httpcore__httpcore___async__http_proxy.py) — Provide httpcore  httpcore   async  http proxy.py content.
- [`httpcore__httpcore___backends__mock.py`](httpcore__httpcore___backends__mock.py) — Provide httpcore  httpcore   backends  mock.py content.
- [`httpcore__httpcore___models.py`](httpcore__httpcore___models.py) — Provide httpcore  httpcore   models.py content.
- [`httpcore__httpcore___sync__http11.py`](httpcore__httpcore___sync__http11.py) — Provide httpcore  httpcore   sync  http11.py content.
- [`httpcore__httpcore___sync__http2.py`](httpcore__httpcore___sync__http2.py) — Provide httpcore  httpcore   sync  http2.py content.
- [`httpcore__httpcore___synchronization.py`](httpcore__httpcore___synchronization.py) — Provide httpcore  httpcore   synchronization.py content.
- [`httpx__httpx___auth.py`](httpx__httpx___auth.py) — Provide httpx  httpx   auth.py content.
- [`httpx__httpx___content.py`](httpx__httpx___content.py) — Provide httpx  httpx   content.py content.
- [`httpx__httpx___decoders.py`](httpx__httpx___decoders.py) — Provide httpx  httpx   decoders.py content.
- [`httpx__httpx___models.py`](httpx__httpx___models.py) — Provide httpx  httpx   models.py content.
- [`httpx__httpx___multipart.py`](httpx__httpx___multipart.py) — Provide httpx  httpx   multipart.py content.
- [`httpx__httpx___transports__default.py`](httpx__httpx___transports__default.py) — Provide httpx  httpx   transports  default.py content.
- [`httpx__httpx___urls.py`](httpx__httpx___urls.py) — Provide httpx  httpx   urls.py content.
- [`httpx__httpx___utils.py`](httpx__httpx___utils.py) — Provide httpx  httpx   utils.py content.
- [`humanize__humanize__i18n.py`](humanize__humanize__i18n.py) — Provide humanize  humanize  i18n.py content.
- [`humanize__humanize__number.py`](humanize__humanize__number.py) — Provide humanize  humanize  number.py content.
- [`humanize__humanize__time.py`](humanize__humanize__time.py) — Provide humanize  humanize  time.py content.
- [`itsdangerous__itsdangerous__serializer.py`](itsdangerous__itsdangerous__serializer.py) — Provide itsdangerous  itsdangerous  serializer.py content.
- [`itsdangerous__itsdangerous__signer.py`](itsdangerous__itsdangerous__signer.py) — Provide itsdangerous  itsdangerous  signer.py content.
- [`itsdangerous__itsdangerous__timed.py`](itsdangerous__itsdangerous__timed.py) — Provide itsdangerous  itsdangerous  timed.py content.
- [`jinja2__jinja2__ext.py`](jinja2__jinja2__ext.py) — Provide jinja2  jinja2  ext.py content.
- [`jinja2__jinja2__idtracking.py`](jinja2__jinja2__idtracking.py) — Provide jinja2  jinja2  idtracking.py content.
- [`jinja2__jinja2__lexer.py`](jinja2__jinja2__lexer.py) — Provide jinja2  jinja2  lexer.py content.
- [`jinja2__jinja2__loaders.py`](jinja2__jinja2__loaders.py) — Provide jinja2  jinja2  loaders.py content.
- [`jinja2__jinja2__nodes.py`](jinja2__jinja2__nodes.py) — Provide jinja2  jinja2  nodes.py content.
- [`jinja2__jinja2__parser.py`](jinja2__jinja2__parser.py) — Provide jinja2  jinja2  parser.py content.
- [`jinja2__jinja2__runtime.py`](jinja2__jinja2__runtime.py) — Provide jinja2  jinja2  runtime.py content.
- [`jinja2__jinja2__utils.py`](jinja2__jinja2__utils.py) — Provide jinja2  jinja2  utils.py content.
- [`markdown-it-py__markdown_it__common__utils.py`](markdown-it-py__markdown_it__common__utils.py) — Provide markdown it py  markdown it  common  utils.py content.
- [`markdown-it-py__markdown_it__main.py`](markdown-it-py__markdown_it__main.py) — Provide markdown it py  markdown it  main.py content.
- [`markdown-it-py__markdown_it__renderer.py`](markdown-it-py__markdown_it__renderer.py) — Provide markdown it py  markdown it  renderer.py content.
- [`markdown-it-py__markdown_it__ruler.py`](markdown-it-py__markdown_it__ruler.py) — Provide markdown it py  markdown it  ruler.py content.
- [`markdown-it-py__markdown_it__rules_block__state_block.py`](markdown-it-py__markdown_it__rules_block__state_block.py) — Provide markdown it py  markdown it  rules block  state block.py content.
- [`markdown-it-py__markdown_it__token.py`](markdown-it-py__markdown_it__token.py) — Provide markdown it py  markdown it  token.py content.
- [`markdown-it-py__markdown_it__tree.py`](markdown-it-py__markdown_it__tree.py) — Provide markdown it py  markdown it  tree.py content.
- [`markdown-it-py__markdown_it__utils.py`](markdown-it-py__markdown_it__utils.py) — Provide markdown it py  markdown it  utils.py content.
- [`packaging__packaging___parser.py`](packaging__packaging___parser.py) — Provide packaging  packaging   parser.py content.
- [`packaging__packaging___ranges.py`](packaging__packaging___ranges.py) — Provide packaging  packaging   ranges.py content.
- [`packaging__packaging__markers.py`](packaging__packaging__markers.py) — Provide packaging  packaging  markers.py content.
- [`packaging__packaging__metadata.py`](packaging__packaging__metadata.py) — Provide packaging  packaging  metadata.py content.
- [`packaging__packaging__pylock.py`](packaging__packaging__pylock.py) — Provide packaging  packaging  pylock.py content.
- [`packaging__packaging__specifiers.py`](packaging__packaging__specifiers.py) — Provide packaging  packaging  specifiers.py content.
- [`packaging__packaging__tags.py`](packaging__packaging__tags.py) — Provide packaging  packaging  tags.py content.
- [`packaging__packaging__version.py`](packaging__packaging__version.py) — Provide packaging  packaging  version.py content.
- [`platformdirs__platformdirs___xdg.py`](platformdirs__platformdirs___xdg.py) — Provide platformdirs  platformdirs   xdg.py content.
- [`platformdirs__platformdirs__android.py`](platformdirs__platformdirs__android.py) — Provide platformdirs  platformdirs  android.py content.
- [`platformdirs__platformdirs__api.py`](platformdirs__platformdirs__api.py) — Provide platformdirs  platformdirs  api.py content.
- [`platformdirs__platformdirs__ios.py`](platformdirs__platformdirs__ios.py) — Provide platformdirs  platformdirs  ios.py content.
- [`platformdirs__platformdirs__macos.py`](platformdirs__platformdirs__macos.py) — Provide platformdirs  platformdirs  macos.py content.
- [`platformdirs__platformdirs__unix.py`](platformdirs__platformdirs__unix.py) — Provide platformdirs  platformdirs  unix.py content.
- [`platformdirs__platformdirs__windows.py`](platformdirs__platformdirs__windows.py) — Provide platformdirs  platformdirs  windows.py content.
- [`pluggy__pluggy___caller.py`](pluggy__pluggy___caller.py) — Provide pluggy  pluggy   caller.py content.
- [`pluggy__pluggy___decorators.py`](pluggy__pluggy___decorators.py) — Provide pluggy  pluggy   decorators.py content.
- [`pluggy__pluggy___manager.py`](pluggy__pluggy___manager.py) — Provide pluggy  pluggy   manager.py content.
- [`pluggy__pluggy___result.py`](pluggy__pluggy___result.py) — Provide pluggy  pluggy   result.py content.
- [`pluggy__pluggy___tracing.py`](pluggy__pluggy___tracing.py) — Provide pluggy  pluggy   tracing.py content.
- [`pytest___pytest__assertion__rewrite.py`](pytest___pytest__assertion__rewrite.py) — Provide pytest   pytest  assertion  rewrite.py content.
- [`pytest___pytest__capture.py`](pytest___pytest__capture.py) — Provide pytest   pytest  capture.py content.
- [`pytest___pytest__hookspec.py`](pytest___pytest__hookspec.py) — Provide pytest   pytest  hookspec.py content.
- [`pytest___pytest__junitxml.py`](pytest___pytest__junitxml.py) — Provide pytest   pytest  junitxml.py content.
- [`pytest___pytest__logging.py`](pytest___pytest__logging.py) — Provide pytest   pytest  logging.py content.
- [`pytest___pytest__main.py`](pytest___pytest__main.py) — Provide pytest   pytest  main.py content.
- [`pytest___pytest__pathlib.py`](pytest___pytest__pathlib.py) — Provide pytest   pytest  pathlib.py content.
- [`pytest___pytest__reports.py`](pytest___pytest__reports.py) — Provide pytest   pytest  reports.py content.
- [`rich__rich___win32_console.py`](rich__rich___win32_console.py) — Provide rich  rich   win32 console.py content.
- [`rich__rich__layout.py`](rich__rich__layout.py) — Provide rich  rich  layout.py content.
- [`rich__rich__markdown.py`](rich__rich__markdown.py) — Provide rich  rich  markdown.py content.
- [`rich__rich__pretty.py`](rich__rich__pretty.py) — Provide rich  rich  pretty.py content.
- [`rich__rich__segment.py`](rich__rich__segment.py) — Provide rich  rich  segment.py content.
- [`rich__rich__style.py`](rich__rich__style.py) — Provide rich  rich  style.py content.
- [`rich__rich__syntax.py`](rich__rich__syntax.py) — Provide rich  rich  syntax.py content.
- [`rich__rich__text.py`](rich__rich__text.py) — Provide rich  rich  text.py content.
- [`starlette__starlette__authentication.py`](starlette__starlette__authentication.py) — Provide starlette  starlette  authentication.py content.
- [`starlette__starlette__datastructures.py`](starlette__starlette__datastructures.py) — Provide starlette  starlette  datastructures.py content.
- [`starlette__starlette__formparsers.py`](starlette__starlette__formparsers.py) — Provide starlette  starlette  formparsers.py content.
- [`starlette__starlette__requests.py`](starlette__starlette__requests.py) — Provide starlette  starlette  requests.py content.
- [`starlette__starlette__responses.py`](starlette__starlette__responses.py) — Provide starlette  starlette  responses.py content.
- [`starlette__starlette__routing.py`](starlette__starlette__routing.py) — Provide starlette  starlette  routing.py content.
- [`starlette__starlette__testclient.py`](starlette__starlette__testclient.py) — Provide starlette  starlette  testclient.py content.
- [`starlette__starlette__websockets.py`](starlette__starlette__websockets.py) — Provide starlette  starlette  websockets.py content.
- [`structlog__structlog___config.py`](structlog__structlog___config.py) — Provide structlog  structlog   config.py content.
- [`structlog__structlog___native.py`](structlog__structlog___native.py) — Provide structlog  structlog   native.py content.
- [`structlog__structlog__dev.py`](structlog__structlog__dev.py) — Provide structlog  structlog  dev.py content.
- [`structlog__structlog__processors.py`](structlog__structlog__processors.py) — Provide structlog  structlog  processors.py content.
- [`structlog__structlog__stdlib.py`](structlog__structlog__stdlib.py) — Provide structlog  structlog  stdlib.py content.
- [`structlog__structlog__threadlocal.py`](structlog__structlog__threadlocal.py) — Provide structlog  structlog  threadlocal.py content.
- [`structlog__structlog__twisted.py`](structlog__structlog__twisted.py) — Provide structlog  structlog  twisted.py content.
- [`structlog__structlog__typing.py`](structlog__structlog__typing.py) — Provide structlog  structlog  typing.py content.
- [`tenacity__tenacity___utils.py`](tenacity__tenacity___utils.py) — Provide tenacity  tenacity   utils.py content.
- [`tenacity__tenacity__asyncio__retry.py`](tenacity__tenacity__asyncio__retry.py) — Provide tenacity  tenacity  asyncio  retry.py content.
- [`tenacity__tenacity__retry.py`](tenacity__tenacity__retry.py) — Provide tenacity  tenacity  retry.py content.
- [`tenacity__tenacity__stop.py`](tenacity__tenacity__stop.py) — Provide tenacity  tenacity  stop.py content.
- [`tenacity__tenacity__wait.py`](tenacity__tenacity__wait.py) — Provide tenacity  tenacity  wait.py content.
- [`tomli__tomli___parser.py`](tomli__tomli___parser.py) — Provide tomli  tomli   parser.py content.
- [`tomlkit__tomlkit__api.py`](tomlkit__tomlkit__api.py) — Provide tomlkit  tomlkit  api.py content.
- [`tomlkit__tomlkit__container.py`](tomlkit__tomlkit__container.py) — Provide tomlkit  tomlkit  container.py content.
- [`tomlkit__tomlkit__exceptions.py`](tomlkit__tomlkit__exceptions.py) — Provide tomlkit  tomlkit  exceptions.py content.
- [`tomlkit__tomlkit__parser.py`](tomlkit__tomlkit__parser.py) — Provide tomlkit  tomlkit  parser.py content.
- [`tomlkit__tomlkit__source.py`](tomlkit__tomlkit__source.py) — Provide tomlkit  tomlkit  source.py content.
- [`werkzeug__werkzeug__datastructures__headers.py`](werkzeug__werkzeug__datastructures__headers.py) — Provide werkzeug  werkzeug  datastructures  headers.py content.
- [`werkzeug__werkzeug__datastructures__mixins.py`](werkzeug__werkzeug__datastructures__mixins.py) — Provide werkzeug  werkzeug  datastructures  mixins.py content.
- [`werkzeug__werkzeug__datastructures__structures.py`](werkzeug__werkzeug__datastructures__structures.py) — Provide werkzeug  werkzeug  datastructures  structures.py content.
- [`werkzeug__werkzeug__local.py`](werkzeug__werkzeug__local.py) — Provide werkzeug  werkzeug  local.py content.
- [`werkzeug__werkzeug__sansio__response.py`](werkzeug__werkzeug__sansio__response.py) — Provide werkzeug  werkzeug  sansio  response.py content.
- [`werkzeug__werkzeug__serving.py`](werkzeug__werkzeug__serving.py) — Provide werkzeug  werkzeug  serving.py content.
- [`werkzeug__werkzeug__test.py`](werkzeug__werkzeug__test.py) — Provide werkzeug  werkzeug  test.py content.
- [`werkzeug__werkzeug__wrappers__response.py`](werkzeug__werkzeug__wrappers__response.py) — Provide werkzeug  werkzeug  wrappers  response.py content.

### Subdirectories

- [`LICENSES/`](LICENSES/README.md) — Provide anyio txt content.

<!-- exactus:inventory:end -->
