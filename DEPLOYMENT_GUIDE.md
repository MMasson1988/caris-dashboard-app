# CARIS Dashboard - Deployment Guide for shinyapps.io

## Overview
This R Shiny application provides an interactive dashboard for tracking beneficiaries of the CARIS project gardening component. It replicates the functionality of the original Python Streamlit application.

## Files for Deployment

### Core Application Files
- `app.R` - Main Shiny application file
- `all_gardens.xlsx` - Data file (gardening beneficiaries data)
- `install_packages.R` - Package installation script
- `manifest.json` - Deployment manifest for shinyapps.io
- `renv.lock` - Package environment lock file

### Deployment Steps for shinyapps.io

#### 1. Install Required R Packages Locally
```r
# Run this in R/RStudio
source("install_packages.R")
```

#### 2. Test Application Locally
```r
# Run this in R/RStudio to test
shiny::runApp("app.R")
```

#### 3. Deploy to shinyapps.io

**Option A: Using RStudio IDE**
1. Open `app.R` in RStudio
2. Click the "Publish" button in the upper right
3. Select "Publish to Server"
4. Choose your shinyapps.io account
5. Select files to include: `app.R`, `all_gardens.xlsx`, `install_packages.R`
6. Click "Publish"

**Option B: Using rsconnect package**
```r
# Install rsconnect if not already installed
install.packages("rsconnect")
library(rsconnect)

# Configure your shinyapps.io account (one-time setup)
rsconnect::setAccountInfo(name='your-account-name',
                         token='your-token',
                         secret='your-secret')

# Deploy the app
rsconnect::deployApp(appDir = ".",
                    appName = "caris-dashboard",
                    appTitle = "CARIS Dashboard - Suivi des Bénéficiaires")
```

**Option C: Using Command Line (with rsconnect-python)**
```bash
# Install rsconnect-python
pip install rsconnect-python

# Configure account
rsconnect add --account your-account --name your-account --token your-token --secret your-secret --server shinyapps.io

# Deploy
rsconnect deploy shiny --name your-account --title "CARIS Dashboard" .
```

## Application Features

### Data Loading
- Automatically loads `all_gardens.xlsx` file
- Handles missing file gracefully with warning message
- Supports Excel files with standard gardening data structure

### Filtering Options
- **Office Selection**: Multi-select dropdown for filtering by office
- **Date Range**: Date picker for filtering by start_date column
- Filters are applied reactively to all visualizations

### Visualizations
- **Data Table**: Interactive table with pagination and search
- **Statistics Cards**: Total beneficiaries, average age, cycle 4 started count
- **Department Histogram**: Bar chart showing distribution by department
- **Time Evolution**: Line chart showing beneficiaries over time
- **Map** (conditional): Shows geographic distribution if latitude/longitude available

### Export Functionality
- Download filtered data as Excel file
- File naming includes current date
- Preserves all filtering applied by user

## Data Requirements

### Expected Excel File Structure
The `all_gardens.xlsx` file should contain these columns:
- `office` - Office/location identifier
- `start_date` - Start date for cycle 4 (Date format)
- `departement` - Department/region name
- `age` - Beneficiary age (numeric)
- `latitude` - Geographic latitude (optional, for mapping)
- `longitude` - Geographic longitude (optional, for mapping)

### Data Preparation Tips
- Ensure dates are in proper Excel date format
- Remove any completely empty rows
- Verify column names match expected structure
- Check for special characters that might cause encoding issues

## Troubleshooting

### Common Issues
1. **Package Installation Errors**: Ensure R version compatibility
2. **Data Loading Issues**: Check Excel file format and column names
3. **Deployment Timeouts**: Large data files may need optimization
4. **Memory Issues**: Consider data sampling for very large datasets

### Dependencies
- R version 4.0 or higher recommended
- All packages listed in `install_packages.R`
- Stable internet connection for deployment

## Customization

### Styling
- Dashboard uses green theme (#28a745) matching CARIS branding
- Responsive layout adapts to different screen sizes
- Custom CSS can be added to `ui` section

### Adding New Features
- Additional filters can be added to sidebar
- New visualization types supported through plotly
- Export formats can be extended (CSV, PDF, etc.)

## Support
For deployment issues:
- Check shinyapps.io documentation
- Verify account limits and usage
- Contact system administrator for access credentials