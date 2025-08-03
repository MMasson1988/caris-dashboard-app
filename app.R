# app.R - Shiny Application for CARIS Dashboard
# Suivi des Bénéficiaires du Programme Gardening
# Equivalent to Python streamlit_app.py

# Load required libraries
library(shiny)
library(shinydashboard)
library(DT)
library(plotly)
library(readxl)
library(dplyr)
library(lubridate)
library(openxlsx)

# Function to load data
load_data <- function() {
  tryCatch({
    # Try to read the Excel file
    df <- read_excel("all_gardens.xlsx")
    return(df)
  }, error = function(e) {
    # Return empty dataframe if file not found
    return(data.frame())
  })
}

# Define UI
ui <- dashboardPage(
  dashboardHeader(title = "🌿 Suivi des Bénéficiaires - Programme Gardening"),
  
  dashboardSidebar(
    sidebarMenu(
      h4("🎯 Filtres", style = "text-align: center; margin: 20px 0;"),
      
      # Office filter
      selectizeInput("office_filter", 
                     "Choisir les offices:",
                     choices = NULL,
                     multiple = TRUE),
      
      # Date range filter  
      dateRangeInput("date_range",
                     "Période (début / fin):",
                     start = Sys.Date() - 365,
                     end = Sys.Date()),
      
      br(),
      downloadButton("download_data", 
                     "📥 Télécharger Excel",
                     class = "btn-success",
                     style = "width: 90%; margin: 10px;")
    )
  ),
  
  dashboardBody(
    tags$head(
      tags$style(HTML("
        .main-header .navbar {
          background-color: #28a745 !important;
        }
        .main-header .logo {
          background-color: #28a745 !important;
        }
        .content-wrapper, .right-side {
          background-color: #f4f4f4;
        }
      "))
    ),
    
    fluidRow(
      box(
        title = "📊 Données Filtrées", 
        status = "primary", 
        solidHeader = TRUE,
        width = 12,
        DT::dataTableOutput("data_table")
      )
    ),
    
    fluidRow(
      # Statistics boxes
      valueBoxOutput("total_beneficiaries"),
      valueBoxOutput("average_age"),
      valueBoxOutput("cycle4_started")
    ),
    
    fluidRow(
      box(
        title = "📍 Répartition par département",
        status = "primary",
        solidHeader = TRUE,
        width = 6,
        plotlyOutput("dept_histogram")
      ),
      
      box(
        title = "📆 Évolution dans le temps", 
        status = "primary",
        solidHeader = TRUE,
        width = 6,
        plotlyOutput("time_evolution")
      )
    ),
    
    # Conditional map box
    conditionalPanel(
      condition = "output.has_coordinates",
      fluidRow(
        box(
          title = "🗺️ Carte des bénéficiaires",
          status = "primary",
          solidHeader = TRUE,
          width = 12,
          plotlyOutput("map_plot")
        )
      )
    )
  )
)

# Define server logic
server <- function(input, output, session) {
  # Load data
  df_raw <- load_data()
  
  # Reactive values
  values <- reactiveValues(
    df = df_raw,
    has_data = nrow(df_raw) > 0
  )
  
  # Check if data loaded successfully
  observe({
    if (nrow(df_raw) == 0) {
      showNotification("Le fichier 'all_gardens.xlsx' est introuvable.", 
                       type = "warning", duration = 10)
    }
  })
  
  # Update office choices when data loads
  observe({
    if (values$has_data && 'office' %in% names(values$df)) {
      office_choices <- sort(unique(values$df$office[!is.na(values$df$office)]))
      updateSelectizeInput(session, "office_filter", 
                          choices = office_choices)
    }
  })
  
  # Update date range based on data
  observe({
    if (values$has_data && 'start_date' %in% names(values$df)) {
      # Convert to date if needed
      if (!inherits(values$df$start_date, "Date")) {
        values$df$start_date <- as.Date(values$df$start_date, origin = "1899-12-30")
      }
      
      date_col <- values$df$start_date[!is.na(values$df$start_date)]
      if (length(date_col) > 0) {
        updateDateRangeInput(session, "date_range",
                           start = min(date_col, na.rm = TRUE),
                           end = max(date_col, na.rm = TRUE))
      }
    }
  })
  
  # Filtered data reactive
  filtered_data <- reactive({
    df <- values$df
    
    if (!values$has_data) return(data.frame())
    
    # Filter by office
    if (!is.null(input$office_filter) && length(input$office_filter) > 0) {
      if ('office' %in% names(df)) {
        df <- df[df$office %in% input$office_filter, ]
      }
    }
    
    # Filter by date range
    if (!is.null(input$date_range) && length(input$date_range) == 2) {
      if ('start_date' %in% names(df)) {
        if (!inherits(df$start_date, "Date")) {
          df$start_date <- as.Date(df$start_date, origin = "1899-12-30")
        }
        df <- df[df$start_date >= input$date_range[1] & 
                df$start_date <= input$date_range[2], ]
      }
    }
    
    return(df)
  })
  
  # Data table output
  output$data_table <- DT::renderDataTable({
    df <- filtered_data()
    if (nrow(df) == 0) return(data.frame())
    
    DT::datatable(df, 
                  options = list(
                    pageLength = 25,
                    scrollX = TRUE,
                    dom = 'Bfrtip'
                  ),
                  class = 'cell-border stripe')
  })
  
  # Value boxes
  output$total_beneficiaries <- renderValueBox({
    df <- filtered_data()
    count <- nrow(df)
    valueBox(
      value = count,
      subtitle = "Bénéficiaires totaux",
      icon = icon("users"),
      color = "blue"
    )
  })
  
  output$average_age <- renderValueBox({
    df <- filtered_data()
    avg_age <- if ('age' %in% names(df) && nrow(df) > 0) {
      mean(df$age, na.rm = TRUE)
    } else {
      0
    }
    valueBox(
      value = paste0(round(avg_age, 1), " ans"),
      subtitle = "Âge moyen",
      icon = icon("birthday-cake"),
      color = "green"
    )
  })
  
  output$cycle4_started <- renderValueBox({
    df <- filtered_data()
    cycle4_count <- if ('start_date' %in% names(df)) {
      sum(!is.na(df$start_date))
    } else {
      0
    }
    valueBox(
      value = cycle4_count,
      subtitle = "Cycle 4 démarré",
      icon = icon("calendar-check"),
      color = "yellow"
    )
  })
  
  # Department histogram
  output$dept_histogram <- renderPlotly({
    df <- filtered_data()
    if (nrow(df) == 0 || !'departement' %in% names(df)) {
      return(plotly_empty())
    }
    
    p <- df %>%
      count(departement) %>%
      plot_ly(x = ~departement, y = ~n, type = 'bar',
              marker = list(color = '#28a745')) %>%
      layout(title = "Répartition par département",
             xaxis = list(title = "Département"),
             yaxis = list(title = "Nombre de bénéficiaires"))
    
    return(p)
  })
  
  # Time evolution plot
  output$time_evolution <- renderPlotly({
    df <- filtered_data()
    if (nrow(df) == 0 || !'start_date' %in% names(df)) {
      return(plotly_empty())
    }
    
    # Convert to date if needed
    if (!inherits(df$start_date, "Date")) {
      df$start_date <- as.Date(df$start_date, origin = "1899-12-30")
    }
    
    p <- df %>%
      filter(!is.na(start_date)) %>%
      count(start_date) %>%
      plot_ly(x = ~start_date, y = ~n, type = 'scatter', mode = 'lines+markers',
              line = list(color = '#28a745')) %>%
      layout(title = "Cycle 4 start - par date",
             xaxis = list(title = "Date"),
             yaxis = list(title = "Nombre"))
    
    return(p)
  })
  
  # Check for coordinates
  output$has_coordinates <- reactive({
    df <- filtered_data()
    'latitude' %in% names(df) && 'longitude' %in% names(df)
  })
  
  outputOptions(output, "has_coordinates", suspendWhenHidden = FALSE)
  
  # Map plot (if coordinates available)
  output$map_plot <- renderPlotly({
    df <- filtered_data()
    if (nrow(df) == 0 || !('latitude' %in% names(df) && 'longitude' %in% names(df))) {
      return(plotly_empty())
    }
    
    df_map <- df %>%
      filter(!is.na(latitude), !is.na(longitude))
    
    if (nrow(df_map) == 0) return(plotly_empty())
    
    p <- plot_ly(df_map, 
                x = ~longitude, y = ~latitude,
                type = 'scattermapbox',
                mode = 'markers',
                marker = list(size = 8, color = '#28a745')) %>%
      layout(
        mapbox = list(
          style = "open-street-map",
          center = list(lon = mean(df_map$longitude, na.rm = TRUE),
                       lat = mean(df_map$latitude, na.rm = TRUE)),
          zoom = 6
        ),
        title = "Localisation des bénéficiaires"
      )
    
    return(p)
  })
  
  # Download handler
  output$download_data <- downloadHandler(
    filename = function() {
      paste("donnees_filtrees_", Sys.Date(), ".xlsx", sep = "")
    },
    content = function(file) {
      df <- filtered_data()
      if (nrow(df) > 0) {
        write.xlsx(df, file, row.names = FALSE)
      }
    }
  )
}

# Run the application
shinyApp(ui = ui, server = server)