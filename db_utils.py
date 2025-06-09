import os
import pyodbc
import streamlit as st
from datetime import datetime
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Create and return a connection to the MS SQL Server database"""
    try:
        # Get database connection details from environment variables
        server = os.environ.get("SQL_SERVER")
        database = os.environ.get("SQL_DATABASE")
        username = os.environ.get("SQL_USERNAME")
        password = os.environ.get("SQL_PASSWORD")
        
        # Create connection string
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        
        # Create connection
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def ensure_tables_exist():
    """Ensure required tables exist in the database"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
            
        cursor = conn.cursor()
        
        # Create logins table if it doesn't exist
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'logins')
        BEGIN
            CREATE TABLE logins (
                id INT IDENTITY(1,1) PRIMARY KEY,
                display_name NVARCHAR(255),
                username NVARCHAR(255),
                email NVARCHAR(255),
                department NVARCHAR(255),
                login_time DATETIME,
                reporting_period NVARCHAR(6),
                client_ip NVARCHAR(50),
                user_agent NVARCHAR(500),
                session_id NVARCHAR(255)
            )
        END
        """)
        
        # Create usage table if it doesn't exist
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'usage')
        BEGIN
            CREATE TABLE usage (
                id INT IDENTITY(1,1) PRIMARY KEY,
                display_name NVARCHAR(255),
                username NVARCHAR(255),
                email NVARCHAR(255),
                app_name NVARCHAR(255),
                app_category NVARCHAR(255),
                app_action NVARCHAR(MAX),
                usage_time DATETIME,
                reporting_period NVARCHAR(6),
                session_id NVARCHAR(255)
            )
        END
        """)
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring tables exist: {str(e)}")
        return False

def log_user_login(user_data):
    """Log user login information to the 'logins' table"""
    try:
        # Extract user data
        display_name = user_data.get("displayName", "Unknown")
        user_email = user_data.get("mail", "Unknown")
        username = user_data.get("userPrincipalName", user_email)
        department = user_data.get("department", "Unknown")
        
        # Get current datetime and reporting period
        current_time = datetime.now()
        reporting_period = current_time.strftime("%Y%m")
        
        # Generate a session ID if not already in session state
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        session_id = st.session_state.session_id
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        # Ensure tables exist
        ensure_tables_exist()
        
        # Create cursor
        cursor = conn.cursor()
        
        # Insert login record
        cursor.execute("""
        INSERT INTO logins (display_name, username, email, department, login_time, reporting_period, client_ip, user_agent, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            display_name,
            username,
            user_email,
            department,
            current_time,
            reporting_period,
            os.environ.get("REMOTE_ADDR", "Unknown"),
            os.environ.get("HTTP_USER_AGENT", "Unknown"),
            session_id
        ))
        
        # Commit the transaction
        conn.commit()
        
        # Close the connection
        conn.close()
        
        logger.info(f"User login logged successfully: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error logging user login: {str(e)}")
        return False

def log_app_usage(app_id, app_metadata=None):
    """Log application usage information to the 'usage' table"""
    try:
        if not st.session_state.get("authenticated", False):
            return False
            
        # Extract user data from session state
        display_name = st.session_state.get("display_name", "Unknown")
        user_email = st.session_state.get("user_email", "Unknown")
        username = user_email  # Using email as username if not available
        
        # If app_metadata is not provided, try to get it from APP_METADATA
        if not app_metadata and app_id in st.session_state.get("APP_METADATA", {}):
            app_metadata = st.session_state.APP_METADATA[app_id]
        
        # If we still don't have metadata, use defaults
        if not app_metadata:
            app_name = app_id
            app_category = "Unknown"
            app_action = f"Accessed {app_id}"
        else:
            app_name = app_metadata.get("name", app_id)
            app_category = app_metadata.get("category", "Unknown")
            parent_app = app_metadata.get("parent_app", "")
            sub_app = app_metadata.get("sub_app", "")
            
            # Create descriptive action
            app_action = f"Launched {app_name}"
            if parent_app and parent_app != app_name:
                app_action += f" from {parent_app}"
            if sub_app and sub_app != "None":
                app_action += f" - {sub_app}"
        
        # Get current datetime and reporting period
        current_time = datetime.now()
        reporting_period = current_time.strftime("%Y%m")
        
        # Use existing session_id or create new one
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        session_id = st.session_state.session_id
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        # Ensure tables exist
        ensure_tables_exist()
        
        # Create cursor
        cursor = conn.cursor()
        
        # Insert usage record
        cursor.execute("""
        INSERT INTO usage (display_name, username, email, app_name, app_category, app_action, usage_time, reporting_period, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            display_name,
            username,
            user_email,
            app_name,
            app_category,
            app_action,
            current_time,
            reporting_period,
            session_id
        ))
        
        # Commit the transaction
        conn.commit()
        
        # Close the connection
        conn.close()
        
        logger.info(f"App usage logged successfully: {username} - {app_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error logging app usage: {str(e)}")
        return False
