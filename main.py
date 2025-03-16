import tkinter as tk
from tkinter import messagebox
import sqlite3
import time

def connect():
    conn = sqlite3.connect("expenseapp.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS expensetable(id INTEGER PRIMARY KEY,itemname TEXT,date TEXT,cost TEXT)")
    conn.commit ()
    cur.execute("CREATE TABLE IF NOT EXISTS savings(amount TEXT)")
    conn.commit()
    # If the savings table is empty, initialize it with an initial amount (e.g., 1000)
    cur.execute("SELECT COUNT(*) FROM savings")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO savings VALUES(1000)")
        conn.commit()
    conn.close()

connect()

def insert(itemname, date, cost):
    conn = sqlite3.connect("expenseapp.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO expensetable VALUES(NULL,?,?,?)", (itemname, date, cost))
    conn.commit()
    conn.close()

def view():
    conn = sqlite3.connect("expenseapp.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM expensetable")
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

def search(itemname="", date="", cost=""):
    conn = sqlite3.connect("expenseapp.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM expensetable WHERE itemname=? OR date=? OR cost=?", (itemname, date, cost))
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

def savings(cost):
    try:
        total_savings = float(get_total_savings())
        cost = float(cost)
        new_savings = total_savings - cost
        if new_savings < 0:
            messagebox.showinfo("Oops something wrong", "Not enough money to make this purchase")
            return
        conn = sqlite3.connect("expenseapp.db")
        cur = conn.cursor()
        cur.execute("UPDATE savings SET amount=?", (str(new_savings),))
        conn.commit()
        conn.close()

        if new_savings < 500:
                messagebox.showwarning("Warning", "Your wallet balance is less than 500!")

    except ValueError:
        messagebox.showinfo("Oops something wrong", "Cost should be a number")


def add_money_to_wallet(amount):
    try:
        current_savings = float(get_total_savings())
        new_savings = current_savings + float(amount)
        conn = sqlite3.connect("expenseapp.db")
        cur = conn.cursor()
        cur.execute("UPDATE savings SET amount=?", (str(new_savings),))
        conn.commit()
        conn.close()
    except ValueError:
        messagebox.showinfo("Oops something wrong", "Amount should be a number")

def delete_selected_item():
    selected_item = list1.curselection()
    if not selected_item:
        messagebox.showinfo("Delete Error", "Please select an item to delete.")
        return

    selected_item_id = list1.get(selected_item)[0]  # Get the ID of the selected item
    conn = sqlite3.connect("expenseapp.db")
    cur = conn.cursor()

    # Retrieve the cost of the selected item
    cur.execute("SELECT cost FROM expensetable WHERE id=?", (selected_item_id,))
    cost_of_selected_item = cur.fetchone()[0]

    # Add the cost back to the wallet
    add_money_to_wallet(cost_of_selected_item)

    # Delete the selected item
    cur.execute("DELETE FROM expensetable WHERE id=?", (selected_item_id,))
    conn.commit()
    conn.close()

    # Update the list and labels
    list1.delete(selected_item)
    update_total_label()
    update_savings_label()

def get_total_savings():
    conn = sqlite3.connect("expenseapp.db")
    cur = conn.cursor()
    cur.execute("SELECT amount FROM savings")
    total = cur.fetchone()
    conn.commit()
    conn.close()
    return total[0] if total else 0

def deletealldata():
    conn = sqlite3.connect("expenseapp.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM expensetable")
    conn.commit()
    conn.close()
    list1.delete(0, tk.END)
    messagebox.showinfo('Successful', 'All data deleted')

def sumofitems():
    conn = sqlite3.connect("expenseapp.db")
    cur = conn.cursor()
    cur.execute("SELECT SUM(cost) FROM expensetable")
    total = cur.fetchone()
    conn.commit()
    conn.close()
    return total[0] if total[0] else 0

def insertitems():
    itemname = exp_itemname.get()
    date = exp_date.get()
    cost = exp_cost.get()

    if not itemname or not date or not cost:
        messagebox.showinfo("Oops something wrong", "All fields should be filled")
        return

    try:
        float(cost)  # Check if cost is a valid number
    except ValueError:
        messagebox.showinfo("Oops something wrong", "Cost should be a number")
        return

    insert(itemname, date, cost)
    savings(cost)
    e1.delete(0, tk.END)
    e2.delete(0, tk.END)
    e3.delete(0, tk.END)
    list1.delete(0, tk.END)
    update_total_label()
    update_savings_label()

def add_money():
    amount = money_entry.get()
    try:
        float(amount)  # Check if amount is a valid number
    except ValueError:
        messagebox.showinfo("Oops something wrong", "Amount should be a number")
        return

    add_money_to_wallet(amount)
    money_entry.delete(0, tk.END)
    update_savings_label()

def viewallitems():
    list1.delete(0, tk.END)
    list1.insert(tk.END, "ID      NAME      DATE      COST")
    for row in view():
        list1.insert(tk.END, f"{row[0]}     {row[1]}    {row[2]}    {row[3]}")
    update_total_label()

def search_item():
    list1.delete(0, tk.END)
    list1.insert(tk.END, "ID  NAME        DATE         COST")
    for row in search(exp_itemname.get(), exp_date.get(), exp_cost.get()):
        list1.insert(tk.END, f"{row[0]}         {row[1]}        {row[2]}        {row[3]}")
    e1.delete(0, tk.END)
    e2.delete(0, tk.END)
    e3.delete(0, tk.END)
    update_total_label()

def update_total_label():
    total_label.config(text=f"Total Expenses: ₹{sumofitems()}")

