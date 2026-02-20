#!/usr/bin/env python
# coding: utf-8
"""TPU Index Aggregation Pipeline: Calculate, normalize, and aggregate TPU indices."""
#%%
import pandas as pd
import os

# Paths
DATA_DIR = '/data/home/xiong/data/Fund/Factiva_News/results'
OUTPUT_DIR = f'{DATA_DIR}/merged_results'


def compute_tpu_index(df, group_cols, id_col='id', flag_col='ILA_TPU_Flag'):
    """Compute TPU index (% of TPU-flagged articles) grouped by specified columns."""
    grouped = df.groupby(group_cols).agg(
        NUMBER_ARTICLES=(id_col, 'count'),
        TPUD_ARTICLES=(flag_col, 'sum')
    ).reset_index()
    grouped['TPUD_index'] = (grouped['TPUD_ARTICLES'] / grouped['NUMBER_ARTICLES'] * 100).round(2)
    return grouped


def normalize_to_base_100(group):
    """Normalize TPU index so first non-zero period = 100 for each country."""
    group = group.sort_values('pub_period')
    # Find first non-zero TPUD_index as base
    nonzero_vals = group[group['TPUD_index'] > 0]['TPUD_index']
    if len(nonzero_vals) > 0:
        base_val = nonzero_vals.iloc[0]
        group['normalized_TPUD_index'] = (group['TPUD_index'] / base_val * 100).round(1)
    else:
        # No non-zero values - all periods have 0% TPU
        group['normalized_TPUD_index'] = float('nan')
    return group


def aggregate_tpu(df, group_col, period_col='pub_period', index_col='normalized_TPUD_index'):
    """Compute GDP-weighted and simple average TPU index by group."""
    def compute_agg(g):
        valid = g[index_col].notna() & g['NGDP_USD_2024'].notna()
        g_valid = g[valid]
        gdp_weighted = (
            (g_valid[index_col] * g_valid['NGDP_USD_2024']).sum() / g_valid['NGDP_USD_2024'].sum()
            if len(g_valid) > 0 and g_valid['NGDP_USD_2024'].sum() > 0 else float('nan')
        )
        return pd.Series({'simple_avg': g[index_col].mean(), 'gdp_weighted_avg': gdp_weighted})

    return df.groupby([group_col, period_col]).apply(compute_agg, include_groups=False).reset_index()

#%%
if __name__ == "__main__":
    # Load data
    df = pd.read_pickle(f'{OUTPUT_DIR}/TPU_aggregated_data_v2.pkl')
    country_meta = pd.read_excel(f'{DATA_DIR}/country_meta_info.xlsx')
    gdp_data = pd.read_excel(f'{DATA_DIR}/ngdp.xlsx', sheet_name='ngdp_USD')[['ISO', 'NGDP_USD_2024']]
    print(f"Date range: {df['publication_date'].min()} to {df['publication_date'].max()}")

    # Process time and country info
    df['pub_period'] = df['publication_date'].dt.to_period('M')
    df['country_name'] = df['ILA_RulebasedCountryTag'].apply(lambda x: x[0] if x else None)
    df = df.merge(country_meta.drop(columns=['country_org']), left_on='country_name', right_on='Formapping', how='left')
    df_imf = df.dropna(subset=['income_group'])

    # Compute country-level TPU index
    group_cols = ['iso', 'country_imf', 'pub_period', 'un_major_region', 'imf_dept_code', 'income_group']
    country_tpu = compute_tpu_index(df_imf, group_cols)

    # Normalize to base 100
    normalized = country_tpu.groupby('iso', group_keys=False).apply(normalize_to_base_100, include_groups=False)
    country_tpu_normalized = country_tpu[['iso', 'pub_period', 'income_group', 'un_major_region', 'imf_dept_code']].join(
        normalized[['NUMBER_ARTICLES', 'TPUD_ARTICLES', 'TPUD_index', 'normalized_TPUD_index']]
    )

    # Merge GDP data
    country_tpu_with_gdp = country_tpu_normalized.merge(gdp_data, left_on='iso', right_on='ISO', how='left').drop(columns=['ISO'])

    # Generate aggregated results
    income_group_agg = aggregate_tpu(country_tpu_with_gdp, 'income_group')
    region_agg = aggregate_tpu(country_tpu_with_gdp, 'un_major_region')
    imf_dept_agg = aggregate_tpu(country_tpu_with_gdp, 'imf_dept_code')

    # Print summary
    print(f"\n=== Results ===")
    print(f"Country-level: {country_tpu_with_gdp.shape} | {country_tpu_with_gdp['iso'].nunique()} countries | {country_tpu_with_gdp['pub_period'].nunique()} periods")
    print(f"Income group agg: {income_group_agg.shape}")
    print(f"Region agg: {region_agg.shape}")
    print(f"IMF dept agg: {imf_dept_agg.shape}")

    # Export to CSV
    exports = {
        'TPU_full_data.csv': df,
        'TPU_imf_countries.csv': df_imf,
        'TPU_country_level.csv': country_tpu_with_gdp,
        'TPU_agg_income_group.csv': income_group_agg,
        'TPU_agg_un_region.csv': region_agg,
        'TPU_agg_imf_dept.csv': imf_dept_agg,
    }
    print(f"\n=== Exporting to {OUTPUT_DIR} ===")
    for filename, data in exports.items():
        data.to_csv(os.path.join(OUTPUT_DIR, filename), index=False)
        print(f"  {filename}: {data.shape}")
