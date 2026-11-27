
"""
Инструмент визуализации графа зависимостей для менеджера пакетов NuGet.
"""

import argparse
import json
import string
import urllib.error
import urllib.request
import xml.etree.ElementTree as xml_tree
import webbrowser
import zlib


HTTP_NOT_FOUND = 404
PLANTUML_CHUNK_SIZE = 3
PLANTUML_COMPRESSION_LEVEL = 9

PLANTUML_ALPHABET = (
    string.digits
    + string.ascii_uppercase
    + string.ascii_lowercase
    + "-_"
)


def parse_args():
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей для NuGet"
    )
    parser.add_argument("--package", help="Имя пакета")
    parser.add_argument("--repo", help="Путь к локальному файлу")
    parser.add_argument("--mode", help="Режим работы")
    parser.add_argument("--version", help="Версия пакета")
    parser.add_argument("--output", help="Имя файла с графом")
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="ASCII-дерево"
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Обратные связи"
    )
    return parser.parse_args()


def print_config(args):
    """Выводит параметры в формате ключ-значение."""
    print("=== Параметры запуска ===")
    print(f"Package: {args.package}")
    print(f"Repo:    {args.repo}")
    print(f"Mode:    {args.mode}")
    print(f"Version: {args.version}")
    print(f"Output:  {args.output}")
    print(f"ASCII:   {args.ascii}")
    print("=========================")


def get_latest_version(package):
    """Получает последнюю версию пакета из NuGet."""
    pkg_lower = package.lower()
    url = (
        "https://api.nuget.org/v3-flatcontainer/"
        f"{pkg_lower}/index.json"
    )

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            versions = data.get("versions", [])
            if versions:
                return versions[-1]
    except Exception:
        return None

    return None


