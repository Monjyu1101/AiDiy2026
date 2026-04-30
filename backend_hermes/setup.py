from pathlib import Path

from setuptools import find_packages, setup


BASE_DIR = Path(__file__).resolve().parent
REQ_FILE = BASE_DIR / "requirements.txt"


def read_requirements() -> list[str]:
    if not REQ_FILE.exists():
        return []

    requirements: list[str] = []
    for line in REQ_FILE.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        requirements.append(item)
    return requirements


setup(
    name="aidiy-hermes",
    version="0.5.1",
    description="AiDiy Hermes CLI",
    packages=find_packages(exclude=("tests", "tests.*")),
    py_modules=["cli_main"],
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "aidiy_hermes=cli_main:main",
        ]
    },
    python_requires=">=3.10",
)
