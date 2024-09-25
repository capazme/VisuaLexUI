@echo off
setlocal

REM Imposta il percorso della directory dello script
set "SCRIPT_DIR=%~dp0"

REM Funzione per controllare se Python è installato
:CHECK_PYTHON
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python non trovato. Installazione di Python...
        powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe -OutFile python_installer.exe"
        start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
        del python_installer.exe
        where python >nul 2>nul
        if errorlevel 1 (
            echo Errore: L'installazione di Python è fallita.
            exit /b 1
        )
        echo Python installato correttamente.
    ) else (
        echo Python è già installato.
    )
    goto :eof

REM Funzione per creare un ambiente virtuale se non esiste
:SETUP_VIRTUALENV
    if not exist "%SCRIPT_DIR%.venv" (
        echo Ambiente virtuale non trovato. Creazione di un nuovo ambiente virtuale...
        python -m venv "%SCRIPT_DIR%.venv"
        if errorlevel 1 (
            echo Errore: Creazione dell'ambiente virtuale fallita.
            exit /b 1
        )
        echo Ambiente virtuale creato.
    ) else (
        echo Ambiente virtuale già presente.
    )
    goto :eof

REM Funzione per attivare l'ambiente virtuale
:ACTIVATE_VIRTUALENV
    call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
    if errorlevel 1 (
        echo Errore: Attivazione dell'ambiente virtuale fallita.
        exit /b 1
    )
    goto :eof

REM Funzione per installare i requisiti
:INSTALL_REQUIREMENTS
    if not exist "%SCRIPT_DIR%requirements.txt" (
        echo Errore: Il file requirements.txt non esiste.
        exit /b 1
    )
    echo Installazione dei requisiti da requirements.txt...
    pip install -r "%SCRIPT_DIR%requirements.txt"
    if errorlevel 1 (
        echo Errore: Installazione dei requisiti fallita.
        exit /b 1
    )
    goto :eof

REM Funzione per aggiornare la versione
:UPDATE_VERSION
    set "level=%1"
    set "version_file=%SCRIPT_DIR%src\visualex_ui\resources\version.txt"

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
    goto :eof

REM Funzione per pulire la build precedente
:CLEAN_PREVIOUS_BUILD
    echo Pulizia delle cartelle di build precedenti...
    rmdir /s /q build
    rmdir /s /q dist
    del /q *.spec
    echo Pulizia completata.
    goto :eof

REM Funzione per costruire l'applicazione
:BUILD_APP
    set /p version=<"%SCRIPT_DIR%src\visualex_ui\resources\version.txt"
    set "output_name=VisualexApp-v%version%"
    set "icon_path=%SCRIPT_DIR%src\visualex_ui\resources\icon.icns"

    REM Pulizia della build precedente
    call :CLEAN_PREVIOUS_BUILD

    REM Esegui il comando PyInstaller
    pyinstaller --onedir --windowed --add-data "%SCRIPT_DIR%src\visualex_ui\resources;visualex_ui/resources" --name "%output_name%" --icon "%icon_path%" --noconfirm "%SCRIPT_DIR%src\main.py"

    REM Controlla se la build è stata creata correttamente
    if exist "dist\%output_name%\%output_name%.exe" (
        REM Verifica che il file .exe non sia già presente nella directory di destinazione
        if exist "%SCRIPT_DIR%\%output_name%.exe" (
            echo Rimuovo il file esistente %output_name%.exe
            del /q "%SCRIPT_DIR%\%output_name%.exe"
        )

        REM Sposta il file .exe fuori dalla cartella dist
        echo Sposto il file .exe fuori dalla cartella dist...
        move "dist\%output_name%\%output_name%.exe" "%SCRIPT_DIR%\%output_name%.exe"

        REM Cancella le cartelle di build e file .spec
        call :CLEAN_PREVIOUS_BUILD

        echo Build completato. L'applicazione si trova in %SCRIPT_DIR%\%output_name%.exe
    ) else (
        echo Errore: Non è stato possibile trovare il file dist\%output_name%\%output_name%.exe. La build potrebbe essere fallita.
    )
    goto :eof

REM Controlla se è stato passato un argomento per aggiornare la versione
if "%1"=="-maj" (
    call :UPDATE_VERSION -maj
) else if "%1"=="-min" (
    call :UPDATE_VERSION -min
) else if "%1"=="-patch" (
    call :UPDATE_VERSION -patch
)

REM Controllo se Python è installato
call :CHECK_PYTHON

REM Creazione e attivazione dell'ambiente virtuale
call :SETUP_VIRTUALENV
call :ACTIVATE_VIRTUALENV

REM Installazione dei requisiti
call :INSTALL_REQUIREMENTS

REM Costruisci l'app
call :BUILD_APP
