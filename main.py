import streamlit as st
import os
from streamlit_option_menu import option_menu
import mysql.connector as sql
import easyocr
import cv2
import matplotlib.pyplot as plt
import re
import pandas as pd
import json
import base64


# -------------------------------This is the configuration page for our Streamlit Application---------------------------
st.set_page_config(
    page_title="BizCardX: Extracting Business Card Data with OCR",
    page_icon="📇",
    layout="wide"
)

# -------------------------------This is the sidebar in a Streamlit application, helps in navigation--------------------
with st.sidebar:
    selected = option_menu("Main Menu", ["About Project", "Extract", "Modify"],
                           icons=["house", "gear", "tools"],
                           styles={"nav-link": {"font": "sans serif", "font-size": "20px", "text-align": "centre"},
                                   "nav-link-selected": {"font": "sans serif", "background-color": "#0072b1"},
                                   "icon": {"font-size": "20px"}
                                   }
                           )

# -----------------------------------------Connecting with MySQL Workbench Database------------------------------------
hostname = "localhost"
database = "business_cards"
username = "root"
pwd = ""

db1 = sql.connect(host=hostname,
                  user=username,
                  password=pwd,
                  database=database
                  )
# If buffered is True , the cursor fetches all rows from the server after an operation is executed.
cursor1 = db1.cursor(buffered=True)

# ----------------------------------------Initializing easyocr reader Python package------------------------------------
reader = easyocr.Reader(['en'])

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# -----------------------------------------------About Project Section--------------------------------------------------
if selected == "About Project":
    st.markdown("# :blue[BizCardX: Extracting Business Card Data with OCR]")
    st.markdown('<div style="height: 90px;"></div>', unsafe_allow_html=True)
    st.markdown("### :blue[Technologies :] OCR,streamlit GUI, SQL,Data Extraction")
    st.markdown("### :blue[Overview :] This Streamlit web application enables users to upload images of "
                "business cards and extract pertinent details from them using EasyOCR. Within this app, users "
                "have the capability to view, edit, or remove the extracted data. Additionally, the application "
                "provides the functionality to save the extracted information, along with the uploaded business "
                "card image, into a database. The database can accommodate multiple entries, each containing its "
                "unique business card image and the corresponding extracted information.")

