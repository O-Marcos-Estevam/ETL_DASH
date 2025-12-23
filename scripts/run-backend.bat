@echo off
echo ============================================================
echo   ETL Dashboard V2 - Backend Java (DEV MODE)
echo ============================================================
echo.

pushd "%~dp0.."
set "ROOT_DIR=%CD%"
popd

set "JAVA_HOME=%ROOT_DIR%\java\jdk-17.0.2"
set "MAVEN_HOME=%ROOT_DIR%\maven\apache-maven-3.9.6"
set "PATH=%JAVA_HOME%\bin;%MAVEN_HOME%\bin;%PATH%"

cd /d "%ROOT_DIR%\backend"
echo Iniciando Spring Boot (mvn spring-boot:run)...
call "%MAVEN_HOME%\bin\mvn.cmd" spring-boot:run
pause
