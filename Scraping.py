from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import pandas as pd

# Initialize the driver
driver = webdriver.Chrome()
driver.maximize_window()
driver.get("https://www.naukri.com/")
time.sleep(2)

# Function to handle reload in case of an error page


def handle_error_page():
    try:
        # Check if the reload button is present
        reload_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'Reload')]"))
        )
        print("Error page detected! Reloading...")
        reload_button.click()
        time.sleep(5)  # Allow time for the page to reload
        return True  # Indicate that a reload occurred
    except Exception:
        return False  # No error page detected


# Function to perform actions with error checking
def perform_action_with_error_check(action_func, *args, **kwargs):
    while True:
        try:
            # Execute the action
            return action_func(*args, **kwargs)
        except Exception as e:
            print(f"Action error: {e}. Checking for reload error...")
            if not handle_error_page():
                raise e  # If no reload error is found, re-raise the original exception


# Search for jobs
search_bar = perform_action_with_error_check(
    WebDriverWait(driver, 10).until,
    EC.presence_of_element_located((By.XPATH, "//input[@class='suggestor-input ']"))
)
search_bar.send_keys("Jobs")
search_bar.send_keys(Keys.RETURN)

# Apply filters
filters = [
    "//span[@title='Work from office']",
    "//span[@title='Hybrid']",
    "//span[@title='Remote']",
    "//span[@title='B.Tech/B.E.']"
]

for filter_xpath in filters:
    try:
        filter_element = perform_action_with_error_check(
            WebDriverWait(driver, 30).until,
            EC.element_to_be_clickable((By.XPATH, filter_xpath))
        )
        filter_element.click()
        time.sleep(2)
    except Exception as e:
        print(f"Error applying filter: {e}")

# Scrape job details
job_details = []
page_number = 1  # Initialize page counter
max_jobs = 40  # Set maximum number of jobs to collect

while True:
    # Check if the maximum number of jobs has been collected
    if len(job_details) >= max_jobs:
        print(f"Collected {max_jobs} jobs. Stopping scraping process.")
        break

    try:
        # Handle error page before attempting to scrape
        handle_error_page()

        # Wait for job cards to load
        job_roles = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='srp-jobtuple-wrapper']"))
        )

        page_jobs = []  # Temporary storage for current page jobs
        for job_role in job_roles:
            try:
                # Scrape details for each job
                title = job_role.find_element(By.XPATH, ".//div[@class=' row1']/h2/a").text
                company = WebDriverWait(job_role, 10).until(
                    EC.presence_of_element_located((By.XPATH, ".//a[@class=' comp-name mw-25']"))
                ).text
                experience = job_role.find_element(By.XPATH, ".//span[@class='expwdth']").text
                salary = job_role.find_element(By.XPATH, ".//span[@class='sal-wrap ver-line']").text
                location = job_role.find_element(By.XPATH, ".//span[@class='loc-wrap ver-line']").text
                desc = job_role.find_element(By.XPATH, ".//div[@class=' row4']/span").text
                tags_elements = job_role.find_elements(By.XPATH, ".//div[@class=' row5']/ul/li")
                tags = ", ".join(tag.text for tag in tags_elements)
                posting_day = job_role.find_element(By.XPATH, ".//span[@class='job-post-day ']").text
                job_link = job_role.find_element(By.XPATH, ".//a[@class='title ']").get_attribute("href")

                # Add to job details
                job = {
                    "Title": title,
                    "Company": company,
                    "Experience": experience,
                    "Salary": salary,
                    "Location": location,
                    "Description": desc,
                    "Tags": tags,
                    "Posting Day": posting_day,
                    "job_link": job_link
                }
                job_details.append(job)
                page_jobs.append(job)
            except Exception as e:
                print(f"Error extracting job details: {e}")

        # Print all job details for the current page with page number
        print(f"Jobs on Page {page_number}:")
        for i, job in enumerate(page_jobs, start=1):
            print(f"Job {i}: {job}")
        print("-" * 100)

        # Navigate to the next page
        try:
            next_page = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@class='styles_btn-secondary__2AsIP']"))
            )
            next_page.click()
            page_number += 1  # Increment page number
            time.sleep(5)  # Allow time for the next page to load
        except Exception as e:
            print("No more pages or unable to navigate to the next page:", e)
            break  # Exit loop if no more pages

    except Exception as e:
        print(f"Error loading job roles: {e}")
        break  # Exit loop in case of critical error

# Save the data to a CSV file
df = pd.DataFrame(job_details)
df.to_csv("scrape.csv", index=False, encoding="utf-8")
print("Data saved to scrape.csv")
print(f"Total jobs collected: {len(job_details)}")

# Close the driver
driver.quit()