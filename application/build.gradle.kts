plugins {
    java
    id("org.springframework.boot") version "3.5.16"
    id("io.spring.dependency-management") version "1.1.7"
}

group = "com.example"
version = "0.0.1-SNAPSHOT"

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(25)
    }
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")

    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

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
