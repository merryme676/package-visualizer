# Package Visualizer

Инструмент визуализации графа зависимостей для менеджера пакетов **.NET (NuGet)**.

## Требования

- Python 3.10+
- macOS / Linux

## Запуск

```bash
./run.sh
```

Или через Makefile:
```bash
make run
```

## Параметры командной строки

Параметр |	Описание |	Пример
--package |	Имя анализируемого пакета |	--package Newtonsoft.Json
--repo |	URL репозитория или путь к файлу |	--repo https://api.nuget.org
--mode |	Режим работы с тестовым репозиторием |	--mode test
--version |	Версия пакета |	--version 13.0.1
--output |	Имя файла с изображением графа |	--output graph.png
--ascii |	Режим вывода в формате ASCII-дерева |	--ascii

## Пример запуска со всеми параметрами:
```bash
./run.sh --package Newtonsoft.Json --version 13.0.1 --output graph.png --ascii
```

## Тестовый режим (Этап 3)

Для проверки алгоритма построения графа (DFS без рекурсии) без обращения к интернету предусмотрен тестовый режим.

1. В корне проекта находится файл `test_repo.txt` с тестовым графом.
2. Запустить программу, указав путь к этому файлу через параметр `--repo`:

## Примеры использования (Этапы 4 и 5)

Поиск обратных зависимостей (Этап 4):
Выводит пакеты, которые зависят от заданного.
```bash
./run.sh --package B --repo test_repo.txt --reverse
```

Визуализация и открытие в браузере (Этап 5):
Генерирует файл .puml, автоматически кодирует его и открывает готовую картинку графа в браузере.
```bash
./run.sh --package A --repo test_repo.txt --ascii --output graph.puml
```

Пример 1:
```bash
./run.sh --package Microsoft.NETCore.Platforms --version 7.0.0 --output first_graph.puml
```

Пример 2:
```bash
./run.sh --package FluentValidation --version 11.9.0 --output second_graph.puml
```

## Тесты
```bash
make test
```

## Проверка стиля
```bash
make lint
```


## Этапы разработки

- [x] Этап 1. Минимальный прототип с конфигурацией
- [x] Этап 2. Сбор данных
- [x] Этап 3. Основные операции
- [x] Этап 4. Дополнительные операции
- [x] Этап 5. Визуализация
