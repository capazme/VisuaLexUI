#!/bin/bash

# Imposta il percorso della directory dello script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Funzione per aggiornare la versione
update_version() {
    local level=$1
    local version_file="$SCRIPT_DIR/version.txt"
    
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
    local version=$(cat "$SCRIPT_DIR/version.txt")
    local output_name="VisualexApp-v$version"
    local icon_path="$SCRIPT_DIR/src/visualex_ui/resources/icon.icns"  # Percorso dinamico dell'icona

    # Esegui il comando PyInstaller
    pyinstaller --onedir --windowed --add-data "$SCRIPT_DIR/src/visualex_ui/resources:visualex_ui/resources" \
        --name "$output_name" --icon "$icon_path" \
        --noconfirm "$SCRIPT_DIR/src/main.py"

    # Sposta l'applicazione fuori dalla cartella dist
    mv "$SCRIPT_DIR/dist/$output_name/$output_name.app" "$SCRIPT_DIR/$output_name.app"
    
    # Cancella le cartelle di build e il file .spec
    clean_previous_build

    echo "Build completato. L'applicazione si trova in $SCRIPT_DIR/$output_name.app"
}

# Controlla se è stato passato un argomento per aggiornare la versione
if [ "$1" == "-maj" ] || [ "$1" == "-min" ] || [ "$1" == "-patch" ]; then
    update_version "$1"
fi

# Costruisci l'app
build_app
