import re



def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = cnx.cursor()

        # Calling the stored procedure
        cursor.callproc('insert_order_item', (food_item, quantity, order_id))

        # Committing the changes
        cnx.commit()

        # Closing the cursor
        cursor.close()

        print("Order item inserted successfully!")

        return 1

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")

        # Rollback changes if necessary
        cnx.rollback()

        return -1

    except Exception as e:
        print(f"An error occurred: {e}")
        # Rollback changes if necessary
        cnx.rollback()

        return -1


def extract_session_id(session_str:str):

    pattern = r"sessions/([a-fA-F0-9\-]{36})/"
    match = re.search(pattern, session_str)
    if match:
        session_id = match.group(1)
        print(session_id)


def get_str_from_food_dict(food_dict: dict):
    result = ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
    return result

def get_str_from_food_dict2(food_dict: dict):
   result=",".join([f"{int(value)} {key}" for key,value in food_dict.items()])
   return result





if __name__=="__main__":
    print(get_str_from_food_dict2(food_dict))