def load_test_repo(package, repo_path):
    """Читает зависимости из локального тестового файла."""
    try:
        with open(repo_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                if line.startswith(package + ":"):
                    deps_str = line.split(":", 1)[1].strip()
                    if not deps_str:
                        return []

                    return [
                        dependency.strip()
                        for dependency in deps_str.split(",")
                    ]

        return []
    except FileNotFoundError:
        print(f"Ошибка: файл {repo_path} не найден.")
        return []


def parse_nuspec_xml(xml_data):
    """Извлекает имена зависимостей из XML-файла NuGet."""
    root = xml_tree.fromstring(xml_data)
    dependencies = []

    for dep in root.iter():
        if dep.tag.endswith("dependency"):
            dep_id = dep.get("id")
            if dep_id and dep_id not in dependencies:
                dependencies.append(dep_id)

    return dependencies


def fetch_from_network(package, version):
    """Скачивает прямые зависимости пакета из NuGet."""
    pkg_lower = package.lower()

    if version == "latest" or not version:
        actual_version = get_latest_version(package)
        if not actual_version:
            print(f"Не удалось найти версию для {package}")
            return []
        version_url = actual_version
    else:
        version_url = version

    url = (
        "https://api.nuget.org/v3-flatcontainer/"
        f"{pkg_lower}/{version_url}/{pkg_lower}.nuspec"
    )

    print(f"Загрузка данных из: {url}")

    try:
        with urllib.request.urlopen(url) as response:
            xml_data = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == HTTP_NOT_FOUND:
            print(
                f"Пакет {package} версии {version_url} не найден."
            )
        else:
            print(f"Ошибка HTTP: {exc.code}")
        return []
    except Exception as exc:
        print(f"Ошибка сети: {exc}")
        return []

    return parse_nuspec_xml(xml_data)


def fetch_dependencies(package, version, repo_path=None):
    """Определяет источник данных и возвращает зависимости."""
    if repo_path:
        return load_test_repo(package, repo_path)

    return fetch_from_network(package, version)


def build_graph(package, version, repo_path=None):
    """Строит транзитивный граф зависимостей без рекурсии."""
    graph = {}
    stack = [(package, version)]
    visited = set()

    while stack:
        current_pkg, current_ver = stack.pop()

        if (current_pkg, current_ver) in visited:
            continue

        visited.add((current_pkg, current_ver))
        deps = fetch_dependencies(
            current_pkg,
            current_ver,
            repo_path
        )
        graph[current_pkg] = deps

        next_ver = "latest" if not repo_path else current_ver

        for dep in deps:
            if (dep, next_ver) not in visited:
                stack.append((dep, next_ver))

    return graph


def print_ascii_tree(graph, root, indent=0, visited=None):
    """Выводит граф в виде ASCII-дерева."""
    if visited is None:
        visited = set()

    print("  " * indent + f"- {root}")

    if root in visited:
        return

    visited.add(root)

    if root in graph:
        for dep in graph[root]:
            print_ascii_tree(
                graph,
                dep,
                indent + 1,
                visited
            )


def find_reverse_dependencies(graph, target_package):
    """Ищет пакеты, которые зависят от указанного пакета."""
    reverse_deps = set()

    for package, dependencies in graph.items():
        if target_package in dependencies:
            reverse_deps.add(package)

    return list(reverse_deps)


def print_reverse_dependencies(graph, target_package):
    """Выводит обратные зависимости на экран."""
    print(
        f"\n=== Обратные зависимости для "
        f"'{target_package}' ==="
    )
    reverse_deps = find_reverse_dependencies(
        graph,
        target_package
    )

    if reverse_deps:
        for package in reverse_deps:
            print(f"- {package}")
    else:
        print("Обратные зависимости не найдены.")


def _encode_plantuml(puml_text):
    """Сжимает текст PlantUML и кодирует его для URL."""
    compressed = zlib.compress(
        puml_text.encode("utf-8"),
        PLANTUML_COMPRESSION_LEVEL
    )[2:-4]

    encoded_parts = []

    for index in range(
        0,
        len(compressed),
        PLANTUML_CHUNK_SIZE
    ):
        chunk = compressed[
            index:index + PLANTUML_CHUNK_SIZE
        ].ljust(PLANTUML_CHUNK_SIZE, b"\x00")

        byte1, byte2, byte3 = chunk

        code1 = byte1 >> 2
        code2 = ((byte1 & 0x03) << 4) | (byte2 >> 4)
        code3 = ((byte2 & 0x0F) << 2) | (byte3 >> 6)
        code4 = byte3 & 0x3F

        encoded_parts.append(
            PLANTUML_ALPHABET[code1]
            + PLANTUML_ALPHABET[code2]
            + PLANTUML_ALPHABET[code3]
            + PLANTUML_ALPHABET[code4]
        )

    return "".join(encoded_parts)


def _write_plantuml_file(puml_text, filename):
    """Сохраняет текст PlantUML в файл."""
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(puml_text)

        print(f"Граф сохранен в файл: {filename}")
        return True
    except Exception as exc:
        print(f"Ошибка сохранения файла: {exc}")
        return False


def _open_plantuml_in_browser(puml_text):
    """Открывает визуализацию графа в браузере."""
    encoded = _encode_plantuml(puml_text)
    url = f"https://www.plantuml.com/plantuml/png/{encoded}"

    print("Открываю граф в браузере...")
    print(f"Ссылка: {url}")
    webbrowser.open(url)


def save_plantuml(graph, filename):
    """Сохраняет граф в формате PlantUML и открывает его в браузере."""
    lines = ["@startuml"]

    for package, dependencies in graph.items():
        if not dependencies:
            lines.append(f"[{package}]")

        for dependency in dependencies:
            lines.append(f"[{package}] --> [{dependency}]")

    lines.append("@enduml")
    puml_text = "\n".join(lines)

    if _write_plantuml_file(puml_text, filename):
        _open_plantuml_in_browser(puml_text)


def download_plantuml_image(puml_text, filename):
    """Скачивает изображение графа PlantUML в формате PNG."""
    encoded = _encode_plantuml(puml_text)
    url = f"https://www.plantuml.com/plantuml/png/{encoded}"

    try:
        with urllib.request.urlopen(url) as response:
            image_data = response.read()

        with open(filename, "wb") as file:
            file.write(image_data)

        print(f"Изображение графа сохранено в файл: {filename}")
    except Exception as exc:
        print(f"Ошибка при скачивании картинки: {exc}")


def main():
    """Точка входа в программу."""
    args = parse_args()
    print_config(args)

    if not args.package:
        print("Ошибка: не указан пакет (--package).")
        return

    root_package = "A" if args.repo else args.package

    print("\n=== Построение графа ===")
    graph = build_graph(
        root_package,
        args.version,
        args.repo
    )

    if args.reverse:
        print_reverse_dependencies(graph, args.package)

    if args.ascii:
        print("\n=== Граф зависимостей (ASCII) ===")
        print_ascii_tree(graph, root_package)

    if args.output:
        save_plantuml(graph, args.output)


if __name__ == "__main__":
    main()
