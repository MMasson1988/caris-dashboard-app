# Deployment script for shinyapps.io
# This script should be run in R to deploy the application

# Install rsconnect if not already installed
if (!require(rsconnect)) {
  install.packages("rsconnect")
  library(rsconnect)
}

# Configure rsconnect (you'll need to add your own account information)
# rsconnect::setAccountInfo(name="your-account-name",
#                          token="your-token",
#                          secret="your-secret")

# Deploy the application
# rsconnect::deployApp(appDir = ".", 
#                     appName = "caris-dashboard",
#                     account = "your-account-name")

cat("To deploy this app to shinyapps.io:\n")
cat("1. Sign up for a free account at https://www.shinyapps.io/\n")
cat("2. Install rsconnect package: install.packages('rsconnect')\n")
cat("3. Configure your account using rsconnect::setAccountInfo()\n")
cat("4. Run rsconnect::deployApp() from this directory\n")
cat("\nFor detailed instructions, see: https://docs.rstudio.com/shinyapps.io/getting-started.html\n")