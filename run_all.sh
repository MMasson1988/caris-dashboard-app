#!/bin/bash

# ================================
# 🚀 SCRIPT D'EXÉCUTION AUTOMATIQUE
# - 4 scripts Python
# - 4 fichiers Quarto
# - Gestion des erreurs par fichier
# ================================

echo "🔁 Début de l'exécution globale"
echo "📅 Date : $(date)"
echo "-------------------------------"

# ========== PYTHON ==========
echo "🐍 [1/2] Exécution des scripts Python..."

PY_SCRIPTS=("oev_pipeline.py" "nutrition_pipeline.py" "ptme_pipeline.py" "garden_pipeline.py")
FAILED_PY=()

for file in "${PY_SCRIPTS[@]}"; do
    echo "⚙️ Exécution : $file"
    
    # Remplacer python3 par python (compatible Windows)
    python "$file"
    
    if [ $? -ne 0 ]; then
        echo "❌ Échec : $file"
        FAILED_PY+=("$file")
    else
        echo "✅ Succès : $file"
    fi
done

# ========== QUARTO ==========
echo ""
echo "📝 [2/2] Rendu des fichiers Quarto..."

QMD_FILES=("tracking-ptme.qmd" "tracking-nutrition.qmd" "tracking-oev.qmd" "tracking-gardening.qmd")
FAILED_QMD=()

for file in "${QMD_FILES[@]}"; do
    echo "📄 Rendu : $file"
    quarto render "$file"
    if [ $? -ne 0 ]; then
        echo "❌ Échec : $file"
        FAILED_QMD+=("$file")
    else
        echo "✅ Succès : $file"
    fi
done

# ========== RAPPORT FINAL ==========
echo ""
echo "==============================="
echo "📋 RAPPORT D'EXÉCUTION FINALE"
echo "==============================="

if [ ${#FAILED_PY[@]} -eq 0 ] && [ ${#FAILED_QMD[@]} -eq 0 ]; then
    echo "🎉 Tous les fichiers ont été exécutés avec succès."
else
    if [ ${#FAILED_PY[@]} -gt 0 ]; then
        echo "❌ Scripts Python échoués :"
        for f in "${FAILED_PY[@]}"; do echo "   - $f"; done
    fi
    if [ ${#FAILED_QMD[@]} -gt 0 ]; then
        echo "❌ Fichiers Quarto échoués :"
        for f in "${FAILED_QMD[@]}"; do echo "   - $f"; done
    fi
fi

echo "🔚 Fin du script."
