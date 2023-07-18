import openai
import argparse
import getpass
import mysql.connector
import inquirer
import re
from termcolor import colored

def chat_with_gpt(api_key, messages):
    try:
        openai.api_key = api_key
        formatted_messages = [{'role': 'system', 'content': messages[0]}]
        for message in messages[1:]:
            formatted_messages.append({
                'role': 'user',
                'content': message + '\n\nWrap all sql codes.'
            })
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=formatted_messages
        )
        return response['choices'][0]['message']['content']
    except Exception as err:
        print(colored(f"Failed to connect to OpenAI: {err}", 'yellow'))
        return None

def connect_to_database(user, password, host, port):
    try:
        cnx = mysql.connector.connect(user=user, password=password,
                                      host=host, port=port)
        return cnx
    except mysql.connector.Error as err:
        print(colored(f"Failed to connect to MySQL: {err}", 'yellow'))
        return None

def get_databases(cnx):
    cursor = cnx.cursor()
    cursor.execute("SHOW DATABASES")
    databases = [db[0] for db in cursor]
    cursor.close()
    return databases

def get_schema_and_tables(cnx, database):
    cursor = cnx.cursor()
    cursor.execute(f"USE {database}")
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor]

    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s
    """, (database,))
    schema_info = cursor.fetchall()

    schema = {}
    for table_name, column_name, data_type in schema_info:
        if table_name not in schema:
            schema[table_name] = []
        schema[table_name].append((column_name, data_type))

    cursor.close()
    return schema, tables

def execute_command(cnx, command):
    cursor = cnx.cursor()
    try:
        cursor.execute(command)
        results = cursor.fetchall()
        print("Command executed successfully. Results:")
        for row in results:
            print(row)
    except mysql.connector.Error as err:
        print(colored(f"Failed to execute command: {err}", 'yellow'))
    finally:
        cursor.close()

def extract_sql_code(text):
    match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def main():
    parser = argparse.ArgumentParser(description='Chat with GPT-3.')
    args = parser.parse_args()

    response = None
    while response is None:
        api_key = getpass.getpass("Please enter your OpenAI API key: ")
        response = chat_with_gpt(api_key, ["Hello, world!", "Hello, world!"])

    cnx = None
    while cnx is None:
        db_user = input("Please enter your MySQL username: ")
        db_password = getpass.getpass("Please enter your MySQL password: ")
        db_host = input("Please enter your MySQL host: ")
        db_port = input("Please enter your MySQL port: ")

        cnx = connect_to_database(db_user, db_password, db_host, db_port)

    databases = get_databases(cnx)
    questions = [
        inquirer.List('db',
                      message="Please select a database",
                      choices=databases,
                      ),
    ]
    answers = inquirer.prompt(questions)
    db_database = answers['db']

    schema, tables = get_schema_and_tables(cnx, db_database)
    schema_message = f"Schema of the mysql db '{db_database}':\n\n"
    for table_name, columns in schema.items():
        schema_message += f"Table '{table_name}':\n"
        for column_name, data_type in columns:
            schema_message += f"  - {column_name}: {data_type}\n"
    schema_message += """Responde SQL queries according to schema.
    Quote all columns and tables to be safe.\nWrap all sql codes.\n"""


    print(schema_message)

    messages = [schema_message]

    print("Tables in the database:", ", ".join(tables))

    print("You can start chatting with GPT now. Type 'quit' to exit.")
    while True:
        user_message = input("> ")
        if user_message.lower() == 'quit':
            break
        messages.append(user_message)
        response = chat_with_gpt(api_key, messages)

        # Extract SQL code
        sql_code = extract_sql_code(response)
        if sql_code:
            execute = input(f"Do you want to execute this command? (yes/no)\n{colored(sql_code, 'green')}\n> ")
            if execute.lower() == 'yes':
                try:
                    execute_command(cnx, sql_code)
                except Exception as err:
                    print(colored(f"Failed to execute command: {err}", 'yellow'))
        else:
            print(response)


    cnx.close()

if __name__ == '__main__':
    main()
