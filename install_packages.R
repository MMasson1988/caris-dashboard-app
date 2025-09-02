# install_packages.R
# Script to install required R packages for CARIS Dashboard

# List of required packages
packages <- c(
  "shiny",
  "shinydashboard", 
  "DT",
  "plotly",
  "readxl",
  "dplyr",
  "lubridate",
  "openxlsx"
)

# Function to install packages if not already installed
install_if_missing <- function(packages) {
  for (pkg in packages) {
    if (!require(pkg, character.only = TRUE)) {
      cat(paste("Installing package:", pkg, "\n"))
      install.packages(pkg, dependencies = TRUE, repos = "https://cran.rstudio.com/")
      library(pkg, character.only = TRUE)
    } else {
      cat(paste("Package", pkg, "already installed\n"))
    }
  }
}

# Install packages
cat("Installing required packages for CARIS Dashboard...\n")
install_if_missing(packages)
cat("All packages installed successfully!\n")