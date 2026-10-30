"""Инструмент визуализации графа зависимостей (NuGet)."""

import argparse


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


def main():
    """Точка входа."""
    args = parse_args()
    print_config(args)


if __name__ == "__main__":
    main()
