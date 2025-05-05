from dotenv import load_dotenv
from exceptions import MissingAgentException
from exceptions import MissingLocalityException
from exceptions import MissingOwnerException
from exceptions import MissingPriceException
from exceptions import MissingTypeException
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import csv
import db
import MiogestObject
import os
import time

load_dotenv()

MIOGEST_MAPPING_FILE = 'miogest_mapping.csv'
MIOGEST_USERNAME = os.getenv("MIOGEST_USERNAME")
MIOGEST_PASSWORD = os.getenv("MIOGEST_PASSWORD")

if not MIOGEST_USERNAME or not MIOGEST_PASSWORD:
    raise ValueError("Miogest credentials are missing. Please check your .env file.")

# Load Miogest mapping
def load_mapping(file_path):
    mapping = {}
    with open(file_path, mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            mapping[row['Code']] = row['Email']
    return mapping

MIOGEST_MAPPING_FILE = 'miogest_mapping.csv'
miogest_mapping = load_mapping(MIOGEST_MAPPING_FILE)

def login(driver):
    try:
        # Step 1: Open Miogest Login Page
        driver.get("https://go.miogest.com")
        time.sleep(2)  # Wait for the page to load

        # Step 2: Insert zenit code
        try:
            input_field = driver.find_element(By.ID, "tcod")  # Locate input field by ID
            input_field.clear()  # Clear the input field, if necessary
            input_field.send_keys("zenitre")  # Type the text into the input field
            input_field.send_keys(Keys.RETURN)  # Simulate pressing Enter
            print("Text entered and Enter key pressed successfully!")
        except Exception as e:
            print(f"Error during zenit code entry: {e}")

        time.sleep(3)  # Wait for the access to complete

        # Step 3: Log In
        username = driver.find_element(By.ID, "tuid")  # The ID of the 'username' input field 
        password = driver.find_element(By.ID, "tpwd")  # The ID of the 'password' input field
        login_button = driver.find_element(By.ID, "btn2")  # The ID of the 'Access' button

        # Dismiss cookie banner or overlay if present
        try:
            cookie_banner = driver.find_element(By.ID, "didomi-notice")
            close_button = cookie_banner.find_element(By.TAG_NAME, "button")
            close_button.click()
            print("Dismissed cookie banner.")
            time.sleep(1)
        except Exception as e:
            print("No cookie banner found or failed to dismiss it.")

        username.send_keys(MIOGEST_USERNAME)  # My Miogest user
        password.send_keys(MIOGEST_PASSWORD)  # My Miogest password
        print("Inserted values")
        login_button.click()
        print("Clicked Login button")

        time.sleep(5)  # Wait for the login to complete

        # Step 4: Navigate to Announcements
        driver.get("https://go.miogest.com/Desk/Annunci/")
        print("Successfully logged in to miogest")
        time.sleep(5)
    except Exception as e:
        print(f"Error during login: {e}") 

def insert_announcement_code(driver, reference):
    
    try:
        # Step 5: Abilitate also expired announcements
        dropdown_options = driver.find_element(By.ID, "fl_ann_off_tit")
        dropdown_options.click()
        time.sleep(1)  # Wait for the dropdown to load

        sospeso_checkbox = driver.find_element(By.XPATH, "//label[@id='fl_ann_off_t0']")
        sospeso_checkbox.click()
        time.sleep(1)

        venduto_checkbox = driver.find_element(By.XPATH, "//label[@id='fl_ann_off_t4']")
        venduto_checkbox.click()
        time.sleep(1)

        # Step 6: Extract Announcements
        announcement_code = driver.find_element(By.ID, "fl_ann_cod")
        announcement_code.clear()
        announcement_code.send_keys(reference)
        announcement_code.send_keys(Keys.RETURN)
        time.sleep(3)
    except Exception as e:
        print(f"Error insertion of code: {e}") 

def find_agents(driver, reference):
    codes = []
    print('Started looking for agent code')
    
    login(driver)
    
    insert_announcement_code(driver, reference)

    try:
        # Step 7: Locate the agent code in the announcement table
        td_element = driver.find_element(By.ID, "cel_ann_0_2")
        
        label_elements = td_element.find_elements(By.XPATH, "./div[2]/label")
        label_count = len(label_elements) + 1
        print(f'found {label_count} labels')

        i = 2
        while i < label_count:
            try:
                agent_code_label = td_element.find_element(By.XPATH, f"./div[2]/label[{i}]")  # i-th <label> inside the second <div>
                code = agent_code_label.text
                print(f"Agent Code number {i-1} Found: {code}")
                codes.append(code)
                i += 1
            except Exception as e:
                print(f"Failed to find agent code: {e}")
                break
        for i in range(len(codes)):
            print(f"codes[{i}] = {codes[i]}")
    except NoSuchElementException as e:
        print(f"Element not found: {e}")
    except WebDriverException as e:
        print(f"WebDriver error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Ensure the WebDriver is always closed
        driver.quit()
    return codes

def find_miogest_object(reference):
    try:
        # Configure the WebDriver
        driver = webdriver.Chrome()  # Make sure you have ChromeDriver installed
        driver.maximize_window()
        
        codes = find_agents(driver, reference)

        # Configure the WebDriver
        driver = webdriver.Chrome()  # Make sure you have ChromeDriver installed
        driver.maximize_window()
        
        login(driver)
        
        insert_announcement_code(driver, reference)
        
        if not codes:
            return None

        # Try to fetch the type (for rent/sale)
        try:
            miogest_type_cell = driver.find_element(By.ID, "cel_ann_0_4").find_element(By.XPATH, "./div[1]/strong")
            miogest_type = miogest_type_cell.text != 'Vendita'
        except NoSuchElementException:
            miogest_address = "Tipo ignoto"
            raise MissingTypeException("Type information not found in the announcement.")

        # Try to fetch the locality
        try:
            miogest_address = driver.find_element(By.ID, "cel_ann_0_5").find_element(By.XPATH, "./div[1]/strong").text
        except NoSuchElementException:
            miogest_address = "Località sconosciuta"
            raise MissingLocalityException("Locality information not found in the announcement.")

        # Try to fetch the owner
        try:
            miogest_owner = driver.find_element(By.ID, "cel_ann_0_6").find_element(By.XPATH, "./div[1]/div[2]/a/strong").text
        except NoSuchElementException:
            miogest_owner = "Proprietario sconosciuto"
            if "Località sconosciuta" in miogest_address:
                raise MissingOwnerException("Owner information not found in the announcement.")

        # Try to fetch the price
        try:
            miogest_price = driver.find_element(By.ID, "cel_ann_0_8").text
        except NoSuchElementException:
            miogest_price = "Prince unknown"
            raise MissingPriceException("Price information not found in the announcement.")

        # Create and return the MiogestObject
        return MiogestObject.MiogestObject(
            code=reference,
            locality=miogest_address,
            owner=miogest_owner,
            price=miogest_price,
            for_rent=miogest_type,
            requests_count=1,
            sellers=codes
        )
    except Exception as e:
        print(f"Error in find_miogest_object: {e}")
        return None
    finally:
        # Ensure the WebDriver is always closed
        driver.quit()

def get_agent_emails_from_list(codes):
    recipients = []
    for code in codes:
        if code:
            if code in miogest_mapping:
                recipients.append(miogest_mapping[code])
            else:
                print(f"Code '{code}' not found in Miogest mapping.")
                return None
        else:
            print("No agent code found.")
            return None
    if not recipients:
        return None
    if len(recipients) == 1:
        return recipients
    if recipients[0] == 'Marco' or recipients[0] == 'Angelo':
        return recipients
    return recipients


# recipients = find_miogest_object("V000842")
# print(f'Recipients: {recipients}')