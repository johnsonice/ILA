cd ..
# Custom directories and parallel processing
python get_all_meta.py --data_dir //data2/CommercialData/Factiva_Repository --output_dir "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/metadata" --jobs 1 --sub_jobs 8

# # Export as CSV instead of JSON
# python get_all_meta.py --return_df

# # Run unit tests first
# python get_all_meta.py --run_tests

# # Quiet mode for minimal output
# python get_all_meta.py --quiet