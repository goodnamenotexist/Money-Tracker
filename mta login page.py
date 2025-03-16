import tkinter as tk
from tkinter import messagebox

# Dummy credentials for login
USER_EMAIL = "user@example.com"
USER_PASSWORD = "password123"

# Function to handle login button click
def login():
    email = email_entry.get()
    password = password_entry.get()

    if email == USER_EMAIL and password == USER_PASSWORD:
        messagebox.showinfo("Login Successful", "Welcome to your Money Tracker dashboard!")
        show_dashboard()
    else:
        messagebox.showerror("Login Failed", "Invalid credentials. Please try again.")

# Function to display the dashboard
def show_dashboard():
    for widget in root.winfo_children():
        widget.destroy()  # Clear all widgets from the window

    root.configure(bg="#e0f7ff")  # Light blue background for the dashboard

    tk.Label(root, text=f"Welcome to your Money Tracker dashboard, {USER_EMAIL}!", 
             font=("Arial", 14, "bold"), fg="#1a73e8", bg="#e0f7ff").pack(pady=20)

    tk.Button(root, text="View Balance", command=view_balance, width=20, 
              font=("Arial", 12), bg="#1a73e8", fg="white", bd=0, pady=5).pack(pady=10)
    tk.Button(root, text="Add Transaction", command=add_transaction, width=20, 
              font=("Arial", 12), bg="#1a73e8", fg="white", bd=0, pady=5).pack(pady=10)
    tk.Button(root, text="Logout", command=show_login_page, width=20, 
              font=("Arial", 12), bg="#1a73e8", fg="white", bd=0, pady=5).pack(pady=10)

def view_balance():
    messagebox.showinfo("Balance", "Your current balance is: $1000.00")

def add_transaction():
    messagebox.showinfo("Add Transaction", "Transaction has been added successfully!")

# Function to show the login page
def show_login_page():
    for widget in root.winfo_children():
        widget.destroy()  # Clear all widgets from the window

    root.configure(bg="#e0f7ff")  # Light blue background

    tk.Label(root, text="Money Tracker Login", font=("Arial", 16, "bold"), 
             fg="#1a73e8", bg="#e0f7ff").pack(pady=20)

    tk.Label(root, text="Email:", font=("Arial", 12), bg="#e0f7ff").pack()
    global email_entry
    email_entry = tk.Entry(root, width=30, font=("Arial", 12))
    email_entry.pack(pady=5)

    tk.Label(root, text="Password:", font=("Arial", 12), bg="#e0f7ff").pack()
    global password_entry
    password_entry = tk.Entry(root, show="*", width=30, font=("Arial", 12))
    password_entry.pack(pady=5)

    tk.Button(root, text="Login", command=login, width=20, font=("Arial", 12), 
              bg="#1a73e8", fg="white", bd=0, pady=5).pack(pady=20)

# Create the main window
root = tk.Tk()
root.title("Money Tracker App")
root.geometry("400x300")

# Show the login page initially
show_login_page()

# Run the application
root.mainloop()
