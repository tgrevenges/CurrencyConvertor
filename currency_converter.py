import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
import urllib.request
import urllib.error

# API конфигурация
API_URL = "https://api.exchangerate-api.com/v4/latest/"


HISTORY_FILE = "conversion_history.json"

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter - Конвертер валют")
        self.root.geometry("900x650")

        # Данные
        self.history = []
        self.exchange_rates = {}
        self.currencies = []
        self.load_history()
        self.load_currencies()

        # Создание интерфейса
        self.create_converter_frame()
        self.create_history_frame()

        # Обновление таблицы истории
        self.refresh_history()

    def load_currencies(self):
        """Загрузка списка валют из API"""
        try:
            # Получаем курсы к USD (базовая валюта)
            with urllib.request.urlopen(API_URL + "USD") as response:
                data = json.loads(response.read().decode())
                self.exchange_rates = data.get("rates", {})
                self.currencies = sorted(self.exchange_rates.keys())
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список валют.\n{e}\n\nИспользуются стандартные валюты.")
            # Стандартные валюты на случай ошибки
            self.currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "RUB", "CAD", "AUD", "CHF", "INR"]
            self.exchange_rates = {c: 1.0 for c in self.currencies}

    def get_exchange_rate(self, from_currency, to_currency):
        """Получение курса конвертации"""
        try:
            # Получаем курсы для базовой валюты from_currency
            with urllib.request.urlopen(API_URL + from_currency) as response:
                data = json.loads(response.read().decode())
                rates = data.get("rates", {})
                if to_currency in rates:
                    return rates[to_currency]
                else:
                    return None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить курсы валют.\n{e}")
            return None

    def create_converter_frame(self):
        """Форма конвертации валют"""
        converter_frame = ttk.LabelFrame(self.root, text="Конвертер валют", padding=15)
        converter_frame.pack(fill="x", padx=10, pady=5)

        # Сумма
        ttk.Label(converter_frame, text="Сумма:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.amount_entry = ttk.Entry(converter_frame, width=20, font=("Arial", 12))
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        # Из валюты
        ttk.Label(converter_frame, text="Из валюты:", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.from_currency_var = tk.StringVar()
        self.from_combo = ttk.Combobox(converter_frame, textvariable=self.from_currency_var,
                                        values=self.currencies, width=10, font=("Arial", 10))
        self.from_combo.grid(row=0, column=3, padx=5, pady=5)
        self.from_combo.set("USD")

        # Меняем местами
        swap_btn = ttk.Button(converter_frame, text="⇄", command=self.swap_currencies, width=3)
        swap_btn.grid(row=0, column=4, padx=5, pady=5)

        # В валюту
        ttk.Label(converter_frame, text="В валюту:", font=("Arial", 10, "bold")).grid(row=0, column=5, padx=5, pady=5, sticky="w")
        self.to_currency_var = tk.StringVar()
        self.to_combo = ttk.Combobox(converter_frame, textvariable=self.to_currency_var,
                                      values=self.currencies, width=10, font=("Arial", 10))
        self.to_combo.grid(row=0, column=6, padx=5, pady=5)
        self.to_combo.set("EUR")

        # Кнопка конвертации
        convert_btn = ttk.Button(converter_frame, text="Конвертировать", command=self.convert, width=15)
        convert_btn.grid(row=0, column=7, padx=10, pady=5)

        # Результат
        self.result_label = ttk.Label(converter_frame, text="Результат: 0.00", font=("Arial", 12, "bold"), foreground="green")
        self.result_label.grid(row=1, column=0, columnspan=8, pady=10)

        # Информация о курсе
        self.rate_label = ttk.Label(converter_frame, text="", font=("Arial", 9), foreground="gray")
        self.rate_label.grid(row=2, column=0, columnspan=8)

    def create_history_frame(self):
        """Таблица истории конвертаций"""
        history_frame = ttk.LabelFrame(self.root, text="История конвертаций", padding=10)
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Создание таблицы
        columns = ("datetime", "amount", "from_currency", "to_currency", "result", "rate")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=12)

        self.tree.heading("datetime", text="Дата/Время")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("from_currency", text="Из")
        self.tree.heading("to_currency", text="В")
        self.tree.heading("result", text="Результат")
        self.tree.heading("rate", text="Курс")

        self.tree.column("datetime", width=150)
        self.tree.column("amount", width=100)
        self.tree.column("from_currency", width=80)
        self.tree.column("to_currency", width=80)
        self.tree.column("result", width=120)
        self.tree.column("rate", width=100)

        # Скроллбар
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Кнопки управления историей
        button_frame = ttk.Frame(history_frame)
        button_frame.pack(side="bottom", fill="x", pady=5)

        clear_btn = ttk.Button(button_frame, text="Очистить историю", command=self.clear_history)
        clear_btn.pack(side="left", padx=5)

        export_btn = ttk.Button(button_frame, text="Экспортировать JSON", command=self.export_history)
        export_btn.pack(side="left", padx=5)

    def validate_amount(self, amount_str):
        """Проверка корректности суммы"""
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, "Сумма должна быть положительным числом"
            return True, amount
        except ValueError:
            return False, "Сумма должна быть числом"

    def swap_currencies(self):
        """Меняет местами валюты"""
        from_curr = self.from_currency_var.get()
        to_curr = self.to_currency_var.get()
        self.from_currency_var.set(to_curr)
        self.to_currency_var.set(from_curr)

    def convert(self):
        """Конвертация валюты"""
        amount_str = self.amount_entry.get().strip()
        from_currency = self.from_currency_var.get()
        to_currency = self.to_currency_var.get()

        # Валидация суммы
        is_valid, amount_or_error = self.validate_amount(amount_str)
        if not is_valid:
            messagebox.showerror("Ошибка", amount_or_error)
            return

        # Проверка выбора валют
        if not from_currency or not to_currency:
            messagebox.showerror("Ошибка", "Выберите валюты для конвертации")
            return

        if from_currency == to_currency:
            result = amount_or_error
            rate = 1.0
            self.result_label.config(text=f"Результат: {result:.4f} {to_currency}")
            self.rate_label.config(text=f"Курс: 1 {from_currency} = {rate:.4f} {to_currency}")
        else:
            # Получение курса
            rate = self.get_exchange_rate(from_currency, to_currency)
            if rate is None:
                messagebox.showerror("Ошибка", f"Не удалось получить курс {from_currency} -> {to_currency}")
                return

            result = amount_or_error * rate
            self.result_label.config(text=f"Результат: {result:.4f} {to_currency}")
            self.rate_label.config(text=f"Курс: 1 {from_currency} = {rate:.4f} {to_currency}")

        # Сохранение в историю
        history_entry = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount_or_error,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "result": result,
            "rate": rate if from_currency != to_currency else 1.0
        }
        self.history.append(history_entry)
        self.save_history()
        self.refresh_history()

        messagebox.showinfo("Успех", f"Конвертация выполнена!\n{amount_or_error} {from_currency} = {result:.4f} {to_currency}")

    def refresh_history(self):
        """Обновление таблицы истории"""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Отображение истории (от новых к старым)
        for entry in reversed(self.history):
            self.tree.insert("", "end", values=(
                entry["datetime"],
                f"{entry['amount']:.4f}",
                entry["from_currency"],
                entry["to_currency"],
                f"{entry['result']:.4f}",
                f"{entry['rate']:.4f}"
            ))

    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.save_history()
            self.refresh_history()
            messagebox.showinfo("История очищена", "История конвертаций успешно очищена")

    def export_history(self):
        """Экспорт истории в JSON файл"""
        if not self.history:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"currency_history_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Экспорт успешен", f"История экспортирована в файл:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать историю:\n{e}")

    def load_history(self):
        """Загрузка истории из JSON"""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []

    def save_history(self):
        """Сохранение истории в JSON"""
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()
