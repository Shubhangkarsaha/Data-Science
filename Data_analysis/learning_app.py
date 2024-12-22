import mysql.connector
from mysql.connector import pooling
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import seaborn as sns

# Database connection pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    pool_reset_session=True,
    host="127.0.0.1",
    user="root",
    passwd="",
    database="LearningDB"
)

# Function to fetch data from the database
def fetch_data():
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM learning_data"
    cursor.execute(query)
    rows = cursor.fetchall()
    connection.close()
    return pd.DataFrame(rows)

# Function to fetch a specific row by serial_no
def fetch_data_by_serial(serial_no):
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM learning_data WHERE Serial_no = %s"
    cursor.execute(query, (serial_no,))
    row = cursor.fetchone()
    connection.close()
    return row

# Function to insert new data into the database
def insert_data(row):
    connection = db_pool.get_connection()
    cursor = connection.cursor()
    query = """
        INSERT INTO learning_data (
            Serial_no, Date, Time_From, Time_To, Topic, Type_of_Learning, 
            Duration_min, Focus_Level, Difficulty, Energy_Level, 
            Distraction_Level, Completion_Percentage, Learning_Mode, Completion_Rate
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, row)
    connection.commit()
    connection.close()

# Function to update existing data in the database
def update_data(serial_no, updated_row):
    connection = db_pool.get_connection()
    cursor = connection.cursor()
    query = """
        UPDATE learning_data 
        SET Date=%s, Time_From=%s, Time_To=%s, Topic=%s, Type_of_Learning=%s, 
            Duration_min=%s, Focus_Level=%s, Difficulty=%s, Energy_Level=%s, 
            Distraction_Level=%s, Completion_Percentage=%s, Learning_Mode=%s, Completion_Rate=%s
        WHERE Serial_no=%s
    """
    cursor.execute(query, (*updated_row, serial_no))
    connection.commit()
    connection.close()

# Function to delete data from the database
def delete_data(serial_no):
    connection = db_pool.get_connection()
    cursor = connection.cursor()
    query = "DELETE FROM learning_data WHERE Serial_no=%s"
    cursor.execute(query, (serial_no,))
    connection.commit()
    connection.close()

# Function to display the dashboard (graph section)
def plot_data():
    data = fetch_data()

    # Clear the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Create a figure
    fig, axs = plt.subplots(2, 2, figsize=(12, 8), dpi=100)
    fig.tight_layout(pad=4)

    # Plot 1: Duration by Topic (Bar chart)
    data_grouped = data.groupby("Topic")["Duration_min"].sum().sort_values()
    axs[0, 0].bar(data_grouped.index, data_grouped.values, color='skyblue')
    axs[0, 0].set_title("Total Duration by Topic")
    axs[0, 0].set_ylabel("Minutes")
    axs[0, 0].set_xlabel("Topics")
    axs[0, 0].tick_params(axis='x', rotation=45, labelsize=8)

    # Plot 2: Learning Mode Distribution (Pie chart)
    learning_mode_counts = data["Learning_Mode"].value_counts()
    axs[0, 1].pie(learning_mode_counts, labels=learning_mode_counts.index, autopct='%1.1f%%', startangle=140)
    axs[0, 1].set_title("Learning Mode Distribution")

    # Plot 3: Focus vs Completion Rate (Box plot)
    sns.boxplot(data=data, x="Focus_Level", y="Completion_Rate", ax=axs[1, 0])
    axs[1, 0].set_title("Focus Level vs Completion Rate")
    axs[1, 0].set_xlabel("Focus Level")
    axs[1, 0].set_ylabel("Completion Rate (%)")

    # Plot 4: Focus vs Duration (Line graph)
    data_sorted = data.sort_values("Focus_Level")
    axs[1, 1].plot(data_sorted["Focus_Level"], data_sorted["Duration_min"], marker='o', color='green')
    axs[1, 1].set_title("Focus Level vs Duration")
    axs[1, 1].set_xlabel("Focus Level")
    axs[1, 1].set_ylabel("Duration (min.)")

    # Attach the figure to the Tkinter canvas
    canvas = FigureCanvasTkAgg(fig, master=content_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Function to display data in a table
def show_data_table():
    data = fetch_data()

    # Clear the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Create a treeview to display data
    tree = ttk.Treeview(content_frame, columns=list(data.columns), show="headings")
    tree.pack(fill=tk.BOTH, expand=True)

    # Add column headings
    for col in data.columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    # Add rows
    for _, row in data.iterrows():
        tree.insert("", "end", values=row.to_list())

    # Add Edit and Delete buttons below the TreeView
    button_frame = tk.Frame(content_frame)
    button_frame.pack(fill=tk.X, pady=10)

    tk.Button(button_frame, text="Edit Selected", command=lambda: edit_selected(tree), bg="#3498DB", fg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="Delete Selected", command=lambda: delete_selected(tree), bg="#E74C3C", fg="white").pack(side=tk.LEFT, padx=10)

# Function to edit selected data
def edit_selected(tree):
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showerror("Selection Error", "No record selected!")
        return

    values = tree.item(selected_item, "values")
    serial_no = values[0]
    row = fetch_data_by_serial(serial_no)

    if row:
        edit_data(serial_no, row)

def edit_data(serial_no, row):
    for widget in content_frame.winfo_children():
        widget.destroy()

    form_frame = tk.Frame(content_frame)
    form_frame.pack(pady=20)

    labels = list(row.keys())
    entries = {}

    for idx, key in enumerate(labels):
        tk.Label(form_frame, text=key+":").grid(row=idx, column=0, padx=5, pady=5)
        entry = tk.Entry(form_frame)
        entry.insert(0, row[key])
        entry.grid(row=idx, column=1, padx=5, pady=5)
        entries[key] = entry

    def save_changes():
        updated_row = tuple(entries[key].get() for key in labels[1:])
        update_data(serial_no, updated_row)
        show_data_table()

    tk.Button(form_frame, text="Save Changes", command=save_changes, bg="#2ECC71", fg="white").grid(row=len(labels), column=0, columnspan=2, pady=10)

# Function to delete selected data
def delete_selected(tree):
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showerror("Selection Error", "No record selected!")
        return

    values = tree.item(selected_item, "values")
    serial_no = values[0]

    if messagebox.askyesno("Delete Confirmation", f"Are you sure you want to delete Serial No {serial_no}?"):
        delete_data(serial_no)
        show_data_table()

# Function to search data by serial number
def search_data_by_serial():
    serial_no = search_entry.get().strip()

    if not serial_no:
        messagebox.showerror("Input Error", "Please enter a Serial No.")
        return

    row = fetch_data_by_serial(serial_no)

    if row:
        display_row_data(row)
    else:
        messagebox.showerror("Record Not Found", f"No record found with Serial No {serial_no}.")

def display_row_data(row):
    for widget in content_frame.winfo_children():
        widget.destroy()

    row_frame = tk.Frame(content_frame)
    row_frame.pack(pady=20)

    for idx, (key, value) in enumerate(row.items()):
        tk.Label(row_frame, text=f"{key}:").grid(row=idx, column=0, padx=5, pady=5)
        tk.Label(row_frame, text=value).grid(row=idx, column=1, padx=5, pady=5)

# Function to add new data
def add_new_data():
    for widget in content_frame.winfo_children():
        widget.destroy()

    form_frame = tk.Frame(content_frame)
    form_frame.pack(pady=20)

    fields = [
        "Serial_no", "Date", "Time_From", "Time_To", "Topic", "Type_of_Learning",
        "Duration_min", "Focus_Level", "Difficulty", "Energy_Level",
        "Distraction_Level", "Completion_Percentage", "Learning_Mode", "Completion_Rate"
    ]
    entries = {}

    for idx, field in enumerate(fields):
        tk.Label(form_frame, text=field+":").grid(row=idx, column=0, padx=5, pady=5)
        entry = tk.Entry(form_frame)
        entry.grid(row=idx, column=1, padx=5, pady=5)
        entries[field] = entry

    def save_data():
        row = tuple(entries[field].get() for field in fields)

        if any(value.strip() == "" for value in row):
            messagebox.showerror("Input Error", "All fields are required!")
            return

        try:
            insert_data(row)
            show_data_table()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(form_frame, text="Add Data", command=save_data, bg="#2ECC71", fg="white").grid(row=len(fields), column=0, columnspan=2, pady=10)

# Main application window
root = tk.Tk()
root.title("Learning Data Dashboard")
root.geometry("1024x768")

# Sidebar
sidebar = tk.Frame(root, bg="#2C3E50", width=200)
sidebar.pack(fill=tk.Y, side=tk.LEFT)

tk.Label(sidebar, text="Dashboard", bg="#2C3E50", fg="white", font=("Arial", 16)).pack(pady=10)

tk.Button(sidebar, text="Dashboard", command=plot_data, bg="#3498DB", fg="white").pack(fill=tk.X, padx=10, pady=5)
tk.Button(sidebar, text="View Data", command=show_data_table, bg="#3498DB", fg="white").pack(fill=tk.X, padx=10, pady=5)
tk.Button(sidebar, text="Add Data", command=add_new_data, bg="#3498DB", fg="white").pack(fill=tk.X, padx=10, pady=5)

tk.Label(sidebar, text="Search Serial No", bg="#2C3E50", fg="white").pack(pady=5)
search_entry = tk.Entry(sidebar)
search_entry.pack(pady=5)
tk.Button(sidebar, text="Search", command=search_data_by_serial, bg="#3498DB", fg="white").pack(fill=tk.X, padx=10, pady=5)

# Content frame
content_frame = tk.Frame(root, bg="white")
content_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)

# Start with the dashboard
plot_data()

root.mainloop()
