the final product is new_converted_report.csv

 \# Step 1: Initial scraping

so I start with :

python ins01-scraper2_combined.py --scrape

I get a file called nba_2025_schedule_april_1.csv

 \# Step 2: Parse schedule

then I run ins05b_parse_down_nba_schedule.py nba_2025_schedule_april_1.csv ./data/converted_report.csv

which returns games_with_boxscore_missing_from_report.csv

so then I go and I scrape with 

 \# Step 3: Scrape missing games

python scrape_with_argument8.py games_with_boxscore_missing_from_report.csv

 \# Step 4: Combine four factors data

and then the ./data/four_factors get populated

then, I go to data to run

python 01ins-combine_four_factors.py --four-factors-dir ./four_factors --schedule games_with_boxscore_missing_from_report.csv --output nba_report.csv

\# Step 5: Convert to ML format

 python z_ins-convert-to-ml-format_02.py -i nba_report.csv

then I move nba_report.csv back to the original folder, I run 

python z_ins-convert-to-ml-format_02.py -i nba_report.csv

to get 

nba_games_stats.csv

 \# Step 6: Copy data files to proper locations

 cp data/converted_report.csv converted_report_protected.csv

I go back to ./data to get converted_report.csv

 \# Step 7: Combine CSVs for final output

 python z_ins_combine_csvs_03.py converted_report_protected.csv nba_games_stats.csv -o

 new_converted_report.csv

and move it back to the original folder 

and run  python z_ins_combine_csvs_03.py converted_report_protected.csv nba_games_stats.csv -o new_report.csv

because converted_report_protected.csv is renamed from converted_report.csv



to get the final new_report.csv which then will be used as converted_report.csv





