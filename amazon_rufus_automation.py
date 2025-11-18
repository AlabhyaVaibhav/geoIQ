#!/usr/bin/env python3
"""
Amazon Rufus AI Automation Script
Automates interaction with Amazon's Rufus AI assistant to ask questions and capture responses.
"""

import json
import re
import random
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rufus_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AmazonRufusAutomation:
    """Automates interactions with Amazon's Rufus AI assistant."""
    
    def __init__(self, email: str, password: str, headless: bool = False):
        """
        Initialize the automation.
        
        Args:
            email: Amazon account email
            password: Amazon account password
            headless: Run browser in headless mode
        """
        self.email = email
        self.password = password
        self.driver = None
        self.results = []
        self.output_dir = Path("rufus_responses")
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.chrome_options = chrome_options
    
    def start_driver(self):
        """Initialize the Chrome WebDriver."""
        try:
            # Use webdriver-manager to automatically handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            self.driver.maximize_window()
            logger.info("Chrome WebDriver started successfully")
        except Exception as e:
            logger.error(f"Failed to start WebDriver: {e}")
            raise
    
    def login(self) -> bool:
        """
        Log into Amazon.com.
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            logger.info("Navigating to Amazon.com...")
            self.driver.get("https://www.amazon.com")
            time.sleep(3)
            
            # Check if already logged in
            if self._is_logged_in():
                logger.info("Already logged in!")
                return True
            
            # Click on "Hello, sign in" / "Your Account" link to open sign-in page
            logger.info("Clicking on 'Hello, sign in' / 'Your Account' link...")
            try:
                # Find the account list link (shows "Hello, sign in" when not logged in)
                account_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "nav-link-accountList"))
                )
                
                # Verify it says "Hello, sign in" (not logged in)
                link_text = account_link.text.strip().lower()
                if "sign in" in link_text:
                    logger.info("Found 'Hello, sign in' link, clicking...")
                    # Scroll into view if needed
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", account_link)
                    time.sleep(0.5)
                    
                    # Click the link - this should navigate to sign-in page
                    account_link.click()
                    time.sleep(3)
                    
                    # Check if a dropdown menu appeared instead of navigation
                    # Look for sign-in link in dropdown
                    try:
                        signin_dropdown = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-nav-ref='nav_ya_signin'], #nav-flyout-accountList a[href*='signin']"))
                        )
                        if signin_dropdown.is_displayed():
                            logger.info("Dropdown menu detected, clicking sign-in link in dropdown...")
                            signin_dropdown.click()
                            time.sleep(3)
                    except TimeoutException:
                        # No dropdown, navigation should have happened
                        pass
                        
                else:
                    # Might already be logged in or link text changed
                    logger.info(f"Link text: {link_text}, checking if logged in...")
                    if self._is_logged_in():
                        logger.info("Already logged in!")
                        return True
                    # Try clicking anyway
                    account_link.click()
                    time.sleep(3)
                    
            except TimeoutException:
                logger.warning("Could not find 'nav-link-accountList', trying direct navigation...")
                # Fallback: navigate directly to sign-in page
                signin_url = "https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2Fgp%2Fcss%2Fhomepage.html%2Fref%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
                self.driver.get(signin_url)
                time.sleep(3)
            
            # Check if we're on a sign-in page or if already logged in
            if self._is_logged_in():
                logger.info("Already logged in after clicking sign-in link!")
                return True
            
            # Wait for sign-in page to load
            logger.info("Waiting for sign-in page to load...")
            time.sleep(2)
            
            # Try multiple selectors for email input
            email_input = None
            email_selectors = [
                (By.ID, "ap_email"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input#ap_email"),
            ]
            
            for selector_type, selector_value in email_selectors:
                try:
                    email_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"Found email input using {selector_type}: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not email_input:
                logger.error("Could not find email input field")
                logger.info("Current URL: " + self.driver.current_url)
                logger.info("Page title: " + self.driver.title)
                # Take a screenshot for debugging
                self.driver.save_screenshot("login_error_email_field.png")
                return False
            
            # Enter email
            logger.info("Entering email...")
            email_input.clear()
            email_input.click()
            time.sleep(0.5)
            email_input.send_keys(self.email)
            time.sleep(1)
            
            # Find and click continue/submit button
            continue_selectors = [
                (By.ID, "continue"),
                (By.CSS_SELECTOR, "input#continue"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
            ]
            
            continue_button = None
            for selector_type, selector_value in continue_selectors:
                try:
                    continue_button = self.driver.find_element(selector_type, selector_value)
                    if continue_button.is_displayed() and continue_button.is_enabled():
                        logger.info(f"Found continue button using {selector_type}: {selector_value}")
                        break
                except NoSuchElementException:
                    continue
            
            if continue_button:
                continue_button.click()
            else:
                # Try pressing Enter
                email_input.send_keys(Keys.RETURN)
            
            time.sleep(3)
            
            # Check for CAPTCHA or other challenges
            if self._check_for_captcha():
                logger.warning("CAPTCHA detected! Please solve it manually and press Enter to continue...")
                input("Press Enter after solving CAPTCHA...")
                time.sleep(2)
            
            # Check for 2FA or OTP
            if self._check_for_2fa():
                logger.warning("2FA/OTP detected! Please enter the code manually.")
                input("Press Enter after entering 2FA code...")
                time.sleep(2)
            
            # Enter password
            password_selectors = [
                (By.ID, "ap_password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input#ap_password"),
            ]
            
            password_input = None
            for selector_type, selector_value in password_selectors:
                try:
                    password_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"Found password input using {selector_type}: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not password_input:
                logger.error("Could not find password input field")
                logger.info("Current URL: " + self.driver.current_url)
                self.driver.save_screenshot("login_error_password_field.png")
                return False
            
            logger.info("Entering password...")
            password_input.clear()
            password_input.click()
            time.sleep(0.5)
            password_input.send_keys(self.password)
            time.sleep(1)
            
            # Find and click sign-in button
            signin_selectors = [
                (By.ID, "signInSubmit"),
                (By.CSS_SELECTOR, "input#signInSubmit"),
                (By.CSS_SELECTOR, "input[type='submit'][name='rememberMe']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
            ]
            
            signin_button = None
            for selector_type, selector_value in signin_selectors:
                try:
                    signin_button = self.driver.find_element(selector_type, selector_value)
                    if signin_button.is_displayed() and signin_button.is_enabled():
                        logger.info(f"Found sign-in button using {selector_type}: {selector_value}")
                        break
                except NoSuchElementException:
                    continue
            
            if signin_button:
                signin_button.click()
            else:
                password_input.send_keys(Keys.RETURN)
            
            time.sleep(5)
            
            # Check for login errors
            error_messages = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".a-alert-content, .a-box-inner.a-alert-container, #auth-error-message-box"
            )
            if error_messages:
                for error in error_messages:
                    if error.is_displayed() and error.text.strip():
                        logger.error(f"Login error detected: {error.text}")
                        self.driver.save_screenshot("login_error_message.png")
                        return False
            
            # Navigate back to home page and verify login
            logger.info("Verifying login...")
            self.driver.get("https://www.amazon.com")
            time.sleep(3)
            
            if self._is_logged_in():
                logger.info("Login successful!")
                return True
            else:
                logger.error("Login verification failed - not logged in")
                self.driver.save_screenshot("login_verification_failed.png")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            try:
                self.driver.save_screenshot("login_exception.png")
                logger.info(f"Current URL: {self.driver.current_url}")
                logger.info(f"Page title: {self.driver.title}")
            except:
                pass
            return False
    
    def _is_logged_in(self) -> bool:
        """Check if user is logged into Amazon."""
        try:
            # Check for account list link (logged in indicator)
            account_link = self.driver.find_element(By.ID, "nav-link-accountList")
            # Check if it shows "Hello, Sign in" (not logged in) or account name (logged in)
            link_text = account_link.text.strip().lower()
            if "sign in" in link_text and "hello" in link_text:
                return False
            # If we can find the element and it doesn't say "Sign in", we're likely logged in
            # Additional check: look for cart or orders
            try:
                self.driver.find_element(By.ID, "nav-cart")
                return True
            except NoSuchElementException:
                # Try checking URL - if we're redirected away from sign-in, we might be logged in
                current_url = self.driver.current_url.lower()
                if "signin" not in current_url and "ap/" not in current_url:
                    return True
                return False
        except NoSuchElementException:
            return False
    
    def _check_for_captcha(self) -> bool:
        """Check if CAPTCHA is present on the page."""
        captcha_indicators = [
            "captcha",
            "robot",
            "verify you're human",
            "unusual activity"
        ]
        page_text = self.driver.page_source.lower()
        page_title = self.driver.title.lower()
        
        for indicator in captcha_indicators:
            if indicator in page_text or indicator in page_title:
                return True
        
        # Check for common CAPTCHA elements
        captcha_selectors = [
            "iframe[title*='captcha']",
            "iframe[title*='challenge']",
            ".a-box.a-alert-inline.a-alert-inline-error"
        ]
        
        for selector in captcha_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    return True
            except NoSuchElementException:
                continue
        
        return False
    
    def _check_for_2fa(self) -> bool:
        """Check if 2FA/OTP input is required."""
        otp_indicators = [
            "enter code",
            "verification code",
            "one-time password",
            "otp",
            "two-step"
        ]
        page_text = self.driver.page_source.lower()
        
        for indicator in otp_indicators:
            if indicator in page_text:
                return True
        
        # Check for OTP input field
        try:
            otp_input = self.driver.find_element(
                By.CSS_SELECTOR, 
                "input[name*='otp'], input[name*='code'], input#auth-mfa-otpcode"
            )
            if otp_input.is_displayed():
                return True
        except NoSuchElementException:
            pass
        
        return False
    
    def find_rufus_button(self) -> bool:
        """
        Find and click the Rufus AI button on the home page.
        
        Returns:
            True if button found and clicked, False otherwise
        """
        try:
            logger.info("Looking for Rufus AI button...")
            
            # Wait for the page to load
            time.sleep(3)
            
            # Try to find the Rufus button by ID
            try:
                rufus_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "nav-rufus-disco"))
                )
                logger.info("Found Rufus button by ID")
                rufus_button.click()
                time.sleep(3)
                return True
            except TimeoutException:
                pass
            
            # Try to find by class name
            try:
                rufus_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "nav-rufus-disco"))
                )
                logger.info("Found Rufus button by class")
                rufus_button.click()
                time.sleep(3)
                return True
            except TimeoutException:
                pass
            
            # Try CSS selector
            try:
                rufus_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.nav-rufus-disco"))
                )
                logger.info("Found Rufus button by CSS selector")
                rufus_button.click()
                time.sleep(3)
                return True
            except TimeoutException:
                logger.error("Could not find Rufus button")
                return False
                
        except Exception as e:
            logger.error(f"Error finding Rufus button: {e}")
            return False
    
    def ask_question(self, question: str) -> Optional[Dict]:
        """
        Ask a question in the Rufus chat window and capture the response.
        
        Args:
            question: The question to ask
            
        Returns:
            Dictionary containing question and response, or None if failed
        """
        try:
            logger.info(f"Asking question: {question}")
            
            # Add random delay of 3-5 seconds before asking (to avoid rate limiting)
            delay = random.uniform(3, 5)
            logger.info(f"Waiting {delay:.1f} seconds before asking question...")
            time.sleep(delay)
            
            # Find the textarea for asking questions
            textarea = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "rufus-text-area"))
            )
            
            # Clear and type the question
            textarea.clear()
            time.sleep(0.5)  # Small delay before typing
            textarea.send_keys(question)
            time.sleep(1)
            
            # Submit the question (press Enter)
            textarea.send_keys(Keys.RETURN)
            logger.info("Question submitted, waiting for response...")
            
            # Wait for response to appear
            time.sleep(5)
            
            # Wait for conversation turn container to appear
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "conversation-turn-container"))
                )
            except TimeoutException:
                logger.warning("Response container not found, waiting longer...")
                time.sleep(10)
            
            # Wait for response to fully load, including products
            self._wait_for_response_complete()
            
            # Extract the response text
            response_text = self.extract_response()
            
            # Extract products (ASIN cards)
            products = self.extract_products()
            logger.info(f"Found {len(products)} products in response")
            
            # Extract follow-up questions
            followup_questions = self.extract_followup_questions()
            logger.info(f"Found {len(followup_questions)} follow-up questions")
            
            result = {
                "question": question,
                "response": response_text,
                "products": products,
                "followup_questions": followup_questions,
                "timestamp": datetime.now().isoformat(),
                "raw_html": self.driver.page_source[:5000]  # Store first 5000 chars of HTML
            }
            
            self.results.append(result)
            logger.info(f"Response captured for question: {question[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Error asking question '{question}': {e}")
            return None
    
    def _wait_for_response_complete(self):
        """
        Wait for the response to be fully loaded, including all products.
        Checks for loading indicators and waits for products to appear.
        """
        max_wait_time = 30
        check_interval = 2
        waited = 0
        
        while waited < max_wait_time:
            try:
                # Check if there are any "Thinking..." or "Gathering products..." indicators
                page_text = self.driver.page_source.lower()
                if "thinking..." in page_text or "gathering products..." in page_text:
                    logger.info("Still loading, waiting...")
                    time.sleep(check_interval)
                    waited += check_interval
                    continue
                
                # Check if ASIN cards are still loading
                # Look for ASIN card containers
                asin_containers = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    ".rufus-sections-container[data-section-class='AsinFaceoutList']"
                )
                
                if asin_containers:
                    # Check if products have loaded (have titles)
                    products_loaded = 0
                    for container in asin_containers:
                        try:
                            # Check if product cards exist and have titles
                            cards = container.find_elements(By.CLASS_NAME, "rufus-asin-faceout")
                            for card in cards:
                                try:
                                    card.find_element(By.CSS_SELECTOR, "h2.a-size-base")
                                    products_loaded += 1
                                except NoSuchElementException:
                                    pass
                        except:
                            pass
                    
                    # If we found containers but no products yet, wait a bit more
                    if len(asin_containers) > 0 and products_loaded == 0:
                        logger.info("ASIN containers found but products not loaded yet, waiting...")
                        time.sleep(check_interval)
                        waited += check_interval
                        continue
                
                # If we get here, response seems complete
                break
                
            except Exception as e:
                logger.warning(f"Error checking response completion: {e}")
                time.sleep(check_interval)
                waited += check_interval
        
        # Final wait to ensure everything is rendered
        time.sleep(2)
        logger.info("Response loading check complete")
    
    def extract_products(self) -> List[Dict]:
        """
        Extract all product information from ASIN cards.
        
        Returns:
            List of product dictionaries with details
        """
        products = []
        
        try:
            # Find all conversation turn containers
            conversation_turns = self.driver.find_elements(
                By.CLASS_NAME, "conversation-turn-container"
            )
            
            if not conversation_turns:
                return products
            
            # Get the latest conversation turn
            latest_turn = conversation_turns[-1]
            
            # Find all ASIN card containers
            asin_containers = latest_turn.find_elements(
                By.CSS_SELECTOR,
                ".rufus-sections-container[data-section-class='AsinFaceoutList']"
            )
            
            for container in asin_containers:
                # Extract section header if present
                section_header = None
                try:
                    header = container.find_element(
                        By.CSS_SELECTOR, ".rufus-asin-faceout-header-left"
                    )
                    section_header = header.text.strip()
                except NoSuchElementException:
                    pass
                
                # Find all product cards in this container
                product_cards = container.find_elements(
                    By.CLASS_NAME, "rufus-asin-faceout"
                )
                
                for card in product_cards:
                    try:
                        product = {}
                        
                        # Extract ASIN from data attributes or URL
                        try:
                            # Try to get ASIN from the link
                            link = card.find_element(
                                By.CSS_SELECTOR, "a[href*='/dp/']"
                            )
                            href = link.get_attribute("href")
                            # Extract ASIN from URL like /dp/B0BJXH83RN
                            asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
                            if asin_match:
                                product["asin"] = asin_match.group(1)
                        except:
                            pass
                        
                        # Extract product title
                        try:
                            title_elem = card.find_element(
                                By.CSS_SELECTOR, "h2.a-size-base, h2[aria-label]"
                            )
                            product["title"] = title_elem.text.strip()
                            # Also get aria-label if available (more complete)
                            aria_label = title_elem.get_attribute("aria-label")
                            if aria_label and len(aria_label) > len(product["title"]):
                                product["title"] = aria_label
                        except NoSuchElementException:
                            product["title"] = "Unknown"
                        
                        # Extract price
                        try:
                            price_elem = card.find_element(
                                By.CSS_SELECTOR, ".a-price .a-offscreen, .a-price"
                            )
                            product["price"] = price_elem.text.strip()
                        except NoSuchElementException:
                            product["price"] = None
                        
                        # Extract rating
                        try:
                            rating_elem = card.find_element(
                                By.CSS_SELECTOR, ".a-size-small.a-color-base"
                            )
                            product["rating"] = rating_elem.text.strip()
                        except NoSuchElementException:
                            product["rating"] = None
                        
                        # Extract review count
                        try:
                            review_link = card.find_element(
                                By.CSS_SELECTOR, "a[aria-label*='ratings'], a[aria-label*='rating']"
                            )
                            review_text = review_link.get_attribute("aria-label")
                            product["review_count"] = review_text
                        except NoSuchElementException:
                            product["review_count"] = None
                        
                        # Extract product image URL
                        try:
                            img = card.find_element(By.CSS_SELECTOR, "img.s-image")
                            product["image_url"] = img.get_attribute("src")
                        except NoSuchElementException:
                            product["image_url"] = None
                        
                        # Extract product URL
                        try:
                            link = card.find_element(By.CSS_SELECTOR, "a[href*='/dp/']")
                            product["url"] = link.get_attribute("href")
                        except NoSuchElementException:
                            product["url"] = None
                        
                        # Extract footer description
                        try:
                            footer = card.find_element(
                                By.CLASS_NAME, "rufus-asin-faceout-footer"
                            )
                            product["description"] = footer.text.strip()
                        except NoSuchElementException:
                            product["description"] = None
                        
                        # Extract delivery information
                        try:
                            delivery = card.find_element(
                                By.CSS_SELECTOR, ".udm-primary-delivery-message"
                            )
                            product["delivery"] = delivery.text.strip()
                        except NoSuchElementException:
                            product["delivery"] = None
                        
                        # Add section header if available
                        if section_header:
                            product["section_header"] = section_header
                        
                        products.append(product)
                        
                    except Exception as e:
                        logger.warning(f"Error extracting product details: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error extracting products: {e}")
        
        return products
    
    def extract_followup_questions(self) -> List[str]:
        """
        Extract follow-up question buttons/pills from the response.
        
        Returns:
            List of follow-up question texts
        """
        followup_questions = []
        
        try:
            # Find all conversation turn containers
            conversation_turns = self.driver.find_elements(
                By.CLASS_NAME, "conversation-turn-container"
            )
            
            if not conversation_turns:
                return followup_questions
            
            # Get the latest conversation turn
            latest_turn = conversation_turns[-1]
            
            # Find all follow-up question pills
            # These are in a carousel with class "rufus-pill"
            try:
                pills = latest_turn.find_elements(
                    By.CSS_SELECTOR, ".rufus-pill, button.rufus-pill"
                )
                
                for pill in pills:
                    try:
                        # Get the text from the pill
                        pill_text = pill.text.strip()
                        if pill_text:
                            followup_questions.append(pill_text)
                    except:
                        pass
                
                # Also try to find pills by their specific structure
                if not followup_questions:
                    pill_elements = latest_turn.find_elements(
                        By.CSS_SELECTOR, 
                        ".rufus-related-question-pill, .rufus-carousel-card .rufus-pill"
                    )
                    for pill in pill_elements:
                        try:
                            text = pill.text.strip()
                            if text:
                                followup_questions.append(text)
                        except:
                            pass
                            
            except NoSuchElementException:
                pass
            
        except Exception as e:
            logger.error(f"Error extracting follow-up questions: {e}")
        
        return followup_questions
    
    def extract_response(self) -> str:
        """
        Extract the response text from the Rufus conversation pane.
        
        Returns:
            Extracted response text
        """
        try:
            response_parts = []
            
            # Find all conversation turn containers
            conversation_turns = self.driver.find_elements(
                By.CLASS_NAME, "conversation-turn-container"
            )
            
            if not conversation_turns:
                logger.warning("No conversation turns found")
                return ""
            
            # Get the latest conversation turn (last one)
            latest_turn = conversation_turns[-1]
            
            # Extract customer question text
            try:
                customer_text = latest_turn.find_element(
                    By.CLASS_NAME, "rufus-customer-text-wrap"
                ).text
                response_parts.append(f"Question: {customer_text}")
            except NoSuchElementException:
                pass
            
            # Extract text subsections (main response text)
            try:
                text_subsections = latest_turn.find_elements(
                    By.CLASS_NAME, "rufus-text-subsections-with-avatar-branding-update"
                )
                for subsection in text_subsections:
                    text = subsection.text.strip()
                    if text:
                        response_parts.append(text)
            except NoSuchElementException:
                pass
            
            # Extract ASIN card information (product recommendations)
            try:
                asin_cards = latest_turn.find_elements(
                    By.CLASS_NAME, "rufus-asin-faceout"
                )
                for card in asin_cards:
                    try:
                        title = card.find_element(
                            By.CSS_SELECTOR, "h2.a-size-base"
                        ).text
                        price = card.find_element(
                            By.CSS_SELECTOR, ".a-price"
                        ).text
                        footer = card.find_element(
                            By.CLASS_NAME, "rufus-asin-faceout-footer"
                        ).text
                        response_parts.append(f"Product: {title} - {price}\n{footer}")
                    except NoSuchElementException:
                        pass
            except NoSuchElementException:
                pass
            
            # Extract footer text
            try:
                footer_text = latest_turn.find_element(
                    By.CLASS_NAME, "rufus-asin-faceout-footer"
                ).text
                if footer_text:
                    response_parts.append(footer_text)
            except NoSuchElementException:
                pass
            
            # If no structured data found, try to get all text
            if not response_parts:
                response_parts.append(latest_turn.text)
            
            return "\n\n".join(response_parts) if response_parts else "No response captured"
            
        except Exception as e:
            logger.error(f"Error extracting response: {e}")
            return f"Error extracting response: {str(e)}"
    
    def ask_questions(self, questions: List[str]) -> List[Dict]:
        """
        Ask multiple questions sequentially.
        
        Args:
            questions: List of questions to ask
            
        Returns:
            List of results for each question
        """
        results = []
        
        for i, question in enumerate(questions, 1):
            logger.info(f"Processing question {i}/{len(questions)}")
            result = self.ask_question(question)
            if result:
                results.append(result)
            
            # Wait between questions to avoid rate limiting
            if i < len(questions):
                time.sleep(3)
        
        return results
    
    def save_results(self, filename: Optional[str] = None):
        """
        Save captured results to a JSON file.
        
        Args:
            filename: Optional custom filename
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rufus_responses_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_questions": len(self.results),
            "results": self.results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {filepath}")
        return filepath
    
    def close(self):
        """Close the browser and cleanup."""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Amazon Rufus AI Automation")
    parser.add_argument("--email", help="Amazon account email (required unless using --manual-login)")
    parser.add_argument("--password", help="Amazon account password (required unless using --manual-login)")
    parser.add_argument("--questions-file", default="questions.txt", 
                       help="File containing questions to ask (one per line)")
    parser.add_argument("--headless", action="store_true", 
                       help="Run browser in headless mode")
    parser.add_argument("--output", help="Output filename for results")
    parser.add_argument("--manual-login", action="store_true",
                       help="Pause for manual login instead of automated login")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.manual_login:
        if not args.email or not args.password:
            parser.error("--email and --password are required unless using --manual-login")
    
    # Load questions from file
    questions = []
    questions_file = Path(args.questions_file)
    if questions_file.exists():
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = [line.strip() for line in f if line.strip()]
    else:
        logger.warning(f"Questions file {args.questions_file} not found. Using default questions.")
        questions = [
            "What are the best 2-liter sodas for Thanksgiving dinner that stay fizzy the longest?",
            "Show me carbonation saver products",
            "Best sodas for holiday parties",
            "Compare regular vs diet fizz retention"
        ]
    
    if not questions:
        logger.error("No questions to ask!")
        return
    
    # Initialize automation
    automation = AmazonRufusAutomation(
        email=args.email or "dummy@example.com",  # Dummy value if manual login
        password=args.password or "dummy",  # Dummy value if manual login
        headless=args.headless
    )
    
    try:
        # Start browser
        automation.start_driver()
        
        # Login
        if args.manual_login:
            logger.info("Manual login mode: Please log in manually in the browser.")
            logger.info("Once logged in, press Enter to continue...")
            input("Press Enter after logging in...")
            time.sleep(2)
            
            # Verify login
            automation.driver.get("https://www.amazon.com")
            time.sleep(3)
            if not automation._is_logged_in():
                logger.error("Login verification failed. Please ensure you're logged in.")
                return
            logger.info("Manual login verified!")
        else:
            if not automation.login():
                logger.error("Failed to login. Exiting.")
                logger.info("Tip: Try using --manual-login flag to log in manually")
                return
        
        # Find and click Rufus button
        if not automation.find_rufus_button():
            logger.error("Failed to find Rufus button. Exiting.")
            return
        
        # Ask questions
        logger.info(f"Starting to ask {len(questions)} questions...")
        automation.ask_questions(questions)
        
        # Save results
        automation.save_results(args.output)
        
        logger.info("Automation completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        automation.close()


if __name__ == "__main__":
    main()

