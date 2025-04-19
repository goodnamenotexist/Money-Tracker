import sys
import os
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox, QTableWidget,
                             QTableWidgetItem, QTabWidget, QDateEdit, QMessageBox,
                             QFrame, QFormLayout, QHeaderView, QSplitter)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont, QIcon


class ExpenseCategories:
    FOOD = "Food"
    TRANSPORT = "Transport"
    ENTERTAINMENT = "Entertainment"
    UTILITIES = "Utilities"
    RENT = "Rent"
    SHOPPING = "Shopping"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    OTHER = "Other"

    @classmethod
    def get_all_categories(cls):
        return [cls.FOOD, cls.TRANSPORT, cls.ENTERTAINMENT, cls.UTILITIES,
                cls.RENT, cls.SHOPPING, cls.HEALTHCARE, cls.EDUCATION, cls.OTHER]


class IncomeCategories:
    SALARY = "Salary"
    FREELANCE = "Freelance"
    INVESTMENT = "Investment"
    GIFT = "Gift"
    REFUND = "Refund"
    OTHER = "Other"

    @classmethod
    def get_all_categories(cls):
        return [cls.SALARY, cls.FREELANCE, cls.INVESTMENT, cls.GIFT, cls.REFUND, cls.OTHER]


class DatabaseManager:
    def __init__(self, db_path='money_tracker.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Create transactions table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            description TEXT
        )
        ''')
        self.conn.commit()

    def add_transaction(self, transaction_type, category, amount, date, description=""):
        self.cursor.execute('''
        INSERT INTO transactions (type, category, amount, date, description)
        VALUES (?, ?, ?, ?, ?)
        ''', (transaction_type, category, amount, date, description))
        self.conn.commit()

    def get_all_transactions(self):
        self.cursor.execute('''
        SELECT * FROM transactions ORDER BY date DESC
        ''')
        return self.cursor.fetchall()

    def get_transactions_by_type(self, transaction_type):
        self.cursor.execute('''
        SELECT * FROM transactions WHERE type = ? ORDER BY date DESC
        ''', (transaction_type,))
        return self.cursor.fetchall()

    def get_transactions_by_date_range(self, start_date, end_date):
        self.cursor.execute('''
        SELECT * FROM transactions WHERE date BETWEEN ? AND ? ORDER BY date DESC
        ''', (start_date, end_date))
        return self.cursor.fetchall()

    def get_category_totals(self, transaction_type, start_date=None, end_date=None):
        query = '''
        SELECT category, SUM(amount) FROM transactions 
        WHERE type = ?
        '''
        params = [transaction_type]

        if start_date and end_date:
            query += ' AND date BETWEEN ? AND ?'
            params.extend([start_date, end_date])

        query += ' GROUP BY category'

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_total_amount_by_type(self, transaction_type, start_date=None, end_date=None):
        query = '''
        SELECT SUM(amount) FROM transactions WHERE type = ?
        '''
        params = [transaction_type]

        if start_date and end_date:
            query += ' AND date BETWEEN ? AND ?'
            params.extend([start_date, end_date])

        self.cursor.execute(query, params)
        result = self.cursor.fetchone()[0]
        return result if result else 0

    def delete_transaction(self, transaction_id):
        self.cursor.execute('''
        DELETE FROM transactions WHERE id = ?
        ''', (transaction_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()


class PieChartWidget(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.layout = QVBoxLayout(self)

        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Period selection
        period_layout = QHBoxLayout()
        self.period_combo = QComboBox()
        self.period_combo.addItems(["This Month", "Last Month", "This Week", "Last Week", "All Time"])
        self.period_combo.currentIndexChanged.connect(self.update_chart)
        period_layout.addWidget(QLabel("Period:"))
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()

        self.layout.addLayout(period_layout)
        self.update_chart()

    def update_chart(self):
        self.ax.clear()

        # Get date range based on selected period
        today = datetime.now().date()
        period = self.period_combo.currentText()

        if period == "This Month":
            start_date = datetime(today.year, today.month, 1).strftime('%Y-%m-%d')
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
            end_date = end_date.strftime('%Y-%m-%d')

        elif period == "Last Month":
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1)
                end_date = datetime(today.year, 1, 1) - timedelta(days=1)
            else:
                start_date = datetime(today.year, today.month - 1, 1)
                end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
            start_date = start_date.strftime('%Y-%m-%d')
            end_date = end_date.strftime('%Y-%m-%d')

        elif period == "This Week":
            start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')

        elif period == "Last Week":
            start_date = (today - timedelta(days=today.weekday() + 7)).strftime('%Y-%m-%d')
            end_date = (today - timedelta(days=today.weekday() + 1)).strftime('%Y-%m-%d')

        else:  # All Time
            start_date = None
            end_date = None

        # Get expense data
        expense_data = self.db_manager.get_category_totals("Expense", start_date, end_date)

        # Check if there's any data to display
        if not expense_data:
            self.ax.text(0.5, 0.5, "No expense data for this period",
                         horizontalalignment='center', verticalalignment='center')
            self.canvas.draw()
            return

        labels = [category for category, _ in expense_data]
        amounts = [amount for _, amount in expense_data]

        # Create pie chart
        self.ax.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=90)
        self.ax.set_title(f"Expense Distribution - {period}")
        self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

        self.canvas.draw()


class BarChartWidget(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.layout = QVBoxLayout(self)

        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Period selection
        period_layout = QHBoxLayout()
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Last 6 Months", "Last 12 Months"])
        self.period_combo.currentIndexChanged.connect(self.update_chart)
        period_layout.addWidget(QLabel("Period:"))
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()

        self.layout.addLayout(period_layout)
        self.update_chart()

    def update_chart(self):
        self.ax.clear()

        # Get date range based on selected period
        today = datetime.now().date()
        months = 6 if self.period_combo.currentText() == "Last 6 Months" else 12

        month_labels = []
        income_data = []
        expense_data = []

        for i in range(months, 0, -1):
            # Calculate month
            if today.month - i + 1 <= 0:
                year = today.year - 1
                month = today.month - i + 1 + 12
            else:
                year = today.year
                month = today.month - i + 1

            # Start of the month
            start_date = datetime(year, month, 1).strftime('%Y-%m-%d')

            # End of the month
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            end_date = end_date.strftime('%Y-%m-%d')

            # Add month label
            month_name = datetime(year, month, 1).strftime('%b %y')
            month_labels.append(month_name)

            # Get income and expense for the month
            income = self.db_manager.get_total_amount_by_type("Income", start_date, end_date)
            expense = self.db_manager.get_total_amount_by_type("Expense", start_date, end_date)

            income_data.append(income)
            expense_data.append(expense)

        # Set width of the bars
        x = range(len(month_labels))
        width = 0.35

        # Plot bars
        self.ax.bar([i - width / 2 for i in x], income_data, width, label='Income')
        self.ax.bar([i + width / 2 for i in x], expense_data, width, label='Expense')

        # Customize plot
        self.ax.set_title(f"Income vs Expenses - {self.period_combo.currentText()}")
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(month_labels)
        self.ax.legend()

        # Rotate x-axis labels for better readability
        plt.setp(self.ax.get_xticklabels(), rotation=45)

        self.figure.tight_layout()
        self.canvas.draw()


class MoneyTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Money Tracker")
        self.setGeometry(100, 100, 1000, 700)

        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Create dashboard
        self.create_dashboard(main_layout)

        # Create tabs
        tabs = QTabWidget()

        # Transactions tab
        transactions_tab = QWidget()
        transactions_layout = QVBoxLayout(transactions_tab)
        self.create_transactions_tab(transactions_layout)
        tabs.addTab(transactions_tab, "Transactions")

        # Analytics tab
        analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(analytics_tab)
        self.create_analytics_tab(analytics_layout)
        tabs.addTab(analytics_tab, "Analytics")

        main_layout.addWidget(tabs)

        self.setCentralWidget(central_widget)

        # Initialize data
        self.update_dashboard()
        self.update_transactions_table()

    def create_dashboard(self, parent_layout):
        dashboard_frame = QFrame()
        dashboard_frame.setFrameShape(QFrame.StyledPanel)
        dashboard_layout = QVBoxLayout(dashboard_frame)

        # Title
        title_label = QLabel("Financial Dashboard")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        dashboard_layout.addWidget(title_label)

        # Summary cards
        cards_layout = QHBoxLayout()

        # Income card
        income_card = QFrame()
        income_card.setFrameShape(QFrame.StyledPanel)
        income_card.setStyleSheet("background-color: #e3f2fd; border-radius: 5px;")
        income_layout = QVBoxLayout(income_card)

        income_title = QLabel("Total Income")
        income_title.setFont(QFont("Arial", 12))
        self.income_amount = QLabel("$0.00")
        self.income_amount.setFont(QFont("Arial", 18, QFont.Bold))

        income_layout.addWidget(income_title)
        income_layout.addWidget(self.income_amount)
        cards_layout.addWidget(income_card)

        # Expense card
        expense_card = QFrame()
        expense_card.setFrameShape(QFrame.StyledPanel)
        expense_card.setStyleSheet("background-color: #ffebee; border-radius: 5px;")
        expense_layout = QVBoxLayout(expense_card)

        expense_title = QLabel("Total Expenses")
        expense_title.setFont(QFont("Arial", 12))
        self.expense_amount = QLabel("$0.00")
        self.expense_amount.setFont(QFont("Arial", 18, QFont.Bold))

        expense_layout.addWidget(expense_title)
        expense_layout.addWidget(self.expense_amount)
        cards_layout.addWidget(expense_card)

        # Balance card
        balance_card = QFrame()
        balance_card.setFrameShape(QFrame.StyledPanel)
        balance_card.setStyleSheet("background-color: #e8f5e9; border-radius: 5px;")
        balance_layout = QVBoxLayout(balance_card)

        balance_title = QLabel("Net Balance")
        balance_title.setFont(QFont("Arial", 12))
        self.balance_amount = QLabel("$0.00")
        self.balance_amount.setFont(QFont("Arial", 18, QFont.Bold))

        balance_layout.addWidget(balance_title)
        balance_layout.addWidget(self.balance_amount)
        cards_layout.addWidget(balance_card)

        dashboard_layout.addLayout(cards_layout)

        # Transaction buttons
        buttons_layout = QHBoxLayout()

        add_income_btn = QPushButton("Add Income")
        add_income_btn.setStyleSheet("background-color: #81c784; color: white; padding: 10px;")
        add_income_btn.clicked.connect(self.show_add_income_dialog)

        add_expense_btn = QPushButton("Add Expense")
        add_expense_btn.setStyleSheet("background-color: #e57373; color: white; padding: 10px;")
        add_expense_btn.clicked.connect(self.show_add_expense_dialog)

        buttons_layout.addWidget(add_income_btn)
        buttons_layout.addWidget(add_expense_btn)

        dashboard_layout.addLayout(buttons_layout)
        parent_layout.addWidget(dashboard_frame)

    def create_transactions_tab(self, parent_layout):
        # Create transaction table
        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(6)
        self.transaction_table.setHorizontalHeaderLabels(["ID", "Type", "Category", "Amount", "Date", "Description"])
        self.transaction_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        # Add delete button
        delete_btn = QPushButton("Delete Selected Transaction")
        delete_btn.clicked.connect(self.delete_selected_transaction)

        parent_layout.addWidget(self.transaction_table)
        parent_layout.addWidget(delete_btn)

    def create_analytics_tab(self, parent_layout):
        # Create a splitter for charts
        splitter = QSplitter(Qt.Horizontal)

        # Add pie chart for expense categories
        pie_chart = PieChartWidget(self.db_manager)
        splitter.addWidget(pie_chart)

        # Add bar chart for income vs expenses
        bar_chart = BarChartWidget(self.db_manager)
        splitter.addWidget(bar_chart)

        parent_layout.addWidget(splitter)

    def show_add_income_dialog(self):
        dialog = QWidget()
        dialog.setWindowTitle("Add Income")
        dialog.setGeometry(300, 300, 400, 300)
        layout = QFormLayout(dialog)

        # Amount input
        amount_input = QLineEdit()
        amount_input.setPlaceholderText("Enter amount")
        layout.addRow("Amount ($):", amount_input)

        # Category selection
        category_combo = QComboBox()
        category_combo.addItems(IncomeCategories.get_all_categories())
        layout.addRow("Category:", category_combo)

        # Date selection
        date_picker = QDateEdit()
        date_picker.setDate(QDate.currentDate())
        date_picker.setCalendarPopup(True)
        layout.addRow("Date:", date_picker)

        # Description
        description_input = QLineEdit()
        description_input.setPlaceholderText("Enter description (optional)")
        layout.addRow("Description:", description_input)

        # Add button
        add_button = QPushButton("Add Income")

        def add_income():
            try:
                amount = float(amount_input.text())
                if amount <= 0:
                    QMessageBox.warning(dialog, "Invalid Input", "Amount must be greater than zero.")
                    return

                category = category_combo.currentText()
                date = date_picker.date().toString("yyyy-MM-dd")
                description = description_input.text()

                self.db_manager.add_transaction("Income", category, amount, date, description)
                self.update_dashboard()
                self.update_transactions_table()
                dialog.close()

            except ValueError:
                QMessageBox.warning(dialog, "Invalid Input", "Please enter a valid amount.")

        add_button.clicked.connect(add_income)
        layout.addRow("", add_button)

        dialog.show()

    def show_add_expense_dialog(self):
        dialog = QWidget()
        dialog.setWindowTitle("Add Expense")
        dialog.setGeometry(300, 300, 400, 300)
        layout = QFormLayout(dialog)

        # Amount input
        amount_input = QLineEdit()
        amount_input.setPlaceholderText("Enter amount")
        layout.addRow("Amount ($):", amount_input)

        # Category selection
        category_combo = QComboBox()
        category_combo.addItems(ExpenseCategories.get_all_categories())
        layout.addRow("Category:", category_combo)

        # Date selection
        date_picker = QDateEdit()
        date_picker.setDate(QDate.currentDate())
        date_picker.setCalendarPopup(True)
        layout.addRow("Date:", date_picker)

        # Description
        description_input = QLineEdit()
        description_input.setPlaceholderText("Enter description (optional)")
        layout.addRow("Description:", description_input)

        # Add button
        add_button = QPushButton("Add Expense")

        def add_expense():
            try:
                amount = float(amount_input.text())
                if amount <= 0:
                    QMessageBox.warning(dialog, "Invalid Input", "Amount must be greater than zero.")
                    return

                category = category_combo.currentText()
                date = date_picker.date().toString("yyyy-MM-dd")
                description = description_input.text()

                self.db_manager.add_transaction("Expense", category, amount, date, description)
                self.update_dashboard()
                self.update_transactions_table()
                dialog.close()

            except ValueError:
                QMessageBox.warning(dialog, "Invalid Input", "Please enter a valid amount.")

        add_button.clicked.connect(add_expense)
        layout.addRow("", add_button)

        dialog.show()

    def update_dashboard(self):
        # Get totals
        total_income = self.db_manager.get_total_amount_by_type("Income")
        total_expense = self.db_manager.get_total_amount_by_type("Expense")
        net_balance = total_income - total_expense

        # Update labels
        self.income_amount.setText(f"${total_income:.2f}")
        self.expense_amount.setText(f"${total_expense:.2f}")

        # Set balance color based on value
        if net_balance >= 0:
            self.balance_amount.setStyleSheet("color: green;")
        else:
            self.balance_amount.setStyleSheet("color: red;")

        self.balance_amount.setText(f"${net_balance:.2f}")

    def update_transactions_table(self):
        transactions = self.db_manager.get_all_transactions()

        self.transaction_table.setRowCount(len(transactions))

        for row, transaction in enumerate(transactions):
            transaction_id, transaction_type, category, amount, date, description = transaction

            # Set ID (hidden)
            id_item = QTableWidgetItem(str(transaction_id))
            self.transaction_table.setItem(row, 0, id_item)

            # Set type with color coding
            type_item = QTableWidgetItem(transaction_type)
            if transaction_type == "Income":
                type_item.setBackground(QColor(200, 230, 200))  # Light green
            else:
                type_item.setBackground(QColor(230, 200, 200))  # Light red
            self.transaction_table.setItem(row, 1, type_item)

            # Set category
            self.transaction_table.setItem(row, 2, QTableWidgetItem(category))

            # Set amount
            amount_item = QTableWidgetItem(f"${amount:.2f}")
            self.transaction_table.setItem(row, 3, amount_item)

            # Set date
            self.transaction_table.setItem(row, 4, QTableWidgetItem(date))

            # Set description
            self.transaction_table.setItem(row, 5, QTableWidgetItem(description))

        self.transaction_table.hideColumn(0)  # Hide ID column

    def delete_selected_transaction(self):
        selected_rows = self.transaction_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a transaction to delete.")
            return

        row = selected_rows[0].row()
        transaction_id = int(self.transaction_table.item(row, 0).text())

        # Ask for confirmation
        reply = QMessageBox.question(self, "Confirm Deletion",
                                     "Are you sure you want to delete this transaction?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db_manager.delete_transaction(transaction_id)
            self.update_dashboard()
            self.update_transactions_table()

    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MoneyTracker()
    window.show()
    sys.exit(app.exec_())
