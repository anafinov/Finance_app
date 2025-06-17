import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .db_manager import get_transactions
import configparser
import os

def load_config() -> Dict[str, str]:
    """Загрузка конфигурации из config.ini"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), os.pardir, 'Scripts', 'config.ini')
    config.read(config_path)
    return {
        'export_path': config['REPORTS']['export_path'],
        'graphics_path': config['REPORTS']['graphics_path']
    }

def generate_text_report(start_date: str, end_date: str) -> str:
    """Генерация текстового отчета"""
    transactions = get_transactions(start_date, end_date)
    df = pd.DataFrame(transactions)
    
    if df.empty:
        return "Нет данных за указанный период"
    
    total_income = df[df['transaction_type'] == 'income']['amount'].sum()
    total_expense = df[df['transaction_type'] == 'expense']['amount'].sum()
    balance = total_income - total_expense
    
    report = f"Отчет за период {start_date} - {end_date}\n"
    report += f"Общий доход: {total_income:.2f}\n"
    report += f"Общий расход: {total_expense:.2f}\n"
    report += f"Баланс: {balance:.2f}\n\n"
    
    # Статистика по категориям
    report += "Расходы по категориям:\n"
    category_stats = df[df['transaction_type'] == 'expense'].groupby('category_name')['amount'].sum()
    for category, amount in category_stats.items():
        report += f"{category}: {amount:.2f}\n"
    
    return report

def generate_pie_chart(start_date: str, end_date: str) -> str:
    """Генерация круговых диаграмм расходов и доходов"""
    transactions = get_transactions(start_date, end_date)
    df = pd.DataFrame(transactions)
    
    if df.empty:
        return "Нет данных для построения графика"
    
    config = load_config()
    filenames = []
    
    # Диаграмма расходов
    expense_df = df[df['transaction_type'] == 'expense']
    if not expense_df.empty:
        plt.figure(figsize=(10, 6))
        plt.pie(expense_df.groupby('category_name')['amount'].sum(),
                labels=expense_df['category_name'].unique(),
                autopct='%1.1f%%')
        plt.title('Распределение расходов по категориям')
        
        filename = f"{config['graphics_path']}expense_pie_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename)
        plt.close()
        filenames.append(filename)
    
    # Диаграмма доходов
    income_df = df[df['transaction_type'] == 'income']
    if not income_df.empty:
        plt.figure(figsize=(10, 6))
        plt.pie(income_df.groupby('category_name')['amount'].sum(),
                labels=income_df['category_name'].unique(),
                autopct='%1.1f%%')
        plt.title('Распределение доходов по категориям')
        
        filename = f"{config['graphics_path']}income_pie_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename)
        plt.close()
        filenames.append(filename)
    
    return filenames[0] if filenames else "Нет данных для построения графика"

def generate_line_chart(start_date: str, end_date: str) -> str:
    """Генерация линейного графика динамики"""
    transactions = get_transactions(start_date, end_date)
    df = pd.DataFrame(transactions)
    
    if df.empty:
        return "Нет данных для построения графика"
    
    df['date'] = pd.to_datetime(df['date'])
    daily_balance = df.groupby('date').apply(
        lambda x: x[x['transaction_type'] == 'income']['amount'].sum() - 
                 x[x['transaction_type'] == 'expense']['amount'].sum()
    ).cumsum()
    
    plt.figure(figsize=(12, 6))
    plt.plot(daily_balance.index, daily_balance.values)
    plt.title('Динамика баланса')
    plt.xlabel('Дата')
    plt.ylabel('Баланс')
    plt.grid(True)
    
    config = load_config()
    filename = f"{config['graphics_path']}line_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename)
    plt.close()
    return filename

def generate_bar_chart(start_date: str, end_date: str) -> str:
    """Генерация столбчатой диаграммы доходов и расходов"""
    transactions = get_transactions(start_date, end_date)
    df = pd.DataFrame(transactions)
    
    if df.empty:
        return "Нет данных для построения графика"
    
    # Преобразуем amount в числовой тип
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    income_df = df[df['transaction_type'] == 'income']
    expense_df = df[df['transaction_type'] == 'expense']
    
    # Группировка по категориям
    income_by_category = income_df.groupby('category_name')['amount'].sum()
    expense_by_category = expense_df.groupby('category_name')['amount'].sum()
    
    # Объединяем данные для графика
    plot_data = pd.DataFrame({
        'Доход': income_by_category,
        'Расход': expense_by_category
    }).fillna(0)
    
    if plot_data.empty or plot_data.sum().sum() == 0:
        return "Нет данных для построения графика"
    
    plt.figure(figsize=(12, 7))
    plot_data.plot(kind='bar', ax=plt.gca())
    plt.title('Доходы и расходы по категориям')
    plt.xlabel('Категория')
    plt.ylabel('Сумма')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    config = load_config()
    filename = f"{config['graphics_path']}bar_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename)
    plt.close()
    return filename 