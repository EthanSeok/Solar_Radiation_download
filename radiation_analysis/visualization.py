import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, r2_score
import os

def set_korean_font():
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False

def calculate_r2_rmse(y_true, y_pred):
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return r2, rmse

def filter_by_date_range(df, start_date, end_date):
    df['timestamp'] = pd.to_datetime(df['날짜'].astype(str) + ' ' + df['시간'])
    if start_date:
        start_date = pd.to_datetime(start_date)
    if end_date:
        end_date = pd.to_datetime(end_date)

    if start_date and end_date:
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    elif start_date:
        df = df[df['timestamp'] >= start_date]
    elif end_date:
        df = df[df['timestamp'] <= end_date]
    return df

def radiation_scatter(today, tomorrow, output_dir, start_date=None, end_date=None):
    set_korean_font()

    today['일사(MJ/m2)'] = pd.to_numeric(today['일사(MJ/m2)'], errors='coerce')
    today['예측광량'] = pd.to_numeric(today['예측광량'], errors='coerce')
    tomorrow['일사(MJ/m2)'] = pd.to_numeric(tomorrow['일사(MJ/m2)'], errors='coerce')
    tomorrow['예측광량'] = pd.to_numeric(tomorrow['예측광량'], errors='coerce')

    today = today.dropna(subset=['일사(MJ/m2)', '예측광량'])
    tomorrow = tomorrow.dropna(subset=['일사(MJ/m2)', '예측광량'])

    today = filter_by_date_range(today, start_date, end_date)
    tomorrow = filter_by_date_range(tomorrow, start_date, end_date)

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    sns.regplot(data=today, x='일사(MJ/m2)', y='예측광량', ax=ax[0], scatter_kws={'s': 50, 'color': 'black', 'alpha': 0.6},
                line_kws={'color': 'red'})
    sns.regplot(data=tomorrow, x='일사(MJ/m2)', y='예측광량', ax=ax[1], scatter_kws={'s': 50, 'color': 'black', 'alpha': 0.6},
                line_kws={'color': 'red'})

    today_r2, today_rmse = calculate_r2_rmse(today['일사(MJ/m2)'], today['예측광량'])
    tomorrow_r2, tomorrow_rmse = calculate_r2_rmse(tomorrow['일사(MJ/m2)'], tomorrow['예측광량'])

    ax[0].set_title(f'Today (R²={today_r2:.2f}, RMSE={today_rmse:.2f})')
    ax[1].set_title(f'Tomorrow (R²={tomorrow_r2:.2f}, RMSE={tomorrow_rmse:.2f})')

    max_value = max(today['일사(MJ/m2)'].max(), tomorrow['일사(MJ/m2)'].max(), today['예측광량'].max(), tomorrow['예측광량'].max())

    for a in ax:
        a.set_xlim(0, max_value)
        a.set_ylim(0, max_value)
        a.plot([0, max_value], [0, max_value], ls='--', color='black')
        a.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'radiation_scatter.png'))

def temp_scatter(today, tomorrow, output_dir, start_date=None, end_date=None):
    set_korean_font()

    today['온도'] = pd.to_numeric(today['온도'], errors='coerce')
    today['예측온도'] = pd.to_numeric(today['예측온도'], errors='coerce')
    tomorrow['온도'] = pd.to_numeric(tomorrow['온도'], errors='coerce')
    tomorrow['예측온도'] = pd.to_numeric(tomorrow['예측온도'], errors='coerce')

    today = today.dropna(subset=['온도', '예측온도'])
    tomorrow = tomorrow.dropna(subset=['온도', '예측온도'])

    today = filter_by_date_range(today, start_date, end_date)
    tomorrow = filter_by_date_range(tomorrow, start_date, end_date)

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    sns.regplot(data=today, x='온도', y='예측온도', ax=ax[0], scatter_kws={'s': 50, 'color': 'black', 'alpha': 0.6},
                line_kws={'color': 'red'})
    sns.regplot(data=tomorrow, x='온도', y='예측온도', ax=ax[1], scatter_kws={'s': 50, 'color': 'black', 'alpha': 0.6},
                line_kws={'color': 'red'})

    today_r2, today_rmse = calculate_r2_rmse(today['온도'], today['예측온도'])
    tomorrow_r2, tomorrow_rmse = calculate_r2_rmse(tomorrow['온도'], tomorrow['예측온도'])

    ax[0].set_title(f'Today (R²={today_r2:.2f}, RMSE={today_rmse:.2f})')
    ax[1].set_title(f'Tomorrow (R²={tomorrow_r2:.2f}, RMSE={tomorrow_rmse:.2f})')

    max_value = max(today['온도'].max(), tomorrow['온도'].max(), today['예측온도'].max(), tomorrow['예측온도'].max())
    min_value = max(today['온도'].min(), tomorrow['온도'].min(), today['예측온도'].min(), tomorrow['예측온도'].min())

    for a in ax:
        a.set_xlim(abs(min_value) - 2, abs(max_value) + 2)
        a.set_ylim(abs(min_value) - 2, abs(max_value) + 2)
        a.plot([min_value, max_value], [min_value, max_value], ls='--', color='black')
        a.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'temp_scatter.png'))