def update_savings_label():
    savings_label.config(text=f"Wallet: ₹{get_total_savings()}")

def recognize_product_name():
    recognizer = speech_recognition.Recognizer()
    with speech_recognition.Microphone() as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=1.0)
        voice = recognizer.listen(mic)
        recognized_text = recognizer.recognize_google(voice, language='English')
        print(f"Recognized Product Name: {recognized_text}")
        exp_itemname.set(recognized_text)

def recognize_date():
    recognizer = speech_recognition.Recognizer()
    with speech_recognition.Microphone() as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=1.0)
        try:
            voice = recognizer.listen(mic)
            recognized_text = recognizer.recognize_google(voice, language='English')
            print(f"Recognized Date: {recognized_text}")
            exp_date.set(recognized_text)
        except speech_recognition.UnknownValueError:
            print("Speech Recognition could not understand audio")
        except speech_recognition.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

def recognize_cost():
    recognizer = speech_recognition.Recognizer()
    with speech_recognition.Microphone() as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=1.0)
        try:
            voice = recognizer.listen(mic)
            recognized_text = recognizer.recognize_google(voice, language='English')
            print(f"Recognized Cost: {recognized_text}")
            exp_cost.set(recognized_text)
        except speech_recognition.UnknownValueError:
            print("Speech Recognition could not understand audio")
        except speech_recognition.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

gui = tk.Tk()
gui.title("MONEY TRACKING APP")
gui.configure(bg='#0066ff')
gui.geometry("900x700")

tk.Label(gui, width=60, height=7, font=("century", 35), bg="#1ad1ff", text="").place(x=450, y=60)
tk.Label(gui, width=100, height=10, font=("century", 35), bg="#1affd1", text="").place(x=-455, y=410)

tk.Label(gui, font=("comic sans ms", 17), bg="#0066ff", text="Product name").place(x=10, y=150)
exp_itemname = tk.StringVar()
e1 = tk.Entry(gui, font=("adobe clean", 15), textvariable=exp_itemname)
e1.place(x=220, y=155, height=27, width=165)
tk.Button(gui, text='🎙', command=recognize_product_name, bg='yellow', activebackground='red').place(x=400, y=155)

tk.Label(gui, font=("comic sans ms", 17), bg="#0066ff", text="Date").place(x=10, y=200)
exp_date = tk.StringVar()
e2 = tk.Entry(gui, font=("adobe clean", 15), textvariable=exp_date)
e2.place(x=220, y=205, height=27, width=165)
tk.Button(gui, text='🎙', command=recognize_date, bg='yellow', activebackground='red').place(x=400, y=205)

tk.Label(gui, font=("comic sans ms", 17), bg="#0066ff", text="Cost of product").place(x=10, y=250)
exp_cost = tk.StringVar()
e3 = tk.Entry(gui, font=("adobe clean", 15), textvariable=exp_cost)
e3.place(x=220, y=255, height=27, width=165)
tk.Button(gui, text='🎙', command=recognize_cost, bg='yellow', activebackground='red').place(x=400, y=255)

tk.Label(gui, font=("comic sans ms", 17), bg="#0066ff", text="Add Money to Wallet").place(x=10, y=305)
money_entry = tk.Entry(gui, font=("adobe clean", 15))
money_entry.place(x=220, y=310, height=27, width=165)
tk.Button(gui, text='Add Money', command=add_money, bg='green', activebackground='darkgreen').place(x=400, y=310)

scroll_bar = tk.Scrollbar(gui)
scroll_bar.place(x=764, y=410, height=277, width=20)

list1 = tk.Listbox(gui, height=7, width=40, font=("comic sans ms", 20), yscrollcommand=scroll_bar.set)
list1.place(x=120, y=410)
scroll_bar.config(command=list1.yview)

tk.Button(gui, text="Add Item", font=("georgia", 17), activebackground="#fffa66", activeforeground="red", width=10, command=insertitems).place(x=30, y=355)
tk.Button(gui, text="View all items", font=("georgia", 17), activebackground="#fffa66", activeforeground="red", width=12, command=viewallitems).place(x=180, y=355)
tk.Button(gui, text="Search", font=("georgia", 17), activebackground="#fffa66", activeforeground="red", width=10, command=search_item).place(x=330, y=355)
tk.Button(gui, text="Total spent", font=("georgia", 17), activebackground="#fffa66", activeforeground="red", width=15, command=sumofitems).place(x=500, y=355)
tk.Button(gui, text="Delete Selected", font=("georgia", 17), activebackground="#fffa66", activeforeground="red", width=15, command=delete_selected_item).place(x=650, y=355)

savings_label = tk.Label(gui, text=f"Wallet: ₹{get_total_savings()}", font=("comic sans ms", 17), bg="#0066ff")
savings_label.place(x=520, y=170)
total_label = tk.Label(gui, text=f"Total Spent:  ₹{sumofitems()}", font=("comic sans ms", 17), bg="#0066ff")
total_label.place(x=520, y=250)

tk.Label(gui, width=60, font=("century", 35), bg="white", fg="blue", text="MONEY TRACKING APP").place(x=-450, y=0)
name = "Welcome, Guest"
tk.Label(gui, width=60, font=("century", 30), bg="#9999ff", fg="black", text=name).place(x=-530, y=61)

ltime = tk.Label(gui, font=("century", 30), bg="#9999ff", fg="black")
ltime.place(x=470, y=61)

def digitalclock():
    text_input = time.strftime("%d-%m-%Y   %H:%M:%S")
    ltime.config(text=text_input)
    ltime.after(1000, digitalclock)

digitalclock()

gui.resizable(False, False)
gui.mainloop()
