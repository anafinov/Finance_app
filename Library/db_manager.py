import mysql.connector
import configparser
from typing import List, Dict, Any
import os

def get_db_config() -> Dict[str, str]:
    """Загрузка конфигурации базы данных из config.ini"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), os.pardir, 'Scripts', 'config.ini')
    config.read(config_path)
    return {
        'host': config['DATABASE']['host'],
        'user': config['DATABASE']['user'],
        'password': config['DATABASE']['password'],
        'database': config['DATABASE']['database']
    }

def get_connection():
    """Создание соединения с базой данных"""
    return mysql.connector.connect(**get_db_config())

def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """Выполнение SQL-запроса"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        conn.commit()
        return result

def get_categories(category_type: str = None) -> List[Dict[str, Any]]:
    """Получение списка категорий"""
    query = "SELECT * FROM categories"
    if category_type:
        query += " WHERE type = %s"
        return execute_query(query, (category_type,))
    return execute_query(query)

def add_transaction(date: str, amount: float, category_id: int, 
                   description: str, type_: str) -> None:
    """Добавление новой транзакции"""
    query = """
    INSERT INTO transactions (date, amount, category_id, description, type)
    VALUES (%s, %s, %s, %s, %s)
    """
    execute_query(query, (date, amount, category_id, description, type_))

def get_transactions(start_date: str = None, end_date: str = None,
                    category_id: int = None, min_amount: float = None, max_amount: float = None) -> List[Dict[str, Any]]:
    """Получение списка транзакций с фильтрацией"""
    query = """
    SELECT t.id, t.date, t.amount, t.category_id, t.description, t.type AS transaction_type, t.created_at, c.name as category_name 
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND t.date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND t.date <= %s"
        params.append(end_date)
    if category_id:
        query += " AND t.category_id = %s"
        params.append(category_id)
    if min_amount is not None:
        query += " AND t.amount >= %s"
        params.append(min_amount)
    if max_amount is not None:
        query += " AND t.amount <= %s"
        params.append(max_amount)
        
    query += " ORDER BY t.date DESC"
    return execute_query(query, tuple(params))

def add_category(name: str, type_: str) -> None:
    """Добавление новой категории"""
    query = "INSERT INTO categories (name, type) VALUES (%s, %s)"
    execute_query(query, (name, type_))

def update_category(category_id: int, new_name: str, new_type: str) -> None:
    """Обновление существующей категории"""
    query = "UPDATE categories SET name = %s, type = %s WHERE id = %s"
    execute_query(query, (new_name, new_type, category_id))

def delete_category(category_id: int) -> None:
    """Удаление категории и связанных с ней транзакций"""
    # Сначала удаляем транзакции, связанные с этой категорией
    execute_query("DELETE FROM transactions WHERE category_id = %s", (category_id,))
    # Затем удаляем саму категорию
    execute_query("DELETE FROM categories WHERE id = %s", (category_id,)) 