def wind_scatter(today, tomorrow, output_dir, start_date=None, end_date=None):
    set_korean_font()

    today['풍속'] = pd.to_numeric(today['풍속'], errors='coerce')
    today['예측풍속'] = pd.to_numeric(today['예측풍속'], errors='coerce')
    tomorrow['풍속'] = pd.to_numeric(tomorrow['풍속'], errors='coerce')
    tomorrow['예측풍속'] = pd.to_numeric(tomorrow['예측풍속'], errors='coerce')

    today = today.dropna(subset=['풍속', '예측풍속'])
    tomorrow = tomorrow.dropna(subset=['풍속', '예측풍속'])

    today = filter_by_date_range(today, start_date, end_date)
    tomorrow = filter_by_date_range(tomorrow, start_date, end_date)

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    sns.regplot(data=today, x='풍속', y='예측풍속', ax=ax[0], scatter_kws={'s': 50, 'color': 'black', 'alpha': 0.6},
                line_kws={'color': 'red'})
    sns.regplot(data=tomorrow, x='풍속', y='예측풍속', ax=ax[1], scatter_kws={'s': 50, 'color': 'black', 'alpha': 0.6},
                line_kws={'color': 'red'})

    today_r2, today_rmse = calculate_r2_rmse(today['풍속'], today['예측풍속'])
    tomorrow_r2, tomorrow_rmse = calculate_r2_rmse(tomorrow['풍속'], tomorrow['예측풍속'])

    ax[0].set_title(f'Today (R²={today_r2:.2f}, RMSE={today_rmse:.2f})')
    ax[1].set_title(f'Tomorrow (R²={tomorrow_r2:.2f}, RMSE={tomorrow_rmse:.2f})')

    max_value = max(today['풍속'].max(), tomorrow['풍속'].max(), today['예측풍속'].max(), tomorrow['예측풍속'].max())
    min_value = max(today['풍속'].min(), tomorrow['풍속'].min(), today['예측풍속'].min(), tomorrow['예측풍속'].min())

    for a in ax:
        a.set_xlim(abs(min_value) - 1, abs(max_value) + 1)
        a.set_ylim(abs(min_value) - 1, abs(max_value) + 1)
        a.plot([min_value, max_value], [min_value, max_value], ls='--', color='black')
        a.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'wind_scatter.png'))


def radiation_line(today, tomorrow, output_dir, start_date=None, end_date=None):
    set_korean_font()

    today = filter_by_date_range(today, start_date, end_date)
    tomorrow = filter_by_date_range(tomorrow, start_date, end_date)

    fig, ax = plt.subplots(2, 1, figsize=(14, 14))

    sns.lineplot(data=today, x='timestamp', y='예측광량', ax=ax[0], label='predict', lw=2.2)
    sns.lineplot(data=today, x='timestamp', y='일사(MJ/m2)', ax=ax[0], label='ASOS', lw=2.2)
    ax[0].set_title('Today')
    ax[0].set_xlabel('Timestamp')
    ax[0].set_ylabel('Radiation')
    ax[0].legend(loc='upper left')

    sns.lineplot(data=tomorrow, x='timestamp', y='예측광량', ax=ax[1], label='predict', lw=2.2)
    sns.lineplot(data=tomorrow, x='timestamp', y='일사(MJ/m2)', ax=ax[1], label='ASOS', lw=2.2)
    ax[1].set_title('Tomorrow')
    ax[1].set_xlabel('Timestamp')
    ax[1].set_ylabel('Radiation')
    ax[1].get_legend().remove()

    for a in ax:
        a.grid(axis="y", which='major', linestyle='--', linewidth=0.5)
        for s in ["left", "right", "top"]:
            a.spines[s].set_visible(False)
        a.set_xlabel('')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'radiation_line.png'))

