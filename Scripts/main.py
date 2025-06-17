import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import configparser
import os
import sys

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from Library.db_manager import get_categories, add_transaction, get_transactions, add_category, update_category, delete_category
from Library.report_generator import generate_text_report, generate_pie_chart, generate_line_chart, generate_bar_chart

class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет личных финансов")
        self.load_config()
        self.setup_ui()
        
    def load_config(self):
        """Загрузка конфигурации из config.ini"""
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        config.read(config_path)
        self.font_family = config['GUI']['font_family']
        self.font_size = int(config['GUI']['font_size'])
        self.bg_color = config['GUI']['background_color']
        self.text_color = config['GUI']['text_color']
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Стили
        style = ttk.Style()
        style.configure('TButton', font=(self.font_family, self.font_size))
        style.configure('TLabel', font=(self.font_family, self.font_size))
        
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Форма добавления транзакции
        ttk.Label(main_frame, text="Новая транзакция").grid(row=0, column=0, columnspan=2)
        
        # Тип транзакции
        self.transaction_type = tk.StringVar(value="expense")
        ttk.Radiobutton(main_frame, text="Расход", variable=self.transaction_type, 
                       value="expense", command=self.on_transaction_type_change).grid(row=1, column=0)
        ttk.Radiobutton(main_frame, text="Доход", variable=self.transaction_type, 
                       value="income", command=self.on_transaction_type_change).grid(row=1, column=1)
        
        # Поля ввода
        ttk.Label(main_frame, text="Сумма:").grid(row=2, column=0)
        self.amount_entry = ttk.Entry(main_frame)
        self.amount_entry.grid(row=2, column=1)
        
        ttk.Label(main_frame, text="Категория:").grid(row=3, column=0)
        self.category_combo = ttk.Combobox(main_frame)
        self.category_combo.grid(row=3, column=1)
        self.update_categories(self.transaction_type.get())
        
        ttk.Label(main_frame, text="Описание:").grid(row=4, column=0)
        self.description_entry = ttk.Entry(main_frame)
        self.description_entry.grid(row=4, column=1)
        
        # Кнопка добавления
        ttk.Button(main_frame, text="Добавить", 
                  command=self.add_transaction).grid(row=5, column=0, columnspan=2)
        
        # Таблица транзакций
        self.transactions_tree = ttk.Treeview(main_frame, columns=("date", "type", "amount", "category", "description"),
                                            show="headings")
        self.transactions_tree.grid(row=6, column=0, columnspan=2)
        
        self.transactions_tree.heading("date", text="Дата")
        self.transactions_tree.heading("type", text="Тип")
        self.transactions_tree.heading("amount", text="Сумма")
        self.transactions_tree.heading("category", text="Категория")
        self.transactions_tree.heading("description", text="Описание")
        
        # Кнопки отчетов
        ttk.Button(main_frame, text="Текстовый отчет", 
                  command=self.show_text_report).grid(row=7, column=0)
        ttk.Button(main_frame, text="Графики", 
                  command=self.show_graphs).grid(row=7, column=1)
        ttk.Button(main_frame, text="Управление категориями", 
                  command=self.open_category_manager).grid(row=8, column=0, columnspan=2, pady=10)
        ttk.Button(main_frame, text="Настройки", 
                  command=self.open_settings_manager).grid(row=10, column=0, columnspan=2, pady=10)
        
        # Фильтры для журнала операций
        filter_frame = ttk.LabelFrame(main_frame, text="Фильтр операций", padding="10")
        filter_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(filter_frame, text="Начальная дата (ГГГГ-ММ-ДД):").grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = ttk.Entry(filter_frame)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Конечная дата (ГГГГ-ММ-ДД):").grid(row=1, column=0, padx=5, pady=5)
        self.end_date_entry = ttk.Entry(filter_frame)
        self.end_date_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Категория:").grid(row=2, column=0, padx=5, pady=5)
        self.filter_category_combo = ttk.Combobox(filter_frame)
        self.filter_category_combo.grid(row=2, column=1, padx=5, pady=5)
        self.filter_category_combo['values'] = ["Все"] + [cat['name'] for cat in get_categories()]
        self.filter_category_combo.set("Все")

        ttk.Label(filter_frame, text="Мин. сумма:").grid(row=3, column=0, padx=5, pady=5)
        self.min_amount_entry = ttk.Entry(filter_frame)
        self.min_amount_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text="Макс. сумма:").grid(row=4, column=0, padx=5, pady=5)
        self.max_amount_entry = ttk.Entry(filter_frame)
        self.max_amount_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Button(filter_frame, text="Применить фильтр", 
                  command=self.apply_filters).grid(row=5, column=0, columnspan=2, pady=10)
        
        self.update_transactions()
        
    def update_categories(self, transaction_type: str = None):
        """Обновление списка категорий в зависимости от типа транзакции"""
        categories = get_categories(transaction_type) # Получаем категории, фильтруя по типу транзакции
        self.category_combo['values'] = [cat['name'] for cat in categories]
        if categories:
            self.category_combo.set(categories[0]['name'])
        else:
            self.category_combo.set("") # Очищаем выбор, если категорий нет
            
    def on_transaction_type_change(self):
        """Обработчик изменения типа транзакции"""
        self.update_categories(self.transaction_type.get())

    def add_transaction(self):
        """Добавление новой транзакции"""
        try:
            amount = float(self.amount_entry.get())
            category = self.category_combo.get()
            description = self.description_entry.get()
            
            if not category:
                messagebox.showerror("Ошибка", "Выберите категорию")
                return
                
            category_id = self.get_category_id(category)
            if category_id is None:
                messagebox.showerror("Ошибка", f"Категория '{category}' не найдена. Пожалуйста, выберите существующую категорию.")
                return

            add_transaction(
                datetime.now().strftime('%Y-%m-%d'),
                amount,
                category_id,
                description,
                self.transaction_type.get()
            )
            
            self.amount_entry.delete(0, tk.END)
            self.description_entry.delete(0, tk.END)
            self.update_transactions()
            messagebox.showinfo("Успех", "Транзакция добавлена")
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")
            
    def get_category_id(self, category_name):
        """Получение ID категории по имени"""
        categories = get_categories() # Получаем все категории, без фильтрации по типу
        for cat in categories:
            if cat['name'] == category_name:
                return cat['id']
        return None # Возвращаем None, если категория не найдена
        
    def update_transactions(self):
        """Обновление таблицы транзакций"""
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)
            
        transactions = get_transactions()
        for trans in transactions:
            self.transactions_tree.insert("", "end", values=(
                trans['date'],
                "Доход" if trans['transaction_type'] == 'income' else "Расход",
                f"{trans['amount']:.2f}",
                trans['category_name'],
                trans['description']
            ))
            
    def show_text_report(self):
        """Показ текстового отчета"""
        report = generate_text_report(
            (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            datetime.now().strftime('%Y-%m-%d')
        )
        
        report_window = tk.Toplevel(self.root)
        report_window.title("Текстовый отчет")
        
        text = tk.Text(report_window, wrap=tk.WORD, width=50, height=20)
        text.pack(padx=10, pady=10)
        text.insert(tk.END, report)
        text.config(state=tk.DISABLED)
        
    def show_graphs(self):
        """Показ графиков"""
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        pie_charts = generate_pie_chart(start_date, end_date)
        line_chart = generate_line_chart(start_date, end_date)
        bar_chart = generate_bar_chart(start_date, end_date)
        
        chart_messages = []
        if isinstance(pie_charts, list):
            chart_messages.extend([f"Круговая диаграмма: {chart}" for chart in pie_charts])
        elif isinstance(pie_charts, str):
            chart_messages.append(f"Круговая диаграмма: {pie_charts}")
            
        if isinstance(line_chart, str):
            chart_messages.append(f"Линейный график: {line_chart}")
        if isinstance(bar_chart, str):
            chart_messages.append(f"Столбчатая диаграмма: {bar_chart}")

        if chart_messages:
            messagebox.showinfo("Успех", "Графики сохранены:\n" + "\n".join(chart_messages))
        else:
            messagebox.showerror("Ошибка", "Не удалось создать графики")

    def open_category_manager(self):
        """Открывает окно управления категориями"""
        category_window = tk.Toplevel(self.root)
        category_window.title("Управление категориями")
        category_window.transient(self.root) # Делает окно модальным
        category_window.grab_set()
        
        # Фрейм для ввода и кнопок
        input_frame = ttk.Frame(category_window, padding="10")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="Название:").grid(row=0, column=0, padx=5, pady=5)
        self.cat_name_entry = ttk.Entry(input_frame, width=30)
        self.cat_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Тип:").grid(row=1, column=0, padx=5, pady=5)
        self.cat_type_var = tk.StringVar(value="expense")
        ttk.Radiobutton(input_frame, text="Расход", variable=self.cat_type_var, value="expense").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(input_frame, text="Доход", variable=self.cat_type_var, value="income").grid(row=1, column=2, sticky=tk.W)
        
        add_btn = ttk.Button(input_frame, text="Добавить", command=lambda: self._add_category())
        add_btn.grid(row=2, column=0, padx=5, pady=5)
        edit_btn = ttk.Button(input_frame, text="Редактировать", command=lambda: self._update_category())
        edit_btn.grid(row=2, column=1, padx=5, pady=5)
        delete_btn = ttk.Button(input_frame, text="Удалить", command=lambda: self._delete_category())
        delete_btn.grid(row=2, column=2, padx=5, pady=5)
        
        # Таблица категорий
        self.categories_tree = ttk.Treeview(category_window, columns=("id", "name", "type"), show="headings")
        self.categories_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.categories_tree.heading("id", text="ID")
        self.categories_tree.heading("name", text="Название")
        self.categories_tree.heading("type", text="Тип")
        
        self.categories_tree.column("id", width=50)
        self.categories_tree.column("name", width=150)
        self.categories_tree.column("type", width=100)
        
        self.categories_tree.bind('<<TreeviewSelect>>', self._load_selected_category)
        
        self._update_categories_tree()
        
    def _add_category(self):
        """Добавление категории"""
        name = self.cat_name_entry.get()
        type_ = self.cat_type_var.get()
        if name:
            add_category(name, type_)
            messagebox.showinfo("Успех", "Категория добавлена")
            self.cat_name_entry.delete(0, tk.END)
            self._update_categories_tree()
            self.update_categories(self.transaction_type.get()) # Обновить комбобокс на главном окне
        else:
            messagebox.showerror("Ошибка", "Введите название категории")
            
    def _update_category(self):
        """Обновление категории"""
        selected_item = self.categories_tree.focus()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите категорию для редактирования")
            return
            
        category_id = self.categories_tree.item(selected_item)['values'][0]
        new_name = self.cat_name_entry.get()
        new_type = self.cat_type_var.get()
        
        if new_name:
            update_category(category_id, new_name, new_type)
            messagebox.showinfo("Успех", "Категория обновлена")
            self.cat_name_entry.delete(0, tk.END)
            self._update_categories_tree()
            self.update_categories(self.transaction_type.get())
        else:
            messagebox.showerror("Ошибка", "Введите новое название категории")
            
    def _delete_category(self):
        """Удаление категории"""
        selected_item = self.categories_tree.focus()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите категорию для удаления")
            return
            
        category_id = self.categories_tree.item(selected_item)['values'][0]
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту категорию? Все связанные транзакции также будут удалены."):
            delete_category(category_id)
            messagebox.showinfo("Успех", "Категория удалена")
            self.cat_name_entry.delete(0, tk.END)
            self._update_categories_tree()
            self.update_categories(self.transaction_type.get())
            
    def _update_categories_tree(self):
        """Обновление таблицы категорий в окне управления"""
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)
            
        categories = get_categories()
        for cat in categories:
            self.categories_tree.insert("", "end", values=(cat['id'], cat['name'], cat['type']))
            
    def _load_selected_category(self, event):
        """Загружает данные выбранной категории в поля ввода"""
        selected_item = self.categories_tree.focus()
        if selected_item:
            values = self.categories_tree.item(selected_item)['values']
            self.cat_name_entry.delete(0, tk.END)
            self.cat_name_entry.insert(0, values[1])
            self.cat_type_var.set(values[2])

    def apply_filters(self):
        """Применяет фильтры к таблице транзакций"""
        start_date = self.start_date_entry.get() if self.start_date_entry.get() else None
        end_date = self.end_date_entry.get() if self.end_date_entry.get() else None
        category_name = self.filter_category_combo.get()
        
        min_amount = None
        if self.min_amount_entry.get():
            try:
                min_amount = float(self.min_amount_entry.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректное значение для минимальной суммы.")
                return

        max_amount = None
        if self.max_amount_entry.get():
            try:
                max_amount = float(self.max_amount_entry.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректное значение для максимальной суммы.")
                return

        category_id = None
        if category_name and category_name != "Все":
            categories = get_categories()
            for cat in categories:
                if cat['name'] == category_name:
                    category_id = cat['id']
                    break
        
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)
            
        transactions = get_transactions(start_date=start_date, end_date=end_date, 
                                        category_id=category_id, min_amount=min_amount, max_amount=max_amount)
        for trans in transactions:
            self.transactions_tree.insert("", "end", values=(
                trans['date'],
                "Доход" if trans['transaction_type'] == 'income' else "Расход",
                f"{trans['amount']:.2f}",
                trans['category_name'],
                trans['description']
            ))

    def open_settings_manager(self):
        """Открывает окно управления настройками"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки")
        settings_window.transient(self.root)
        settings_window.grab_set()

        settings_frame = ttk.Frame(settings_window, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # GUI Settings
        ttk.Label(settings_frame, text="Настройки интерфейса", font=(self.font_family, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Label(settings_frame, text="Шрифт:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.setting_font_family = ttk.Entry(settings_frame, width=30)
        self.setting_font_family.grid(row=1, column=1, padx=5, pady=5, sticky=tk.E)

        ttk.Label(settings_frame, text="Размер шрифта:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.setting_font_size = ttk.Entry(settings_frame, width=30)
        self.setting_font_size.grid(row=2, column=1, padx=5, pady=5, sticky=tk.E)

        ttk.Label(settings_frame, text="Цвет фона:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.setting_bg_color = ttk.Entry(settings_frame, width=30)
        self.setting_bg_color.grid(row=3, column=1, padx=5, pady=5, sticky=tk.E)

        ttk.Label(settings_frame, text="Цвет текста:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.setting_text_color = ttk.Entry(settings_frame, width=30)
        self.setting_text_color.grid(row=4, column=1, padx=5, pady=5, sticky=tk.E)

        # Database Settings (Simplified for now, can be expanded)
        ttk.Label(settings_frame, text="Настройки базы данных", font=(self.font_family, self.font_size, "bold")).grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Label(settings_frame, text="Хост:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        self.setting_db_host = ttk.Entry(settings_frame, width=30)
        self.setting_db_host.grid(row=6, column=1, padx=5, pady=5, sticky=tk.E)

        ttk.Label(settings_frame, text="Пользователь:").grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
        self.setting_db_user = ttk.Entry(settings_frame, width=30)
        self.setting_db_user.grid(row=7, column=1, padx=5, pady=5, sticky=tk.E)

        ttk.Label(settings_frame, text="Пароль:").grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)
        self.setting_db_password = ttk.Entry(settings_frame, show="*", width=30)
        self.setting_db_password.grid(row=8, column=1, padx=5, pady=5, sticky=tk.E)

        ttk.Label(settings_frame, text="База данных:").grid(row=9, column=0, padx=5, pady=5, sticky=tk.W)
        self.setting_db_name = ttk.Entry(settings_frame, width=30)
        self.setting_db_name.grid(row=9, column=1, padx=5, pady=5, sticky=tk.E)

        # Report Settings
        ttk.Label(settings_frame, text="Настройки отчетов", font=(self.font_family, self.font_size, "bold")).grid(row=10, column=0, columnspan=2, pady=10)
        ttk.Label(settings_frame, text="Период по умолчанию (дни):").grid(row=11, column=0, padx=5, pady=5, sticky=tk.W)
        self.setting_default_period = ttk.Entry(settings_frame, width=30)
        self.setting_default_period.grid(row=11, column=1, padx=5, pady=5, sticky=tk.E)
        
        self._load_current_settings()

        save_button = ttk.Button(settings_frame, text="Сохранить настройки", command=self._save_settings)
        save_button.grid(row=12, column=0, columnspan=2, pady=10)

    def _load_current_settings(self):
        """Загружает текущие настройки из config.ini в поля ввода"""
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        config.read(config_path)

        self.setting_font_family.delete(0, tk.END)
        self.setting_font_family.insert(0, config['GUI']['font_family'])
        self.setting_font_size.delete(0, tk.END)
        self.setting_font_size.insert(0, config['GUI']['font_size'])
        self.setting_bg_color.delete(0, tk.END)
        self.setting_bg_color.insert(0, config['GUI']['background_color'])
        self.setting_text_color.delete(0, tk.END)
        self.setting_text_color.insert(0, config['GUI']['text_color'])

        self.setting_db_host.delete(0, tk.END)
        self.setting_db_host.insert(0, config['DATABASE']['host'])
        self.setting_db_user.delete(0, tk.END)
        self.setting_db_user.insert(0, config['DATABASE']['user'])
        self.setting_db_password.delete(0, tk.END)
        self.setting_db_password.insert(0, config['DATABASE']['password'])
        self.setting_db_name.delete(0, tk.END)
        self.setting_db_name.insert(0, config['DATABASE']['database'])

        self.setting_default_period.delete(0, tk.END)
        self.setting_default_period.insert(0, config['REPORTS']['default_period'])

    def _save_settings(self):
        """Сохраняет настройки из полей ввода в config.ini"""
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        config.read(config_path)

        try:
            config['GUI']['font_family'] = self.setting_font_family.get()
            config['GUI']['font_size'] = self.setting_font_size.get()
            config['GUI']['background_color'] = self.setting_bg_color.get()
            config['GUI']['text_color'] = self.setting_text_color.get()

            config['DATABASE']['host'] = self.setting_db_host.get()
            config['DATABASE']['user'] = self.setting_db_user.get()
            config['DATABASE']['password'] = self.setting_db_password.get()
            config['DATABASE']['database'] = self.setting_db_name.get()

            # Validate integer for default_period
            default_period = int(self.setting_default_period.get())
            if default_period <= 0:
                raise ValueError("Default period must be a positive integer.")
            config['REPORTS']['default_period'] = str(default_period)

            with open(config_path, 'w') as configfile:
                config.write(configfile)
            messagebox.showinfo("Успех", "Настройки сохранены. Некоторые изменения вступят в силу после перезапуска приложения.")
            self.load_config() # Reload for immediate GUI changes
            self.setup_ui() # Reapply GUI settings
        except ValueError as e:
            messagebox.showerror("Ошибка сохранения", f"Некорректные данные: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop() 