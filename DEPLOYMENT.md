# Deployment to shinyapps.io

This directory contains an R Shiny version of the Caris Dashboard application, ready for deployment to shinyapps.io.

## Files for Deployment

- `app.R` - Main Shiny application file
- `all_gardens.xlsx` - Data file used by the application
- `deploy.R` - Deployment helper script
- Additional Excel files with program data

## Deployment Instructions

1. **Create a shinyapps.io account**
   - Go to https://www.shinyapps.io/
   - Sign up for a free account

2. **Install rsconnect package** (if not already installed)
   ```r
   install.packages("rsconnect")
   ```

3. **Configure your account**
   - Go to your shinyapps.io dashboard
   - Click on your name in the top right → Tokens
   - Click "Show" next to a token to see your account info
   - In R, run:
   ```r
   rsconnect::setAccountInfo(name="your-account-name",
                            token="your-token", 
                            secret="your-secret")
   ```

4. **Deploy the application**
   ```r
   # Set working directory to this folder
   setwd("/path/to/caris-dashboard-app")
   
   # Deploy the app
   rsconnect::deployApp(appDir = ".", 
                       appName = "caris-dashboard",
                       account = "your-account-name")
   ```

## Application Features

The Shiny app includes:
- Interactive dashboard with filters for offices and date ranges
- Statistics overview (total beneficiaries, average age, cycle 4 progress)
- Charts showing distribution by department and time evolution
- Data table view with download functionality
- Responsive design using shinydashboard

## Data Requirements

The application expects an Excel file named `all_gardens.xlsx` with columns:
- `office` - Office locations
- `start_date` - Start dates for cycle 4
- `age` - Beneficiary ages
- `departement` - Department/region information

## Troubleshooting

- Ensure all required packages are included in the deployment
- Check that data files are present and readable
- Verify account credentials are correct
- Check shinyapps.io dashboard for deployment logs

For more detailed information, see the [shinyapps.io documentation](https://docs.rstudio.com/shinyapps.io/getting-started.html).