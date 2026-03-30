from __future__ import annotations

from pathlib import Path
import sys
import tomllib
import zipfile


REQUIRED_RELEASE_FILES = [
    "uestc-wifi-autologin.exe",
    "uestc-wifi-autologin-no-console.exe",
    "account_config.example.yaml",
    "README.txt",
    "\u5f00\u542f\u4ee3\u7406\u540e\u65e0\u6cd5\u767b\u5f55\u7684\u89e3\u51b3\u65b9\u6cd5.txt",
]


def get_repo_dir() -> Path:
    return Path(__file__).resolve().parent


def get_version(repo_dir: Path) -> str:
    pyproject_path = repo_dir / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def build_release_zip() -> Path:
    repo_dir = get_repo_dir()
    release_dir = repo_dir / "release"
    version = get_version(repo_dir)
    zip_path = release_dir / f"uestc-wifi-autologin-{version}.zip"

    missing_files = [name for name in REQUIRED_RELEASE_FILES if not (release_dir / name).exists()]
    if missing_files:
        missing_text = "\n".join(f"- {name}" for name in missing_files)
        raise FileNotFoundError(f"release directory is missing required files:\n{missing_text}")

    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in REQUIRED_RELEASE_FILES:
            zf.write(release_dir / name, arcname=name)

    return zip_path


def main() -> int:
    zip_path = build_release_zip()
    print(f"Created: {zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
