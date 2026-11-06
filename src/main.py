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


def get_latest_version(package):
    """
    Получает последнюю версию пакета из NuGet.
    """
    pkg_lower = package.lower()
    url = f"https://api.nuget.org/v3-flatcontainer/{pkg_lower}/index.json"

    try:
        with urllib.request.urlopen(url) as response:
            import json
            data = json.loads(response.read())
            versions = data.get("versions", [])
            if versions:
                return versions[-1]  # Самая последняя
    except Exception:
        pass
    return None


def fetch_dependencies(package, version, repo_path=None):
    """
    Скачивает прямые зависимости из NuGet ИЛИ читает из локального файла.
    """
    # --- ТЕСТОВЫЙ РЕЖИМ ---
    if repo_path:
        try:
            with open(repo_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith(package + ":"):
                        deps_str = line.split(":", 1)[1].strip()
                        if not deps_str:
                            return []
                        return [d.strip() for d in deps_str.split(",")]
            return []
        except FileNotFoundError:
            print(f"Ошибка: файл {repo_path} не найден.")
            return []

        # --- РЕАЛЬНЫЙ РЕЖИМ (Интернет) ---
    pkg_lower = package.lower()

    # Если версия 'latest', узнаем точную цифру
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


def build_graph(package, version, repo_path=None):
    """Строит граф зависимостей (DFS без рекурсии)."""
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
    """Выводит граф в виде ASCII-дерева."""
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
    """Точка входа."""
    args = parse_args()
    print_config(args)

    if not args.package:
        print("Ошибка: не указан пакет (--package).")
        return

    print("\n=== Построение графа ===")

    # Если указан --repo, передаем путь в функцию (тестовый режим)
    # Если нет - функция пойдет в интернет
    graph = build_graph(args.package, args.version, args.repo)

    if args.ascii:
        print("\n=== Граф зависимостей (ASCII) ===")
        print_ascii_tree(graph, args.package)


if __name__ == "__main__":
    main()
