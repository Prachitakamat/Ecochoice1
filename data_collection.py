import requests
import re
from serpapi import GoogleSearch
print("serpapi imported")
api_key = ""
api_url="https://api.openai.com/v1/chat/completions"

def fetch_data(url, headers, payload):
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("request error",e)

def generate_data(product):
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt=(f"Generate a list of 3 eco-friendly {product}."
            "Begin with '###' before every product. For example, ###Product 1: (product name)."
            "Include manufacturer name, price (mention the currency(INR) after the price in numbers), quantity, and a brief description(200 characters)."
            "Provide the certifications the product has."
            "Each product's information should follow this strict format:"
            "###Product 1: product name"
            "Manufacturer: Manufacturer name"
            "Price: price (like 500 rupees)"
            "Quantity: quantity "
            "Description: description"
            "Certifications:(cannot be None)")#prompt text

    data_payload={
        "model":"gpt-4o",
        "messages": [
            {"role": "system",
             "content":("You are a strict environmental compliance analyst and database ingest tool. "
                        "Your job is to look for eco-friendly products."
                        "Do not accept vague marketing words like 'eco-friendly' or 'green'."
                        "Look for evidence based on raw materials, packaging, distribution, and disposal."
                        "Follow the Life Cycle Assessment method."
                        "Check for third party sustainability certifications."
                        "Products must be relevant and in use in India."
                        "Return strictly what product is asked for."
                        ) },
            {"role": "user",
             "content": prompt}
        ],
        "temperature":0.0
    }

    try:
        data = fetch_data(api_url, headers, data_payload)
        if 'choices' in data:
            extracted_text = data['choices'][0]['message']['content']

        else:
            return[]
        return extracted_text
    except requests.exceptions.RequestException as e:
        print("request error",e)
        return []



missing_data=[]
def parse_data(product_blocks, product_type):
    products=[]
    for product_block in product_blocks:
        block_no=-1

        try:
            block_no+=1

            #name
            match=re.search(r"Product (\d+):\s*(.*)", product_block, re.IGNORECASE)
            if not match:
                pass
                #missing_data.append(f'pid of block {block_no} in category {product_type}')
                #raise Exception

            i=str(match.group(1).strip())
            pid=str(product_type+1)+i
            product_name = match.group(2).strip()
            #products+=[product_name.split(": ")[1].strip()]

            #manufacturer
            match=re.search(r"Manufacturer: (.*)", product_block, re.IGNORECASE)
            if not match:
                missing_data.append(f'manufacturer of block {block_no} in category {product_type}')
                raise Exception
            manufacturer = match.group(1).strip()

            #price
            match=re.search(r"Price: (.*)", product_block, re.IGNORECASE)
            if not match:
                missing_data.append(f'price of block {block_no} in category {product_type}')
                raise Exception
            price = match.group(1).split()[0].strip()

            #qty
            match=re.search(r"Quantity: (.*)", product_block, re.IGNORECASE)
            if not match:
                missing_data.append(f'quantity of block {block_no} in category {product_type}')
                raise Exception
            quantity = match.group(1).strip()

            #description
            match=re.search(r"Description: (.*)", product_block, re.IGNORECASE)
            if not match:
                missing_data.append(f'description of block {block_no} in category {product_type}')
                raise Exception
            description = match.group(1).strip()


            #certifications
            match=re.search(r"Certifications: (.+)", product_block, re.IGNORECASE)
            if not match:
                missing_data.append(f'certifications of block {block_no} in category {product_type}')
                raise Exception
            certifications = match.group(1).strip()

            products.append({'id':pid, 'name': product_name, 'manufacturer': manufacturer, 'price': price, 'quantity': quantity, 'description': description, 'certifications': certifications})




        except Exception:
            continue
    #print(missing_data)
    return products


def get_image_url(products):
    for p in products:
        manufacturer = p["manufacturer"]
        product_name = p["name"]
        query = f'{manufacturer} "{product_name}" product'
        params = {
            "engine": "google_images",
            "q": query,
            "api_key": ""
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        images = results.get("images_results", [])
        #print(images[:2])

        if images:
            image_url1 = images[0].get("original")
            #image_url2 = images[1].get("original")
            #print(image_url1)
            p["image1"] = image_url1
            #p["image2"] = image_url2
        else:
            missing_data.append(f'image1 of {product_name} not found')
            p["image1"] = None
            #p["image2"] = None









import pandas

'''product_file=[]
category_id=0
product_lst=[['liquid detergent', 'fabric softener', 'dryer sheets', 'stain remover']]
for product_type in range (len(product_lst)):
    generated_data=generate_data(product_lst[category_id][product_type])
    #print(generated_data)
    product_blocks=generated_data.split("###")
    product_file.append(parse_data(product_blocks,product_type))

print(product_file)'''

category_dict={1:'laundry',2:'cleaning', 3:'misc_household', 4:'stationery', 5:'self_care', 6:'health'}
product_rep=[
    ['liquid detergent', 'fabric softener', 'stain remover'],
    ['All-purpose cleaners','glass cleaner', 'floor cleaners', 'bathroom cleaners', 'sponges', 'dish soap', 'dishwasher detergent'],
    ['Room freshener','toilet paper', 'paper towels'],
    ['pens','pencils', 'markers', 'highlighters', 'notebooks', 'printer paper', 'sticky notes', 'tape', 'erasers', 'sharpeners', 'glue', 'paint brushes'],
    ['Face wash', 'moisturizer', 'sunscreen', 'lip balm', 'shampoo', 'conditioner', 'hairbrushes', 'toothpaste', 'toothbrushes', 'floss', 'mouthwash', 'body wash', 'bar soap', 'deodorant', 'body lotion', 'hand soap'],
    ['bandages', 'general antiseptic', 'thermometers', 'gauze', 'antacids']
]

def create_file(category_id, product_lst):
    product_file=[]
    for product_type in range(len(product_lst)):
        generated_data = generate_data(product_lst[product_type])
        #print(generated_data)
        product_blocks = generated_data.split("###")
        products=parse_data(product_blocks, product_type)
        #print(products)

        get_image_url(products)
        #print(products)
        for prod in products:
           product_file.append(prod)

    file_name=category_dict[category_id]
    df = pandas.DataFrame(product_file)
    #print(df)
    df.to_csv(f"{file_name}.csv", index=False)
    print(f"{file_name}.csv created")

for category_id in category_dict.keys():
    print(category_id, category_dict[category_id])
    create_file(category_id, product_rep[category_id-1])

print("missing_data:", missing_data)

