#!/bin/bash

# Funzione per aggiornare la versione
update_version() {
    local level=$1
    local version_file="version.txt"
    
    # Leggi la versione attuale
    current_version=$(cat "$version_file")
    IFS='.' read -r major minor patch <<< "$current_version"
    
    # Aggiorna la versione
    case $level in
        -maj)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        -min)
            minor=$((minor + 1))
            patch=0
            ;;
        -patch)
            patch=$((patch + 1))
            ;;
        *)
            echo "Opzione non valida. Usa -maj, -min o -patch."
            exit 1
            ;;
    esac
    
    # Scrivi la nuova versione nel file
    new_version="$major.$minor.$patch"
    echo "$new_version" > "$version_file"
    
    echo "Versione aggiornata a $new_version"
}

# Funzione per pulire la build precedente
clean_previous_build() {
    echo "Pulizia delle cartelle di build precedenti..."
    rm -rf build/
    rm -rf dist/
    rm -rf *.spec
    echo "Pulizia completata."
}

# Funzione per costruire l'applicazione
build_app() {
    local version=$(cat version.txt)
    local output_name="VisualexApp-v$version"
    
    # Esegui il comando PyInstaller
    pyinstaller --onedir --windowed --add-data "src/visualex_ui/resources:visualex_ui/resources" \
        --name "$output_name" --icon /Users/guglielmo/Desktop/CODE/VISUALEX/VisuaLexUI/icon.icns \
        --noconfirm src/main.py

    # Sposta l'applicazione fuori dalla cartella dist
    mv "dist/$output_name.app" "./$output_name.app"
    
    # Cancella le cartelle di build e il file .spec
    clean_previous_build

    echo "Build completato. L'applicazione si trova in $PWD/$output_name.app"
}

# Controlla se è stato passato un argomento per aggiornare la versione
if [ "$1" == "-maj" ] || [ "$1" == "-min" ] || [ "$1" == "-patch" ]; then
    update_version "$1"
fi

# Costruisci l'app
build_app
