# Caris Dashboard - R Shiny Application
# Suivi des Bénéficiaires du Programme Gardening

library(shiny)
library(shinydashboard)
library(DT)
library(dplyr)
library(ggplot2)
library(plotly)
library(readxl)

# Load data function
load_data <- function() {
  tryCatch({
    data <- read_excel("all_gardens.xlsx")
    return(data)
  }, error = function(e) {
    # Return empty data frame if file not found
    return(data.frame())
  })
}

# UI
ui <- dashboardPage(
  dashboardHeader(title = "🌿 Suivi des Bénéficiaires - Programme Gardening"),
  
  dashboardSidebar(
    sidebarMenu(
      menuItem("Dashboard", tabName = "dashboard", icon = icon("dashboard")),
      menuItem("Data", tabName = "data", icon = icon("table"))
    ),
    
    # Filters
    hr(),
    h4("🎯 Filtres"),
    uiOutput("office_filter"),
    uiOutput("date_filter")
  ),
  
  dashboardBody(
    tabItems(
      tabItem(tabName = "dashboard",
        fluidRow(
          # Statistics boxes
          valueBoxOutput("total_beneficiaires"),
          valueBoxOutput("avg_age"),
          valueBoxOutput("cycle4_started")
        ),
        
        fluidRow(
          # Département distribution chart
          box(
            title = "📍 Répartition par département", 
            status = "primary", 
            solidHeader = TRUE,
            width = 6,
            plotlyOutput("dept_chart")
          ),
          
          # Time evolution chart
          box(
            title = "📆 Évolution dans le temps", 
            status = "primary", 
            solidHeader = TRUE,
            width = 6,
            plotlyOutput("time_chart")
          )
        ),
        
        fluidRow(
          # Map placeholder
          box(
            title = "🗺️ Carte des bénéficiaires", 
            status = "info", 
            solidHeader = TRUE,
            width = 12,
            div("Carte interactive (à implémenter si coordonnées disponibles)")
          )
        )
      ),
      
      tabItem(tabName = "data",
        fluidRow(
          box(
            title = "📊 Données Filtrées", 
            status = "primary", 
            solidHeader = TRUE,
            width = 12,
            DT::dataTableOutput("data_table"),
            br(),
            downloadButton("download_data", "📥 Télécharger en Excel", 
                         class = "btn-primary")
          )
        )
      )
    )
  )
)

# Server
server <- function(input, output, session) {
  
  # Reactive data loading
  raw_data <- reactive({
    data <- load_data()
    if (nrow(data) == 0) {
      showNotification("Le fichier 'all_gardens.xlsx' est introuvable.", type = "warning")
    }
    return(data)
  })
  
  # Generate filters based on data
  output$office_filter <- renderUI({
    data <- raw_data()
    if (nrow(data) > 0 && "office" %in% names(data)) {
      choices <- sort(unique(data$office[!is.na(data$office)]))
      selectInput("office", "Choisir les offices:", 
                 choices = choices, 
                 selected = NULL, 
                 multiple = TRUE)
    }
  })
  
  output$date_filter <- renderUI({
    data <- raw_data()
    if (nrow(data) > 0 && "start_date" %in% names(data)) {
      # Convert to date if needed
      if (!inherits(data$start_date, "Date")) {
        data$start_date <- as.Date(data$start_date)
      }
      
      min_date <- min(data$start_date, na.rm = TRUE)
      max_date <- max(data$start_date, na.rm = TRUE)
      
      if (!is.na(min_date) && !is.na(max_date)) {
        dateRangeInput("date_range", "Période (début / fin):",
                      start = min_date,
                      end = max_date,
                      min = min_date,
                      max = max_date)
      }
    }
  })
  
  # Filtered data
  filtered_data <- reactive({
    data <- raw_data()
    
    if (nrow(data) == 0) return(data)
    
    # Apply office filter
    if (!is.null(input$office) && length(input$office) > 0) {
      data <- data[data$office %in% input$office, ]
    }
    
    # Apply date filter
    if (!is.null(input$date_range) && "start_date" %in% names(data)) {
      if (!inherits(data$start_date, "Date")) {
        data$start_date <- as.Date(data$start_date)
      }
      data <- data[data$start_date >= input$date_range[1] & 
                   data$start_date <= input$date_range[2], ]
    }
    
    return(data)
  })
  
  # Value boxes
  output$total_beneficiaires <- renderValueBox({
    data <- filtered_data()
    valueBox(
      value = nrow(data),
      subtitle = "Bénéficiaires totaux",
      icon = icon("users"),
      color = "blue"
    )
  })
  
  output$avg_age <- renderValueBox({
    data <- filtered_data()
    avg_age <- if ("age" %in% names(data) && nrow(data) > 0) {
      round(mean(data$age, na.rm = TRUE), 1)
    } else {
      "N/A"
    }
    valueBox(
      value = paste(avg_age, "ans"),
      subtitle = "Âge moyen",
      icon = icon("calendar"),
      color = "green"
    )
  })
  
  output$cycle4_started <- renderValueBox({
    data <- filtered_data()
    cycle4_count <- if ("start_date" %in% names(data)) {
      sum(!is.na(data$start_date))
    } else {
      0
    }
    valueBox(
      value = cycle4_count,
      subtitle = "Cycle 4 démarré",
      icon = icon("play-circle"),
      color = "yellow"
    )
  })
  
  # Charts
  output$dept_chart <- renderPlotly({
    data <- filtered_data()
    if (nrow(data) > 0 && "departement" %in% names(data)) {
      p <- ggplot(data, aes(x = departement)) +
        geom_bar(fill = "steelblue") +
        theme_minimal() +
        labs(x = "Département", y = "Nombre de bénéficiaires") +
        theme(axis.text.x = element_text(angle = 45, hjust = 1))
      ggplotly(p)
    } else {
      plotly_empty() %>% layout(title = "Pas de données disponibles")
    }
  })
  
  output$time_chart <- renderPlotly({
    data <- filtered_data()
    if (nrow(data) > 0 && "start_date" %in% names(data)) {
      if (!inherits(data$start_date, "Date")) {
        data$start_date <- as.Date(data$start_date)
      }
      p <- ggplot(data, aes(x = start_date)) +
        geom_histogram(binwidth = 7, fill = "lightcoral") +
        theme_minimal() +
        labs(x = "Date de début Cycle 4", y = "Nombre de bénéficiaires")
      ggplotly(p)
    } else {
      plotly_empty() %>% layout(title = "Pas de données de date disponibles")
    }
  })
  
  # Data table
  output$data_table <- DT::renderDataTable({
    data <- filtered_data()
    if (nrow(data) > 0) {
      DT::datatable(data, options = list(pageLength = 25, scrollX = TRUE))
    } else {
      DT::datatable(data.frame(Message = "Aucune donnée disponible"))
    }
  })
  
  # Download handler
  output$download_data <- downloadHandler(
    filename = function() {
      paste("donnees_filtrees_", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      write.csv(filtered_data(), file, row.names = FALSE)
    }
  )
}

# Run the application
shinyApp(ui = ui, server = server)