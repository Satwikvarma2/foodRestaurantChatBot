from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import db_helper
import helper_reg
from fastapi.responses import FileResponse

app = FastAPI()

inprogress_orders={}

app = FastAPI()

# Mount the static directory to serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    print(output_contexts)

    session_id=extract_session_id(output_contexts[0]['name'])

    print(intent)

    intent_handler_dict = {
        'order.add': add_to_order,
        'track.order context:ongoing-tracking': track_order,
        'order.complete':order_complete,
        'order.remove context:ongoing':remove_from_my_order
    }
    return intent_handler_dict[intent](parameters,session_id)


def extract_session_id(session_str:str):
    import re
    pattern = r"sessions/([a-fA-F0-9\-]{36})/"
    match = re.search(pattern, session_str)
    if match:
        session_id = match.group(1)
        return session_id


def remove_from_my_order(parameters,session_id):
    removed_items =[]
    itemsNotCurrent=[]
    if session_id in inprogress_orders:
        food_items=parameters["food-item"]
        current_order= inprogress_orders[session_id]
        for item in food_items:
            if item not in current_order:
                itemsNotCurrent.append(item)
            else:
                removed_items.append(item)
                del current_order[item]

        if len(removed_items)>0:
            fulfillmentText=f"Items {', '.join(removed_items)} are removed from the order."

        if len(itemsNotCurrent)>0:
            fulfillmentText=f"These orders {', '.join(removed_items)} are not in your order."

        if len(current_order)==0:
            fulfillmentText += "You order is empty now please order!!"
        else:
            order_str = helper_reg.get_str_from_food_dict2(current_order)
            print(order_str)
            fulfillmentText += f"here is what is left in the order {order_str}"

        return JSONResponse(content={
            "fulfillmentText": fulfillmentText
        })




def add_to_order(parameters: dict,session_id):
    flag=False
    food_items = parameters["food-item"]
    quantities = parameters["number"]
    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry I didn't understand. Can you please specify food items and quantities clearly?"
        flag=True
    else:
        new_food_dict=dict(zip(food_items,quantities))
        fulfillment_text = f" Received {food_items} and quantities {quantities} in the back end"
    if flag==False:
        if session_id in inprogress_orders:
            current_food_dict=inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id]=current_food_dict
        else:
           inprogress_orders[session_id]=new_food_dict

    order_str=helper_reg.get_str_from_food_dict2(inprogress_orders[session_id])
    fulfillment_text= f"so far you have {order_str} do you want to order anything else, please mention the product name for me to understand"
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def order_complete(parameters,session_id):
    if session_id not in inprogress_orders:
        fulfillment_text="I think I am having some trouble with your order!. Can you try it once more"
    else:
        order=inprogress_orders[session_id]
        order_id=save_to_db(order)

        if order_id == -1:
            fulfillment_text=" Sorry we are having a issue with your order can you try ordering again"
        else:
            order_total=db_helper.get_order_total(order_id)
            fulfillment_text=(f"Great, your order has been succesfully placed, "
                              f"your order_id is {order_id},"
                              f" your total comes up as ${order_total} you can pay this amount at the time of delivery")
    del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def save_to_db(order):
    next_order_id=db_helper.get_next_order_id()
    print(next_order_id)
    for food_items,quantity in order.items():
        db_helper.insert_order_item(food_items,
                                    quantity,
                                    next_order_id)
    db_helper.insert_order_tracking(next_order_id,"in progress")
    return next_order_id

def track_order(parameters:dict,session_id):
    order_id=int(parameters['number6'][0])
    order_status = db_helper.get_order_status(order_id)

    if order_status:
        fulfilmentText=f"the order status for the {order_id} is {order_status}"
    else:
        fulfilmentText=f"No order found with order_id {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfilmentText
    })


