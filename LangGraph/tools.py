import os
import re
import subprocess
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from langchain_core.tools import ToolException, tool
from langgraph.types import interrupt


WORKSPACE = (Path(__file__).parent.parent / "application").resolve()
MAVEN_REPOSITORIES = [
    "https://repo1.maven.org/maven2",
    "https://plugins.gradle.org/m2",
]
STABLE_VERSION = re.compile(r"\d+(\.\d+)*")
MAX_RELEASE_LINES = 6
PROTECTED_FILES = ("gradlew", "gradlew.bat")
PROTECTED_DIR = "gradle/wrapper"
IGNORED_DIRS = {".git", ".gradle", "build"}


def _resolve(path: str) -> Path:
    # normpath collapses ".." as text, without touching the disk: resolve() on Windows may return a "\\?\C:\..."
    # path while a parallel write_file is creating the same folder, and that path fails the check below.
    full_path = Path(os.path.normpath(WORKSPACE / path.lstrip("/\\")))
    if not full_path.is_relative_to(WORKSPACE):
        raise ToolException(f"Path '{path}' is outside of the project directory.")
    return full_path


def _is_protected(file: Path) -> bool:
    # Lowercase because Windows paths are case-insensitive: "GRADLEW.BAT" is the same file.
    relative = file.relative_to(WORKSPACE).as_posix().lower()
    return relative in PROTECTED_FILES or relative == PROTECTED_DIR or relative.startswith(f"{PROTECTED_DIR}/")


@tool
def list_files() -> str:
    """List all files in the project, as paths relative to the project root."""
    files = sorted(
        p.relative_to(WORKSPACE).as_posix()
        for p in WORKSPACE.rglob("*")
        # parts splits the path into folders: ("build", "classes", ...); skip the file if any of them is ignored.
        if p.is_file() and not IGNORED_DIRS.intersection(p.relative_to(WORKSPACE).parts)
    )
    return "\n".join(files) if files else "The project is empty."


@tool
def read_file(path: str) -> str:
    """Read a text file from the project.

    Args:
        path: File path relative to the project root, e.g. "src/main/java/App.java".
    """
    file = _resolve(path)
    if not file.is_file():
        return f"File not found: {path}"
    return file.read_text(encoding="utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a file in the project with the given content.

    Args:
        path: File path relative to the project root, e.g. "pom.xml".
        content: Full new content of the file.
    """
    file = _resolve(path)
    if _is_protected(file):
        raise ToolException(f"'{path}' is part of the Gradle wrapper and must not be modified.")
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")
    return f"Written {path} ({len(content)} chars)."


@tool
def delete_file(path: str) -> str:
    """Delete a file from the project. To move a file, write it to the new path with write_file, then delete the old one.

    Args:
        path: File path relative to the project root, e.g. "src/test/java/com/example/AppIT.java".
    """
    file = _resolve(path)
    # .git holds the demo baseline of the project, so it is protected like the wrapper.
    in_ignored_dir = IGNORED_DIRS.intersection(part.lower() for part in file.relative_to(WORKSPACE).parts)
    if _is_protected(file) or in_ignored_dir:
        raise ToolException(f"'{path}' is part of the Gradle wrapper, git or the build output and must not be deleted.")
    if not file.is_file():
        return f"File not found: {path}"
    file.unlink()
    return f"Deleted {path}."


@tool
def get_java_version() -> str:
    """Get java version on local machine"""
    result = subprocess.run(
        ["java", "--version"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    return result.stdout


@tool
def get_gradle_version() -> str:
    """Get gradle version on local machine"""
    result = subprocess.run(
        [str(WORKSPACE / "gradlew.bat"), "--version"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    return result.stdout


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _fetch_versions(group_id: str, artifact_id: str) -> list[str] | None:
    path = f"{group_id.replace('.', '/')}/{artifact_id}/maven-metadata.xml"
    for repository in MAVEN_REPOSITORIES:
        try:
            with urllib.request.urlopen(f"{repository}/{path}", timeout=10) as response:
                root = ET.fromstring(response.read())
        except urllib.error.HTTPError as error:
            if error.code == 404:
                continue
            raise ToolException(f"{repository} returned HTTP {error.code}.")
        except urllib.error.URLError as error:
            raise ToolException(f"Cannot reach {repository}: {error.reason}")
        return [element.text for element in root.iter("version") if element.text]
    return None


@tool
def get_library_version(group_id: str, artifact_id: str) -> str:
    """Look up the latest stable versions of a library or Gradle plugin in Maven Central and the Gradle Plugin Portal.

    Use it before writing any version into build files: do not rely on memory.
    For a Gradle plugin, pass the plugin id as both arguments with ".gradle.plugin" added to the artifact,
    e.g. group_id="org.springframework.boot", artifact_id="org.springframework.boot.gradle.plugin".

    Args:
        group_id: Maven group id, e.g. "org.springframework.boot".
        artifact_id: Maven artifact id, e.g. "spring-boot-starter-web".
    """
    versions = _fetch_versions(group_id, artifact_id)
    if versions is None:
        raise ToolException(f"Artifact {group_id}:{artifact_id} not found.")

    stable = sorted((v for v in versions if STABLE_VERSION.fullmatch(v)), key=_version_key)
    if not stable:
        return f"{group_id}:{artifact_id} has no stable versions, only: {', '.join(versions[-5:])}"

    latest_per_line: dict[tuple[int, ...], str] = {}
    for version in stable:
        latest_per_line[_version_key(version)[:2]] = version
    recent_lines = list(latest_per_line.values())[-MAX_RELEASE_LINES:]

    return (
        f"Latest stable version of {group_id}:{artifact_id}: {recent_lines[-1]}\n"
        f"Latest version of each recent release line: {', '.join(recent_lines)}"
    )


@tool
def ask_human(question: str) -> str:
    """Ask the human a question and wait for the answer.

    Use it only when the task is ambiguous, neither the task nor the conventions answer the question,
    and a wrong guess would be costly to redo. Ask one concrete question, list the options and say which one
    you recommend. Call this tool on its own, not together with other tools in the same step.

    Args:
        question: The question, the options and your recommendation.
    """
    # Pauses the whole graph; the answer passed to Command(resume=...) becomes the tool result.
    return str(interrupt(question))


TOOLS = [
    list_files, read_file, write_file, delete_file,
    get_java_version, get_gradle_version, get_library_version, ask_human,
]

for _tool in TOOLS:
    _tool.handle_tool_error = True