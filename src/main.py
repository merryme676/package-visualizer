"""Инструмент визуализации графа зависимостей (NuGet)."""

import json
import argparse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET


def parse_args():
    """
    Разбирает параметры командной строки.

    Returns:
        argparse.Namespace: объект с параметрами.
    """
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей для NuGet",
    )
    parser.add_argument("--package", help="Имя анализируемого пакета")
    parser.add_argument("--repo", help="URL или путь к тестовому файлу")
    parser.add_argument("--mode", help="Режим работы с тестовым репо")
    parser.add_argument("--version", help="Версия пакета")
    parser.add_argument("--output", help="Имя файла с графом")
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="Режим вывода ASCII-дерева",
    )
    return parser.parse_args()


def get_latest_version(package):
    """
    Получает последнюю версию пакета из NuGet.

    Args:
        package: имя пакета.

    Returns:
        str: последняя версия или None при ошибке.
    """
    pkg_lower = package.lower()
    url = f"https://api.nuget.org/v3-flatcontainer/{pkg_lower}/index.json"

    try:
        with urllib.request.urlopen(url) as response:
            import json
            data = json.loads(response.read())
            versions = data.get("versions", [])
            if versions:
                return versions[-1]  # последняя в списке
    except Exception:
        pass
    return None


def print_config(args):
    """
    Выводит все параметры в формате ключ-значение.

    Args:
        args: объект с параметрами.
    """
    print("=== Параметры запуска ===")
    print(f"Package: {args.package}")
    print(f"Repo:    {args.repo}")
    print(f"Mode:    {args.mode}")
    print(f"Version: {args.version}")
    print(f"Output:  {args.output}")
    print(f"ASCII:   {args.ascii}")
    print("=========================")


def fetch_dependencies(package, version):
    """
    Скачивает прямые зависимости пакета из NuGet.
    """
    pkg_lower = package.lower()

        # Если версия не указана или равна 'latest', получаем последнюю
    if not version or version == "latest":
        actual_version = get_latest_version(package)
        if not actual_version:
            print(f"Не удалось определить версию для {package}")
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
        # Если 404, возможно, версия не та. Пробуем latest
        if exc.code == 404 and version_url != "latest":
            print(f"Версия {version} не найдена, пробуем latest...")
            return fetch_dependencies(package, "latest")
        else:
            print(f"Ошибка HTTP: {exc.code}")
            return []
    except Exception as exc:
        print(f"Ошибка сети: {exc}")
        return []

    root = ET.fromstring(xml_data)
    dependencies = []

    for dep in root.iter():
        if dep.tag.endswith('dependency'):
            dep_id = dep.get('id')
            if dep_id and dep_id not in dependencies:
                dependencies.append(dep_id)

    return dependencies


def build_graph(package, version):
    """
    Строит граф зависимостей (DFS без рекурсии).

    Args:
        package: корневой пакет.
        version: версия корневого пакета.

    Returns:
        dict: граф в виде {пакет: [его зависимости]}.
    """
    graph = {}
    stack = [(package, version)]
    visited = set()

    while stack:
        current_pkg, current_ver = stack.pop()

        if (current_pkg, current_ver) in visited:
            continue

        visited.add((current_pkg, current_ver))

        # Получаем зависимости текущего пакета
        deps = fetch_dependencies(current_pkg, current_ver)
        graph[current_pkg] = deps

        # Добавляем в стек еще не посещенные зависимости
        for dep in deps:
            if (dep, "latest") not in visited:
                stack.append((dep, "latest"))

    return graph


def print_ascii_tree(graph, root, indent=0):
    """
    Выводит граф в виде ASCII-дерева.

    Args:
        graph: словарь зависимостей.
        root: корневой пакет.
        indent: отступ (для рекурсивного вызова).
    """
    print("  " * indent + f"- {root}")

    if root in graph:
        for dep in graph[root]:
            print_ascii_tree(graph, dep, indent + 1)


def main():
    """Точка входа."""
    args = parse_args()
    print_config(args)

    if args.package and args.version:
        print("\n=== Прямые зависимости ===")
        deps = fetch_dependencies(args.package, args.version)
        if deps:
            for d in deps:
                print(f"- {d}")
        else:
            print("Зависимости не найдены.")

        if args.ascii:
            print("\n=== Граф зависимостей (ASCII) ===")
            graph = build_graph(args.package, args.version)
            print_ascii_tree(graph, args.package)


if __name__ == "__main__":
    main()
