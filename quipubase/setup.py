# type: ignore
from Cython.Build import cythonize
from setuptools import Extension, setup  # pylint: disable=E0401

ext_modules = [
    Extension(
        "quipubase",
        sources=["quipubase.pyx"],
        include_dirs=["/usr/local/include"],
        library_dirs=["/usr/local/lib"],
        libraries=["rocksdb"],
        extra_compile_args=["-std=c++17"],
        language="c++",
    )
]

setup(
    name="rocksdb",
    ext_modules=cythonize(ext_modules),
)
