import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timedelta
import pandas as pd
from streamlit_option_menu import option_menu
import time

# SQLAlchemy setup
Base = declarative_base()

# Database models
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

class Machine(Base):
    __tablename__ = 'machines'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    last_maintenance = Column(DateTime, default=datetime.now)

class Production(Base):
    __tablename__ = 'productions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    run_time = Column(Float, nullable=False)  # Run time in hours
    production_quantity = Column(Integer, nullable=False)  # Quantity produced

# Create database connection (SQLite for example)
DATABASE_URL = "sqlite:///manufacturing.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()

# Function to create a top navigation bar
def main():
    selected = option_menu(
        menu_title=None,
        options=["Home", "Add Machine", "Add Product", "Production Data", "Daily Report"],
        icons=["house", "gear", "box", "list-task", "file-earmark-text"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "black"},
            "icon": {"color": "white", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#333"},
            "nav-link-selected": {"background-color": "#02ab21"},
        }
    )

    if selected == "Home":
        home_page()
    elif selected == "Add Machine":
        add_machine_page()
    elif selected == "Add Product":
        add_product_page()
    elif selected == "Production Data":
        production_data_page()
    elif selected == "Daily Report":
        daily_report_page()

# Home Page
def home_page():
    st.title("Manufacturing Asset Management")
    st.write("Welcome to the Manufacturing Asset Management System!")

# Page to add a machine
def add_machine_page():
    st.title("Add New Machine")
    with st.form("machine_form"):
        machine_name = st.text_input("Machine Name")
        machine_status = st.selectbox("Status", ("Running", "Idle", "Maintenance"))
        submitted = st.form_submit_button("Add Machine")

        if submitted:
            if machine_name.strip() == "":
                st.error("Machine name cannot be empty!")
            else:
                new_machine = Machine(name=machine_name, status=machine_status)
                session.add(new_machine)
                session.commit()
                st.success(f"Added machine: {machine_name}")
                st.balloons()

# Page to add a product
def add_product_page():
    st.title("Add New Product")
    product_name = st.text_input("Product Name")
    product_price = 0.0
    quantity = st.number_input("Quantity", min_value=0)
    submitted = st.button("Add Product")

    if submitted:
        if product_name.strip() == "":
            st.error("Product name cannot be empty!")
        elif quantity <= 0:
            st.error("Quantity must be greater than 0!")
        else:
            new_product = Product(name=product_name, price=product_price, quantity=quantity)
            session.add(new_product)
            session.commit()
            st.success(f"Added product: {product_name} with price: ₹{product_price:.2f}")
            st.balloons()

# Page to display production data
def production_data_page():
    st.title("Production Data")
    productions = session.query(Production).all()
    if productions:
        production_data = {
            "Production ID": [prod.id for prod in productions],
            "Machine ID": [prod.machine_id for prod in productions],
            "Start Time": [prod.start_time.strftime("%Y-%m-%d %H:%M:%S") for prod in productions],
            "End Time": [prod.end_time.strftime("%Y-%m-%d %H:%M:%S") if prod.end_time else "Running" for prod in productions],
            "Run Time (hours)": [prod.run_time for prod in productions],
            "Production Quantity": [prod.production_quantity for prod in productions]
        }
        production_df = pd.DataFrame(production_data)
        st.dataframe(production_df)
    else:
        st.write("No production data available.")

# Daily Report Page
def daily_report_page():
    st.title("Daily Report")
    machines = session.query(Machine).all()
    report_data = []

    for machine in machines:
        productions = session.query(Production).filter(Production.machine_id == machine.id).all()
        total_run_time = sum(prod.run_time for prod in productions)
        total_production_quantity = sum(prod.production_quantity for prod in productions)
        
        report_data.append({
            "Machine Name": machine.name,
            "Total Run Time (hours)": total_run_time,
            "Total Production Quantity": total_production_quantity
        })

    if report_data:
        report_df = pd.DataFrame(report_data)
        st.dataframe(report_df)
    else:
        st.write("No report data available.")

# Machine Monitoring with Start/Stop Button
def monitor_machine(machine_id):
    machine = session.query(Machine).get(machine_id)
    if machine is None:
        st.error("Machine not found.")
        return

    if st.button(f"Start Monitoring {machine.name}"):
        st.session_state.running_machine = machine_id
        start_time = datetime.now()
        production_quantity = 0  # Initialize production quantity

        while machine.status == "Running":
            # Simulate production
            production_quantity += 1  # Simulate producing 1 unit
            time.sleep(1)  # Simulate time taken to produce 1 unit
            # Update run time in production table
            run_time = (datetime.now() - start_time).total_seconds() / 3600.0
            production_entry = Production(machine_id=machine.id, start_time=start_time, end_time=None, run_time=run_time, production_quantity=production_quantity)
            session.add(production_entry)
            session.commit()

        st.success(f"Monitoring {machine.name} stopped. Total Production: {production_quantity} units.")

    elif st.button(f"Stop Monitoring {machine.name}"):
        if hasattr(st.session_state, 'running_machine') and st.session_state.running_machine == machine_id:
            machine.status = "Idle"  # Update machine status
            session.commit()
            st.session_state.running_machine = None
        else:
            st.warning("This machine is not currently being monitored.")

# Run the app
if __name__ == "__main__":
    st.set_page_config(page_title="Manufacturing Asset Management", layout="wide")
    main()