# -----------------------------------------------Extract Data Section---------------------------------------------------
if selected == "Extract":
    st.markdown("# :blue[Data Extraction]")
    st.markdown("### Upload a Business Card")
    imageUploaded = st.file_uploader('Upload your image here', type=["jpeg", "png", "jpg"])

    if imageUploaded is not None:
        current_directory = os.getcwd()
        directory_name = "uploaded_cards"
        file_name = imageUploaded.name

        # Function to process the image and extract data using easyocr
        def ocr_image(image, result):
            for detection in result:
                top_left = tuple(detection[0][0])
                top_left = (int(top_left[0]), int(top_left[1]))
                bottom_right = tuple(detection[0][2])
                bottom_right = (int(bottom_right[0]), int(bottom_right[1]))
                text = detection[1]
                confidence_score = str(detection[2])

                cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

                org = (top_left[0], top_left[1] - 11)
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(image, text, org, font, 0.75, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (17, 17)
            plt.axis('off')
            plt.imshow(image)

        # Display uploaded card before processing
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.write(" ")
            st.markdown("### Uploaded Card before Processing")
            st.image(imageUploaded)

        # Display uploaded card's processed Image with Data Extraction
        with col2:
            st.write(" ")
            with st.spinner("Processing image..."):
                card_img = os.path.join(current_directory, directory_name, file_name)
                image = cv2.imread(card_img)
                result = reader.readtext(card_img)
                st.markdown("### Processed Image with Data Extraction")
                st.set_option('deprecation.showPyplotGlobalUse', False)
                st.pyplot(ocr_image(image, result))

        # Extract text data using easyOCR
        card_img = os.path.join(current_directory, directory_name, file_name)
        result = reader.readtext(card_img, detail=0, paragraph=False)

        # Function to convert image to binary data
        def binaryData_Conversion(f1):
            with open(f1, 'rb') as f1:
                binary_image = f1.read()
            return base64.b64encode(binary_image).decode('utf-8')

        # Initialize data dictionary with empty strings
        data = {
            "company_name": [""],
            "card_holder_name": [""],
            "designation": [""],
            "mobile_phone_number": [""],
            "email_address": [""],
            "website": [""],
            "area": [""],
            "city": [""],
            "state": [""],
            "pincode": [""],
            "image": binaryData_Conversion(card_img)
        }

        def extractData(res):
            for list_index, i in enumerate(res):
                # Website
                if "www " in i.lower() or "www." in i.lower():
                    data["website"][0] = i
                elif "WWW" in i:
                    data["website"][0] = res[4] + "." + res[5]

                # Company Name
                elif i in ["selva", "digitals", "GLOBAL", "INSURANCE", "BORCELLE", "AIRLINES", "Family", "Restaurant", "Sun Electricals"]:
                    data["company_name"][0] = i if not data["company_name"][0] else data["company_name"][0] + " " + i

                # Email Address
                elif "@" in i:
                    data["email_address"][0] = i

                # Designation
                elif list_index == 1:
                    data["designation"][0] = i

                # Card Holder Name
                elif list_index == 0:
                    data["card_holder_name"][0] = i

                # Mobile Phone Number
                elif "-" in i:
                    data["mobile_phone_number"][0] = i if not data["mobile_phone_number"][0] else data["mobile_phone_number"][0] + " and " + i

                # Area
                p1_area = re.findall('^[0-9].+, [a-zA-Z]+', i)
                p2_area = re.findall('^[0-9].+ [a-zA-Z]+', i)
                if p1_area:
                    data["area"][0] = p1_area[0].split(",")[0].strip(" ")
                elif p2_area:
                    data["area"][0] = p2_area[0]

                # City
                p1_city = re.findall('.+St , ([a-zA-Z]+).+', i)
                p2_city = re.findall('^E.*', i)
                p3_city = re.findall('.+St,, ([a-zA-Z]+).+', i)
                if p1_city:
                    data["city"][0] = p1_city[0]
                elif p2_city:
                    data["city"][0] = p2_city[0].strip(',')
                elif p3_city:
                    data["city"][0] = p3_city[0]

                # State
                indian_states = [
                    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam",
                    "Bihar", "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli",
                    "Daman and Diu", "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
                    "Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep",
                    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
                    "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "TamilNadu", "Telangana",
                    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
                ]
                state_pattern = r'\b(?:' + '|'.join(indian_states) + r')\b'
                p1_state = re.findall(state_pattern, i)
                if p1_state:
                    data["state"][0] = p1_state[0]

                # Pincode
                regex_pincode = r'\b\d{6,7}\b'
                p1_pincode = re.findall(regex_pincode, i)
                if p1_pincode:
                    data["pincode"][0] = p1_pincode[0]

        extractData(result)
        df = pd.DataFrame(data)
        st.write(df)
        st.success("##### Data Extraction Successful")

        if st.button("Save Data as JSON"):
            json_data = json.dumps(data, indent=4)
            with open(f"{directory_name}/{file_name.split('.')[0]}_data.json", "w") as json_file:
                json_file.write(json_data)
            st.success("Data saved as JSON successfully!")

        if st.button("Upload to SQL Database"):
            with st.spinner("Uploading..."):
                for index, row in df.iterrows():
                    sql = """INSERT INTO business_card_info VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                    cursor1.execute(sql, tuple(row))
                    db1.commit()
            st.success("##### Data Transfer/Upload Successful")

# ------------------------------------------------Modify Data Section---------------------------------------------------
if selected == "Modify":
    st.markdown("# :blue[Data Modification]")
    try:
        # --------To select a from the select-box particular Business Card-------
        st.markdown("### :orange[Select Card Holder]")
        cursor1.execute("SELECT card_holder_name FROM business_card_info")
        result = cursor1.fetchall()
        # print(result)
        B_cards = [item for sublist in result for item in sublist]
        # print(B_cards)
        selected_card = st.selectbox("Select a name for updating data", B_cards)

        # UPDATING
        # --------To update the data of a particular Business Card-------
        st.markdown("### :orange[Update Card Data]")
        cursor1.execute(
            "SELECT company_name, card_holder_name, designation, mobile_phone_number, email_address, "
            "website, area, city, state, pincode FROM business_card_info "
            "WHERE card_holder_name=%s", (selected_card,))
        result = cursor1.fetchall()

        # -----st.text_input('Header', 'Default text Value') is used here to display the data-----
        company_name = st.text_input("Company_Name", result[0][0])
        card_holder_name = st.text_input("Card_Holder_Name", result[0][1])
        designation = st.text_input("Designation", result[0][2])
        mobile_phone_number = st.text_input("Mobile_Phone_Number", result[0][3])
        email_address = st.text_input("Email_Address", result[0][4])
        website = st.text_input("Website", result[0][5])
        area = st.text_input("Area", result[0][6])
        city = st.text_input("City", result[0][7])
        state = st.text_input("State", result[0][8])
        pincode = st.text_input("PinCode", result[0][9])

        # -----Saving the changes to the SQL Database-----
        if st.button("Click to save the changes in DataBase"):
            cursor1.execute("UPDATE business_card_info SET company_name=%s, card_holder_name=%s, designation=%s, "
                            "mobile_phone_number=%s, email_address=%s, website=%s, area=%s, city=%s, state=%s, "
                            "pincode=%s WHERE card_holder_name=%s ", (company_name, card_holder_name, designation,
                                                                      mobile_phone_number, email_address, website,
                                                                      area, city, state, pincode, selected_card))
            db1.commit()
            st.success("Updated Successfully!!")

        # DELETING
        # --------To delete a particular Business Card that is deleting all data of that business card at once-------
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
        st.markdown("### :orange[Delete a Card]")
        cursor1.execute("SELECT card_holder_name FROM business_card_info")
        result = cursor1.fetchall()
        B_cards = [item for sublist in result for item in sublist]
        selected_card = st.selectbox("Select a card holder name to Delete", B_cards)
        st.write(f"##### Click the below button to confirm the deletion of :red[**{selected_card}'s**] card")

        if st.button("Yes Delete Card"):
            cursor1.execute("DELETE FROM business_card_info WHERE card_holder_name=%s", (selected_card,))
            db1.commit()
            st.success("Successfully Deleted!!")
    except:
        st.warning("Empty Database - No Cards to Display")

    # DISPLAYING FINAL UPDATED DATA
    # ----------To check the final updated data in the SQL database in the form of a dataframe in streamlit App---------
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    st.markdown("### :orange[Updated Data]")
    if st.button("Click to view updated data"):
        cursor1.execute("SELECT company_name, card_holder_name, designation, mobile_phone_number, email_address, "
                        "website, area, city, state, pincode FROM business_card_info")
        df2 = pd.DataFrame(cursor1.fetchall(), columns=["Company_Name", "Card_Holder_Name", "Designation",
                                                        "Mobile_Phone_Number", "Email_Address", "Website",
                                                        "Area", "City", "State", "PinCode"])
        st.write(df2)
