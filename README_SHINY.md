# CARIS Dashboard - R Shiny Application

## Quick Start for shinyapps.io Deployment

This folder contains all the files needed to deploy the CARIS dashboard as an R Shiny application on shinyapps.io.

### 📁 Files Overview

| File | Purpose |
|------|---------|
| `app.R` | Main Shiny application (dashboard version) |
| `app_simple.R` | Simplified Shiny application (fallback) |
| `all_gardens.xlsx` | Data file for gardening beneficiaries |
| `install_packages.R` | Install required R packages |
| `test_app.R` | Test environment setup |
| `DEPLOYMENT_GUIDE.md` | Complete deployment instructions |
| `setup_r_environment.sh` | Environment setup script |
| `manifest.json` | Deployment manifest for shinyapps.io |
| `renv.lock` | Package environment lock file |

### 🚀 Quick Deployment Steps

#### Prerequisites
- R (version 4.0+) installed
- RStudio (recommended)
- shinyapps.io account

#### Step 1: Setup Environment
```bash
# Run setup script (Linux/macOS)
./setup_r_environment.sh
```

#### Step 2: Install R Packages
```r
# In R/RStudio
source("install_packages.R")
```

#### Step 3: Test Application
```r
# Test environment
source("test_app.R")

# Test app locally
shiny::runApp("app.R")
```

#### Step 4: Deploy to shinyapps.io
```r
# Install rsconnect if needed
install.packages("rsconnect")

# Configure account (one-time setup)
library(rsconnect)
rsconnect::setAccountInfo(name='your-account',
                         token='your-token', 
                         secret='your-secret')

# Deploy
rsconnect::deployApp(appName = "caris-dashboard")
```

### 🎯 Application Features

- **Interactive Filtering**: Filter by office and date range
- **Data Visualization**: Charts for department distribution and time trends
- **Statistics Dashboard**: Key metrics display
- **Data Export**: Download filtered data as Excel
- **Responsive Design**: Works on desktop and mobile
- **Error Handling**: Graceful handling of missing data files

### 📊 Data Requirements

The application expects an Excel file `all_gardens.xlsx` with these columns:
- `office` - Office/location identifier
- `start_date` - Start date for cycle 4
- `departement` - Department/region name
- `age` - Beneficiary age
- `latitude`, `longitude` - Geographic coordinates (optional)

### 🔧 Troubleshooting

**Common Issues:**
- **Missing packages**: Run `source("install_packages.R")`
- **Data file not found**: Ensure `all_gardens.xlsx` is in the same folder
- **Deployment timeout**: Try the simplified version `app_simple.R`
- **Account issues**: Verify shinyapps.io credentials

**Getting Help:**
- Check `DEPLOYMENT_GUIDE.md` for detailed instructions
- Run `test_app.R` to diagnose environment issues
- Try `app_simple.R` if the main app has problems

### 🌐 Access Your Deployed App

After successful deployment, your app will be available at:
```
https://your-account.shinyapps.io/caris-dashboard/
```

### 📝 Notes

- The app automatically adapts if the data file is missing
- All filtering is reactive and updates visualizations instantly
- The dashboard maintains the same functionality as the original Python Streamlit app
- Green color scheme (#28a745) matches CARIS branding

### 🔄 Updates

To update the deployed app:
1. Make changes to `app.R`
2. Test locally with `shiny::runApp("app.R")`
3. Redeploy with `rsconnect::deployApp()`

---

**Created by**: CARIS Dashboard Migration Project  
**Original**: Python Streamlit → **Current**: R Shiny  
**Target**: shinyapps.io deployment