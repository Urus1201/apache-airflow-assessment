import pandas as pd
import requests
import os
import json
import time
import logging
from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException, AirflowFailException
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Table, MetaData, and_, Column, String, Integer, Float, Date

API_URL = 'http://api-services:5000/api'
AIRFLOW_DATA_DIR = '/opt/airflow/data'
DATA_DIR = f'{AIRFLOW_DATA_DIR}/order_analysis'
DATABASE_FILE = f'{AIRFLOW_DATA_DIR}/api_database.db'

# TODO: Configure logging
# Hint: Set up a logger with appropriate formatting and level
logger = logging.getLogger(__name__)

@dag(
    description='ETL pipeline for order analysis. ' +
                'Extracts data from the microservices API and loads it into a SQLite database.',
    schedule='@daily',
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': datetime(2024, 6, 17),
        'retries': 10,
        'retry_delay': timedelta(minutes=1),
    }
    # TODO: Add catchup and max_active_runs parameters
    # Hint: Consider preventing backfills and limiting concurrent runs
)
def order_analysis_dag():

    @task(provide_context=True)
    def extract(**kwargs):
        """Extract data from the API into CSV files"""
        # TODO: Add performance metrics tracking
        # Hint: Track start and end times to measure performance
        
        # Use the execution date to get orders for the current date
        date = kwargs["logical_date"].strftime("%Y-%m-%d")

        # Skip this task if the files exist
        for file in ['customers', 'orders', 'products']:
            if os.path.exists(f'{DATA_DIR}/{file}-{date}.csv'):
                print(f'{DATA_DIR}/{file}-{date}.csv already exists, skipping extract task')
                return
        
        # Create data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)

        # TODO: Add error handling and retry logic for API calls
        # Hint: Use try-except blocks and implement retries for failed API calls
        
        # Extract data from the API
        customers = requests.get(f'{API_URL}/customers').json()
        orders = requests.get(f'{API_URL}/orders?order_date={date}').json()
        products = requests.get(f'{API_URL}/products').json()
        
        # TODO: Add data validation
        # Hint: Validate the data structure and content before proceeding
            
        # Save data to CSV files
        pd.DataFrame(customers).to_csv(f'{DATA_DIR}/customers-{date}.csv', index=False)
        pd.DataFrame(orders).to_csv(f'{DATA_DIR}/orders-{date}.csv', index=False)
        pd.DataFrame(products).to_csv(f'{DATA_DIR}/products-{date}.csv', index=False)
        
        # TODO: Return metrics for the next task to use
        # Hint: Return information about the extraction process

    @task(provide_context=True)
    def transform(**kwargs):
        """Join the data from the CSV files"""
        # TODO: Add performance metrics tracking
        # Hint: Track start and end times to measure performance

        # Use the execution date to get orders for the current date
        date = kwargs["logical_date"].strftime("%Y-%m-%d")

        # Skip this task if there are no files or they're empty
        for file in ['customers', 'orders', 'products']:
            if (
                not os.path.exists(f'{DATA_DIR}/{file}-{date}.csv')
                or os.path.getsize(f'{DATA_DIR}/{file}-{date}.csv') == 0
            ):
                print(f'{DATA_DIR}/{file}-{date}.csv does not exist or is empty, skipping transform task')
                raise AirflowSkipException

        try:
            # Load data
            customers = pd.read_csv(f'{DATA_DIR}/customers-{date}.csv')
            orders = pd.read_csv(f'{DATA_DIR}/orders-{date}.csv')
            products = pd.read_csv(f'{DATA_DIR}/products-{date}.csv')
            
            # TODO: Add data validation
            # Hint: Check for required columns and data types
            
            # TODO: Optimize this processing for better performance
            # Hint: Consider processing data in chunks for better memory usage
            
            # Normalize the product quantities from a list of {ID:quantity} dictionaries to separate rows
            normalized_orders = pd.concat(
                orders.apply(normalize_product_quantities, axis=1).values
            )

            normalized_orders.drop(columns=['product_quantities'], inplace=True)

            # Join the data
            # TODO: Optimize the join operations
            # Hint: Use indexes to improve join performance
            transformed_data = pd.merge(
                pd.merge(normalized_orders, customers, on='customer_id', how='left'),
                products, on='product_id', how='left'
            )
            
            # TODO: Handle missing values and edge cases
            # Hint: Check for nulls and implement appropriate handling
            
            # Save the transformed data to a CSV file
            transformed_data.to_csv(f'{DATA_DIR}/transformed_data-{date}.csv', index=False)
            
            # TODO: Return metrics for the next task to use
            # Hint: Return information about the transformation process
            
        except pd.errors.EmptyDataError as e:
            print(f'{e}, skipping transform task')
            raise AirflowSkipException
        except Exception as e:
            # TODO: Add better error handling
            # Hint: Log details and raise appropriate Airflow exception
            raise e

    @task(provide_context=True)
    def load(**kwargs):
        """Load the transformed data into a SQLite database"""
        # TODO: Add performance metrics tracking
        # Hint: Track start and end times to measure performance
        
        # Use the execution date to get orders for the current date
        date = kwargs["logical_date"].strftime("%Y-%m-%d")

        # Skip this task if the file is empty
        if (
            not os.path.exists(f'{DATA_DIR}/transformed_data-{date}.csv')
            or os.path.getsize(f'{DATA_DIR}/transformed_data-{date}.csv') == 0
        ):
            print(f'{DATA_DIR}/transformed_data-{date}.csv does not exist or is empty, skipping load task')
            raise AirflowSkipException
        
        # Read transformed data
        transformed_data = pd.read_csv(f'{DATA_DIR}/transformed_data-{date}.csv')
        transformed_data['order_date'] = pd.to_datetime(date)

        # TODO: Add data validation before loading
        # Hint: Ensure data integrity before database operations
        
        # Set up database connection
        conn, final_data_table = setup_database_connection()
        
        # TODO: Add transaction management
        # Hint: Use database transactions to ensure all-or-nothing updates
        
        # TODO: Implement batch processing for better performance
        # Hint: Process data in batches instead of row-by-row
        
        # Insert or update data in the database
        for _index, row in transformed_data.iterrows():
            upsert(conn, final_data_table, row)
        
        conn.close()
        
        rows_inserted = len(transformed_data)
        print(f'{rows_inserted} rows inserted into final_data table')
        
        # TODO: Return metrics about the load process
        # Hint: Return information about the database operations

    # Define the task dependencies
    # TODO: Update task dependencies to pass data between tasks
    # Hint: Use the task outputs to pass data between tasks
    extract() >> transform() >> load()

