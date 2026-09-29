# Project conventions

These rules are shared by the developer and the reviewer. They refine the best practices above and take precedence over them.

## 1. Priorities

When rules conflict, the one higher on the list wins:

1. **The task text and the human's answers.** Paths, names, versions, formats and response codes from the task are followed literally. An answer received via `ask_human` clarifies the task and has the same weight.
2. **These conventions.**
3. **General best practices** from the prompt above. They are the default rules for whatever the task and the conventions don't define.

Example: the task says `GET /hello`, so the endpoint is exactly `/hello`, without `/api/v1`, even though the best practices recommend versioning.

## 2. Working environment

- You work in an automated pipeline. Final messages are not read by a human during the run: don't ask questions or request confirmation in them.
- You can't run commands (gradle, mvn, git, java). Only the provided tools are available. The rules above about running `./mvnw` or `./gradlew` don't apply.
- Paths in tools are relative to the project root, without a leading `/`: `build.gradle.kts`, `src/main/java/...`.
- The pipeline checks the project in two steps: `gradlew.bat assemble testClasses testIntegrationClasses` (compiles the code and both test source sets), then `gradlew.bat test testIntegration` (runs all tests). The task names `test` and `testIntegration` are fixed: if one of them is missing, the check fails (section 7).
- If something is missing from the task, choose a solution according to these conventions and record it as an assumption.

## 3. Stack and versions

- **Java 25.** The version is set only via the toolchain:
  ```kotlin
  java {
      toolchain {
          languageVersion = JavaLanguageVersion.of(25)
      }
  }
  ```
  Don't use `options.release`, `sourceCompatibility`/`targetCompatibility` or the `foojay-resolver` plugin: JDK 25 is installed locally, and Gradle finds it on its own.
- **Build:** Gradle Kotlin DSL (`build.gradle.kts`, `settings.gradle.kts`) and the Gradle Wrapper that is already in the project. Don't touch the `gradlew`, `gradlew.bat`, `gradle/wrapper/*` files. Don't use Maven.
- **Spring Boot:** the latest version of the 3.5.x line. Move to 4.x only if the task explicitly requires it: the test packages moved in 4.x, and the upgrade is a separate migration.
- **Plugin** `io.spring.dependency-management`. For dependencies whose versions Spring Boot manages, don't specify a version.
- **Plugin and library versions** are taken only via `get_library_version`, not from memory.
- **Don't downgrade** versions that are specified in the task or already chosen in the project. If a requirement can't be met, don't work around it silently: state plainly in the final message what didn't work and why.
- **New dependencies** — only if the task can't be solved without them. Prefer Spring Boot starters. Don't use Lombok: use `record` and plain constructors instead.

## 4. Project structure

- **The base package** already exists in the project — use it. For a new project: `com.example.<service name without hyphens>`.
- **The main class** `@SpringBootApplication` lives in the base package.
- **Code for new features** goes into per-feature subpackages: `<base package>.<feature>`, e.g. `com.example.hello.greeting`. If the project already uses a different structure, follow it. Don't move existing classes unless the task requires it.
- **Class names:**
  - `XxxController`, `XxxService`, `XxxRepository`;
  - DTOs: `XxxRequest`, `XxxResponse`;
  - exceptions: `XxxNotFoundException` and similar;
  - configuration: `XxxProperties` (`@ConfigurationProperties`), `XxxConfig` (`@Configuration`).
- **Configuration** — only `src/main/resources/application.yml` (YAML, not `.properties`).

## 5. REST API

- **Paths, HTTP methods, JSON field names and response codes** — exactly as in the task.
- **If the task doesn't specify a path:** `/api/v1/<resource in plural>`.
- **The response** is always a JSON object (a DTO `record`), not a bare string. Fields in `camelCase`.
- **Errors** — `ProblemDetail` via a single `@RestControllerAdvice`. Don't send the stack trace to the client.
- **Input** — `@Valid` + Jakarta Validation. Validation error → 400.
- **Response codes:** 200 (read), 201 + `Location` header (create), 204 (delete), 400 (invalid request), 404 (not found), 409 (conflict).

## 6. Code

- **Dependency injection** — constructor only, `private final` fields, no `@Autowired`.
- **DTOs** — `record`. Don't expose JPA entities.
- **Business logic** goes in the service; the controller is thin. Don't create layers just for show: if an endpoint simply returns a constant, a separate service isn't needed.
- **`var`** — only if the type is obvious from the right-hand side.
- **Logging** — SLF4J (`LoggerFactory.getLogger`), no `System.out`.
- **Don't leave behind:** wildcard imports, unused classes and dependencies, commented-out code, `TODO` stubs.
- **Comments** explain "why", not "what".

