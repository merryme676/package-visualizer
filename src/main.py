"""
Инструмент визуализации графа зависимостей для менеджера пакетов NuGet.
"""

import argparse
import json
import urllib.error
import urllib.request
import xml.etree.ElementTree as xml_tree


http_not_found = 404


def parse_args():
    """
    Разбирает параметры командной строки.
    """
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей для NuGet",
    )
    parser.add_argument("--package", help="Имя пакета")
    parser.add_argument("--repo", help="Путь к локальному файлу")
    parser.add_argument("--mode", help="Режим работы")
    parser.add_argument("--version", help="Версия пакета")
    parser.add_argument("--output", help="Имя файла с графом")
    parser.add_argument(
        "--ascii", action="store_true", help="ASCII-дерево"
    )
    parser.add_argument(
        "--reverse", action="store_true", help="Обратные связи"
    )
    return parser.parse_args()


def print_config(args):
    """
    Выводит параметры в формате ключ-значение.
    """
    print("=== Параметры запуска ===")
    print(f"Package: {args.package}")
    print(f"Repo:    {args.repo}")
    print(f"Mode:    {args.mode}")
    print(f"Version: {args.version}")
    print(f"Output:  {args.output}")
    print(f"ASCII:   {args.ascii}")
    print("=========================")


def get_latest_version(package):
    """
    Получает последнюю версию пакета из NuGet.
    """
    pkg_lower = package.lower()
    url = f"https://api.nuget.org/v3-flatcontainer/{pkg_lower}/index.json"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            versions = data.get("versions", [])
            if versions:
                return versions[-1]
    except Exception:
        pass
    return None


def load_test_repo(package, repo_path):
    """
    Читает зависимости из локального тестового файла.
    """
    try:
        with open(repo_path, "r", encoding="utf-8") as file:
            for line in file:
                if line.strip().startswith(package + ":"):
                    deps_str = line.split(":", 1)[1].strip()
                    if not deps_str:
                        return []
                    return [d.strip() for d in deps_str.split(",")]
        return []
    except FileNotFoundError:
        print(f"Ошибка: файл {repo_path} не найден.")
        return []


def parse_nuspec_xml(xml_data):
    """
    Извлекает имена зависимостей из XML-файла NuGet.
    """
    root = xml_tree.fromstring(xml_data)
    dependencies = []
    for dep in root.iter():
        if dep.tag.endswith('dependency'):
            dep_id = dep.get('id')
            if dep_id and dep_id not in dependencies:
                dependencies.append(dep_id)
    return dependencies


def fetch_from_network(package, version):
    """
    Скачивает прямые зависимости пакета из NuGet.
    """
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
        f"https://api.nuget.org/v3-flatcontainer/"
        f"{pkg_lower}/{version_url}/{pkg_lower}.nuspec"
    )

    print(f"Загрузка данных из: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            xml_data = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == http_not_found:
            print(f"Пакет {package} версии {version_url} не найден.")
        else:
            print(f"Ошибка HTTP: {exc.code}")
        return []
    except Exception as exc:
        print(f"Ошибка сети: {exc}")
        return []

    return parse_nuspec_xml(xml_data)


def fetch_dependencies(package, version, repo_path=None):
    """
    Определяет источник данных и возвращает зависимости.
    """
    if repo_path:
        return load_test_repo(package, repo_path)
    return fetch_from_network(package, version)


def build_graph(package, version, repo_path=None):
    """
    Строит транзитивный граф зависимостей методом DFS без рекурсии.
    """
    graph = {}
    stack = [(package, version)]
    visited = set()

    while stack:
        current_pkg, current_ver = stack.pop()

        if (current_pkg, current_ver) in visited:
            continue
        visited.add((current_pkg, current_ver))

        deps = fetch_dependencies(current_pkg, current_ver, repo_path)
        graph[current_pkg] = deps

        next_ver = "latest" if not repo_path else current_ver

        for dep in deps:
            if (dep, next_ver) not in visited:
                stack.append((dep, next_ver))

    return graph


def print_ascii_tree(graph, root, indent=0, visited=None):
    """
    Выводит граф в виде ASCII-дерева.
    """
    if visited is None:
        visited = set()

    print("  " * indent + f"- {root}")

    if root in visited:
        return
    visited.add(root)

    if root in graph:
        for dep in graph[root]:
            print_ascii_tree(graph, dep, indent + 1, visited)


def main():
    """
    Точка входа в программу.
    """
    args = parse_args()
    print_config(args)

    if not args.package:
        print("Ошибка: не указан пакет (--package).")
        return

    print("\n=== Построение графа ===")
    graph = build_graph(args.package, args.version, args.repo)

    if args.ascii:
        print("\n=== Граф зависимостей (ASCII) ===")
        print_ascii_tree(graph, args.package)


if __name__ == "__main__":
    main()