# Instantiate the DAG
order_analysis_dag()

# Utility functions

def normalize_product_quantities(row):
    """Normalize product quantities from JSON to separate rows"""
    product_quantities = json.loads(row['product_quantities'].replace("'", '"'))
    normalized_rows = []
    for product_id, quantity in product_quantities.items():
        normalized_row = row.copy()
        normalized_row['product_id'] = product_id
        normalized_row['quantity'] = quantity
        normalized_rows.append(normalized_row)
    return pd.DataFrame(normalized_rows)

# TODO: Add retry mechanism for API calls
# Hint: Implement a function that retries API calls with exponential backoff

# TODO: Add data validation functions
# Hint: Create functions to validate the structure and content of data

def setup_database_connection():
    """Set up a connection to the SQLite database"""
    engine = create_engine(f'sqlite:///{DATABASE_FILE}')
    conn = engine.connect()
    metadata = MetaData(bind=engine)

    final_data_table = Table('final_data', metadata,
        Column('order_id', String, primary_key=True),
        Column('customer_id', String, primary_key=True),
        Column('product_id', String, primary_key=True),
        Column('product_name', String),
        Column('product_description', String),
        Column('product_price', Float),
        Column('quantity', Integer),
        Column('order_date', Date),
        Column('order_total', Float),
        Column('first_name', String),
        Column('last_name', String),
        Column('email', String),
        Column('address', String),
        Column('phone_number', String),
        Column('state', String),
        Column('city', String),
        Column('zip_code', String),
        extend_existing=True,
    )

    # Create the table if it doesn't exist
    metadata.create_all(engine)
    return conn, final_data_table

def upsert(conn, table, row):
    """Insert or update a row in the database"""
    # TODO: Optimize this function for better performance
    # Hint: Consider batch operations instead of row-by-row processing
    
    # Try to fetch existing row
    stmt = table.select().where(
        and_(
            table.c.order_id == row['order_id'],
            table.c.customer_id == row['customer_id'],
            table.c.product_id == row['product_id']
        )
    )
    result = conn.execute(stmt).fetchone()

    if result:
        # Update existing row
        stmt = table.update().where(
            and_(
                table.c.order_id == row['order_id'],
                table.c.customer_id == row['customer_id'],
                table.c.product_id == row['product_id']
            )
        ).values(row.to_dict())
    else:
        # Insert new row
        stmt = table.insert().values(row.to_dict())

    conn.execute(stmt)

# TODO: Add batch upsert functionality
# Hint: Implement a function that processes records in batches for better performance