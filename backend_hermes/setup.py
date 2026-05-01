from pathlib import Path

from setuptools import setup


def _requirements() -> list[str]:
    req_file = Path(__file__).with_name("requirements.txt")
    if not req_file.exists():
        return []
    return [
        line.strip()
        for line in req_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


setup(
    name="aidiy-hermes",
    version="0.12.0",
    py_modules=["cli_main"],
    packages=["base", "gateway", "hermes_cli", "core"],
    install_requires=_requirements(),
    package_dir={
        "base": "base",
        "gateway": "gateway",
        "hermes_cli": "hermes_cli",
        "core": "core",
    },
    entry_points={
        "console_scripts": [
            "aidiy_hermes=cli_main:cli_entry",
            "text-hermes=cli_main:text_main",
        ],
    },
)
