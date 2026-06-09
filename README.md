# Software Purchase Billing System (Flask & MySQL)

A modern, high-fidelity **Software Purchase Billing System** developed using **Python, Flask, MySQL, Bootstrap 5, and Custom CSS**. This system provides a premium user interface with a glassmorphism theme, real-time sales statistics widgets, customer search functionality, sequential bill numbering, and professional print/PDF invoice generation.

---

## Features

1. **Dashboard Overview**: View live total revenue, sales counts, and unique customer statistics.
2. **Billing Records List**: View all past transactions, search instantly by customer name or phone number.
3. **New Invoice Generator**: Custom forms with autocomplete inputs for popular software, plus a built-in mock **License Key Generator**.
4. **Professional Invoice Layout**: A clean print-friendly invoice displaying customer details, version control, unit rates, tax breakdowns (GST at 18%), and a digital PAID stamp.
5. **PDF Export & Printing**: One-click browser print layout styling and instant client-side PDF downloading via `html2pdf.js`.

---

## Prerequisites

Before running the application, make sure you have the following installed:

1. **Python** (version 3.8 or above)
2. **VS Code** (Visual Studio Code)
3. **MySQL Server** (via direct installation, XAMPP, or WampServer)

---

## Step-by-Step Setup in VS Code

### Step 1: Open Project in VS Code
1. Open VS Code.
2. Click **File > Open Folder** and select the project directory:  
   `c:\Users\patel\OneDrive\Desktop\A1`

---

### Step 2: Start MySQL Server
Make sure your MySQL server is running. 
- If using **XAMPP**, open the XAMPP Control Panel and click **Start** next to MySQL.
- If using **MySQL Installer/Service**, ensure the service is running.
- By default, the application connects using the following standard credentials:
  - **Host**: `localhost`
  - **Port**: `3306`
  - **User**: `root`
  - **Password**: *(Empty / No Password)*

> [!NOTE]
> If your MySQL configurations differ, you can set the following environment variables in your command prompt before launching the app, or customize them in `database.py`:
> ```powershell
> $env:DB_HOST="localhost"
> $env:DB_USER="your_username"
> $env:DB_PASSWORD="your_password"
> $env:DB_PORT="3306"
> ```

---

### Step 3: Open Terminal & Create Virtual Environment
1. In VS Code, open the integrated terminal: **Terminal > New Terminal** (or press `` Ctrl + ` ``).
2. Create a virtual environment by running:
   ```powershell
   python -m venv venv
   ```
3. Activate the virtual environment:
   - On Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - On Windows (Command Prompt):
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   *(You will see `(venv)` prefixing your terminal prompt when activated successfully).*

---

### Step 4: Install Dependencies
Install all required libraries (`Flask`, `PyMySQL`, `cryptography`):
```powershell
pip install -r requirements.txt
```

---

### Step 5: Initialize Database & Table
The application automatically creates the database `software_billing_db` and the required `bills` table on startup. 

However, if you want to test your connection or initialize it manually, you can run:
```powershell
python database.py
```
If successful, you will see the output:
`✅ Database initialized successfully!`

*(If it fails, double-check that your MySQL server is running and your database username/password match the values in `database.py`).*

---

### Step 6: Start the Flask Application
Run the main script to start the web server:
```powershell
python app.py
```

You will see output indicating the server is running:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

### Step 7: Access and Use the System
1. Open your web browser and go to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.
2. Click **New Software Purchase** to create a purchase record:
   - Fill in Customer Name, 10-digit Phone Number, and Address.
   - Enter Software details (choose a popular software from the autocomplete datalist or write your own).
   - Input the price.
   - Click **Auto-Generate** to create a mock product license key.
   - Click **Generate & Save Invoice**.
3. You will be redirected to the generated **Tax Invoice**. Click **Print Invoice** or **Download PDF** to save it!
4. Return to the **Dashboard** to see the updated revenue counters and query customer records using the search bar.
