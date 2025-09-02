
# Installation forcée des packages requis
packages <- c('gsubfn', 'DBI', 'dplyr', 'ggplot2', 'knitr', 'rmarkdown', 'plotly', 'DT', 'lubridate', 'stringr')
for(pkg in packages) {
  if(!require(pkg, character.only = TRUE, quietly = TRUE)) {
    install.packages(pkg, repos='https://cran.rstudio.com/')
    library(pkg, character.only = TRUE)
  }
}