def temp_line(today, tomorrow, output_dir, start_date=None, end_date=None):
    set_korean_font()

    today = filter_by_date_range(today, start_date, end_date)
    tomorrow = filter_by_date_range(tomorrow, start_date, end_date)

    fig, ax = plt.subplots(2, 1, figsize=(14, 14))

    sns.lineplot(data=today, x='timestamp', y='예측온도', ax=ax[0], label='predict', lw=2.2)
    sns.lineplot(data=today, x='timestamp', y='온도', ax=ax[0], label='ASOS', lw=2.2)
    ax[0].set_title('Today')
    ax[0].set_xlabel('Timestamp')
    ax[0].set_ylabel('Radiation')
    ax[0].legend(loc='upper left')

    sns.lineplot(data=tomorrow, x='timestamp', y='예측온도', ax=ax[1], label='predict', lw=2.2)
    sns.lineplot(data=tomorrow, x='timestamp', y='온도', ax=ax[1], label='ASOS', lw=2.2)
    ax[1].set_title('Tomorrow')
    ax[1].set_xlabel('Timestamp')
    ax[1].set_ylabel('Radiation')
    ax[1].get_legend().remove()

    for a in ax:
        a.grid(axis="y", which='major', linestyle='--', linewidth=0.5)
        for s in ["left", "right", "top"]:
            a.spines[s].set_visible(False)
        a.set_xlabel('')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'temp_line.png'))

def wind_line(today, tomorrow, output_dir, start_date=None, end_date=None):
    set_korean_font()

    today = filter_by_date_range(today, start_date, end_date)
    tomorrow = filter_by_date_range(tomorrow, start_date, end_date)

    fig, ax = plt.subplots(2, 1, figsize=(14, 14))

    sns.lineplot(data=today, x='timestamp', y='예측풍속', ax=ax[0], label='predict', lw=2.2)
    sns.lineplot(data=today, x='timestamp', y='풍속', ax=ax[0], label='ASOS', lw=2.2)
    ax[0].set_title('Today')
    ax[0].set_xlabel('Timestamp')
    ax[0].set_ylabel('Radiation')
    ax[0].legend(loc='upper left')

    sns.lineplot(data=tomorrow, x='timestamp', y='예측풍속', ax=ax[1], label='predict', lw=2.2)
    sns.lineplot(data=tomorrow, x='timestamp', y='풍속', ax=ax[1], label='ASOS', lw=2.2)
    ax[1].set_title('Tomorrow')
    ax[1].set_xlabel('Timestamp')
    ax[1].set_ylabel('Radiation')
    ax[1].get_legend().remove()

    for a in ax:
        a.grid(axis="y", which='major', linestyle='--', linewidth=0.5)
        for s in ["left", "right", "top"]:
            a.spines[s].set_visible(False)
        a.set_xlabel('')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'wind_line.png'))

def main():
    merged_today = pd.read_csv('output/merged_today.csv')
    merged_tomorrow = pd.read_csv('output/merged_tomorrow.csv')

    output_dir = 'output/figures'
    os.makedirs(output_dir, exist_ok=True)

    start_date = '2024-07-11'
    end_date = '2024-07-16'

    radiation_scatter(merged_today, merged_tomorrow, output_dir, start_date, end_date)
    temp_scatter(merged_today, merged_tomorrow, output_dir, start_date, end_date)
    radiation_line(merged_today, merged_tomorrow, output_dir, start_date, end_date)
    temp_line(merged_today, merged_tomorrow, output_dir, start_date, end_date)
    wind_scatter(merged_today, merged_tomorrow, output_dir, start_date, end_date)
    wind_line(merged_today, merged_tomorrow, output_dir, start_date, end_date)


if __name__ == "__main__":
    main()