## 7. Tests

Tests are split between two Gradle tasks. The pipeline runs both, so the task names, folders and class name suffixes are fixed:

| Task | Folder | Class name | What goes there |
|---|---|---|---|
| `test` | `src/test/java` | `XxxTest` | Tests without the full application context: plain unit tests and `@WebMvcTest` slices. |
| `testIntegration` | `src/testIntegration/java` | `XxxIT` | Tests with the full application context: `@SpringBootTest`, real HTTP. |

- **Setup in `build.gradle.kts`** — exactly this block. The JVM Test Suite plugin built into Gradle creates the `testIntegration` source set and task; `testIntegration` gets all dependencies of `test`:
  ```kotlin
  testing {
      suites {
          register<JvmTestSuite>("testIntegration") {
              dependencies {
                  implementation(project())
              }
          }
      }
  }

  configurations {
      named("testIntegrationImplementation") { extendsFrom(testImplementation.get()) }
      named("testIntegrationRuntimeOnly") { extendsFrom(testRuntimeOnly.get()) }
  }

  tasks.withType<Test> {
      useJUnitPlatform()
  }

  tasks.check {
      dependsOn(testing.suites.named("testIntegration"))
  }
  ```
  Test dependencies are declared as `testImplementation` / `testRuntimeOnly`, including `testRuntimeOnly("org.junit.platform:junit-platform-launcher")`. Don't set up tests in any other way (a `sourceSets` block, your own `Test` tasks) and don't rename the tasks or folders.
- **Tests in the wrong place:** if the project has `@SpringBootTest` or `*IT` classes in `src/test/java`, move them to `src/testIntegration/java` (same package) and name them `XxxIT`, even if the task doesn't mention tests. This takes precedence over "don't move existing classes" in section 4.
- **The project always has integration tests.** If there is no `testIntegration` suite or it runs no tests, the pipeline fails the check. Then set up the suite and write the tests: at least the smoke test below plus the moved `*IT` classes, even if the task doesn't mention tests.
- **Tests are JUnit 5** `@Test` methods. Gradle fails a test task that has test classes but finds no tests in them.
- **Every endpoint:** a `@WebMvcTest` + `MockMvc` slice test in `test`, dependencies via `@MockitoBean`. At minimum: the success scenario and every error the endpoint can return (400, 404, etc.).
- **A service with logic:** unit tests in `test` with JUnit 5 + AssertJ, without the Spring context.
- **The application:** one smoke test `XxxApplicationIT` in `testIntegration`: `@SpringBootTest` with an empty `contextLoads` method.
- **Tests with real HTTP** (`@SpringBootTest(webEnvironment = RANDOM_PORT)`) go in `testIntegration`, only if the task requires them or they already exist.
- **A failing test** is fixed at the cause. Change a test only if it contradicts the task; don't delete, disable (`@Disabled`) or weaken tests to make them pass.
- **Don't switch off test checks** in `build.gradle.kts`: no `failOnNoDiscoveredTests = false`, `ignoreFailures`, test filters or excludes.
- **Assertions** via AssertJ (`assertThat`), not `assertEquals`.
- **Test names:** `shouldReturnGreeting`, `shouldReturn404WhenOrderNotFound`. Inside — Given / When / Then blocks.
- **Tests are independent:** they don't depend on execution order, the network or external services. For databases — Testcontainers, not H2.

## 8. Done when

- The task is fully completed; paths, names and versions are as in the task.
- There are tests according to section 7.
- There are no violations of sections 3–6.
- The code and both test source sets compile, and the `test` and `testIntegration` tasks pass — the pipeline checks this.

## 9. Review rules

- **Criteria:** the task text and these conventions, not personal taste.
- **An issue is raised only if** it is one of:
  - the task is not fully completed or not done as written;
  - these conventions are violated;
  - a bug or a logic error;
  - a security problem;
  - required tests from section 7 are missing, are in the wrong task or folder, or were deleted, disabled or weakened, or test checks were switched off.
- **Not issues:**
  - style that the conventions don't regulate;
  - "it could also…";
  - functionality that isn't in the task;
  - moving existing code without a need;
  - requirements that contradict the task.
- **Each issue** starts with its source: `(task)`, `(conventions, section N)`, `(bug)`, `(security)`. Then: the file, what's wrong, how to fix it.
