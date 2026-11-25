#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DIR"
cat > "$APP_DIR/cidade-viva.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Cidade Viva
Comment=Simulador de civilização
Exec=python3 "$ROOT/scripts/launcher.py"
Icon=$ROOT/frontend/public/assets/icon.png
Terminal=false
Categories=Game;Simulation;
StartupNotify=true
EOF
chmod +x "$APP_DIR/cidade-viva.desktop"
printf 'Atalho instalado no menu de aplicativos.\n'
