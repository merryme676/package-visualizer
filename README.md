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

## Проверка стиля
```bash
make lint
```

## Этапы разработки

[x] Этап 1. Минимальный прототип с конфигурацией
[ ] Этап 2. Сбор данных
[ ] Этап 3. Основные операции
[ ] Этап 4. Дополнительные операции
[ ] Этап 5. Визуализация
