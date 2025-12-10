from __future__ import annotations

import os
import pathlib
import subprocess
import sys
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py

ROOT = pathlib.Path(__file__).resolve().parent
NATIVE_DIR = ROOT / "srw_tools" / "native"


class build_native(_build_py):
    """Custom build command which builds the native shared library using CMake."""

    def run(self):
        # First run the original build_py
        super().run()
        # Now build native
        build_dir = NATIVE_DIR / "build"
        if build_dir.exists():
            # keep it clean
            import shutil

            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)
        # Configure and build
        cmake_cmd = ["cmake", ".."]
        build_cmd = ["cmake", "--build", ".", "--config", "Release"]
        print("Configuring native build:", " ".join(cmake_cmd))
        subprocess.check_call(cmake_cmd, cwd=str(build_dir))
        print("Building native build:", " ".join(build_cmd))
        subprocess.check_call(build_cmd, cwd=str(build_dir))
        # Find the produced library and copy it to the python package directory
        import glob
        import shutil

        patterns = ["srwfast*", "nativelib*"]
        for root, dirs, files in os.walk(str(build_dir)):
            for pat in patterns:
                for fn in glob.glob(os.path.join(root, pat)):
                    dest = ROOT / "srw_tools" / os.path.basename(fn)
                    print(f"Copying native library {fn} -> {dest}")
                    shutil.copyfile(fn, str(dest))


if __name__ == "__main__":
    ROOT = pathlib.Path(__file__).resolve().parent
    long_desc = (ROOT / "README.md").read_text(encoding="utf8") if (ROOT / "README.md").exists() else ""
    setup(
        name="srw-ui",
        version="0.1.0",
        description="Lightweight SRW simulation visualization tools",
        long_description=long_desc,
        long_description_content_type="text/markdown",
        packages=find_packages(exclude=("tests",)),
        include_package_data=True,
        python_requires=">=3.8",
        install_requires=[
            "numpy",
            "scipy",
            "scikit-image",
            "matplotlib",
            "srwpy",
            "asyncssh",
        ],
        extras_require={
            "dev": ["pytest"],
            "native": [],
        },
        entry_points={
            "console_scripts": [
                "srw-cli = srw_tools.cli:main",
                "srw-gui = srw_tools.gui:run_gui",
            ],
        },
        cmdclass={
            "build_py": build_native,
        },
        author="You",
        author_email="you@example.com",
        keywords=["srw", "visualization", "sim"],
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
    )
