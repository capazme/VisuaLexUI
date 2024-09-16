@echo off
setlocal

REM Funzione per aggiornare la versione
:UPDATE_VERSION
    set "level=%1"
    set "version_file=version.txt"

    REM Leggi la versione attuale
    for /f "delims=" %%v in (%version_file%) do set "current_version=%%v"
    for /f "tokens=1-3 delims=." %%a in ("%current_version%") do (
        set "major=%%a"
        set "minor=%%b"
        set "patch=%%c"
    )

    REM Aggiorna la versione
    if "%level%"=="-maj" (
        set /a major+=1
        set "minor=0"
        set "patch=0"
    ) else if "%level%"=="-min" (
        set /a minor+=1
        set "patch=0"
    ) else if "%level%"=="-patch" (
        set /a patch+=1
    ) else (
        echo Opzione non valida. Usa -maj, -min o -patch.
        exit /b 1
    )

    REM Scrivi la nuova versione nel file
    set "new_version=%major%.%minor%.%patch%"
    echo %new_version% > "%version_file%"

    echo Versione aggiornata a %new_version%
    exit /b 0

REM Funzione per pulire la build precedente
:CLEAN_PREVIOUS_BUILD
    echo Pulizia delle cartelle di build precedenti...
    rmdir /s /q build
    rmdir /s /q dist
    del /q *.spec
    echo Pulizia completata.
    exit /b 0

REM Funzione per costruire l'applicazione
:BUILD_APP
    set /p version=<version.txt
    set "output_name=VisualexApp-v%version%"

    REM Esegui il comando PyInstaller
    pyinstaller --onedir --windowed --add-data "src/visualex_ui/resources;visualex_ui/resources" --name "%output_name%" --icon "C:\Users\guglielmo\Desktop\CODE\VISUALEX\VisuaLexUI\icon.icns" --noconfirm src\main.py

    echo Build completato. Il file si trova nella cartella dist\%output_name%
    exit /b 0

REM Controlla se è stato passato un argomento per aggiornare la versione
if "%1"=="-maj" (
    call :UPDATE_VERSION -maj
) else if "%1"=="-min" (
    call :UPDATE_VERSION -min
) else if "%1"=="-patch" (
    call :UPDATE_VERSION -patch
)

REM Pulizia della build precedente
call :CLEAN_PREVIOUS_BUILD

REM Costruisci l'app
call :BUILD_APP
