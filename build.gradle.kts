plugins {
    java
    id("org.springframework.boot") version "3.3.4"
    id("io.spring.dependency-management") version "1.1.6"
}

group = "com.example"
version = "0.0.1-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")

    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.withType<JavaCompile> {
    // Compile bytecode for Java 21 using the JDK that Gradle itself runs on
    // (not necessarily version 21 — it just must not be older).
    // This removes the need for toolchain plugins that auto-download the JDK
    // (org.gradle.toolchains.foojay-resolver-convention failed with the error
    // "JvmVendorSpec does not have member field IBM_SEMERU" because the plugin
    // version is incompatible with Gradle 9.x).
    options.release.set(21)
}

tasks.withType<Test> {
    useJUnitPlatform()
}
