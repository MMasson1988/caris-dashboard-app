# app_simple.R - Simplified Shiny Application for CARIS Dashboard
# Alternative simpler version if the dashboard version has issues

library(shiny)
library(DT)
library(plotly)
library(readxl)
library(dplyr)

# Function to load data
load_data <- function() {
  tryCatch({
    df <- read_excel("all_gardens.xlsx")
    return(df)
  }, error = function(e) {
    return(data.frame(
      office = c("Example Office"),
      departement = c("Example Dept"),
      age = c(30),
      start_date = c(Sys.Date()),
      message = c("Data file not found - using sample data")
    ))
  })
}

# Define UI
ui <- fluidPage(
  titlePanel("🌿 Suivi des Bénéficiaires du Programme Gardening"),
  
  tags$head(
    tags$style(HTML("
      body { background-color: #f8f9fa; }
      .navbar-default { background-color: #28a745; }
      h1 { color: #28a745; }
    "))
  ),
  
  sidebarLayout(
    sidebarPanel(
      h4("🎯 Filtres"),
      
      selectizeInput("office_filter", 
                     "Choisir les offices:",
                     choices = NULL,
                     multiple = TRUE),
      
      dateRangeInput("date_range",
                     "Période:",
                     start = Sys.Date() - 365,
                     end = Sys.Date()),
      
      br(),
      downloadButton("download_data", 
                     "📥 Télécharger Excel",
                     class = "btn-success")
    ),
    
    mainPanel(
      tabsetPanel(
        tabPanel("📊 Données", 
                 br(),
                 fluidRow(
                   column(4, wellPanel(
                     h4(textOutput("total_count"), style = "color: #28a745;"),
                     p("Bénéficiaires totaux")
                   )),
                   column(4, wellPanel(
                     h4(textOutput("avg_age"), style = "color: #28a745;"),
                     p("Âge moyen")
                   )),
                   column(4, wellPanel(
                     h4(textOutput("cycle4_count"), style = "color: #28a745;"),
                     p("Cycle 4 démarré")
                   ))
                 ),
                 DT::dataTableOutput("data_table")
        ),
        
        tabPanel("📊 Graphiques",
                 br(),
                 plotlyOutput("dept_plot", height = "400px"),
                 br(),
                 plotlyOutput("time_plot", height = "400px")
        )
      )
    )
  )
)

# Define server logic
server <- function(input, output, session) {
  # Load data
  df_raw <- load_data()
  
  # Update choices
  observe({
    if ('office' %in% names(df_raw)) {
      choices <- sort(unique(df_raw$office[!is.na(df_raw$office)]))
      updateSelectizeInput(session, "office_filter", choices = choices)
    }
  })
  
  # Filtered data
  filtered_data <- reactive({
    df <- df_raw
    
    # Filter by office
    if (!is.null(input$office_filter) && length(input$office_filter) > 0) {
      if ('office' %in% names(df)) {
        df <- df[df$office %in% input$office_filter, ]
      }
    }
    
    # Filter by date
    if (!is.null(input$date_range) && 'start_date' %in% names(df)) {
      df$start_date <- as.Date(df$start_date)
      df <- df[df$start_date >= input$date_range[1] & 
              df$start_date <= input$date_range[2], ]
    }
    
    return(df)
  })
  
  # Outputs
  output$total_count <- renderText({
    nrow(filtered_data())
  })
  
  output$avg_age <- renderText({
    df <- filtered_data()
    if ('age' %in% names(df) && nrow(df) > 0) {
      paste0(round(mean(df$age, na.rm = TRUE), 1), " ans")
    } else {
      "N/A"
    }
  })
  
  output$cycle4_count <- renderText({
    df <- filtered_data()
    if ('start_date' %in% names(df)) {
      sum(!is.na(df$start_date))
    } else {
      "N/A"
    }
  })
  
  output$data_table <- DT::renderDataTable({
    DT::datatable(filtered_data(), 
                  options = list(pageLength = 25, scrollX = TRUE))
  })
  
  output$dept_plot <- renderPlotly({
    df <- filtered_data()
    if ('departement' %in% names(df) && nrow(df) > 0) {
      p <- df %>%
        count(departement) %>%
        plot_ly(x = ~departement, y = ~n, type = 'bar',
                marker = list(color = '#28a745')) %>%
        layout(title = "Répartition par département")
      return(p)
    } else {
      return(plotly_empty())
    }
  })
  
  output$time_plot <- renderPlotly({
    df <- filtered_data()
    if ('start_date' %in% names(df) && nrow(df) > 0) {
      df$start_date <- as.Date(df$start_date)
      p <- df %>%
        filter(!is.na(start_date)) %>%
        count(start_date) %>%
        plot_ly(x = ~start_date, y = ~n, type = 'scatter', mode = 'lines+markers') %>%
        layout(title = "Évolution dans le temps")
      return(p)
    } else {
      return(plotly_empty())
    }
  })
  
  # Download handler
  output$download_data <- downloadHandler(
    filename = function() {
      paste("donnees_", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      write.csv(filtered_data(), file, row.names = FALSE)
    }
  )
}

# Run the application
shinyApp(ui = ui, server = server)