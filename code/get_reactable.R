# To produce the tables
library(reactable)
library(tidyverse)
library(reactablefmtr)
data_path <- '../data/natural_side.txt' # Path to the data, set working space to code
df <- read.csv(data_path)
table <- reactable(df)
tit <- 'My table' # include the title
table %>% add_title(tit, align='right')