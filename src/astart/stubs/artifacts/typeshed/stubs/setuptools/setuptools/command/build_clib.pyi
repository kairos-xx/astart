from setuptools.dist import Distribution

from .._distutils.command import build_clib as orig

class build_clib(orig.build_clib):
    distribution: Distribution
    def build_libraries(self, libraries) -> None: ...
