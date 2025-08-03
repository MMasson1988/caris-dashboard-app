# Test script to verify Shiny app functionality
library(shiny)
library(shinydashboard) 
library(DT)
library(dplyr)
library(ggplot2)
library(plotly)
library(readxl)

cat("Testing Caris Dashboard Shiny App...\n")

# Test 1: Check if app.R exists and loads
if (file.exists("app.R")) {
  cat("✓ app.R file found\n")
  
  tryCatch({
    source("app.R", echo = FALSE)
    cat("✓ app.R loads without errors\n")
  }, error = function(e) {
    cat("✗ Error loading app.R:", e$message, "\n")
  })
} else {
  cat("✗ app.R file not found\n")
}

# Test 2: Check if data file exists
if (file.exists("all_gardens.xlsx")) {
  cat("✓ Data file 'all_gardens.xlsx' found\n")
  
  tryCatch({
    data <- read_excel("all_gardens.xlsx")
    cat("✓ Data file loads successfully\n")
    cat("  - Rows:", nrow(data), "\n")
    cat("  - Columns:", ncol(data), "\n")
    if (ncol(data) > 0) {
      cat("  - Column names:", paste(names(data)[1:min(5, ncol(data))], collapse = ", "), "\n")
    }
  }, error = function(e) {
    cat("✗ Error reading data file:", e$message, "\n")
  })
} else {
  cat("✗ Data file 'all_gardens.xlsx' not found\n")
}

# Test 3: Check required packages
required_packages <- c("shiny", "shinydashboard", "DT", "dplyr", "ggplot2", "plotly", "readxl")
for (pkg in required_packages) {
  if (require(pkg, character.only = TRUE, quietly = TRUE)) {
    cat("✓ Package", pkg, "available\n")
  } else {
    cat("✗ Package", pkg, "not available\n")
  }
}

cat("\nTest completed. App should be ready for deployment to shinyapps.io\n")