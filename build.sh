#!/bin/bash

# Imposta il percorso della directory dello script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Funzione per aggiornare la versione
update_version() {
    local level=$1
    local version_file="$SCRIPT_DIR/src/visualex_ui/resources/version.txt"
    
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
    local version=$(cat "$SCRIPT_DIR/src/visualex_ui/resources/version.txt")
    local output_name="VisualexApp-v$version"
    local icon_path="$SCRIPT_DIR/src/visualex_ui/resources/icon.icns"  # Percorso dinamico dell'icona

    # Pulizia della build precedente
    clean_previous_build

    # Esegui il comando PyInstaller
    pyinstaller --onedir --windowed \
        --add-data "$SCRIPT_DIR/src/visualex_ui/resources:visualex_ui/resources" \
        --name "$output_name" --icon "$icon_path" \
        --noconfirm "$SCRIPT_DIR/src/main.py"

    # Controlla se la build è stata creata correttamente
    if [ -d "$SCRIPT_DIR/dist/$output_name" ]; then
        # Cerca il file .app nella cartella di output
        app_path="$SCRIPT_DIR/dist/$output_name.app"

        # Controlla se il file .app esiste
        if [ -e "$app_path" ]; then
            # Verifica che il file .app non sia già presente nella directory di destinazione
            if [ -e "$SCRIPT_DIR/$output_name.app" ]; then
                echo "Rimuovo il file esistente $output_name.app"
                rm -rf "$SCRIPT_DIR/$output_name.app"
            fi

            # Sposta il file .app fuori dalla cartella dist
            echo "Sposto il file .app fuori dalla cartella dist..."
            mv "$app_path" "$SCRIPT_DIR/$output_name.app"

            # Verifica se il movimento è riuscito
            if [ $? -eq 0 ]; then
                # Cancella le cartelle di build e il file .spec
                rm -rf "$SCRIPT_DIR/dist/"
                rm -rf "$SCRIPT_DIR/build/"
                rm -f "$SCRIPT_DIR/$output_name.spec"

                echo "Build completato. L'applicazione si trova in $SCRIPT_DIR/$output_name.app"
            else
                echo "Errore durante lo spostamento del file .app."
            fi
        else
            echo "Errore: Il file $output_name.app non è stato trovato nella cartella dist. La build potrebbe essere fallita."
        fi
    else
        echo "Errore: Non è stato possibile trovare la cartella dist/$output_name. La build potrebbe essere fallita."
    fi
}

# Controlla se è stato passato un argomento per aggiornare la versione
if [ "$1" == "-maj" ] || [ "$1" == "-min" ] || [ "$1" == "-patch" ]; then
    update_version "$1"
fi

# Costruisci l'app
build_app
