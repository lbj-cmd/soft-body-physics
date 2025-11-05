from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    name="soft-body-physics",
    ext_modules=cythonize("src/World_cython.pyx"),
    include_dirs=[numpy.get_include()],
)