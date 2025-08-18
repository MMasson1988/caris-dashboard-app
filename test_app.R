# test_app.R
# Simple test script to verify R environment and package setup

cat("=== CARIS Dashboard Test Script ===\n")

# Test 1: Check R version
cat("1. Checking R version...\n")
cat(paste("R version:", R.Version()$version.string, "\n"))

# Test 2: Check if required packages can be loaded
cat("\n2. Testing package availability...\n")
required_packages <- c("shiny", "shinydashboard", "DT", "plotly", "readxl", "dplyr", "lubridate", "openxlsx")

missing_packages <- c()
for (pkg in required_packages) {
  if (require(pkg, character.only = TRUE, quietly = TRUE)) {
    cat(paste("✓", pkg, "- OK\n"))
  } else {
    cat(paste("✗", pkg, "- MISSING\n"))
    missing_packages <- c(missing_packages, pkg)
  }
}

# Test 3: Check if data file exists
cat("\n3. Checking data file...\n")
if (file.exists("all_gardens.xlsx")) {
  cat("✓ all_gardens.xlsx - Found\n")
  
  # Try to read the file
  tryCatch({
    library(readxl)
    df <- read_excel("all_gardens.xlsx", n_max = 5)
    cat(paste("✓ Data file readable, columns:", paste(names(df), collapse = ", "), "\n"))
    cat(paste("✓ Sample rows:", nrow(df), "\n"))
  }, error = function(e) {
    cat("✗ Error reading data file:", e$message, "\n")
  })
} else {
  cat("⚠ all_gardens.xlsx - Not found (will show warning in app)\n")
}

# Test 4: Quick app structure test
cat("\n4. Testing app structure...\n")
if (file.exists("app.R")) {
  cat("✓ app.R - Found\n")
  
  # Check if app can be parsed
  tryCatch({
    source("app.R", local = TRUE)
    cat("✓ app.R syntax - OK\n")
  }, error = function(e) {
    cat("✗ app.R syntax error:", e$message, "\n")
  })
} else {
  cat("✗ app.R - Not found\n")
}

# Summary
cat("\n=== TEST SUMMARY ===\n")
if (length(missing_packages) == 0) {
  cat("✓ All required packages available\n")
} else {
  cat("✗ Missing packages:", paste(missing_packages, collapse = ", "), "\n")
  cat("Run: source('install_packages.R') to install missing packages\n")
}

cat("\n=== DEPLOYMENT READINESS ===\n")
if (length(missing_packages) == 0 && file.exists("app.R")) {
  cat("✓ Ready for deployment to shinyapps.io!\n")
  cat("Next steps:\n")
  cat("1. Test locally: shiny::runApp('app.R')\n")
  cat("2. Deploy: rsconnect::deployApp()\n")
} else {
  cat("⚠ Fix issues above before deployment\n")
}

cat("\nTest completed.\n")