# Задача: доработать демо-проект LangGraph под доклад

Корень проекта: `D:\Programming\AI projects\LangGraph`. Пайплайн лежит в `LangGraph/`, Spring Boot-приложение, над которым он работает, — в `application/`.

## Ограничения
- Никаких платных или облачных сервисов: без LangSmith, LangGraph Studio и LangGraph Platform. Только локальные и бесплатные средства.
- Содержимое `application/` не менять: текущее состояние (Spring Boot 3.3.4, `options.release(21)`) — исходная точка демо-задачи «Upgrade the project to Java 25 and the latest Spring Boot 3.5.x».
- Стиль как в существующем коде: pyright strict (`pyrightconfig.json`), строки и комментарии на английском, комментарии только к неочевидным местам.
- Полный прогон пайплайна не запускать: он идёт 20+ минут и тратит API. Проверять импортом, компиляцией графа и pyright.
- Сохранить эти имена: по ним сделан слайд презентации.

## 1. Пауза на подтверждение человеком
- `graph.py`: новый узел `human_approval`:

  ```python
  def human_approval(state: BackendState) -> dict[str, Any]:
      answer = interrupt("Reviewer approved. Accept the changes?")
      return {"human_approved": answer == "yes"}
  ```

- `route_after_review`: при одобрении ведёт в `human_approval`. При исчерпании раундов, как и сейчас, ведёт в `END`. Из `human_approval` — в `END` при любом ответе.
- `backend_state.py`: добавить `human_approved: NotRequired[bool]`.

## 2. Сохранение состояния
- Установить `langgraph-checkpoint-sqlite` в `LangGraph/.venv`.
- `build_graph(checkpointer: BaseCheckpointSaver | None = None)` передаёт его в `builder.compile(checkpointer=...)`.
- `main.py` использует `SqliteSaver(sqlite3.connect("demo.db", check_same_thread=False))`.

## 3. Режимы main.py
- `python main.py [--thread <id>] "<task>"` — новый прогон. Если `--thread` не задан, сгенерировать id и напечатать его в начале.
- Когда стрим дошёл до `interrupt`, напечатать вопрос и подсказку: `waiting for approval — resume with: python main.py --resume <id> [--answer yes|no]`.
- `python main.py --resume <id> [--answer yes|no]` (по умолчанию `yes`):
  - если поток стоит на interrupt — продолжить через `Command(resume=answer)`;
  - если процесс упал посреди прогона — продолжить с последнего чекпоинта через `graph.stream(None, config)`.
- `python main.py --history <id>` — печать `graph.get_state_history(config)`: по строке на чекпоинт (шаг, следующие узлы, `build_attempts`, `review_rounds`, `compile_status`, `review_approved`).
- Текущий формат вывода шагов (`print_message`, `print_build`, `print_review`) не менять.

## 4. Сводка по прогону
В конце каждого запуска (новый прогон или `--resume`) печатать таблицу по узлам: сколько раз запускался, суммарное время, input/output токены. Токены брать из `usage_metadata` у `AIMessage` agent и reviewer, время — по интервалам между обновлениями стрима. Это замена трассировки LangSmith.

## 5. Картинка графа
`python main.py --draw` сохраняет `graph.mmd` из `build_graph().get_graph().draw_mermaid()`. Только текст Mermaid, без внешних сервисов рендеринга.

## 6. Таймаут сборки
`nodes/gradle_build.py`: перехватывать `subprocess.TimeoutExpired` и возвращать упавшую сборку (`compile_status: False`, увеличенный `build_attempts`, сообщение агенту `Gradle build timed out after N s`), а не ронять граф.

## 7. Защита путей
`tools.py`: `write_file` отказывает (`ToolException`) при записи в `gradlew`, `gradlew.bat` и `gradle/wrapper/*`. Чтение этих файлов оставить.

## 8. Git для сброса application/
- `git init` в `application/`, закоммитить текущее состояние как baseline. `.gitignore` там уже есть — проверить, что `build/` и `.gradle/` игнорируются.
- Команда сброса перед прогоном: `git -C application reset --hard && git -C application clean -fdx`.

## 9. Файлы для переноса на другую машину
- `LangGraph/requirements.txt` с точными версиями прямых зависимостей из `.venv` (`pip freeze`): langgraph, langchain, langchain-core, langchain-anthropic, langgraph-checkpoint-sqlite, python-dotenv.
- `LangGraph/.gitignore`: `.env`, `.venv/`, `__pycache__/`, `demo.db`, `graph.mmd`.
- `LangGraph/README.md`:
  - требования: Windows, JDK 25, Python 3.14, `ANTHROPIC_API_KEY` в `.env`;
  - какие хосты должны быть доступны: `api.anthropic.com`, `repo1.maven.org`, `plugins.gradle.org`, `services.gradle.org`;
  - установка;
  - сценарий демо по шагам: сброс application → запуск → `--history` → `--resume`.

## Проверка
- `python -c "from graph import build_graph; build_graph()"` — без ошибок.
- `python main.py --draw` создаёт `graph.mmd` с узлом `human_approval`.
- pyright без новых ошибок.

## В конце
Выведи список изменённых файлов, итоговый `graph.py` целиком и команды запуска всех режимов `main.py`.