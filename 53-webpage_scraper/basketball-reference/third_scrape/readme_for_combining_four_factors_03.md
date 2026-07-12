python z_ins-combine_four_factors.py --four-factors-dir ./data/four_factors --schedule games_with_boxscore_missing_from_report.csv --output pre_converted_report.csv





then after this, 



python z_ins_combine_csvs_03.py new_converted_report.csv ./data/converted_report.csv -o combined_report.csv (this is converted_report.csv)
