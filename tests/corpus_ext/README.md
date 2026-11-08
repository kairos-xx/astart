# External annotation-recovery corpus

Real, already fully annotated library and application code, to complement the
stdlib corpus in `tests/corpus` (which is mostly untyped). The recovery
benchmark strips every annotation, runs the fixer, and scores what comes back
against the original, so the original annotations are the ground truth.

* **Source of truth:** `benchmarks/external_corpus.json` pins each
  distribution by version and wheel SHA-256. `MANIFEST.json` records, per file,
  where it came from (`distribution`, `version`, `origin` path inside the
  wheel), its SHA-256, size, function count and annotation density.
* **Files are unmodified** copies of the wheel's modules with a `.py.txt`
  suffix, so editors and tools do not treat them as live code.
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
python -m benchmarks.build_corpus build   # verifies every wheel hash
python -m benchmarks recovery --corpus tests/corpus_ext --json report.json
```

Refresh the pins deliberately with `python -m benchmarks.build_corpus pin`
and review the diff of `MANIFEST.json`.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`MANIFEST.json`](MANIFEST.json) — Provide MANIFEST json content.
- [`anyio__anyio___backends___trio.py.txt`](anyio__anyio___backends___trio.py.txt) — Provide anyio  anyio   backends   trio.py txt content.
- [`anyio__anyio___core___fileio.py.txt`](anyio__anyio___core___fileio.py.txt) — Provide anyio  anyio   core   fileio.py txt content.
- [`anyio__anyio___core___sockets.py.txt`](anyio__anyio___core___sockets.py.txt) — Provide anyio  anyio   core   sockets.py txt content.
- [`anyio__anyio___core___synchronization.py.txt`](anyio__anyio___core___synchronization.py.txt) — Provide anyio  anyio   core   synchronization.py txt content.
- [`anyio__anyio___core___tempfile.py.txt`](anyio__anyio___core___tempfile.py.txt) — Provide anyio  anyio   core   tempfile.py txt content.
- [`anyio__anyio__abc___eventloop.py.txt`](anyio__anyio__abc___eventloop.py.txt) — Provide anyio  anyio  abc   eventloop.py txt content.
- [`anyio__anyio__from_thread.py.txt`](anyio__anyio__from_thread.py.txt) — Provide anyio  anyio  from thread.py txt content.
- [`anyio__anyio__itertools.py.txt`](anyio__anyio__itertools.py.txt) — Provide anyio  anyio  itertools.py txt content.
- [`arrow__arrow__api.py.txt`](arrow__arrow__api.py.txt) — Provide arrow  arrow  api.py txt content.
- [`arrow__arrow__factory.py.txt`](arrow__arrow__factory.py.txt) — Provide arrow  arrow  factory.py txt content.
- [`arrow__arrow__parser.py.txt`](arrow__arrow__parser.py.txt) — Provide arrow  arrow  parser.py txt content.
- [`arrow__arrow__util.py.txt`](arrow__arrow__util.py.txt) — Provide arrow  arrow  util.py txt content.
- [`cattrs__cattrs__disambiguators.py.txt`](cattrs__cattrs__disambiguators.py.txt) — Provide cattrs  cattrs  disambiguators.py txt content.
- [`cattrs__cattrs__errors.py.txt`](cattrs__cattrs__errors.py.txt) — Provide cattrs  cattrs  errors.py txt content.
- [`cattrs__cattrs__gen__typeddicts.py.txt`](cattrs__cattrs__gen__typeddicts.py.txt) — Provide cattrs  cattrs  gen  typeddicts.py txt content.
- [`cattrs__cattrs__preconf__msgspec.py.txt`](cattrs__cattrs__preconf__msgspec.py.txt) — Provide cattrs  cattrs  preconf  msgspec.py txt content.
- [`click__click___compat.py.txt`](click__click___compat.py.txt) — Provide click  click   compat.py txt content.
- [`click__click___termui_impl.py.txt`](click__click___termui_impl.py.txt) — Provide click  click   termui impl.py txt content.
- [`click__click__decorators.py.txt`](click__click__decorators.py.txt) — Provide click  click  decorators.py txt content.
- [`click__click__shell_completion.py.txt`](click__click__shell_completion.py.txt) — Provide click  click  shell completion.py txt content.
- [`click__click__termui.py.txt`](click__click__termui.py.txt) — Provide click  click  termui.py txt content.
- [`click__click__testing.py.txt`](click__click__testing.py.txt) — Provide click  click  testing.py txt content.
- [`click__click__types.py.txt`](click__click__types.py.txt) — Provide click  click  types.py txt content.
- [`click__click__utils.py.txt`](click__click__utils.py.txt) — Provide click  click  utils.py txt content.
- [`fastapi__fastapi___compat__shared.py.txt`](fastapi__fastapi___compat__shared.py.txt) — Provide fastapi  fastapi   compat  shared.py txt content.
- [`fastapi__fastapi___compat__v2.py.txt`](fastapi__fastapi___compat__v2.py.txt) — Provide fastapi  fastapi   compat  v2.py txt content.
- [`fastapi__fastapi__datastructures.py.txt`](fastapi__fastapi__datastructures.py.txt) — Provide fastapi  fastapi  datastructures.py txt content.
- [`fastapi__fastapi__dependencies__models.py.txt`](fastapi__fastapi__dependencies__models.py.txt) — Provide fastapi  fastapi  dependencies  models.py txt content.
- [`fastapi__fastapi__dependencies__utils.py.txt`](fastapi__fastapi__dependencies__utils.py.txt) — Provide fastapi  fastapi  dependencies  utils.py txt content.
- [`fastapi__fastapi__openapi__utils.py.txt`](fastapi__fastapi__openapi__utils.py.txt) — Provide fastapi  fastapi  openapi  utils.py txt content.
- [`fastapi__fastapi__params.py.txt`](fastapi__fastapi__params.py.txt) — Provide fastapi  fastapi  params.py txt content.
- [`fastapi__fastapi__telemetry___asgi.py.txt`](fastapi__fastapi__telemetry___asgi.py.txt) — Provide fastapi  fastapi  telemetry   asgi.py txt content.
- [`filelock__filelock___async.py.txt`](filelock__filelock___async.py.txt) — Provide filelock  filelock   async.py txt content.
- [`filelock__filelock___async_read_write.py.txt`](filelock__filelock___async_read_write.py.txt) — Provide filelock  filelock   async read write.py txt content.
- [`filelock__filelock___soft.py.txt`](filelock__filelock___soft.py.txt) — Provide filelock  filelock   soft.py txt content.
- [`filelock__filelock___soft_rw___protocol.py.txt`](filelock__filelock___soft_rw___protocol.py.txt) — Provide filelock  filelock   soft rw   protocol.py txt content.
- [`filelock__filelock___soft_rw___sync.py.txt`](filelock__filelock___soft_rw___sync.py.txt) — Provide filelock  filelock   soft rw   sync.py txt content.
- [`filelock__filelock___strict.py.txt`](filelock__filelock___strict.py.txt) — Provide filelock  filelock   strict.py txt content.
- [`filelock__filelock___windows.py.txt`](filelock__filelock___windows.py.txt) — Provide filelock  filelock   windows.py txt content.
- [`filelock__filelock__asyncio.py.txt`](filelock__filelock__asyncio.py.txt) — Provide filelock  filelock  asyncio.py txt content.
- [`flask__flask__cli.py.txt`](flask__flask__cli.py.txt) — Provide flask  flask  cli.py txt content.
- [`flask__flask__ctx.py.txt`](flask__flask__ctx.py.txt) — Provide flask  flask  ctx.py txt content.
- [`flask__flask__helpers.py.txt`](flask__flask__helpers.py.txt) — Provide flask  flask  helpers.py txt content.
- [`flask__flask__json__tag.py.txt`](flask__flask__json__tag.py.txt) — Provide flask  flask  json  tag.py txt content.
- [`flask__flask__sansio__app.py.txt`](flask__flask__sansio__app.py.txt) — Provide flask  flask  sansio  app.py txt content.
- [`flask__flask__sansio__blueprints.py.txt`](flask__flask__sansio__blueprints.py.txt) — Provide flask  flask  sansio  blueprints.py txt content.
- [`flask__flask__sansio__scaffold.py.txt`](flask__flask__sansio__scaffold.py.txt) — Provide flask  flask  sansio  scaffold.py txt content.
- [`flask__flask__sessions.py.txt`](flask__flask__sessions.py.txt) — Provide flask  flask  sessions.py txt content.
- [`h11__h11___connection.py.txt`](h11__h11___connection.py.txt) — Provide h11  h11   connection.py txt content.
- [`h11__h11___events.py.txt`](h11__h11___events.py.txt) — Provide h11  h11   events.py txt content.
- [`h11__h11___headers.py.txt`](h11__h11___headers.py.txt) — Provide h11  h11   headers.py txt content.
- [`h11__h11___readers.py.txt`](h11__h11___readers.py.txt) — Provide h11  h11   readers.py txt content.
- [`h11__h11___receivebuffer.py.txt`](h11__h11___receivebuffer.py.txt) — Provide h11  h11   receivebuffer.py txt content.
- [`h11__h11___state.py.txt`](h11__h11___state.py.txt) — Provide h11  h11   state.py txt content.
- [`h11__h11___util.py.txt`](h11__h11___util.py.txt) — Provide h11  h11   util.py txt content.
- [`h11__h11___writers.py.txt`](h11__h11___writers.py.txt) — Provide h11  h11   writers.py txt content.
- [`httpcore__httpcore___async__http11.py.txt`](httpcore__httpcore___async__http11.py.txt) — Provide httpcore  httpcore   async  http11.py txt content.
- [`httpcore__httpcore___async__http2.py.txt`](httpcore__httpcore___async__http2.py.txt) — Provide httpcore  httpcore   async  http2.py txt content.
- [`httpcore__httpcore___async__http_proxy.py.txt`](httpcore__httpcore___async__http_proxy.py.txt) — Provide httpcore  httpcore   async  http proxy.py txt content.
- [`httpcore__httpcore___backends__mock.py.txt`](httpcore__httpcore___backends__mock.py.txt) — Provide httpcore  httpcore   backends  mock.py txt content.
- [`httpcore__httpcore___models.py.txt`](httpcore__httpcore___models.py.txt) — Provide httpcore  httpcore   models.py txt content.
- [`httpcore__httpcore___sync__http11.py.txt`](httpcore__httpcore___sync__http11.py.txt) — Provide httpcore  httpcore   sync  http11.py txt content.
- [`httpcore__httpcore___sync__http2.py.txt`](httpcore__httpcore___sync__http2.py.txt) — Provide httpcore  httpcore   sync  http2.py txt content.
- [`httpcore__httpcore___synchronization.py.txt`](httpcore__httpcore___synchronization.py.txt) — Provide httpcore  httpcore   synchronization.py txt content.
- [`httpx__httpx___auth.py.txt`](httpx__httpx___auth.py.txt) — Provide httpx  httpx   auth.py txt content.
- [`httpx__httpx___content.py.txt`](httpx__httpx___content.py.txt) — Provide httpx  httpx   content.py txt content.
- [`httpx__httpx___decoders.py.txt`](httpx__httpx___decoders.py.txt) — Provide httpx  httpx   decoders.py txt content.
- [`httpx__httpx___models.py.txt`](httpx__httpx___models.py.txt) — Provide httpx  httpx   models.py txt content.
- [`httpx__httpx___multipart.py.txt`](httpx__httpx___multipart.py.txt) — Provide httpx  httpx   multipart.py txt content.
- [`httpx__httpx___transports__default.py.txt`](httpx__httpx___transports__default.py.txt) — Provide httpx  httpx   transports  default.py txt content.
- [`httpx__httpx___urls.py.txt`](httpx__httpx___urls.py.txt) — Provide httpx  httpx   urls.py txt content.
- [`httpx__httpx___utils.py.txt`](httpx__httpx___utils.py.txt) — Provide httpx  httpx   utils.py txt content.
- [`humanize__humanize__i18n.py.txt`](humanize__humanize__i18n.py.txt) — Provide humanize  humanize  i18n.py txt content.
- [`humanize__humanize__number.py.txt`](humanize__humanize__number.py.txt) — Provide humanize  humanize  number.py txt content.
- [`humanize__humanize__time.py.txt`](humanize__humanize__time.py.txt) — Provide humanize  humanize  time.py txt content.
- [`itsdangerous__itsdangerous__serializer.py.txt`](itsdangerous__itsdangerous__serializer.py.txt) — Provide itsdangerous  itsdangerous  serializer.py txt content.
- [`itsdangerous__itsdangerous__signer.py.txt`](itsdangerous__itsdangerous__signer.py.txt) — Provide itsdangerous  itsdangerous  signer.py txt content.
- [`itsdangerous__itsdangerous__timed.py.txt`](itsdangerous__itsdangerous__timed.py.txt) — Provide itsdangerous  itsdangerous  timed.py txt content.
- [`jinja2__jinja2__ext.py.txt`](jinja2__jinja2__ext.py.txt) — Provide jinja2  jinja2  ext.py txt content.
- [`jinja2__jinja2__idtracking.py.txt`](jinja2__jinja2__idtracking.py.txt) — Provide jinja2  jinja2  idtracking.py txt content.
- [`jinja2__jinja2__lexer.py.txt`](jinja2__jinja2__lexer.py.txt) — Provide jinja2  jinja2  lexer.py txt content.
- [`jinja2__jinja2__loaders.py.txt`](jinja2__jinja2__loaders.py.txt) — Provide jinja2  jinja2  loaders.py txt content.
- [`jinja2__jinja2__nodes.py.txt`](jinja2__jinja2__nodes.py.txt) — Provide jinja2  jinja2  nodes.py txt content.
- [`jinja2__jinja2__parser.py.txt`](jinja2__jinja2__parser.py.txt) — Provide jinja2  jinja2  parser.py txt content.
- [`jinja2__jinja2__runtime.py.txt`](jinja2__jinja2__runtime.py.txt) — Provide jinja2  jinja2  runtime.py txt content.
- [`jinja2__jinja2__utils.py.txt`](jinja2__jinja2__utils.py.txt) — Provide jinja2  jinja2  utils.py txt content.
- [`markdown-it-py__markdown_it__common__utils.py.txt`](markdown-it-py__markdown_it__common__utils.py.txt) — Provide markdown it py  markdown it  common  utils.py txt content.
- [`markdown-it-py__markdown_it__main.py.txt`](markdown-it-py__markdown_it__main.py.txt) — Provide markdown it py  markdown it  main.py txt content.
- [`markdown-it-py__markdown_it__renderer.py.txt`](markdown-it-py__markdown_it__renderer.py.txt) — Provide markdown it py  markdown it  renderer.py txt content.
- [`markdown-it-py__markdown_it__ruler.py.txt`](markdown-it-py__markdown_it__ruler.py.txt) — Provide markdown it py  markdown it  ruler.py txt content.
- [`markdown-it-py__markdown_it__rules_block__state_block.py.txt`](markdown-it-py__markdown_it__rules_block__state_block.py.txt) — Provide markdown it py  markdown it  rules block  state block.py txt content.
- [`markdown-it-py__markdown_it__token.py.txt`](markdown-it-py__markdown_it__token.py.txt) — Provide markdown it py  markdown it  token.py txt content.
- [`markdown-it-py__markdown_it__tree.py.txt`](markdown-it-py__markdown_it__tree.py.txt) — Provide markdown it py  markdown it  tree.py txt content.
- [`markdown-it-py__markdown_it__utils.py.txt`](markdown-it-py__markdown_it__utils.py.txt) — Provide markdown it py  markdown it  utils.py txt content.
- [`packaging__packaging___parser.py.txt`](packaging__packaging___parser.py.txt) — Provide packaging  packaging   parser.py txt content.
- [`packaging__packaging___ranges.py.txt`](packaging__packaging___ranges.py.txt) — Provide packaging  packaging   ranges.py txt content.
- [`packaging__packaging__markers.py.txt`](packaging__packaging__markers.py.txt) — Provide packaging  packaging  markers.py txt content.
- [`packaging__packaging__metadata.py.txt`](packaging__packaging__metadata.py.txt) — Provide packaging  packaging  metadata.py txt content.
- [`packaging__packaging__pylock.py.txt`](packaging__packaging__pylock.py.txt) — Provide packaging  packaging  pylock.py txt content.
- [`packaging__packaging__specifiers.py.txt`](packaging__packaging__specifiers.py.txt) — Provide packaging  packaging  specifiers.py txt content.
- [`packaging__packaging__tags.py.txt`](packaging__packaging__tags.py.txt) — Provide packaging  packaging  tags.py txt content.
- [`packaging__packaging__version.py.txt`](packaging__packaging__version.py.txt) — Provide packaging  packaging  version.py txt content.
- [`platformdirs__platformdirs___xdg.py.txt`](platformdirs__platformdirs___xdg.py.txt) — Provide platformdirs  platformdirs   xdg.py txt content.
- [`platformdirs__platformdirs__android.py.txt`](platformdirs__platformdirs__android.py.txt) — Provide platformdirs  platformdirs  android.py txt content.
- [`platformdirs__platformdirs__api.py.txt`](platformdirs__platformdirs__api.py.txt) — Provide platformdirs  platformdirs  api.py txt content.
- [`platformdirs__platformdirs__ios.py.txt`](platformdirs__platformdirs__ios.py.txt) — Provide platformdirs  platformdirs  ios.py txt content.
- [`platformdirs__platformdirs__macos.py.txt`](platformdirs__platformdirs__macos.py.txt) — Provide platformdirs  platformdirs  macos.py txt content.
- [`platformdirs__platformdirs__unix.py.txt`](platformdirs__platformdirs__unix.py.txt) — Provide platformdirs  platformdirs  unix.py txt content.
- [`platformdirs__platformdirs__windows.py.txt`](platformdirs__platformdirs__windows.py.txt) — Provide platformdirs  platformdirs  windows.py txt content.
- [`pluggy__pluggy___caller.py.txt`](pluggy__pluggy___caller.py.txt) — Provide pluggy  pluggy   caller.py txt content.
- [`pluggy__pluggy___decorators.py.txt`](pluggy__pluggy___decorators.py.txt) — Provide pluggy  pluggy   decorators.py txt content.
- [`pluggy__pluggy___manager.py.txt`](pluggy__pluggy___manager.py.txt) — Provide pluggy  pluggy   manager.py txt content.
- [`pluggy__pluggy___result.py.txt`](pluggy__pluggy___result.py.txt) — Provide pluggy  pluggy   result.py txt content.
- [`pluggy__pluggy___tracing.py.txt`](pluggy__pluggy___tracing.py.txt) — Provide pluggy  pluggy   tracing.py txt content.
- [`pytest___pytest__assertion__rewrite.py.txt`](pytest___pytest__assertion__rewrite.py.txt) — Provide pytest   pytest  assertion  rewrite.py txt content.
- [`pytest___pytest__capture.py.txt`](pytest___pytest__capture.py.txt) — Provide pytest   pytest  capture.py txt content.
- [`pytest___pytest__hookspec.py.txt`](pytest___pytest__hookspec.py.txt) — Provide pytest   pytest  hookspec.py txt content.
- [`pytest___pytest__junitxml.py.txt`](pytest___pytest__junitxml.py.txt) — Provide pytest   pytest  junitxml.py txt content.
- [`pytest___pytest__logging.py.txt`](pytest___pytest__logging.py.txt) — Provide pytest   pytest  logging.py txt content.
- [`pytest___pytest__main.py.txt`](pytest___pytest__main.py.txt) — Provide pytest   pytest  main.py txt content.
- [`pytest___pytest__pathlib.py.txt`](pytest___pytest__pathlib.py.txt) — Provide pytest   pytest  pathlib.py txt content.
- [`pytest___pytest__reports.py.txt`](pytest___pytest__reports.py.txt) — Provide pytest   pytest  reports.py txt content.
- [`rich__rich___win32_console.py.txt`](rich__rich___win32_console.py.txt) — Provide rich  rich   win32 console.py txt content.
- [`rich__rich__layout.py.txt`](rich__rich__layout.py.txt) — Provide rich  rich  layout.py txt content.
- [`rich__rich__markdown.py.txt`](rich__rich__markdown.py.txt) — Provide rich  rich  markdown.py txt content.
- [`rich__rich__pretty.py.txt`](rich__rich__pretty.py.txt) — Provide rich  rich  pretty.py txt content.
- [`rich__rich__segment.py.txt`](rich__rich__segment.py.txt) — Provide rich  rich  segment.py txt content.
- [`rich__rich__style.py.txt`](rich__rich__style.py.txt) — Provide rich  rich  style.py txt content.
- [`rich__rich__syntax.py.txt`](rich__rich__syntax.py.txt) — Provide rich  rich  syntax.py txt content.
- [`rich__rich__text.py.txt`](rich__rich__text.py.txt) — Provide rich  rich  text.py txt content.
- [`starlette__starlette__authentication.py.txt`](starlette__starlette__authentication.py.txt) — Provide starlette  starlette  authentication.py txt content.
- [`starlette__starlette__datastructures.py.txt`](starlette__starlette__datastructures.py.txt) — Provide starlette  starlette  datastructures.py txt content.
- [`starlette__starlette__formparsers.py.txt`](starlette__starlette__formparsers.py.txt) — Provide starlette  starlette  formparsers.py txt content.
- [`starlette__starlette__requests.py.txt`](starlette__starlette__requests.py.txt) — Provide starlette  starlette  requests.py txt content.
- [`starlette__starlette__responses.py.txt`](starlette__starlette__responses.py.txt) — Provide starlette  starlette  responses.py txt content.
- [`starlette__starlette__routing.py.txt`](starlette__starlette__routing.py.txt) — Provide starlette  starlette  routing.py txt content.
- [`starlette__starlette__testclient.py.txt`](starlette__starlette__testclient.py.txt) — Provide starlette  starlette  testclient.py txt content.
- [`starlette__starlette__websockets.py.txt`](starlette__starlette__websockets.py.txt) — Provide starlette  starlette  websockets.py txt content.
- [`structlog__structlog___config.py.txt`](structlog__structlog___config.py.txt) — Provide structlog  structlog   config.py txt content.
- [`structlog__structlog___native.py.txt`](structlog__structlog___native.py.txt) — Provide structlog  structlog   native.py txt content.
- [`structlog__structlog__dev.py.txt`](structlog__structlog__dev.py.txt) — Provide structlog  structlog  dev.py txt content.
- [`structlog__structlog__processors.py.txt`](structlog__structlog__processors.py.txt) — Provide structlog  structlog  processors.py txt content.
- [`structlog__structlog__stdlib.py.txt`](structlog__structlog__stdlib.py.txt) — Provide structlog  structlog  stdlib.py txt content.
- [`structlog__structlog__threadlocal.py.txt`](structlog__structlog__threadlocal.py.txt) — Provide structlog  structlog  threadlocal.py txt content.
- [`structlog__structlog__twisted.py.txt`](structlog__structlog__twisted.py.txt) — Provide structlog  structlog  twisted.py txt content.
- [`structlog__structlog__typing.py.txt`](structlog__structlog__typing.py.txt) — Provide structlog  structlog  typing.py txt content.
- [`tenacity__tenacity___utils.py.txt`](tenacity__tenacity___utils.py.txt) — Provide tenacity  tenacity   utils.py txt content.
- [`tenacity__tenacity__asyncio__retry.py.txt`](tenacity__tenacity__asyncio__retry.py.txt) — Provide tenacity  tenacity  asyncio  retry.py txt content.
- [`tenacity__tenacity__retry.py.txt`](tenacity__tenacity__retry.py.txt) — Provide tenacity  tenacity  retry.py txt content.
- [`tenacity__tenacity__stop.py.txt`](tenacity__tenacity__stop.py.txt) — Provide tenacity  tenacity  stop.py txt content.
- [`tenacity__tenacity__wait.py.txt`](tenacity__tenacity__wait.py.txt) — Provide tenacity  tenacity  wait.py txt content.
- [`tomli__tomli___parser.py.txt`](tomli__tomli___parser.py.txt) — Provide tomli  tomli   parser.py txt content.
- [`tomlkit__tomlkit__api.py.txt`](tomlkit__tomlkit__api.py.txt) — Provide tomlkit  tomlkit  api.py txt content.
- [`tomlkit__tomlkit__container.py.txt`](tomlkit__tomlkit__container.py.txt) — Provide tomlkit  tomlkit  container.py txt content.
- [`tomlkit__tomlkit__exceptions.py.txt`](tomlkit__tomlkit__exceptions.py.txt) — Provide tomlkit  tomlkit  exceptions.py txt content.
- [`tomlkit__tomlkit__parser.py.txt`](tomlkit__tomlkit__parser.py.txt) — Provide tomlkit  tomlkit  parser.py txt content.
- [`tomlkit__tomlkit__source.py.txt`](tomlkit__tomlkit__source.py.txt) — Provide tomlkit  tomlkit  source.py txt content.
- [`werkzeug__werkzeug__datastructures__headers.py.txt`](werkzeug__werkzeug__datastructures__headers.py.txt) — Provide werkzeug  werkzeug  datastructures  headers.py txt content.
- [`werkzeug__werkzeug__datastructures__mixins.py.txt`](werkzeug__werkzeug__datastructures__mixins.py.txt) — Provide werkzeug  werkzeug  datastructures  mixins.py txt content.
- [`werkzeug__werkzeug__datastructures__structures.py.txt`](werkzeug__werkzeug__datastructures__structures.py.txt) — Provide werkzeug  werkzeug  datastructures  structures.py txt content.
- [`werkzeug__werkzeug__local.py.txt`](werkzeug__werkzeug__local.py.txt) — Provide werkzeug  werkzeug  local.py txt content.
- [`werkzeug__werkzeug__sansio__response.py.txt`](werkzeug__werkzeug__sansio__response.py.txt) — Provide werkzeug  werkzeug  sansio  response.py txt content.
- [`werkzeug__werkzeug__serving.py.txt`](werkzeug__werkzeug__serving.py.txt) — Provide werkzeug  werkzeug  serving.py txt content.
- [`werkzeug__werkzeug__test.py.txt`](werkzeug__werkzeug__test.py.txt) — Provide werkzeug  werkzeug  test.py txt content.
- [`werkzeug__werkzeug__wrappers__response.py.txt`](werkzeug__werkzeug__wrappers__response.py.txt) — Provide werkzeug  werkzeug  wrappers  response.py txt content.

### Subdirectories

- [`LICENSES/`](LICENSES/README.md) — Provide anyio txt content.

<!-- exactus:inventory:end -->
