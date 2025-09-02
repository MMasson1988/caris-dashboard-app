#!/bin/bash
# setup_r_environment.sh
# Setup script for CARIS Dashboard R environment

echo "=== CARIS Dashboard Setup Script ==="
echo "This script will help you prepare the R environment for deployment"

# Check if R is installed
if command -v R &> /dev/null; then
    echo "✓ R is installed"
    R --version | head -1
else
    echo "✗ R is not installed"
    echo "Please install R from: https://cran.r-project.org/"
    echo "For Ubuntu/Debian: sudo apt-get install r-base"
    echo "For macOS: brew install r"
    echo "For Windows: Download from CRAN website"
    exit 1
fi

# Check if RStudio is available (optional)
if command -v rstudio &> /dev/null; then
    echo "✓ RStudio is available"
else
    echo "ℹ RStudio not found (optional but recommended)"
    echo "Install from: https://rstudio.com/products/rstudio/download/"
fi

echo ""
echo "=== Next Steps ==="
echo "1. Open R or RStudio"
echo "2. Set working directory to this folder"
echo "3. Run: source('install_packages.R')"
echo "4. Run: source('test_app.R')"
echo "5. Test locally: shiny::runApp('app.R')"
echo "6. Deploy to shinyapps.io following DEPLOYMENT_GUIDE.md"

echo ""
echo "=== Files Created ==="
echo "✓ app.R - Main Shiny application"
echo "✓ app_simple.R - Simplified version (fallback)"
echo "✓ install_packages.R - Package installation"
echo "✓ test_app.R - Environment test script"
echo "✓ DEPLOYMENT_GUIDE.md - Complete deployment instructions"
echo "✓ manifest.json - Deployment manifest"
echo "✓ renv.lock - Package lock file"

echo ""
echo "Setup script completed!"