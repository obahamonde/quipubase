# type: ignore
from Cython.Build import cythonize
from setuptools import Extension, setup  # pylint: disable=E0401

ext_modules = [
    Extension(
        "quipubase",
        sources=["./quipubase.pyx"],
        include_dirs=["/usr/local/include", "/usr/include"],
        library_dirs=[
            "/usr/local/lib",
            "/lib/x86_64-linux-gnu",
            "/usr/lib/x86_64-linux-gnu",
        ],
        libraries=[
            "rocksdb",
            "bz2",
            "lz4",
            "zstd",
            "snappy",  # Ensure the Snappy library is linked
        ],
        extra_compile_args=["-std=c++17"],
        language="c++",
    )
]

setup(
    name="quipubase",
    ext_modules=cythonize(ext_modules),
)
