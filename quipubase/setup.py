# type: ignore
from Cython.Build import cythonize
from setuptools import Extension, setup  # pylint: disable=E0401

ext_modules = [
    Extension(
        "quipubase",
        sources=["./quipubase.pyx"],
        include_dirs=["/usr/local/include", "/usr/include"],
        library_dirs=["/usr/local/lib", "/usr/lib/x86_64-linux-gnu"],
        libraries=[
            "rocksdb",
            "bz2",
        ],  # Ensure the Bzip2 library is also linked if needed
        extra_compile_args=["-std=c++17"],
        language="c++",
    )
]

setup(
    name="quipubase",
    ext_modules=cythonize(ext_modules),
)
